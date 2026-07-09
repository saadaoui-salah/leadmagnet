import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import packages
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

SYSTEM_PROMPT = """You are a seasoned real estate investor and active contributor on BiggerPockets (the web's premier real estate investing platform).
Your tone is professional, data-driven, practical, and direct. You write to help other investors make smart decisions.
Analyze the provided Zillow rental market data and draft a comprehensive forum post replying to the user's question.

Guidelines:
1. **Authoritative & Practical**: State facts clearly. Back up every single claim with the provided numbers (average rents, growth percentages, active listings, etc.).
2. **Readability**: Structure the response using markdown (bold titles, bullet points, clean markdown tables). No wall of text. Keep paragraphs short (2-3 sentences).
3. **BiggerPockets Tone**: Sounds like a real experienced investor (not overly academic, not marketing fluff). Use terms like cash-on-cash yield, inventory compression, supply/demand dynamics, tenant base, and rent-to-price ratio.
4. **Actionable Advice**: End the response with 2-3 specific, actionable recommendations for the investor based on the data.
5. **No AI Clichés**: Avoid phrases like "As an AI, I..." or "Here is the data you requested". Jump straight into the expert reply.
"""

def generate_fallback_response(question, data_context):
    """
    Generates a high-quality, template-based response in case the LLM APIs are not configured.
    """
    lines = [
        "### BiggerPockets Market Insights (Database Snapshot)",
        "",
        "Hey! I pulled the latest rental statistics from our Zillow database tracking tool. Here is what the current data looks like for your query:",
        ""
    ]

    # Format Top Rent Growth
    if "top_rent_growth" in data_context:
        lines.append("#### Hottest Rental Growth Markets (Past 30 Days)")
        lines.append("| Zip Code | City | State | Avg Rent | 30d growth | Active Listings |")
        lines.append("|---|---|---|---|---|---|")
        for item in data_context["top_rent_growth"]:
            lines.append(f"| {item['zipcode']} | {item['city']} | {item['state']} | ${item['avg_rent']} | {item['rent_growth_pct']}% | {item['active_listings']} |")
        lines.append("")

    # Format Rent Drops
    if "biggest_rent_drops" in data_context:
        lines.append("#### Markets Experiencing Rent Declines (Past 30 Days)")
        lines.append("| Zip Code | City | State | Avg Rent | Rent Decline | Active Listings |")
        lines.append("|---|---|---|---|---|---|")
        for item in data_context["biggest_rent_drops"]:
            lines.append(f"| {item['zipcode']} | {item['city']} | {item['state']} | ${item['avg_rent']} | {item['rent_decline_pct']}% | {item['active_listings']} |")
        lines.append("")

    # Format Yield Report
    if "yield_report" in data_context:
        lines.append("#### Top Gross Rental Yield Markets")
        lines.append("| Zip Code | City | State | Avg Rent | Median Home Value | Gross Yield (Annual) |")
        lines.append("|---|---|---|---|---|---|")
        for item in data_context["yield_report"]:
            lines.append(f"| {item['zipcode']} | {item['city']} | {item['state']} | ${item['avg_rent']} | ${item['median_home_value']:,} | {item['yield_pct']}% |")
        lines.append("")

    # Format Hidden Gems
    if "hidden_gems" in data_context:
        lines.append("#### Middle-Class 'Hidden Gems' (Income >= $60k, Price <= $400k)")
        lines.append("| Zip Code | City | State | Avg Rent | Rent Growth | Median Home Value |")
        lines.append("|---|---|---|---|---|---|")
        for item in data_context["hidden_gems"]:
            lines.append(f"| {item['zipcode']} | {item['city']} | {item['state']} | ${item['avg_rent']} | {item['rent_growth_pct']}% | ${item['median_home_value']:,} |")
        lines.append("")

    # Format Investor Opportunities
    if "investor_opportunities" in data_context:
        lines.append("#### Investor Opportunities (Rising Rents + Shrinking Inventory)")
        lines.append("| Zip Code | City | State | Avg Rent | Rent Growth | Inventory Change | Gross Yield |")
        lines.append("|---|---|---|---|---|---|---|")
        for item in data_context["investor_opportunities"]:
            yield_str = f"{item.get('yield_pct', 0)}%" if 'yield_pct' in item else "N/A"
            lines.append(f"| {item['zipcode']} | {item['city']} | {item['state']} | ${item['avg_rent']} | {item['rent_growth_pct']}% | {item['inventory_change_pct']}% | {yield_str} |")
        lines.append("")

    # Format State summary
    for k, v in data_context.items():
        if k.startswith("state_") and k.endswith("_summary"):
            lines.append(f"#### State-Level Snapshot: {v['state']} (As of {v['date']})")
            lines.append(f"- **Average Rent:** ${v['summary']['avg_rent']}")
            lines.append(f"- **Avg 30-day Rent Growth:** {v['summary']['avg_growth_pct']}%")
            lines.append(f"- **Total Active Listings:** {v['summary']['total_listings']}")
            lines.append(f"- **Total Tracked Zips:** {v['summary']['zip_count']}")
            lines.append("")
            lines.append("##### Top Zip Codes in State")
            lines.append("| Zip Code | City | Avg Rent | Rent Growth | Listings |")
            lines.append("|---|---|---|---|---|")
            for z in v["zipcodes"]:
                lines.append(f"| {z['zipcode']} | {z['city']} | ${z['avg_rent']} | {z['rent_growth_pct']}% | {z['listings']} |")
            lines.append("")

        # Format Zipcode Detail
        if k.startswith("zipcode_") and k.endswith("_detail"):
            curr = v.get("current_metrics")
            lines.append(f"#### Zip Code Deep-Dive: {v['zipcode']} ({v['city']}, {v['state']})")
            lines.append(f"- **Median Income:** ${v['median_income']:,}" if v['median_income'] else "- **Median Income:** N/A")
            lines.append(f"- **Median Home Value:** ${v['median_home_value']:,}" if v['median_home_value'] else "- **Median Home Value:** N/A")
            if curr:
                lines.append(f"- **Average Rent:** ${curr['avg_rent']}")
                lines.append(f"- **Active Listings:** {curr['active_listings']}")
                lines.append(f"- **Rent Growth:** {curr['rent_change_pct']}%")
                lines.append(f"- **Inventory Change:** {curr['inventory_change_pct']}%")
            lines.append("")
            
            if v.get("history"):
                lines.append("##### Recent Trends")
                lines.append("| Date | Avg Rent | Listings | Rent Change |")
                lines.append("|---|---|---|---|")
                for h in v["history"]:
                    lines.append(f"| {h['date']} | ${h['avg_rent']} | {h['active_listings']} | {h['rent_change_pct']}% |")
                lines.append("")

            if v.get("events"):
                lines.append("##### Recent Market Events")
                for e in v["events"]:
                    lines.append(f"- **{e['title']}** ({e['date']}): {e['description']} (Severity: {e['severity']})")
                lines.append("")

    # Format Market Pulse
    if "market_pulse" in data_context:
        pulse = data_context["market_pulse"]
        lines.append("#### Nationwide Rental Market Pulse")
        lines.append(f"- **Tracked Date:** {pulse['date']}")
        lines.append(f"- **Average Monthly Rent:** ${pulse['avg_rent']}")
        lines.append(f"- **30-Day Rent Change:** {pulse['rent_change_pct']}%")
        lines.append(f"- **Total Active Listings:** {pulse['total_listings']}")
        lines.append(f"- **Database Stats:** {pulse['total_properties']} properties across {pulse['total_tracked_zipcodes']} zipcodes.")
        lines.append("")

    lines.append("---")
    lines.append("**Takeaways for Investors:**")
    lines.append("1. **Verify Supply Pipelines**: Before buying in high-growth zips, check local building permits to ensure you won't be hit by inventory spikes.")
    lines.append("2. **Focus on Cashflow**: Underwrite deals with conservative rent growth assumptions (1-2% annually) rather than extrapolating short-term spikes.")
    lines.append("3. **Screen Tenants Thoroughly**: Markets with falling rents often correlate with lower median incomes; adjust your tenant screening criteria accordingly.")
    lines.append("")
    lines.append("*(Note: This is a fallback reply because no LLM API key was detected in the environment and local Ollama server was not detected. Set GEMINI_API_KEY, OPENAI_API_KEY, or run Ollama to generate a natural BiggerPockets-style forum response.)*")

    return "\n".join(lines)

def is_ollama_available(host):
    """
    Checks if Ollama server is up and running.
    """
    try:
        response = requests.get(f"{host.rstrip('/')}/api/tags", timeout=1.0)
        return response.status_code == 200
    except Exception:
        return False

def ask_ollama(host, model, question, data_context_str):
    """
    Calls local Ollama API to generate response.
    """
    url = f"{host.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"User Question: {question}\n\nLive Zillow Data Context:\n{data_context_str}"}
        ],
        "stream": False
    }
    
    # Allow up to 3 minutes — large models (32B) need time for cold-start VRAM loading
    timeout_secs = float(os.environ.get("OLLAMA_TIMEOUT", "180"))
    logger.info(f"Calling Ollama ({model}) — timeout: {timeout_secs}s")
    response = requests.post(url, json=payload, timeout=timeout_secs)
    response.raise_for_status()
    result = response.json()
    return result["message"]["content"]

def ask_gemini(api_key, question, data_context_str):
    """
    Calls Gemini API (gemini-2.0-flash) to write the response.
    """
    if not HAS_GEMINI:
        raise ImportError("google-generativeai is not installed.")

    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )
    
    prompt = f"User Question: {question}\n\nLive Zillow Data Context:\n{data_context_str}"
    
    response = model.generate_content(prompt)
    return response.text

def ask_openai(api_key, question, data_context_str):
    """
    Calls OpenAI API (gpt-4o-mini) to write the response.
    """
    if not HAS_OPENAI:
        raise ImportError("openai is not installed.")
        
    client = OpenAI(api_key=api_key)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"User Question: {question}\n\nLive Zillow Data Context:\n{data_context_str}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

def generate_forum_reply(question, data_context):
    """
    Main function called by views to get the BiggerPockets-style forum reply.
    """
    # Serialize data context to string for LLM readability
    data_context_str = json.dumps(data_context, indent=2)
    
    # 1. Try Ollama (Local & Free)
    use_ollama = os.environ.get("USE_OLLAMA", "true").lower() == "true"
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3")
    
    if use_ollama and is_ollama_available(ollama_host):
        try:
            logger.info(f"Ollama server detected. Generating response with model '{ollama_model}'...")
            return ask_ollama(ollama_host, ollama_model, question, data_context_str)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}. Falling back to cloud APIs...")

    # Check cloud keys
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    # 2. Try Gemini
    if gemini_key and HAS_GEMINI:
        try:
            logger.info("Using Gemini to generate response...")
            return ask_gemini(gemini_key, question, data_context_str)
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            if not openai_key:
                logger.warning("No OpenAI fallback available. Falling back to template.")
                return generate_fallback_response(question, data_context)
                
    # 3. Try OpenAI
    if openai_key and HAS_OPENAI:
        try:
            logger.info("Using OpenAI to generate response...")
            return ask_openai(openai_key, question, data_context_str)
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            
    # Ultimate fallback
    return generate_fallback_response(question, data_context)


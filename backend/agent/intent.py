import re
from . import tools

# Regex for matching US Zipcodes (5 digits)
ZIPCODE_PATTERN = re.compile(r"\b\d{5}\b")

# Regex for matching state names or abbreviations
# We list standard state abbreviations as well as full names
STATE_ABBRS = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", 
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", 
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
}

STATE_NAMES_MAP = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO", 
    "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID", 
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA", 
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS", 
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ", 
    "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", 
    "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", 
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", 
    "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY"
}

def extract_state(text):
    text_lower = text.lower()
    # Check full names first (case-insensitive)
    for name, abbr in STATE_NAMES_MAP.items():
        if name in text_lower:
            return abbr
    
    # Check abbreviations — only match UPPERCASE tokens to avoid false positives
    # e.g. "me" (common pronoun) must NOT match Maine (ME)
    # We require the abbreviation to appear as an uppercase standalone token.
    for abbr in STATE_ABBRS:
        # Must be uppercase as written in the original text, with word boundaries
        # This prevents lowercase 'me', 'in', 'or', 'hi' from matching state codes
        pattern = r"(?<![A-Za-z])" + re.escape(abbr) + r"(?![A-Za-z])"
        if re.search(pattern, text):  # no IGNORECASE — requires exact uppercase
            return abbr
    return None

def extract_limit_and_days(text):
    limit = 10
    days = 30
    
    # Simple limit extraction, e.g. "top 5", "limit of 20"
    limit_match = re.search(r"\btop\s+(\d+)\b", text, re.IGNORECASE)
    if limit_match:
        limit = int(limit_match.group(1))
    else:
        limit_match_alt = re.search(r"\blimit\s+(\d+)\b", text, re.IGNORECASE)
        if limit_match_alt:
            limit = int(limit_match_alt.group(1))
            
    # Simple days extraction, e.g. "last 90 days", "past 60 days"
    days_match = re.search(r"\b(last|past|over\s+the\s+last)\s+(\d+)\s+days\b", text, re.IGNORECASE)
    if days_match:
        days = int(days_match.group(2))
    return limit, days

def classify_intent_and_fetch_data(question):
    """
    Analyzes the user's question, invokes matching database query helper functions (tools),
    and returns a combined data context.
    """
    question_lower = question.lower()
    data_context = {}
    tools_used = []
    
    limit, days = extract_limit_and_days(question)
    
    # 1. Zip Code Check
    zipcodes = ZIPCODE_PATTERN.findall(question)
    if zipcodes:
        for zip_code in zipcodes[:3]:  # Limit to first 3 zipcodes to avoid huge payload
            detail = tools.get_zipcode_detail(zip_code)
            if "error" not in detail:
                data_context[f"zipcode_{zip_code}_detail"] = detail
                tools_used.append(f"get_zipcode_detail({zip_code})")

    # 2. State Check
    state = extract_state(question)
    if state:
        summary = tools.get_state_summary(state)
        data_context[f"state_{state}_summary"] = summary
        tools_used.append(f"get_state_summary({state})")

    # 3. Yield Report Check
    if any(k in question_lower for k in ["yield", "cap rate", "cash flow", "return", "roi"]):
        yield_data = tools.get_yield_report(limit=limit)
        data_context["yield_report"] = yield_data
        tools_used.append(f"get_yield_report(limit={limit})")

    # 4. Hidden Gems Check
    if any(k in question_lower for k in ["gem", "hidden", "undervalued"]):
        gems_data = tools.get_hidden_gems(limit=limit)
        data_context["hidden_gems"] = gems_data
        tools_used.append(f"get_hidden_gems(limit={limit})")

    # 5. Rent Drops Check
    if any(k in question_lower for k in ["drop", "fall", "decline", "decrease", "cheapest", "falling", "dropping"]):
        drops_data = tools.get_biggest_rent_drops(limit=limit, days=days)
        data_context["biggest_rent_drops"] = drops_data
        tools_used.append(f"get_biggest_rent_drops(limit={limit}, days={days})")

    # 6. Rent Growth Check
    if any(k in question_lower for k in ["growth", "grow", "highest", "increase", "rising", "best rent", "hottest"]):
        growth_data = tools.get_top_rent_growth(limit=limit, days=days)
        data_context["top_rent_growth"] = growth_data
        tools_used.append(f"get_top_rent_growth(limit={limit}, days={days})")

    # 7. Investor Opportunities Check
    if any(k in question_lower for k in ["opportunity", "invest", "buyer", "deal", "inventory compression"]):
        opps_data = tools.get_investor_opportunities(limit=limit, days=days)
        data_context["investor_opportunities"] = opps_data
        tools_used.append(f"get_investor_opportunities(limit={limit}, days={days})")

    # 8. If nothing matched, or if they ask generic overview questions, get Market Pulse
    if not tools_used or any(k in question_lower for k in ["market pulse", "overview", "nationwide", "summary", "general"]):
        pulse_data = tools.get_market_pulse()
        data_context["market_pulse"] = pulse_data
        tools_used.append("get_market_pulse()")

    return data_context, tools_used

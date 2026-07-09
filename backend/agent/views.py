from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as drf_status

from .intent import classify_intent_and_fetch_data
from .llm import generate_forum_reply

@api_view(["POST"])
def ask_agent(request):
    """
    Main endpoint for the BiggerPockets AI Agent.
    Expects a POST request with a JSON payload:
    {
      "question": "What is the rent growth like in Florida?"
    }
    """
    # Accept both "question" and "prompt"
    question = request.data.get("question") or request.data.get("prompt")
    
    if not question:
        return Response(
            {"error": "Please provide a 'question' or 'prompt' in the request body."},
            status=drf_status.HTTP_400_BAD_REQUEST
        )
        
    question = str(question).strip()
    if not question:
        return Response(
            {"error": "Question cannot be empty."},
            status=drf_status.HTTP_400_BAD_REQUEST
        )

    try:
        # 1. Match intent and pull DB stats
        data_context, tools_used = classify_intent_and_fetch_data(question)
        
        # 2. Feed DB stats to LLM to write BP-style reply
        answer = generate_forum_reply(question, data_context)
        
        return Response({
            "question": question,
            "answer": answer,
            "tools_used": tools_used,
            "data_snapshot": data_context
        }, status=drf_status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": f"An error occurred while processing the request: {str(e)}"},
            status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
def agent_info(request):
    """
    Returns information about the BiggerPockets AI Agent and its capabilities.
    """
    return Response({
        "name": "BiggerPockets Zillow AI Agent",
        "description": "An AI agent that translates natural language real estate questions into database queries and formats the results as forum-ready posts.",
        "supported_intents": [
            {
                "intent": "Zipcode Deep-Dive",
                "examples": ["What is the status of zip 10001?", "Show me history for 33101"],
                "database_tables": ["ZipCode", "ZipCodeDailyMetrics", "Property", "UnitSnapshot", "MarketEvent"]
            },
            {
                "intent": "State summary",
                "examples": ["Rent growth in FL", "New York market report", "State summary for CA"],
                "database_tables": ["ZipCodeDailyMetrics"]
            },
            {
                "intent": "Top Rent Growth",
                "examples": ["Which markets are growing fastest?", "Top rent growth last 90 days"],
                "database_tables": ["ZipCodeDailyMetrics"]
            },
            {
                "intent": "Biggest Rent Drops",
                "examples": ["Where are rents falling?", "Zipcodes with biggest rent drops"],
                "database_tables": ["ZipCodeDailyMetrics"]
            },
            {
                "intent": "Rental Yield Report",
                "examples": ["Best rental yield", "Highest cap rate zipcodes"],
                "database_tables": ["ZipCodeDailyMetrics", "ZipCode"]
            },
            {
                "intent": "Hidden Gems",
                "examples": ["Middle class hidden gems", "Undervalued high income zips"],
                "database_tables": ["ZipCodeDailyMetrics", "ZipCode"]
            },
            {
                "intent": "Investor Opportunities",
                "examples": ["Hottest investor opportunities", "Rising rents and falling inventory"],
                "database_tables": ["ZipCodeDailyMetrics", "ZipCode"]
            },
            {
                "intent": "Market Overview",
                "examples": ["How is the market doing?", "Tracked properties overview"],
                "database_tables": ["ZipCodeDailyMetrics", "Property", "ZipCode"]
            }
        ]
    })

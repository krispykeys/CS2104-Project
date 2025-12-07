#!/usr/bin/env python3
"""
Customer Agent Server - FastAPI backend for Home Value Estimator chatbot
Integrates ATTOM API property search with Google Gemini conversational AI
"""

import os
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import components
from agents.customer_agent import CustomerAgent
from find_property import ATTOMPropertyFinder

# Data models
class FrontendPreferences(BaseModel):
    location: Optional[str] = None
    property_types: Optional[List[str]] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None

class ChatStartRequest(BaseModel):
    user_id: Optional[str] = None
    frontend_data: Optional[FrontendPreferences] = None

class ChatStartResponse(BaseModel):
    session_id: str
    message: str
    status: str

class ChatMessageRequest(BaseModel):
    session_id: str
    message: str

class ChatMessageResponse(BaseModel):
    session_id: str
    message: str
    current_step: str
    completed: bool
    preferences_collected: Optional[Dict[str, Any]] = None

# Helper functions
def extract_location_from_message(message: str) -> Optional[Dict[str, str]]:
    """Extract location information from user message"""
    message_lower = message.lower()
    
    # ZIP code pattern (5 digits)
    zip_pattern = r'\b\d{5}\b'
    zip_match = re.search(zip_pattern, message)
    if zip_match:
        return {'zip_code': zip_match.group()}
    
    # City, State patterns
    city_state_patterns = [
        r'(?:in|near|around)\s+([a-zA-Z\s]+),\s*([a-zA-Z]{2})\b',
        r'(?:in|near|around)\s+([a-zA-Z\s]+)\s+([a-zA-Z]{2})\b',
        r'([a-zA-Z\s]+),\s*([a-zA-Z]{2})\b',
    ]
    
    for pattern in city_state_patterns:
        match = re.search(pattern, message)
        if match:
            city = match.group(1).strip().title()
            state = match.group(2).strip().upper()
            if len(city) > 1 and city not in ['The', 'In', 'On', 'At', 'Is', 'Are']:
                return {'city': city, 'state': state}
    
    # Common cities
    common_cities = {
        'austin': {'city': 'Austin', 'state': 'TX'},
        'denver': {'city': 'Denver', 'state': 'CO'},
        'miami': {'city': 'Miami', 'state': 'FL'},
    }
    
    for city_key, location in common_cities.items():
        if city_key in message_lower:
            return location
    
    return None

def format_properties_for_chat(properties: List, location: Dict[str, str]) -> str:
    """Format property results for chatbot conversation with dual pricing"""
    location_str = location.get('zip_code', f"{location.get('city', '')}, {location.get('state', '')}")
    
    if not properties:
        return f"I searched for properties in {location_str} but didn't find any available right now. Would you like me to search in a different area?"
    
    response = f"Great! I found {len(properties)} properties in {location_str}:\n\n"
    
    for i, prop in enumerate(properties[:5], 1):  # Limit to 5 properties for chat
        response += f"🏠 **Property {i}**\n"
        response += f"📍 {prop.address}\n"
        
        # Show both price estimates with clear labels
        if hasattr(prop, 'fair_value_estimate') and prop.fair_value_estimate:
            confidence_emoji = {"high": "🎯", "medium": "📊", "low": "📈"}.get(
                getattr(prop, 'ai_confidence', 'medium'), "💰"
            )
            response += f"{confidence_emoji} **Fair Value (AI)**: ${prop.fair_value_estimate:,.0f}\n"
        
        if hasattr(prop, 'listing_price') and prop.listing_price:
            response += f"🏷️ **Listed Price**: ${prop.listing_price:,.0f}\n"
        
        # Add property details if available
        details = []
        if hasattr(prop, 'bedrooms') and prop.bedrooms:
            details.append(f"{prop.bedrooms} bed")
        if hasattr(prop, 'bathrooms') and prop.bathrooms:
            details.append(f"{prop.bathrooms} bath")
        if hasattr(prop, 'square_feet') and prop.square_feet:
            details.append(f"{prop.square_feet:,} sqft")
        
        if details:
            response += f"🏡 {' • '.join(details)}\n"
        
        if hasattr(prop, 'year_built') and prop.year_built:
            response += f"📅 Built: {prop.year_built}\n"
        
        # Add AI confidence note for transparency
        if hasattr(prop, 'ai_confidence') and prop.ai_confidence:
            confidence_text = {
                "high": "High confidence",
                "medium": "Moderate confidence", 
                "low": "Preliminary estimate"
            }.get(prop.ai_confidence, "AI analyzed")
            response += f"🤖 {confidence_text}\n"
        
        response += "\n"
    
    response += "Would you like to see more details about any of these properties, or search in a different area?"
    return response

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is required")

# Initialize FastAPI app
app = FastAPI(title="Home Value Estimator Customer Agent API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
customer_agent = CustomerAgent(api_key)
property_finder = ATTOMPropertyFinder()

logger.info("✅ Customer Agent Server initialized")

@app.post("/chat/start", response_model=ChatStartResponse)
async def start_chat(request: ChatStartRequest):
    """Start a new chatbot session"""
    try:
        session = customer_agent.start_chatbot_session()
        
        return ChatStartResponse(
            session_id=session.session_id,
            message="👋 Hi! I'm your Home Value Estimator assistant. I can help you find real estate investment opportunities. What area are you interested in?",
            status="active"
        )
    except Exception as e:
        logger.error(f"Error starting chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to start chat session")

@app.post("/chat/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """Send a message to the chatbot"""
    try:
        # Check if it's a property request
        user_message_lower = request.message.lower()
        property_keywords = [
            'properties', 'homes', 'houses', 'real estate',
            'show me', 'find', 'search', 'get me', 'give me'
        ]
        
        is_property_request = any(keyword in user_message_lower for keyword in property_keywords)
        has_zip_code = bool(re.search(r'\b\d{5}\b', user_message_lower))
        
        if is_property_request or has_zip_code:
            location = extract_location_from_message(request.message)
            if location:
                try:
                    properties = await property_finder.find_properties_by_location(
                        city=location.get('city'),
                        state=location.get('state'),
                        zip_code=location.get('zip_code'),
                        max_results=5
                    )
                    
                    response_message = format_properties_for_chat(properties, location)
                    
                    return ChatMessageResponse(
                        session_id=request.session_id,
                        message=response_message,
                        current_step="property_search",
                        completed=False
                    )
                except Exception as e:
                    logger.error(f"Property search error: {e}")
        
        # Default conversational response
        response_message = await customer_agent.handle_chatbot_message(
            request.session_id, 
            request.message
        )
        
        return ChatMessageResponse(
            session_id=request.session_id,
            message=response_message,
            current_step="conversation",
            completed=False
        )
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

if __name__ == "__main__":
    uvicorn.run("customer_agent_server:app", host="0.0.0.0", port=8001, reload=True)

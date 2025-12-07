#!/usr/bin/env python3
# FastAPI server for the chatbot - handles all API requests

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
import sys
from pathlib import Path

# Setup paths for imports
code_dir = Path(__file__).parent
project_root = code_dir.parent
sys.path.insert(0, str(code_dir))

# Load API keys
load_dotenv(project_root / ".env")

# Import our modules
from agents.customer_agent import CustomerAgent
from find_property import ATTOMPropertyFinder

# Request/response models for the API
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
    """Pull out city/state or ZIP from user's message"""
    message_lower = message.lower()
    
    # Check for ZIP code first (easiest)
    zip_pattern = r'\b\d{5}\b'
    zip_match = re.search(zip_pattern, message)
    if zip_match:
        return {'zip_code': zip_match.group()}
    
    # Try different city/state formats
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
    
    # Fallback for common cities mentioned alone
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
    """Turn property data into a nice chat message"""
    location_str = location.get('zip_code', f"{location.get('city', '')}, {location.get('state', '')}")
    
    if not properties:
        return f"I searched for properties in {location_str} but didn't find any available right now. Would you like me to search in a different area?"
    
    response = f"Great! I found {len(properties)} properties in {location_str}:\n\n"
    
    for i, prop in enumerate(properties[:5], 1):  # Limit to 5 properties for chat
        response += f"🏠 **Property {i}**\n"
        response += f"📍 {prop.address}\n"
        
        # Show AI estimate first
        if hasattr(prop, 'fair_value_estimate') and prop.fair_value_estimate:
            confidence_emoji = {"high": "🎯", "medium": "📊", "low": "📈"}.get(
                getattr(prop, 'ai_confidence', 'medium'), "💰"
            )
            response += f"{confidence_emoji} **Fair Value (AI)**: ${prop.fair_value_estimate:,.0f}\n"
        
        if hasattr(prop, 'listing_price') and prop.listing_price:
            response += f"🏷️ **Listed Price**: ${prop.listing_price:,.0f}\n"
        
        # Add basic property info
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
        
        # Show how confident the AI is
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Make sure we have API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is required")

# Create FastAPI app
app = FastAPI(title="Home Value Estimator Customer Agent API")

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create our main objects
customer_agent = CustomerAgent(api_key)
property_finder = ATTOMPropertyFinder()

logger.info("✅ Customer Agent Server initialized")

@app.post("/chat/start", response_model=ChatStartResponse)
async def start_chat(request: ChatStartRequest):
    """Creates a new chat session"""
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
    """Handles user messages and responses"""
    try:
        # See if user wants property search
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
                    # Search for properties
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
        
        # Regular conversation if not searching
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

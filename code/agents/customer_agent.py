"""
Agent 1: Customer-Facing Agent for Real Estate Investment Platform
Handles user interactions, explains analysis in simple terms, provides conversational responses using Gemini Flash
"""

import google.generativeai as genai
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import uuid
from enum import Enum
from pydantic import BaseModel

from models.data_models import PropertyAnalysis, QuickAnalysisResponse, ATTOMSearchCriteria, InvestmentStrategy, PropertyType

logger = logging.getLogger(__name__)


class UserType(str, Enum):
    """Types of users on the undervalued home website"""
    NEW_HOMEBUYER = "new_homebuyer"
    REALTOR = "realtor"
    INVESTOR = "investor"
    UNKNOWN = "unknown"


class ChatbotStep(str, Enum):
    """Chatbot conversation flow steps"""
    GREETING = "greeting"
    LOCATION = "location"
    PROPERTY_TYPE = "property_type"
    PROPERTY_SPECS = "property_specs"
    BUDGET = "budget"
    INVESTMENT_STRATEGY = "investment_strategy"
    TIMELINE = "timeline"
    SUMMARY = "summary"
    HANDOFF = "handoff"


class UserPreferences:
    """User preference collection model for property search"""
    
    def __init__(self):
        self.location_preferences = {
            'cities': [],
            'states': [],
            'zip_codes': [],
            'radius_miles': None
        }
        self.property_preferences = {
            'property_types': [],
            'min_bedrooms': None,
            'max_bedrooms': None,
            'min_bathrooms': None,
            'max_bathrooms': None,
            'min_sqft': None,
            'max_sqft': None,
            'min_year_built': None,
            'max_year_built': None
        }
        self.financial_preferences = {
            'min_price': None,
            'max_price': None,
            'target_cash_flow': None,
            'max_investment': None,
            'down_payment_percentage': None,
            'investment_strategies': []
        }
        self.timeline_preferences = {
            'purchase_timeline': None,
            'hold_period': None
        }
        self.completed_sections = set()
        self.is_complete = False
    
    def to_search_criteria(self) -> ATTOMSearchCriteria:
        """Convert user preferences to ATTOM search criteria"""
        cities = self.location_preferences.get('cities', [])
        states = self.location_preferences.get('states', [])
        zip_codes = self.location_preferences.get('zip_codes', [])
        
        return ATTOMSearchCriteria(
            city=cities[0] if cities else None,
            state=states[0] if states else None,
            zip_code=zip_codes[0] if zip_codes else None,
            radius_miles=self.location_preferences.get('radius_miles'),
            min_price=self.financial_preferences.get('min_price'),
            max_price=self.financial_preferences.get('max_price'),
            min_beds=self.property_preferences.get('min_bedrooms'),
            max_beds=self.property_preferences.get('max_bedrooms'),
            min_baths=self.property_preferences.get('min_bathrooms'),
            max_baths=self.property_preferences.get('max_bathrooms'),
            min_sqft=self.property_preferences.get('min_sqft'),
            max_sqft=self.property_preferences.get('max_sqft'),
            min_year_built=self.property_preferences.get('min_year_built'),
            property_types=[pt.value if isinstance(pt, PropertyType) else pt for pt in self.property_preferences.get('property_types', [])]
        )
    
    def get_progress_percentage(self) -> int:
        """Get completion percentage"""
        total_sections = 6  # location, property_type, property_specs, budget, investment_strategy, timeline
        return int((len(self.completed_sections) / total_sections) * 100) if total_sections > 0 else 0


class FrontendPreferences(BaseModel):
    """Structured data from frontend form inputs"""
    location: Optional[str] = None
    property_types: List[str] = []  # e.g., ['primary-residence', 'fix-flip', 'rental-property']
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None


class ChatbotSession:
    """Manages a chatbot session for collecting user preferences"""
    
    def __init__(self, session_id: str = None, handoff_callback: Optional[Callable] = None, frontend_data: Optional[FrontendPreferences] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_preferences = UserPreferences()
        self.current_step = ChatbotStep.GREETING
        self.conversation_history = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.awaiting_handoff = False
        self.handoff_callback = handoff_callback
        
        # Track what we're currently collecting
        self.pending_clarification = None
        self.retry_count = 0
        self.max_retries = 3
        
        # User type detection for tailored responses
        self.user_type = UserType.UNKNOWN
        
        # Property results from deal_finder
        self.property_results: List[Dict[str, Any]] = []
        
        # Frontend form data - pre-populated preferences
        self.frontend_data = frontend_data
        self._populate_from_frontend_data()
    
    def _populate_from_frontend_data(self):
        """Populate user preferences from frontend form data"""
        if not self.frontend_data:
            return
            
        # Parse location data
        if self.frontend_data.location:
            location = self.frontend_data.location.strip()
            # Try to parse common location formats
            if ',' in location:
                parts = [p.strip() for p in location.split(',')]
                if len(parts) >= 2:
                    # Assume "City, State" or "City, State ZIP" format
                    self.user_preferences.location_preferences['cities'].append(parts[0])
                    # Check if second part looks like a state (2 chars) or contains state
                    state_part = parts[1]
                    if len(state_part) == 2:
                        self.user_preferences.location_preferences['states'].append(state_part.upper())
                    else:
                        # Try to extract state from longer string
                        state_words = state_part.split()
                        for word in state_words:
                            if len(word) == 2 and word.isalpha():
                                self.user_preferences.location_preferences['states'].append(word.upper())
                                break
            elif location.isdigit() and len(location) == 5:
                # ZIP code
                self.user_preferences.location_preferences['zip_codes'].append(location)
            else:
                # Single city or state name
                self.user_preferences.location_preferences['cities'].append(location)
        
        # Map frontend property types to our internal types
        property_type_mapping = {
            'primary-residence': InvestmentStrategy.BUY_AND_HOLD,  # Closest match
            'fix-flip': InvestmentStrategy.FIX_AND_FLIP,
            'rental-property': InvestmentStrategy.BUY_AND_HOLD,
            'multi-family': InvestmentStrategy.BUY_AND_HOLD,  # Multi-family for buy & hold
            'quick-deals': InvestmentStrategy.WHOLESALE
        }
        
        for frontend_type in self.frontend_data.property_types:
            if frontend_type in property_type_mapping:
                strategy = property_type_mapping[frontend_type]
                if strategy not in self.user_preferences.financial_preferences['investment_strategies']:
                    self.user_preferences.financial_preferences['investment_strategies'].append(strategy)
        
        # Set budget preferences
        if self.frontend_data.budget_min:
            self.user_preferences.financial_preferences['min_price'] = self.frontend_data.budget_min
        if self.frontend_data.budget_max:
            self.user_preferences.financial_preferences['max_price'] = self.frontend_data.budget_max
        
        # Mark sections as completed if we have data
        if self.frontend_data.location:
            self.user_preferences.completed_sections.add('location')
        if self.frontend_data.property_types:
            self.user_preferences.completed_sections.add('investment_strategy')
        if self.frontend_data.budget_min or self.frontend_data.budget_max:
            self.user_preferences.completed_sections.add('budget')
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.update_activity()
    
    def get_conversation_context(self, last_n_messages: int = 10) -> str:
        """Get recent conversation context for AI"""
        recent_messages = self.conversation_history[-last_n_messages:] if self.conversation_history else []
        if not recent_messages:
            return "This is the start of the conversation."
        
        context_lines = []
        for msg in recent_messages:
            role_display = "User" if msg['role'] == 'user' else "Assistant"
            context_lines.append(f"{role_display}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def get_deal_finder_data(self) -> Dict[str, Any]:
        """Get structured data for passing to deal_finder agent"""
        return {
            'session_id': self.session_id,
            'user_type': self.user_type.value,
            'search_criteria': self.user_preferences.to_search_criteria().dict(),
            'preferences': {
                'location_preferences': self.user_preferences.location_preferences,
                'property_preferences': self.user_preferences.property_preferences,
                'financial_preferences': self.user_preferences.financial_preferences,
                'timeline_preferences': self.user_preferences.timeline_preferences,
                'investment_strategies': [strategy.value for strategy in self.user_preferences.financial_preferences.get('investment_strategies', [])]
            },
            'frontend_data': self.frontend_data.dict() if self.frontend_data else None,
            'completion_status': {
                'completed_sections': list(self.user_preferences.completed_sections),
                'progress_percentage': self.user_preferences.get_progress_percentage(),
                'is_complete': self.user_preferences.is_complete
            },
            'conversation_summary': self._get_conversation_summary(),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
    
    def _get_conversation_summary(self) -> str:
        """Get a brief summary of the conversation for context"""
        if not self.conversation_history:
            return "No conversation history"
        
        # Get key points from conversation
        key_messages = []
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            if msg['role'] == 'user' and len(msg['content']) > 20:
                key_messages.append(f"User: {msg['content'][:100]}...")
        
        return " | ".join(key_messages) if key_messages else "Brief conversation"


class CustomerAgent:
    """
    Agent 1: Customer-Facing Agent
    Uses Gemini 2.5 Flash for fast, conversational responses
    Explains complex real estate analysis in simple, understandable terms
    """
    
    def __init__(self, api_key: str, deal_finder_callback: Optional[Callable] = None):
        """Initialize the Customer Agent with Gemini Flash model"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Use Gemini Flash for fast conversational responses
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Customer-friendly prompts and templates
        self.explanation_templates = self._load_explanation_templates()
        
        # Chatbot session management
        self.active_sessions: Dict[str, ChatbotSession] = {}
        self.deal_finder_callback = deal_finder_callback
        
        logger.info("Customer Agent initialized with Gemini 2.5 Flash")
    
    def get_session_deal_finder_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get deal finder data for a specific session"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return session.get_deal_finder_data()
    
    def trigger_deal_finder_handoff(self, session_id: str) -> Dict[str, Any]:
        """Trigger handoff to deal_finder agent with collected data"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        deal_finder_data = session.get_deal_finder_data()
        
        # Call the callback if provided
        if self.deal_finder_callback:
            try:
                result = self.deal_finder_callback(deal_finder_data)
                logger.info(f"Deal finder callback completed for session {session_id}")
                return result
            except Exception as e:
                logger.error(f"Deal finder callback failed: {e}")
                return {"error": f"Deal finder callback failed: {str(e)}"}
        
        # Return the data structure for the deal_finder agent
        logger.info(f"Prepared deal finder data for session {session_id}")
        return {
            "status": "ready_for_deal_finder",
            "data": deal_finder_data,
            "message": "User preferences collected and ready for property search"
        }
    
    def _detect_user_type(self, user_message: str, conversation_history: List[Dict] = None) -> UserType:
        """Detect user type based on their message and conversation history"""
        user_message_lower = user_message.lower()
        
        # Keywords for different user types
        investor_keywords = [
            'investment', 'roi', 'cash flow', 'rental', 'flip', 'brrrr', 'portfolio', 
            'cap rate', 'investor', 'investing', 'rental property', 'appreciation',
            'leverage', 'financing', 'debt service', 'noi', 'yield'
        ]
        
        realtor_keywords = [
            'realtor', 'agent', 'listing', 'mls', 'client', 'buyer', 'seller',
            'commission', 'closing', 'contract', 'showing', 'market analysis',
            'comp', 'comparable', 'licensed', 'brokerage', 'referral'
        ]
        
        homebuyer_keywords = [
            'first home', 'buying my first', 'home buyer', 'homebuyer', 
            'moving', 'family', 'neighborhood', 'schools', 'mortgage',
            'down payment', 'closing costs', 'home inspection', 'primary residence'
        ]
        
        # Count matches for each category
        investor_score = sum(1 for keyword in investor_keywords if keyword in user_message_lower)
        realtor_score = sum(1 for keyword in realtor_keywords if keyword in user_message_lower)
        homebuyer_score = sum(1 for keyword in homebuyer_keywords if keyword in user_message_lower)
        
        # Check conversation history for additional context
        if conversation_history:
            history_text = ' '.join([msg.get('content', '').lower() 
                                   for msg in conversation_history[-3:]])  # Last 3 messages
            
            investor_score += sum(1 for keyword in investor_keywords if keyword in history_text)
            realtor_score += sum(1 for keyword in realtor_keywords if keyword in history_text)
            homebuyer_score += sum(1 for keyword in homebuyer_keywords if keyword in history_text)
        
        # Determine user type based on highest score
        if investor_score > realtor_score and investor_score > homebuyer_score and investor_score > 0:
            return UserType.INVESTOR
        elif realtor_score > homebuyer_score and realtor_score > 0:
            return UserType.REALTOR
        elif homebuyer_score > 0:
            return UserType.NEW_HOMEBUYER
        
        return UserType.UNKNOWN
    
    def _get_conversation_context_for_ai(self, session: ChatbotSession) -> str:
        """Get context for more natural AI responses"""
        user_type_context = {
            UserType.NEW_HOMEBUYER: "They're looking for their first home or a home to live in",
            UserType.REALTOR: "They're a real estate professional helping clients", 
            UserType.INVESTOR: "They're looking for investment properties for financial returns",
            UserType.UNKNOWN: "Their goals aren't clear yet"
        }
        
        return user_type_context.get(session.user_type, user_type_context[UserType.UNKNOWN])
    
    def _load_explanation_templates(self) -> Dict[str, str]:
        """Load user-type-specific templates for the undervalued home website"""
        return {
            # Templates for NEW HOMEBUYERS
            "new_homebuyer_deal_explanation": """
            You are a friendly home buying advisor helping someone find their first undervalued home.
            
            Property Score: {score}/100
            Value Rating: {rating}
            
            Explain this in encouraging, non-technical terms focusing on:
            - Whether this is a good deal for a primary residence
            - How much money they could save vs market rate
            - What this means for building equity
            - Simple next steps for a new homebuyer
            
            Avoid investment jargon. Focus on home ownership benefits and value.
            """,
            
            # Templates for REALTORS
            "realtor_deal_explanation": """
            You are providing professional analysis to a licensed realtor about an undervalued property.
            
            Deal Score: {score}/100
            Market Assessment: {rating}
            
            Provide professional insights focusing on:
            - Comparative market analysis implications
            - Why this property is undervalued
            - Key selling points to present to clients
            - Potential concerns to disclose
            - Strategic pricing recommendations
            
            Use professional real estate terminology appropriately.
            """,
            
            # Templates for INVESTORS
            "investor_deal_explanation": """
            You are a real estate investment analyzer providing detailed investment metrics.
            
            Deal Score: {score}/100
            Investment Rating: {rating}
            
            Provide comprehensive investment analysis including:
            - ROI potential and cash flow projections
            - Investment strategy recommendations
            - Risk assessment and mitigation strategies
            - Market timing considerations
            - Portfolio fit analysis
            
            Use investment terminology and focus on financial metrics.
            """,
            
            # General undervalued home website templates
            "undervalued_property_explanation": """
            You are helping someone understand why a property on our undervalued home website is a good opportunity.
            
            Property: {address}
            Undervalued by: {undervalued_amount}
            Market Value: {market_value}
            List Price: {list_price}
            
            Explain the opportunity based on user type: {user_type}
            Tailor your language and focus accordingly.
            """
        }
    
    # Chatbot Conversation Methods
    
    def start_chatbot_session(self, session_id: str = None, frontend_data: Optional[FrontendPreferences] = None) -> ChatbotSession:
        """Start a new chatbot session for preference collection"""
        session = ChatbotSession(session_id, self.deal_finder_callback, frontend_data)
        self.active_sessions[session.session_id] = session
        
        logger.info(f"Started new chatbot session: {session.session_id}")
        if frontend_data:
            logger.info(f"Session initialized with frontend data: location={frontend_data.location}, types={frontend_data.property_types}, budget={frontend_data.budget_min}-{frontend_data.budget_max}")
        return session
    
    async def handle_chatbot_message(self, session_id: str, user_message: str) -> str:
        """Handle a message in an ongoing chatbot conversation"""
        
        if session_id not in self.active_sessions:
            return "I'm sorry, I couldn't find your conversation session. Let's start fresh! What can I help you with today?"
        
        session = self.active_sessions[session_id]
        session.add_message("user", user_message)
        
        # Process the message based on current step
        response = await self._process_chatbot_step(session, user_message)
        
        session.add_message("assistant", response)
        return response
    
    async def _process_chatbot_step(self, session: ChatbotSession, user_message: str) -> str:
        """Process user message with natural conversation flow"""
        
        step = session.current_step
        
        if step == ChatbotStep.GREETING:
            return await self._handle_greeting_step(session, user_message)
        else:
            # Use flexible conversation handling instead of rigid steps
            return await self._handle_natural_conversation(session, user_message)
    
    async def _handle_greeting_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle initial greeting and start natural conversation"""
        
        # Detect user type from their message
        session.user_type = self._detect_user_type(user_message, session.conversation_history)
        
        # Get full conversation history for context
        conversation_context = session.get_conversation_context(last_n_messages=10)
        
        # Build context about pre-filled data
        prefilled_context = ""
        if session.frontend_data:
            prefilled_info = []
            if session.frontend_data.location:
                prefilled_info.append(f"location: {session.frontend_data.location}")
            if session.frontend_data.property_types:
                types_str = ", ".join(session.frontend_data.property_types)
                prefilled_info.append(f"property types: {types_str}")
            if session.frontend_data.budget_min or session.frontend_data.budget_max:
                budget_str = f"${session.frontend_data.budget_min or 0:,} - ${session.frontend_data.budget_max or 'unlimited'}"
                prefilled_info.append(f"budget: {budget_str}")
            
            if prefilled_info:
                prefilled_context = f"\n\nIMPORTANT: The user has already provided some preferences through a form: {', '.join(prefilled_info)}. Acknowledge this information naturally and build on it rather than asking for it again."
        
        # Create a natural, conversational response that builds on what they said
        greeting_prompt = f"""
        You are a friendly, knowledgeable real estate assistant having a conversation with someone who seems to be a {session.user_type.value.replace('_', ' ')}.
        
        CONVERSATION HISTORY:
        {conversation_context}
        
        CURRENT MESSAGE: "{user_message}"
        {prefilled_context}
        
        REMEMBER: You are having an ongoing conversation. Reference what was said before when appropriate. 
        Build on the conversation naturally like a real person would.
        
        Respond naturally to what they actually said, acknowledging the conversation flow. 
        Don't use templates or cookie-cutter responses. Build on their specific words and situation.
        
        If they've already provided information through the form, acknowledge it and show that you understand their preferences.
        Ask thoughtful follow-up questions based on what they've shared.
        
        Keep it human, warm, and genuinely helpful. Avoid sounding like a form or questionnaire.
        """
        
        try:
            response = await self.model.generate_content_async(greeting_prompt)
            # Move to a more flexible conversation state instead of rigid steps
            session.current_step = ChatbotStep.LOCATION
            return response.text
        except Exception as e:
            logger.error(f"Error in greeting step: {e}")
            session.current_step = ChatbotStep.LOCATION
            return "Hi there! I'd love to help you find some great property opportunities. What kind of situation are you in right now?"
    
    async def _handle_location_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle conversation naturally, extracting info as it comes up"""
        
        # Extract any location info mentioned
        user_message_lower = user_message.lower()
        if any(word in user_message_lower for word in ['virginia', 'va', 'richmond', 'norfolk', 'virginia beach']):
            session.user_preferences.location_preferences['states'].append('VA')
        
        if 'richmond' in user_message_lower:
            session.user_preferences.location_preferences['cities'].append('Richmond')
        elif 'norfolk' in user_message_lower:
            session.user_preferences.location_preferences['cities'].append('Norfolk')
        
        # Get full conversation history for context
        conversation_context = session.get_conversation_context(last_n_messages=10)
        
        conversation_prompt = f"""
        You are having a natural conversation about real estate with someone who is a {session.user_type.value.replace('_', ' ')}.
        
        FULL CONVERSATION HISTORY:
        {conversation_context}
        
        CURRENT MESSAGE: "{user_message}"
        
        REMEMBER: This is an ongoing conversation. Reference previous messages and build on what was discussed.
        Show that you remember what they told you before.
        
        Respond naturally to what they said. If they mentioned a location, acknowledge it specifically.
        If they shared details about their situation, ask a thoughtful follow-up question.
        
        Don't follow a script - have a real conversation that flows naturally from what came before.
        Ask questions that show you're genuinely interested in helping them with their specific situation.
        
        Avoid bullet points, lists, or formal structures unless they specifically ask for them.
        """
        
        try:
            response = await self.model.generate_content_async(conversation_prompt)
            
            # Intelligently decide next step based on what we've learned
            if any(session.user_preferences.location_preferences['cities']) or any(session.user_preferences.location_preferences['states']):
                session.user_preferences.completed_sections.add('location')
                session.current_step = ChatbotStep.PROPERTY_TYPE
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            return "Tell me more about what you're looking for. I'm here to help!"
    
    async def _handle_natural_conversation(self, session: ChatbotSession, user_message: str) -> str:
        """Handle natural, flowing conversation instead of rigid steps"""
        
        # Extract any useful information from what they said
        self._extract_preferences_naturally(session, user_message)
        
        # Build context about what we know so far
        known_info = self._summarize_known_preferences(session)
        
        # Check if we have enough to start a search
        if self._ready_for_search(session):
            return await self._handle_summary_step(session, user_message)
        
        # Get full conversation history for context - THIS IS KEY!
        conversation_context = session.get_conversation_context(last_n_messages=15)
        
        conversation_prompt = f"""
        You are having a natural conversation about real estate with someone who is a {session.user_type.value.replace('_', ' ')}.
        
        FULL CONVERSATION HISTORY:
        {conversation_context}
        
        CURRENT MESSAGE: "{user_message}"
        
        WHAT YOU KNOW SO FAR: {known_info}
        
        CRITICAL: This is an ongoing conversation. You MUST remember and reference what was discussed before.
        Build on previous messages naturally. Show that you remember their preferences, situation, and concerns.
        
        Continue the conversation naturally based on the FULL HISTORY above. 
        Ask follow-up questions that feel organic to the conversation flow.
        Show that you're listening to what they're saying and remember previous details.
        
        If they seem ready to see some properties, offer to search for them.
        If they're still exploring their options, keep the conversation going naturally.
        
        Be human, warm, and genuinely helpful. Reference specific things they mentioned earlier to show you remember.
        """
        
        try:
            response = await self.model.generate_content_async(conversation_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in natural conversation: {e}")
            return "That's interesting! Tell me more about what you're thinking."
    
    def _extract_preferences_naturally(self, session: ChatbotSession, user_message: str):
        """Extract preferences from natural conversation without being obvious about it"""
        user_message_lower = user_message.lower()
        
        # Location extraction
        cities = ['richmond', 'norfolk', 'virginia beach', 'charlotte', 'raleigh', 'atlanta', 'nashville']
        states = ['virginia', 'va', 'north carolina', 'nc', 'georgia', 'ga', 'tennessee', 'tn']
        
        for city in cities:
            if city in user_message_lower:
                if city not in session.user_preferences.location_preferences['cities']:
                    session.user_preferences.location_preferences['cities'].append(city.title())
                    session.user_preferences.completed_sections.add('location')
        
        for state in states:
            if state in user_message_lower:
                state_code = {'virginia': 'VA', 'va': 'VA', 'north carolina': 'NC', 'nc': 'NC', 
                            'georgia': 'GA', 'ga': 'GA', 'tennessee': 'TN', 'tn': 'TN'}
                if state in state_code and state_code[state] not in session.user_preferences.location_preferences['states']:
                    session.user_preferences.location_preferences['states'].append(state_code[state])
                    session.user_preferences.completed_sections.add('location')
        
        # Property type extraction
        if any(word in user_message_lower for word in ['single family', 'house', 'home']):
            if PropertyType.SINGLE_FAMILY not in session.user_preferences.property_preferences['property_types']:
                session.user_preferences.property_preferences['property_types'].append(PropertyType.SINGLE_FAMILY)
                session.user_preferences.completed_sections.add('property_type')
        
        if any(word in user_message_lower for word in ['condo', 'townhouse']):
            for pt in [PropertyType.CONDO, PropertyType.TOWNHOUSE]:
                if pt not in session.user_preferences.property_preferences['property_types']:
                    session.user_preferences.property_preferences['property_types'].append(pt)
                    session.user_preferences.completed_sections.add('property_type')
        
        # Budget extraction
        import re
        price_matches = re.findall(r'\$?([\\d,]+)k?', user_message_lower)
        for price_str in price_matches:
            try:
                price = int(price_str.replace(',', ''))
                if price > 10:  # Assume it's a reasonable price
                    if 'k' in user_message_lower or price < 1000:
                        price *= 1000 if price < 1000 else 1
                    
                    if any(word in user_message_lower for word in ['budget', 'max', 'under', 'below']):
                        session.user_preferences.financial_preferences['max_price'] = price
                        session.user_preferences.completed_sections.add('budget')
            except:
                pass
        
        # Strategy extraction
        if any(word in user_message_lower for word in ['rental', 'rent out', 'cash flow', 'passive income']):
            if InvestmentStrategy.BUY_AND_HOLD not in session.user_preferences.financial_preferences['investment_strategies']:
                session.user_preferences.financial_preferences['investment_strategies'].append(InvestmentStrategy.BUY_AND_HOLD)
                session.user_preferences.completed_sections.add('investment_strategy')
        
        if any(word in user_message_lower for word in ['flip', 'renovate', 'fix up']):
            if InvestmentStrategy.FIX_AND_FLIP not in session.user_preferences.financial_preferences['investment_strategies']:
                session.user_preferences.financial_preferences['investment_strategies'].append(InvestmentStrategy.FIX_AND_FLIP)
                session.user_preferences.completed_sections.add('investment_strategy')
    
    def _summarize_known_preferences(self, session: ChatbotSession) -> str:
        """Create a natural summary of what we know so far"""
        info_parts = []
        
        if session.user_preferences.location_preferences['cities']:
            info_parts.append(f"Looking in {', '.join(session.user_preferences.location_preferences['cities'])}")
        elif session.user_preferences.location_preferences['states']:
            info_parts.append(f"Interested in {', '.join(session.user_preferences.location_preferences['states'])}")
        
        if session.user_preferences.property_preferences['property_types']:
            types = [pt.value.replace('_', ' ').title() for pt in session.user_preferences.property_preferences['property_types']]
            info_parts.append(f"Property types: {', '.join(types)}")
        
        if session.user_preferences.financial_preferences['max_price']:
            info_parts.append(f"Budget: up to ${session.user_preferences.financial_preferences['max_price']:,}")
        
        if session.user_preferences.financial_preferences['investment_strategies']:
            strategies = [s.value.replace('_', ' ').title() for s in session.user_preferences.financial_preferences['investment_strategies']]
            info_parts.append(f"Strategy: {', '.join(strategies)}")
        
        return '; '.join(info_parts) if info_parts else "Still getting to know their preferences"
    
    def _ready_for_search(self, session: ChatbotSession) -> bool:
        """Check if we have enough info to start a meaningful search"""
        has_location = (session.user_preferences.location_preferences['cities'] or 
                       session.user_preferences.location_preferences['states'])
        has_some_criteria = len(session.user_preferences.completed_sections) >= 2
        
        return has_location and has_some_criteria
    
    def _get_conversation_context_for_ai(self, session: ChatbotSession) -> str:
        """Get context for more natural AI responses"""
        user_type_context = {
            UserType.NEW_HOMEBUYER: "They're looking for their first home or a home to live in",
            UserType.REALTOR: "They're a real estate professional helping clients", 
            UserType.INVESTOR: "They're looking for investment properties for financial returns",
            UserType.UNKNOWN: "Their goals aren't clear yet"
        }
        
        return user_type_context.get(session.user_type, user_type_context[UserType.UNKNOWN])

    # Keep the summary step handler since we still need it for search handoff
    async def _handle_summary_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle property type preferences"""
        
        # Parse property types (simplified)
        user_message_lower = user_message.lower()
        property_types = []
        
        if any(word in user_message_lower for word in ['single family', 'house', 'home']):
            property_types.append(PropertyType.SINGLE_FAMILY)
        if any(word in user_message_lower for word in ['condo', 'townhouse']):
            property_types.extend([PropertyType.CONDO, PropertyType.TOWNHOUSE])
        if any(word in user_message_lower for word in ['multi', 'duplex', 'triplex']):
            property_types.append(PropertyType.MULTI_FAMILY)
        
        if not property_types:  # Default if unclear
            property_types = [PropertyType.SINGLE_FAMILY]
        
        session.user_preferences.property_preferences['property_types'] = property_types
        session.user_preferences.completed_sections.add('property_type')
        session.current_step = ChatbotStep.PROPERTY_SPECS
        
        property_prompt = f"""
        The user specified property type preferences: "{user_message}"
        
        Acknowledge their choice and now ask about property specifications like:
        - Number of bedrooms (minimum/maximum)
        - Number of bathrooms
        - Square footage preferences
        
        Keep it conversational and mention that this helps narrow down the search.
        """
        
        try:
            response = await self.model.generate_content_async(property_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in property type step: {e}")
            return """Perfect! I've noted your property type preferences.
            
Now let's talk about size requirements:
• How many bedrooms would you prefer? (minimum and maximum if you have a range)
• Any preferences on bathrooms?
• Any minimum square footage you'd want?

These details help me find properties that fit your needs perfectly!"""
    
    async def _handle_property_specs_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle property specification preferences"""
        
        # Parse specifications (simplified)
        import re
        
        # Look for bedroom numbers
        bed_matches = re.findall(r'(\d+)\s*(?:bed|br)', user_message.lower())
        if bed_matches:
            session.user_preferences.property_preferences['min_bedrooms'] = int(bed_matches[0])
        
        # Look for bathroom numbers
        bath_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', user_message.lower())
        if bath_matches:
            session.user_preferences.property_preferences['min_bathrooms'] = float(bath_matches[0])
        
        # Look for square footage
        sqft_matches = re.findall(r'(\d+)\s*(?:sq|square|sqft)', user_message.lower())
        if sqft_matches:
            session.user_preferences.property_preferences['min_sqft'] = int(sqft_matches[0])
        
        session.user_preferences.completed_sections.add('property_specs')
        session.current_step = ChatbotStep.BUDGET
        
        try:
            budget_prompt = f"""
            The user specified property specifications: "{user_message}"
            
            Acknowledge their preferences and now ask about their budget:
            - What's their maximum purchase price?
            - How much are they looking to invest?
            - Any target for monthly cash flow?
            
            Be encouraging and mention that understanding their budget helps find the best deals.
            """
            
            response = await self.model.generate_content_async(budget_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in property specs step: {e}")
            return """Great! I've captured your property size preferences.

Now for the important part - let's talk budget:
• What's your maximum purchase price?
• How much total are you looking to invest (including down payment, closing costs, etc.)?
• Do you have a target for monthly cash flow?

Understanding your budget helps me find properties that make financial sense for your goals!"""
    
    async def _handle_budget_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle budget preferences"""
        
        # Parse budget information (simplified)
        import re
        
        # Look for dollar amounts
        price_matches = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:k|000)?)', user_message.lower())
        if price_matches:
            price_str = price_matches[0].replace(',', '').replace('k', '000')
            try:
                max_price = int(price_str)
                if max_price < 1000:  # Assume it's in thousands
                    max_price *= 1000
                session.user_preferences.financial_preferences['max_price'] = max_price
            except ValueError:
                pass
        
        session.user_preferences.completed_sections.add('budget')
        session.current_step = ChatbotStep.INVESTMENT_STRATEGY
        
        try:
            strategy_prompt = f"""
            The user specified their budget: "{user_message}"
            
            Acknowledge their budget and now ask about investment strategy:
            - Buy and hold for rental income?
            - Fix and flip for quick profits?
            - BRRRR (Buy, Rehab, Rent, Refinance, Repeat)?
            
            Explain briefly what each strategy means and ask which appeals to them.
            """
            
            response = await self.model.generate_content_async(strategy_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in budget step: {e}")
            return """Perfect! I've noted your budget preferences.

Now let's discuss investment strategy. What's your goal with these properties?

**Buy and Hold**: Purchase properties to rent out for steady monthly income and long-term appreciation

**Fix and Flip**: Buy undervalued properties, renovate them, and sell quickly for profit

**BRRRR**: Buy, Rehab, Rent, Refinance, Repeat - a strategy to scale your portfolio using recycled capital

Which strategy interests you most, or are you open to multiple approaches?"""
    
    async def _handle_investment_strategy_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle investment strategy preferences"""
        
        # Parse strategy (simplified)
        user_message_lower = user_message.lower()
        strategies = []
        
        if any(word in user_message_lower for word in ['buy and hold', 'rental', 'cash flow']):
            strategies.append(InvestmentStrategy.BUY_AND_HOLD)
        if any(word in user_message_lower for word in ['flip', 'renovate', 'fix']):
            strategies.append(InvestmentStrategy.FIX_AND_FLIP)
        if any(word in user_message_lower for word in ['brrrr', 'refinance']):
            strategies.append(InvestmentStrategy.BRRRR)
        
        if not strategies:  # Default
            strategies = [InvestmentStrategy.BUY_AND_HOLD]
        
        session.user_preferences.financial_preferences['investment_strategies'] = strategies
        session.user_preferences.completed_sections.add('investment_strategy')
        session.current_step = ChatbotStep.TIMELINE
        
        try:
            timeline_prompt = f"""
            The user specified their investment strategy: "{user_message}"
            
            Acknowledge their strategy choice and ask about timeline:
            - How soon are they looking to purchase?
            - Are they looking to buy one property or multiple?
            
            Keep it brief as we're near the end of preference collection.
            """
            
            response = await self.model.generate_content_async(timeline_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in investment strategy step: {e}")
            return """Excellent choice! I've noted your investment strategy preferences.

Just a couple more quick questions:
• How soon are you looking to purchase? (next month, 3 months, 6 months?)
• Are you planning to buy just one property or multiple properties?

This helps me prioritize the search results for you!"""
    
    async def _handle_timeline_step(self, session: ChatbotSession, user_message: str) -> str:
        """Handle timeline preferences and move to summary"""
        
        # Parse timeline (simplified)
        user_message_lower = user_message.lower()
        if any(word in user_message_lower for word in ['month', 'soon', 'asap']):
            session.user_preferences.timeline_preferences['purchase_timeline'] = 'immediate'
        elif any(word in user_message_lower for word in ['3', 'three', 'quarter']):
            session.user_preferences.timeline_preferences['purchase_timeline'] = '3_months'
        else:
            session.user_preferences.timeline_preferences['purchase_timeline'] = '6_months'
        
        session.user_preferences.completed_sections.add('timeline')
        session.current_step = ChatbotStep.SUMMARY
        
        return await self._handle_summary_step(session, user_message)
    
    async def _handle_summary_step(self, session: ChatbotSession, user_message: str) -> str:
        """Summarize preferences and hand off to deal_finder"""
        
        preferences = session.user_preferences
        
        # Create summary
        summary_parts = []
        
        # Location
        if preferences.location_preferences['cities']:
            summary_parts.append(f"Location: {', '.join(preferences.location_preferences['cities'])}")
        elif preferences.location_preferences['states']:
            summary_parts.append(f"State: {', '.join(preferences.location_preferences['states'])}")
        
        # Property types
        if preferences.property_preferences['property_types']:
            types = [pt.value.replace('_', ' ').title() if hasattr(pt, 'value') else str(pt) for pt in preferences.property_preferences['property_types']]
            summary_parts.append(f"Property Types: {', '.join(types)}")
        
        # Budget
        if preferences.financial_preferences['max_price']:
            summary_parts.append(f"Max Budget: ${preferences.financial_preferences['max_price']:,}")
        
        # Strategy
        if preferences.financial_preferences['investment_strategies']:
            strategies = [s.value.replace('_', ' ').title() if hasattr(s, 'value') else str(s) for s in preferences.financial_preferences['investment_strategies']]
            summary_parts.append(f"Strategy: {', '.join(strategies)}")
        
        summary_text = "\\n• ".join(summary_parts)
        
        # Mark preferences as complete
        preferences.is_complete = True
        session.current_step = ChatbotStep.HANDOFF
        
        # Get conversation context for a natural summary
        conversation_context = session.get_conversation_context(last_n_messages=20)
        
        try:
            summary_prompt = f"""
            You are wrapping up a conversation about real estate preferences and preparing to search for properties.
            
            FULL CONVERSATION HISTORY:
            {conversation_context}
            
            CURRENT MESSAGE: "{user_message}"
            
            COLLECTED PREFERENCES:
            {summary_text}
            
            REMEMBER: Reference the conversation naturally. Show that you remember their specific needs and situation.
            
            Create a friendly, personalized summary that:
            1. Acknowledges their current message
            2. References key things they told you during the conversation  
            3. Summarizes their preferences in a natural, conversational way
            4. Shows enthusiasm about finding properties for their specific situation
            5. Lets them know you're now searching for matching properties
            
            Be enthusiastic and personal - reference specific details they shared to show you were listening.
            """
            
            ai_response = await self.model.generate_content_async(summary_prompt)
            
            # Trigger handoff to deal_finder
            await self._handoff_to_deal_finder(session)
            
            return ai_response.text
            
        except Exception as e:
            logger.error(f"Error in summary step: {e}")
            await self._handoff_to_deal_finder(session)  # Still do handoff
            return f"""Perfect! Here's what I have for your property search:

• {summary_text}

I'm now searching for undervalued properties that match your criteria. I'll hand this information off to our deal-finding system to locate the best opportunities for you!

Give me a moment to analyze the market and find some great deals... 🏠"""
    
    async def _handoff_to_deal_finder(self, session: ChatbotSession):
        """Hand off user preferences to deal_finder"""
        
        session.awaiting_handoff = True
        
        # Convert preferences to search criteria
        search_criteria = session.user_preferences.to_search_criteria()
        
        # Create handoff data
        handoff_data = {
            'session_id': session.session_id,
            'user_preferences': {
                'location': session.user_preferences.location_preferences,
                'property': session.user_preferences.property_preferences,
                'financial': session.user_preferences.financial_preferences,
                'timeline': session.user_preferences.timeline_preferences
            },
            'search_criteria': search_criteria.dict() if hasattr(search_criteria, 'dict') else search_criteria.__dict__,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Handing off session {session.session_id} to deal_finder")
        
        # Call the deal_finder callback if provided
        if self.deal_finder_callback:
            try:
                await self.deal_finder_callback(handoff_data)
            except Exception as e:
                logger.error(f"Error in deal_finder handoff: {e}")
        
        return handoff_data
    
    # Property Results Handling Methods
    
    async def receive_property_results(self, session_id: str, property_results: List[Dict[str, Any]]) -> str:
        """Receive and process property results from deal_finder"""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Received results for unknown session: {session_id}")
            return "I'm sorry, I couldn't find your search session. Please start a new search."
        
        session = self.active_sessions[session_id]
        
        if not property_results:
            return await self._handle_no_results(session)
        
        # Store results in session
        session.property_results = property_results
        session.awaiting_handoff = False
        
        logger.info(f"Received {len(property_results)} property results for session {session_id}")
        
        # Create summary of best properties
        summary = await self._create_property_summary(session, property_results)
        
        session.add_message("assistant", summary)
        return summary
    
    async def _handle_no_results(self, session: ChatbotSession) -> str:
        """Handle case when no properties are found"""
        
        no_results_prompt = f"""
        No undervalued properties were found matching the user's criteria.
        
        User preferences:
        - Location: {session.user_preferences.location_preferences}
        - Property type: {session.user_preferences.property_preferences.get('property_types', [])}
        - Budget: ${session.user_preferences.financial_preferences.get('max_price', 'Not specified')}
        - Strategy: {session.user_preferences.financial_preferences.get('investment_strategies', [])}
        
        Provide encouraging response suggesting:
        1. Expanding search criteria (different areas, price range, property types)
        2. Setting up alerts for when new properties become available
        3. Adjusting expectations or strategy
        
        Be supportive and offer to help modify their search.
        """
        
        try:
            response = await self.model.generate_content_async(no_results_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating no results response: {e}")
            return """I wasn't able to find any undervalued properties matching your exact criteria right now, but don't worry - this is actually pretty common in competitive markets!

Here are a few options to consider:

🔍 **Expand Your Search:**
• Consider nearby areas or different neighborhoods
• Adjust your price range slightly higher or lower
• Look at different property types (condos, townhouses, small multi-family)

⏰ **Set Up Alerts:**
• I can monitor the market for new listings that match your criteria
• Get notified when prices drop on properties you're interested in

📈 **Strategy Adjustment:**
• Consider properties that need minor cosmetic work
• Look at emerging neighborhoods with growth potential

Would you like me to search with broader criteria, or would you prefer to modify any of your preferences?"""
    
    async def _create_property_summary(self, session: ChatbotSession, property_results: List[Dict[str, Any]]) -> str:
        """Create a user-friendly summary of the best properties found"""
        
        # Sort properties by deal_score (assuming this field exists)
        sorted_properties = sorted(property_results, 
                                 key=lambda p: p.get('deal_score', 0), 
                                 reverse=True)
        
        # Take top 5 properties
        top_properties = sorted_properties[:5]
        
        # Get conversation context to personalize the results
        conversation_context = session.get_conversation_context(last_n_messages=15)
        
        # Create summary prompt for AI
        summary_prompt = f"""
        Create an enthusiastic, personalized summary of the best undervalued investment properties found for the user.
        
        CONVERSATION HISTORY (remember their specific situation and needs):
        {conversation_context}
        
        User's preferences collected:
        - Location: {', '.join(session.user_preferences.location_preferences.get('cities', []) or session.user_preferences.location_preferences.get('states', []))}
        - Property types: {[str(pt) for pt in session.user_preferences.property_preferences.get('property_types', [])]}
        - Max budget: ${session.user_preferences.financial_preferences.get('max_price', 'Not specified')}
        - Strategy: {[str(s) for s in session.user_preferences.financial_preferences.get('investment_strategies', [])]}
        
        Top properties found:
        {json.dumps(top_properties, indent=2)}
        
        REMEMBER: Reference the conversation naturally. Show that you remember their specific situation and why they're looking for properties.
        
        Create a summary that:
        1. Celebrates finding great deals based on their SPECIFIC situation mentioned in the conversation
        2. Highlights the top 3-5 properties with key details
        3. Explains why each matches their particular needs and situation
        4. Mentions deal scores and cash flow potential relevant to their strategy
        5. Encourages next steps (viewing, making offers, etc.) that make sense for their situation
        
        Use bullet points and clear formatting. Be enthusiastic but professional.
        Reference specific things they mentioned earlier to show you remember their conversation.
        """
        
        try:
            response = await self.model.generate_content_async(summary_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error creating AI summary: {e}")
            # Fallback to manual summary
            return self._create_fallback_summary(top_properties, session.user_preferences)
    
    def _create_fallback_summary(self, properties: List[Dict[str, Any]], preferences: UserPreferences) -> str:
        """Create a fallback summary when AI is unavailable"""
        
        if not properties:
            return "No properties found matching your criteria."
        
        summary_lines = []
        summary_lines.append(f"🎉 **Great news! I found {len(properties)} undervalued investment properties matching your criteria!**\n")
        
        for i, prop in enumerate(properties[:5], 1):
            address = prop.get('address', 'Address not available')
            deal_score = prop.get('deal_score', 0)
            price = prop.get('listing_price', prop.get('price', 0))
            cash_flow = prop.get('monthly_cash_flow', prop.get('projected_cash_flow', 0))
            
            summary_lines.append(f"**{i}. {address}**")
            summary_lines.append(f"   💰 Price: ${price:,} | Deal Score: {deal_score}/100")
            
            if cash_flow > 0:
                summary_lines.append(f"   📈 Monthly Cash Flow: ${cash_flow:.0f}")
            
            # Add key insight if available
            insight = prop.get('key_insight', prop.get('analysis_summary', ''))
            if insight:
                summary_lines.append(f"   🎯 Why it's great: {insight[:100]}{'...' if len(insight) > 100 else ''}")
            
            summary_lines.append("")  # Empty line
        
        summary_lines.append("🚀 **Next Steps:**")
        summary_lines.append("• Schedule property viewings for your top choices")
        summary_lines.append("• Get pre-approved for financing if you haven't already")
        summary_lines.append("• Consider making offers with appropriate contingencies")
        summary_lines.append("• Conduct thorough due diligence on your favorites")
        
        return "\n".join(summary_lines)
    
    async def get_property_details(self, session_id: str, property_index: int) -> str:
        """Get detailed information about a specific property from results"""
        
        if session_id not in self.active_sessions:
            return "Session not found. Please start a new search."
        
        session = self.active_sessions[session_id]
        
        if not hasattr(session, 'property_results') or not session.property_results:
            return "No property results available. Please run a search first."
        
        if property_index < 1 or property_index > len(session.property_results):
            return f"Invalid property number. Please choose between 1 and {len(session.property_results)}."
        
        property_data = session.property_results[property_index - 1]
        
        # Create detailed explanation prompt
        detail_prompt = f"""
        Provide a detailed analysis of this investment property for the user.
        
        Property data:
        {json.dumps(property_data, indent=2)}
        
        Create a comprehensive breakdown including:
        1. Property overview (address, size, type, price)
        2. Financial analysis (deal score, cash flow, ROI)
        3. Investment highlights and opportunities
        4. Potential risks or considerations
        5. Recommended next steps for this specific property
        
        Make it detailed but easy to understand.
        """
        
        try:
            response = await self.model.generate_content_async(detail_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error creating property details: {e}")
            return self._create_fallback_property_details(property_data)
    
    def _create_fallback_property_details(self, property_data: Dict[str, Any]) -> str:
        """Create fallback property details when AI is unavailable"""
        
        details = []
        details.append(f"🏠 **Property Details**")
        details.append(f"Address: {property_data.get('address', 'Not available')}")
        details.append(f"Price: ${property_data.get('listing_price', property_data.get('price', 0)):,}")
        details.append(f"Deal Score: {property_data.get('deal_score', 0)}/100")
        
        # Property specs
        if property_data.get('bedrooms'):
            details.append(f"Bedrooms: {property_data.get('bedrooms')}")
        if property_data.get('bathrooms'):
            details.append(f"Bathrooms: {property_data.get('bathrooms')}")
        if property_data.get('square_feet'):
            details.append(f"Square Feet: {property_data.get('square_feet'):,}")
        
        # Financial details
        details.append(f"\n💰 **Financial Analysis**")
        if property_data.get('monthly_cash_flow'):
            details.append(f"Monthly Cash Flow: ${property_data.get('monthly_cash_flow'):.0f}")
        if property_data.get('cap_rate'):
            details.append(f"Cap Rate: {property_data.get('cap_rate'):.1f}%")
        if property_data.get('arv_estimate'):
            details.append(f"After Repair Value: ${property_data.get('arv_estimate'):,}")
        
        # Key insight
        if property_data.get('key_insight'):
            details.append(f"\n🎯 **Key Insight**")
            details.append(property_data.get('key_insight'))
        
        return "\n".join(details)
    
    async def request_more_properties(self, session_id: str, modified_criteria: Optional[Dict[str, Any]] = None) -> str:
        """Request more properties with potentially modified criteria"""
        
        if session_id not in self.active_sessions:
            return "Session not found. Please start a new search."
        
        session = self.active_sessions[session_id]
        
        # Update criteria if provided
        if modified_criteria:
            self._update_search_criteria(session, modified_criteria)
        
        # Trigger new handoff to deal_finder
        session.awaiting_handoff = True
        await self._handoff_to_deal_finder(session)
        
        return "I'm searching for more properties with your updated criteria. Give me a moment to find some great deals for you!"
    
    def _update_search_criteria(self, session: ChatbotSession, modifications: Dict[str, Any]):
        """Update user preferences based on modifications"""
        
        preferences = session.user_preferences
        
        # Update location if provided
        if 'location' in modifications:
            if 'cities' in modifications['location']:
                preferences.location_preferences['cities'] = modifications['location']['cities']
            if 'states' in modifications['location']:
                preferences.location_preferences['states'] = modifications['location']['states']
        
        # Update financial criteria
        if 'budget' in modifications:
            if 'max_price' in modifications['budget']:
                preferences.financial_preferences['max_price'] = modifications['budget']['max_price']
            if 'min_price' in modifications['budget']:
                preferences.financial_preferences['min_price'] = modifications['budget']['min_price']
        
        # Update property criteria
        if 'property' in modifications:
            for key, value in modifications['property'].items():
                preferences.property_preferences[key] = value
        
        logger.info(f"Updated search criteria for session {session.session_id}")
    
    def get_session_property_count(self, session_id: str) -> int:
        """Get the number of properties found in a session"""
        
        if session_id not in self.active_sessions:
            return 0
        
        session = self.active_sessions[session_id]
        return len(getattr(session, 'property_results', []))
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a chatbot session"""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "current_step": session.current_step.value,
            "progress_percentage": session.user_preferences.get_progress_percentage(),
            "completed_sections": list(session.user_preferences.completed_sections),
            "is_complete": session.user_preferences.is_complete,
            "awaiting_handoff": session.awaiting_handoff,
            "message_count": len(session.conversation_history),
            "last_activity": session.last_activity.isoformat(),
            "created_at": session.created_at.isoformat()
        }
    
    def end_session(self, session_id: str) -> bool:
        """End a chatbot session"""
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Ended chatbot session: {session_id}")
            return True
        return False

    async def handle_general_query(self, query: str, context: Optional[Dict[str, Any]] = None, user_type: UserType = None, session: Optional[ChatbotSession] = None) -> str:
        """Handle general questions naturally and conversationally"""
        
        # Detect user type if not provided
        if not user_type:
            user_type = self._detect_user_type(query)
        
        # Create a session-like object for context method if no session provided
        if not session:
            session = type('obj', (object,), {'user_type': user_type})()
        
        user_context = self._get_conversation_context_for_ai(session)
        
        # Include conversation history if we have a real session
        conversation_context = ""
        if hasattr(session, 'get_conversation_context'):
            conversation_context = f"\nCONVERSATION HISTORY:\n{session.get_conversation_context(last_n_messages=10)}\n"
        
        # Add context if provided
        context_text = ""
        if context:
            context_text = f"\nAdditional context: {json.dumps(context, indent=2)}"
        
        full_prompt = f"""
        You're a knowledgeable, friendly real estate assistant having a natural conversation.
        
        The person you're talking to: {user_context}
        {conversation_context}
        CURRENT QUESTION: "{query}"
        
        REMEMBER: If there's conversation history above, reference it naturally and build on what was discussed.
        Show that you remember previous parts of the conversation.
        
        Respond naturally and helpfully. You specialize in undervalued properties - homes priced below market value.
        Be conversational, not formal. Answer their actual question directly.
        
        {context_text}
        """
        
        try:
            response = await self.model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            return "I'm not sure I understood that completely. Could you tell me more about what you're looking for?"
    
    async def explain_analysis_results(self, analysis_result: Dict[str, Any], user_type: UserType = None) -> str:
        """Explain property analysis results with user-type-specific language"""
        
        if not user_type:
            user_type = UserType.UNKNOWN
        
        deal_score = analysis_result.get("deal_score", 0)
        investment_potential = analysis_result.get("investment_potential", "Unknown")
        address = analysis_result.get("address", "the property")
        market_value = analysis_result.get('market_value', analysis_result.get('arv_estimate', 'N/A'))
        list_price = analysis_result.get('list_price', 'N/A')
        
        # Calculate undervalued amount if possible
        undervalued_amount = "N/A"
        if isinstance(market_value, (int, float)) and isinstance(list_price, (int, float)):
            undervalued_amount = f"${market_value - list_price:,.0f}"
        
        # User-type-specific prompts
        prompts = {
            UserType.NEW_HOMEBUYER: f"""
            You are explaining why this undervalued home is a great opportunity for a first-time homebuyer.
            
            Property: {address}
            Value Score: {deal_score}/100
            Market Value: ${market_value:,} (estimated)
            List Price: ${list_price:,}
            Potential Savings: {undervalued_amount}
            
            Explain in homebuyer-friendly terms:
            1. How much money they could save vs typical market prices
            2. How this builds instant equity in their home
            3. Why this property offers great value
            4. Simple next steps for a home purchase
            
            Focus on home ownership benefits, not investment returns.
            """,
            
            UserType.REALTOR: f"""
            You are providing professional analysis to a realtor about an undervalued property opportunity.
            
            Property: {address}
            Market Analysis Score: {deal_score}/100
            Estimated Market Value: ${market_value:,}
            Current List Price: ${list_price:,}
            Below-Market Opportunity: {undervalued_amount}
            
            Provide professional insights on:
            1. Why this property is undervalued in the current market
            2. Key selling points to present to clients
            3. Comparative market analysis implications
            4. Strategic considerations for offers and negotiations
            
            Use professional real estate language appropriate for an agent.
            """,
            
            UserType.INVESTOR: f"""
            You are analyzing an undervalued investment property opportunity.
            
            Property: {address}
            Deal Score: {deal_score}/100
            Investment Rating: {investment_potential}
            Market Value: ${market_value:,}
            Purchase Price: ${list_price:,}
            Equity Opportunity: {undervalued_amount}
            Monthly Cash Flow: ${analysis_result.get('monthly_cash_flow', 0):,.2f}
            Recommended Strategy: {analysis_result.get('recommended_strategy', 'N/A')}
            
            Provide investment analysis covering:
            1. ROI potential from below-market purchase
            2. Cash flow and appreciation prospects
            3. Risk assessment and mitigation strategies
            4. Strategic recommendations for this investment
            
            Use investment terminology and focus on financial metrics.
            """
        }
        
        prompt = prompts.get(user_type, prompts[UserType.INVESTOR])  # Default to investor if unknown
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error explaining analysis results: {e}")
            return self._fallback_explanation(analysis_result, user_type)
    
    async def explain_deal_score(self, score: float, rating: str) -> str:
        """Explain what a deal score means"""
        
        template = self.explanation_templates["deal_score_explanation"]
        prompt = template.format(score=score, rating=rating)
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error explaining deal score: {e}")
            return self._fallback_deal_score_explanation(score, rating)
    
    async def explain_investment_strategy(self, strategy: str, address: str, metrics: Dict[str, Any]) -> str:
        """Explain why a particular investment strategy is recommended"""
        
        template = self.explanation_templates["investment_strategy_explanation"]
        prompt = template.format(
            strategy=strategy,
            address=address,
            metrics=json.dumps(metrics, indent=2)
        )
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error explaining investment strategy: {e}")
            return self._fallback_strategy_explanation(strategy)
    
    async def explain_risks(self, risk_assessment: Dict[str, Any]) -> str:
        """Explain investment risks in customer-friendly terms"""
        
        template = self.explanation_templates["risk_explanation"]
        prompt = template.format(risks=json.dumps(risk_assessment, indent=2))
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error explaining risks: {e}")
            return "There are some risks to consider with this investment. I'd recommend reviewing the detailed risk assessment and consulting with a real estate professional."
    
    async def explain_market_conditions(self, market_data: Dict[str, Any], location: str) -> str:
        """Explain local market conditions"""
        
        template = self.explanation_templates["market_explanation"]
        prompt = template.format(
            market_data=json.dumps(market_data, indent=2),
            location=location
        )
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error explaining market conditions: {e}")
            return f"The market conditions in {location} show mixed signals. I'd recommend getting a more detailed market analysis."
    
    async def provide_next_steps(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on analysis results"""
        
        deal_score = analysis_result.get("deal_score", 0)
        investment_potential = analysis_result.get("investment_potential", "Unknown")
        
        prompt = f"""
        Based on this property analysis, suggest 3-5 specific next steps for the investor:
        
        Deal Score: {deal_score}/100
        Investment Rating: {investment_potential}
        Recommended Strategy: {analysis_result.get('recommended_strategy', 'N/A')}
        
        Provide actionable, specific steps they should take next.
        Format as a JSON array of strings: ["step 1", "step 2", ...]
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group())
                return steps if isinstance(steps, list) else []
        except Exception as e:
            logger.error(f"Error generating next steps: {e}")
        
        # Fallback steps based on deal score
        return self._fallback_next_steps(deal_score, investment_potential)
    
    async def answer_followup_question(self, question: str, analysis_context: Dict[str, Any]) -> str:
        """Answer follow-up questions about a property analysis"""
        
        prompt = f"""
        You are helping an investor understand their property analysis. Answer their follow-up question clearly and helpfully.
        
        Original Analysis Context:
        {json.dumps(analysis_context, indent=2)}
        
        Follow-up Question: {question}
        
        Provide a helpful, specific answer based on the analysis data. If you don't have enough information, 
        suggest what additional data or analysis might be needed.
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error answering follow-up question: {e}")
            return "I'd be happy to help with that question, but I'm having trouble accessing the analysis details right now. Could you please be more specific about what you'd like to know?"
    
    # Fallback methods when AI fails
    
    def _fallback_explanation(self, analysis_result: Dict[str, Any], user_type: UserType = None) -> str:
        """Fallback explanation when AI fails, tailored by user type"""
        deal_score = analysis_result.get("deal_score", 0)
        investment_potential = analysis_result.get("investment_potential", "Unknown")
        
        if not user_type:
            user_type = UserType.UNKNOWN
        
        # User-type-specific fallback messages
        if user_type == UserType.NEW_HOMEBUYER:
            if deal_score >= 80:
                return f"This looks like an excellent undervalued home opportunity with a score of {deal_score}/100! You could save significant money compared to typical market prices and build instant equity."
            elif deal_score >= 60:
                return f"This property shows good value with a score of {deal_score}/100. It appears to be priced below market value, which could mean great savings for you as a homebuyer."
            elif deal_score >= 40:
                return f"This property has moderate value ({deal_score}/100). While it may be somewhat undervalued, you might want to negotiate on price or look for better deals."
            else:
                return f"This property scores {deal_score}/100, which suggests it may not offer the best value. You might want to keep looking for homes with better pricing opportunities."
        
        elif user_type == UserType.REALTOR:
            if deal_score >= 80:
                return f"This is an excellent below-market opportunity scoring {deal_score}/100. Strong potential for client satisfaction and competitive advantage in pricing."
            elif deal_score >= 60:
                return f"Good undervalued property opportunity ({deal_score}/100). Worth presenting to clients interested in below-market purchases."
            elif deal_score >= 40:
                return f"Moderate opportunity ({deal_score}/100). May require strategic pricing negotiations to maximize client benefit."
            else:
                return f"Limited opportunity ({deal_score}/100). May want to focus on properties with stronger below-market potential."
        
        else:  # INVESTOR or UNKNOWN
            if deal_score >= 80:
                return f"This looks like an excellent investment opportunity with a deal score of {deal_score}/100! The analysis suggests this property has strong potential for good returns."
            elif deal_score >= 60:
                return f"This property shows good investment potential with a score of {deal_score}/100. It's worth taking a closer look and maybe getting a professional inspection."
            elif deal_score >= 40:
                return f"This property has moderate potential ({deal_score}/100). You might want to negotiate on price or look for ways to improve the returns."
            else:
                return f"This property scores {deal_score}/100, which suggests it may not be the best investment opportunity. You might want to keep looking for better deals."
    
    def _fallback_deal_score_explanation(self, score: float, rating: str) -> str:
        """Fallback deal score explanation"""
        if score >= 80:
            return f"A score of {score}/100 is excellent! This means the property is likely undervalued and has strong cash flow potential. These are the deals investors dream of finding."
        elif score >= 60:
            return f"A score of {score}/100 is good. This property meets most investment criteria and could be a solid addition to your portfolio with proper due diligence."
        elif score >= 40:
            return f"A score of {score}/100 is fair. The property has some positive aspects but also some concerns. You'd want to negotiate or find ways to improve the returns."
        else:
            return f"A score of {score}/100 suggests this property doesn't meet typical investment criteria. You might want to look for better opportunities."
    
    def _fallback_strategy_explanation(self, strategy: str) -> str:
        """Fallback strategy explanation"""
        strategy_explanations = {
            "buy_and_hold": "Buy and hold means purchasing this property to rent out for steady monthly income and long-term appreciation. It's great for building wealth over time.",
            "flip": "Flipping means buying, renovating, and quickly reselling this property for a profit. It requires more work but can provide faster returns.",
            "brrrr": "BRRRR (Buy, Rehab, Rent, Refinance, Repeat) means improving the property, renting it out, then refinancing to pull your money out and do it again.",
            "wholesale": "Wholesaling means getting this property under contract and selling that contract to another investor for a quick profit without owning the property."
        }
        
        return strategy_explanations.get(strategy, f"The recommended {strategy} strategy could be a good approach for this property.")
    
    def _fallback_next_steps(self, deal_score: float, investment_potential: str) -> List[str]:
        """Fallback next steps based on deal score"""
        
        if deal_score >= 70:
            return [
                "Schedule a property inspection to verify condition",
                "Research the neighborhood and comparable sales",
                "Get pre-approved for financing",
                "Make an offer with appropriate contingencies",
                "Plan your renovation budget if needed"
            ]
        elif deal_score >= 50:
            return [
                "Negotiate a lower purchase price",
                "Get a detailed inspection to identify issues",
                "Research local rental rates more thoroughly",
                "Consider different financing options",
                "Look for ways to increase property value"
            ]
        else:
            return [
                "Keep searching for better deals",
                "Review your investment criteria",
                "Consider different neighborhoods or property types",
                "Build your knowledge of local markets",
                "Network with other investors for deal flow"
            ]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Customer Agent health status"""
        try:
            test_response = await self.model.generate_content_async("Hello, are you working?")
            response_time = 0.5  # Placeholder for actual timing
            
            return {
                "status": "healthy" if test_response.text else "degraded",
                "model": "gemini-2.5-flash",
                "response_time_ms": int(response_time * 1000),
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": "gemini-2.5-flash",
                "last_check": datetime.now().isoformat()
            }
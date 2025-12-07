# Code Documentation - Home Value Estimator

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Core Modules](#core-modules)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Services](#services)
6. [Frontend Components](#frontend-components)

---

## System Architecture

### Overview
The Home Value Estimator is a full-stack web application that combines:
- **FastAPI** backend server for REST API
- **Google Gemini AI** for conversational interface and property valuation
- **ATTOM Data API** for real estate property data
- **Vanilla JavaScript** frontend for user interaction

### Architecture Diagram
```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI Server │
│  (Python)       │
└────────┬────────┘
         │
    ┌────┴────┬───────────┬──────────┐
    ▼         ▼           ▼          ▼
┌──────┐ ┌────────┐ ┌─────────┐ ┌────────┐
│Customer│ │Property│ │ ATTOM   │ │Gemini  │
│ Agent  │ │Analysis│ │   API   │ │  AI    │
└────────┘ └────────┘ └─────────┘ └────────┘
```

---

## Core Modules

### 1. customer_agent_server.py
**Purpose**: Main FastAPI application server that handles HTTP requests and coordinates between frontend and backend services.

#### Key Components:

**Data Models (Pydantic)**
```python
class FrontendPreferences(BaseModel):
    """User preferences from frontend form"""
    location: Optional[str]           # City, state, or ZIP
    property_types: Optional[List[str]]  # Types of properties
    budget_min: Optional[int]         # Minimum budget
    budget_max: Optional[int]         # Maximum budget

class ChatStartRequest(BaseModel):
    """Request to start a new chat session"""
    user_id: Optional[str]            # Unique user identifier
    frontend_data: Optional[FrontendPreferences]  # Pre-filled data

class ChatMessageRequest(BaseModel):
    """User message in conversation"""
    session_id: str                   # Session identifier
    message: str                      # User's message text
```

**Helper Functions**

```python
def extract_location_from_message(message: str) -> Optional[Dict[str, str]]
```
- Extracts location information from natural language text
- Supports ZIP codes (5 digits)
- Parses "City, ST" format
- Recognizes common city names
- Returns: `{'city': 'Miami', 'state': 'FL'}` or `{'zip_code': '33101'}`

```python
def format_properties_for_chat(properties: List, location: Dict[str, str]) -> str
```
- Formats property search results for chatbot display
- Includes dual pricing: ATTOM price + AI fair value estimate
- Highlights undervalued properties
- Returns formatted string for conversation

**API Endpoints**
- `POST /chat/start` - Initialize new chat session
- `POST /chat/message` - Send message to chatbot
- `GET /` - Serve frontend HTML

---

### 2. find_property.py
**Purpose**: Integration with ATTOM Data API for property search and data retrieval.

#### Key Components:

**Data Classes**
```python
@dataclass
class PropertyResult:
    """Complete property information with valuations"""
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    lot_size: Optional[float]
    year_built: Optional[int]
    
    # Pricing
    listing_price: Optional[float]        # ATTOM market value
    fair_value_estimate: Optional[float]  # AI estimate
    ai_confidence: Optional[str]          # Confidence level
    ai_reasoning: Optional[str]           # AI explanation
    
    # Additional data
    assessed_value: Optional[float]
    market_value: Optional[float]
    last_sale_price: Optional[float]
    last_sale_date: Optional[str]
```

**ATTOMPropertyFinder Class**

```python
class ATTOMPropertyFinder:
    def __init__(self):
        """Initialize with API key and AI analysis engine"""
        
    async def find_properties_by_location(
        city: str = None, 
        state: str = None,
        zip_code: str = None,
        max_results: int = 50
    ) -> List[PropertyResult]:
        """
        Search for properties by location
        
        Flow:
        1. Resolve city/state to ZIP codes
        2. Query ATTOM API for properties
        3. Parse and structure property data
        4. Request AI fair value estimates
        5. Return enriched property results
        """
```

**Key Methods**
- `_search_by_zip_code()` - Query ATTOM API by ZIP
- `_parse_attom_property()` - Convert API response to PropertyResult
- `_get_ai_valuation()` - Get AI fair value estimate
- `_generate_mock_data()` - Fallback data when API unavailable

---

### 3. property_analysis_engine.py
**Purpose**: AI-powered property valuation using Google Gemini.

#### Key Components:

**Data Classes**
```python
@dataclass
class PropertyForAnalysis:
    """Input data for AI analysis"""
    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[float]
    lot_size: Optional[float]
    year_built: Optional[int]
    property_type: Optional[str]
    listing_price: Optional[float]
    zestimate: Optional[float]
    rent_estimate: Optional[float]
    last_sale_price: Optional[float]
    last_sale_date: Optional[str]
    property_taxes: Optional[float]
    hoa_fee: Optional[float]

@dataclass 
class FairValueEstimate:
    """AI valuation result"""
    estimated_value: float
    confidence_level: str              # "high", "medium", "low"
    analysis_factors: List[str]        # Key factors considered
    market_comparison: Optional[str]   # Market context
    reasoning: Optional[str]           # Detailed explanation
```

**PropertyAnalysisEngine Class**

```python
class PropertyAnalysisEngine:
    def __init__(self):
        """Initialize Gemini AI model"""
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    async def estimate_fair_value(
        property_data: PropertyForAnalysis
    ) -> FairValueEstimate:
        """
        Generate AI-powered property valuation
        
        Process:
        1. Build comprehensive analysis prompt
        2. Send to Gemini AI
        3. Parse JSON response
        4. Validate and structure result
        5. Return fair value estimate
        """
```

**Analysis Prompt Structure**
The AI prompt includes:
- Property characteristics (beds, baths, sqft, year)
- Location context
- Current market data (listing price, last sale)
- Comparables information
- Market conditions

**Response Format**
```json
{
  "estimated_value": 425000,
  "confidence_level": "high",
  "analysis_factors": [
    "Property size and condition",
    "Location desirability",
    "Recent market trends"
  ],
  "market_comparison": "Above median for area",
  "reasoning": "Detailed explanation..."
}
```

---

### 4. agents/customer_agent.py
**Purpose**: Conversational AI agent for natural language interaction with users.

#### Key Components:

**Enumerations**
```python
class UserType(Enum):
    NEW_HOMEBUYER = "new_homebuyer"
    REALTOR = "realtor"
    INVESTOR = "investor"
    UNKNOWN = "unknown"

class ChatbotStep(Enum):
    GREETING = "greeting"
    LOCATION = "location"
    PROPERTY_TYPE = "property_type"
    PROPERTY_SPECS = "property_specs"
    BUDGET = "budget"
    INVESTMENT_STRATEGY = "investment_strategy"
    TIMELINE = "timeline"
    SUMMARY = "summary"
    HANDOFF = "handoff"
```

**UserPreferences Class**
```python
class UserPreferences:
    """Collects and structures user search preferences"""
    
    location_preferences = {
        'cities': [],
        'states': [],
        'zip_codes': [],
        'radius_miles': None
    }
    
    property_preferences = {
        'property_types': [],
        'min_bedrooms': None,
        'max_bedrooms': None,
        'min_bathrooms': None,
        'max_bathrooms': None,
        'min_sqft': None,
        'max_sqft': None
    }
    
    financial_preferences = {
        'min_price': None,
        'max_price': None,
        'target_cash_flow': None,
        'max_investment': None
    }
    
    def to_search_criteria() -> ATTOMSearchCriteria:
        """Convert to ATTOM API search format"""
```

**CustomerAgent Class**
```python
class CustomerAgent:
    def __init__(self, user_id: str):
        """Initialize conversational agent with Gemini"""
        
    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process user message and generate response
        
        Flow:
        1. Determine current conversation step
        2. Extract information from message
        3. Update user preferences
        4. Generate contextual response
        5. Progress to next step if complete
        """
```

**Conversation Flow**
1. **GREETING** - Welcome user, understand their needs
2. **LOCATION** - Collect city/state/ZIP information
3. **PROPERTY_TYPE** - Determine property preferences
4. **PROPERTY_SPECS** - Get bedroom/bathroom requirements
5. **BUDGET** - Understand financial constraints
6. **INVESTMENT_STRATEGY** - For investors, understand goals
7. **TIMELINE** - When they want to purchase
8. **SUMMARY** - Confirm all collected information
9. **HANDOFF** - Execute property search

---

## Data Models

### models/data_models.py
**Purpose**: Shared data structures used across the application.

**Key Models**

```python
class PropertyType(Enum):
    """Supported property categories"""
    PRIMARY_RESIDENCE = "primary-residence"
    FIX_FLIP = "fix-flip"
    RENTAL_PROPERTY = "rental-property"
    MULTI_FAMILY = "multi-family"
    COMMERCIAL = "commercial"
    LAND = "land"

class InvestmentStrategy(Enum):
    """Investment approaches"""
    BUY_AND_HOLD = "buy-and-hold"
    FIX_AND_FLIP = "fix-and-flip"
    WHOLESALE = "wholesale"
    BRRRR = "brrrr"  # Buy, Rehab, Rent, Refinance, Repeat
    RENTAL = "rental"

@dataclass
class Property:
    """Comprehensive property data structure"""
    # Basic info
    id: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    
    # Physical characteristics
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[float]
    lot_size: Optional[float]
    year_built: Optional[int]
    
    # Dual pricing system
    listing_price: Optional[float]        # ATTOM data
    fair_value_estimate: Optional[float]  # AI estimate
    ai_confidence: Optional[str]
    ai_reasoning: Optional[str]
    
    # Financial data
    zestimate: Optional[float]
    rent_estimate: Optional[float]
    property_taxes: Optional[float]
    hoa_fee: Optional[float]

class ATTOMSearchCriteria(BaseModel):
    """Search parameters for ATTOM API"""
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    min_price: Optional[int]
    max_price: Optional[int]
    min_beds: Optional[int]
    max_beds: Optional[int]
    min_baths: Optional[float]
    max_baths: Optional[float]
    property_types: Optional[List[str]]
    max_results: Optional[int] = 10
```

---

## Services

### services/city_state_zip_mapper.py
**Purpose**: Convert city/state names to ZIP codes for property searches.

**Key Components**

```python
@dataclass
class CityInfo:
    """City information with ZIP codes"""
    city: str
    state: str
    zip_codes: List[str]
    place_type: Optional[str]
    county_names: Optional[List[str]]
    aliases: Optional[List[str]]
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    
    @property
    def city_state_key(self) -> str:
        """Returns 'City, ST' format"""
        
    @property
    def primary_zips(self) -> List[str]:
        """First 5 ZIP codes for quick search"""
        
    @property
    def all_zips(self) -> List[str]:
        """All ZIP codes for comprehensive search"""

class CityStateZipMapper:
    """Service for city/state to ZIP conversion"""
    
    def __init__(self, mapping_file_path: str = None):
        """Load mapping data from JSON file"""
        
    def load_mapping_data(self) -> bool:
        """Load city2zip_data.json"""
        
    def get_zip_codes(
        self, 
        city: str, 
        state: str,
        primary_only: bool = False
    ) -> List[str]:
        """
        Get ZIP codes for a city/state
        
        Args:
            city: City name (e.g., "Miami")
            state: State code (e.g., "FL")
            primary_only: Return only primary ZIPs (default: False)
            
        Returns:
            List of ZIP codes
        """
```

**Convenience Functions**
```python
def get_city_zip_mapper() -> CityStateZipMapper:
    """Get global singleton mapper instance"""

def get_zip_codes_for_city(
    city: str, 
    state: str,
    primary_only: bool = False
) -> List[str]:
    """Quick function to get ZIPs for a city"""
```

---

## API Endpoints

### POST /chat/start
**Purpose**: Initialize a new chat session with the customer agent.

**Request Body**
```json
{
  "user_id": "optional-user-id",
  "frontend_data": {
    "location": "Miami, FL",
    "property_types": ["primary-residence"],
    "budget_min": 200000,
    "budget_max": 500000
  }
}
```

**Response**
```json
{
  "session_id": "uuid-session-id",
  "message": "Welcome! I'm here to help you find properties...",
  "status": "active"
}
```

---

### POST /chat/message
**Purpose**: Send a user message and receive chatbot response.

**Request Body**
```json
{
  "session_id": "uuid-session-id",
  "message": "I'm looking for a 3 bedroom house in Miami"
}
```

**Response**
```json
{
  "session_id": "uuid-session-id",
  "message": "Great! I found several 3-bedroom properties in Miami...",
  "current_step": "property_specs",
  "completed": false,
  "preferences_collected": {
    "location": {"city": "Miami", "state": "FL"},
    "bedrooms": 3
  }
}
```

**Conversation States**
- `completed: false` - Still collecting preferences
- `completed: true` - Ready to search properties
- `current_step` - Current stage in conversation flow

---

### GET /
**Purpose**: Serve the frontend application HTML.

**Response**: HTML file with embedded chat interface

---

## Frontend Components

### index (1).html
**Purpose**: Main application interface

**Key Elements**
- Chat container for conversation
- Message input field
- Property display cards
- Responsive layout

**Structure**
```html
<div id="chat-container">
  <div id="messages"></div>
  <div id="properties"></div>
  <input id="user-input" type="text" />
  <button id="send-btn">Send</button>
</div>
```

---

### script (1).js
**Purpose**: Frontend JavaScript for chat interaction

**Key Functions**

```javascript
async function startChat(userData) {
    // Initialize chat session
    // POST to /chat/start
    // Store session_id
}

async function sendMessage(message) {
    // Send user message
    // POST to /chat/message
    // Display response
    // Render properties if available
}

function displayMessage(message, isUser) {
    // Add message to chat UI
    // Apply appropriate styling
}

function displayProperties(properties) {
    // Create property cards
    // Show dual pricing
    // Highlight undervalued properties
}
```

**Event Handlers**
- `sendBtn.click` - Send message on button click
- `userInput.keypress` - Send on Enter key
- `window.load` - Initialize chat on page load

---

### styles (1).css
**Purpose**: Application styling and layout

**Key Styles**
- Chat container layout
- Message bubbles (user vs bot)
- Property cards
- Responsive design
- Color scheme and typography

---

## Data Flow

### Property Search Flow
```
1. User sends message "I want a house in Miami"
2. Frontend → POST /chat/message
3. CustomerAgent extracts location
4. Agent calls ATTOMPropertyFinder
5. PropertyFinder resolves city → ZIP codes
6. PropertyFinder queries ATTOM API
7. For each property:
   a. Parse ATTOM data
   b. Call PropertyAnalysisEngine
   c. Get AI fair value estimate
   d. Combine data into PropertyResult
8. Return formatted results to agent
9. Agent formats conversational response
10. Response → Frontend
11. Frontend displays properties + chat
```

### AI Valuation Flow
```
1. PropertyAnalysisEngine receives property data
2. Build comprehensive analysis prompt
3. Include property characteristics
4. Include market context
5. Send to Gemini AI
6. Parse JSON response
7. Validate data structure
8. Return FairValueEstimate
```

---

## Error Handling

### API Errors
- **Missing API Keys**: Falls back to mock data
- **ATTOM API Errors**: Logs error, uses mock data
- **Gemini API Errors**: Returns default estimate

### Validation
- Input sanitization for location queries
- Price range validation
- Property specification validation

### Logging
```python
logger.info()    # Informational messages
logger.warning() # Warnings (e.g., missing API key)
logger.error()   # Error conditions
```

---

## Configuration

### Environment Variables (.env)
```bash
# Required
ATTOM_API_KEY=your_attom_api_key
GEMINI_API_KEY=your_gemini_api_key

# Optional
LOG_LEVEL=INFO
MAX_PROPERTIES=50
```

### File Paths
All paths are relative to project root:
- Data files: `data/`
- Configuration: `.env` in root
- Code: `code/`

---

## Testing

### Test Structure
```
tests/
└── test_agent_communication_fixed.py
```

### Test Cases
1. **test_property_finder()** - Property search functionality
2. **test_customer_agent_initialization()** - Agent setup

### Running Tests
```bash
python -m pytest tests/ -v
```

---

## Performance Considerations

### Caching
- City-to-ZIP mapper uses singleton pattern
- Loaded once per application lifecycle

### Async Operations
- All API calls are async (async/await)
- Non-blocking I/O for better performance

### Rate Limiting
- ATTOM API: Respect rate limits
- Gemini API: Batch requests when possible

---

## Security

### API Key Management
- Stored in `.env` file
- Never committed to Git (in `.gitignore`)
- Loaded at runtime

### Input Validation
- Sanitize user messages
- Validate location queries
- Prevent injection attacks

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment

### Requirements
- Python 3.8+
- All dependencies in `requirements.txt`
- Valid API keys

### Startup
```bash
# Development
python start_server.py

# Production
uvicorn customer_agent_server:app --host 0.0.0.0 --port 8000
```

### Server Configuration
- Host: `0.0.0.0` (all interfaces)
- Port: `8000`
- Reload: Enabled in development

---

## Future Enhancements

### Planned Features
1. Property image integration
2. Historical price trends
3. Neighborhood analytics
4. Mortgage calculator
5. Saved searches
6. Email notifications

### Scalability
- Database integration for user sessions
- Redis caching for API responses
- Load balancing for multiple instances
- CDN for static assets

---

## Appendix

### External APIs

**ATTOM Data API**
- Endpoint: `https://api.gateway.attomdata.com/propertyapi/v1.0.0`
- Documentation: https://api.developer.attomdata.com/
- Features: Property search, valuations, sales history

**Google Gemini AI**
- Model: `gemini-2.0-flash-exp`
- Documentation: https://ai.google.dev/
- Features: Natural language, analysis, JSON output

### Data Files

**city2zip_data.json**
- Format: JSON
- Size: ~15MB
- Records: 30,000+ cities
- Fields: city, state, ZIP codes, coordinates, FIPS codes

### Dependencies
See `requirements.txt` for complete list:
- fastapi - Web framework
- uvicorn - ASGI server
- google-generativeai - Gemini AI
- httpx - Async HTTP client
- pydantic - Data validation
- python-dotenv - Environment management

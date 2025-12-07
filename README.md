# CS2104 Project - Home Value Estimator Chatbot

## Project Overview and Purpose

The Home Value Estimator Chatbot is an AI-powered real estate assistant that helps users find properties and estimate their fair market values. The system integrates:
- **ATTOM Data API** for real estate property search and data
- **Google Gemini AI** for conversational agent interaction and intelligent value analysis
- **FastAPI Backend** for RESTful API services
- **Interactive Frontend** for user-friendly property exploration

The chatbot guides users through property searches, retrieves comprehensive property details, and provides AI-powered fair value estimates based on multiple factors including property characteristics, market conditions, and comparable sales data.

## Video Link

https://www.youtube.com/watch?v=aooYItFJ-6w&feature=youtu.be

## Installation and Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip package manager
- API Keys:
  - ATTOM Data API key (get from https://api.developer.attomdata.com/)
  - Google Gemini API key (get from https://aistudio.google.com/app/apikey)

### Step 1: Clone the Repository

```bash
git clone https://github.com/krispykeys/CS2104-Project.git
cd CS2104-Project
```

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r data/requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory with your API keys:

```env
ATTOM_API_KEY=your_attom_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## How to Run the Program and Reproduce Results

### Start the Backend Server

```bash
# From the project root directory
cd code
python -m uvicorn customer_agent_server:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`

### Access the Frontend

1. Open your web browser
2. Navigate to `http://localhost:8000` or open `code/frontend/index (1).html` directly
3. The chatbot interface will load

### Using the Application

1. **Start a Conversation**: Click "Send" or type a greeting
2. **Specify Location**: Tell the bot where you want to search (e.g., "I'm looking in Miami, FL")
3. **Set Preferences**: Provide budget, property type, bedrooms, etc.
4. **Review Results**: The bot will find properties matching your criteria
5. **Get Value Estimates**: Each property includes:
   - ATTOM's Automated Valuation Model (AVM) estimate
   - Zestimate (when available)
   - AI-powered fair value estimate from Gemini
   - Detailed property characteristics

### Testing

Run the test suite:

```bash
# From the project root directory
python -m pytest tests/
```

## Technologies and Libraries Used

### Backend
- **FastAPI** - Modern web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI
- **Pydantic** - Data validation using Python type hints
- **python-dotenv** - Environment variable management

### AI & Machine Learning
- **google-generativeai** - Google Gemini 2.5 Pro AI integration
- **ATTOM Data API** - Real estate data and property valuations

### Data Processing
- **httpx** - Async HTTP client for API calls
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing

### Testing
- **pytest** - Testing framework
- **pytest-asyncio** - Async testing support
- **respx** - HTTP mocking for tests

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling
- **JavaScript (ES6+)** - Interactive functionality
- **Fetch API** - Backend communication

## Project Structure

```
CS2104-Project/
├── code/                          # All source code files
│   ├── agents/                    # AI agent components
│   │   ├── __init__.py
│   │   └── customer_agent.py      # Conversational AI agent
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   └── data_models.py         # Pydantic data structures
│   ├── services/                  # Business logic services
│   │   ├── __init__.py
│   │   └── city_state_zip_mapper.py  # Location mapping
│   ├── frontend/                  # Web interface
│   │   ├── index (1).html         # Main HTML page
│   │   ├── script (1).js          # Frontend JavaScript
│   │   ├── styles (1).css         # Styling
│   │   └── [image assets]         # UI images
│   ├── customer_agent_server.py   # FastAPI server
│   ├── find_property.py           # ATTOM API integration
│   └── property_analysis_engine.py # AI value estimation
├── data/                          # Configuration and data files
│   ├── city2zip.json              # City to ZIP code mapping
│   ├── city2zip_data.json         # Extended location data
│   └── requirements.txt           # Python dependencies
├── tests/                         # Test scripts
│   └── test_agent_communication_fixed.py
├── docs/                          # Documentation and screenshots
│   └── README.md
├── report/                        # Final report document
│   └── README.md
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## Author(s) and Contribution Summary

**Insung Lee**
- Full-stack development of the chatbot application
- Integration of ATTOM Data API and Google Gemini AI
- Backend API design and implementation
- Frontend user interface development
- AI prompt engineering for property analysis
- Testing and documentation

## Features

### Core Functionality
- Natural language conversational interface
- Real-time property search by location
- Multi-criteria filtering (budget, bedrooms, bathrooms, property type)
- Comprehensive property details display
- Multiple valuation methods (AVM, Zestimate, AI estimate)

### AI-Powered Analysis
- Context-aware conversation flow
- Intelligent property value estimation
- Market condition analysis
- Comparable sales consideration
- Detailed reasoning for estimates

### User Experience
- Clean, intuitive interface
- Real-time chat interaction
- Property cards with images and details
- Responsive design
- Error handling and validation

## API Endpoints

- `POST /chat/start` - Initialize chat session
- `POST /chat/message` - Send message to chatbot
- `GET /` - Serve frontend application

## Future Enhancements

- Property image gallery integration
- Historical price trend visualization
- Neighborhood statistics and demographics
- Mortgage calculator integration
- Saved searches and favorites
- Email notifications for new listings
- Mobile application development


## Acknowledgments

- ATTOM Data Solutions for property data API
- Google for Gemini AI capabilities
- CS2104 course staff for project guidance
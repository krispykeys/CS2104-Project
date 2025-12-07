"""
Data models for Home Value Estimator Real Estate Platform
==============================================

This module contains all the data models and type definitions used throughout
the Home Value Estimator platform for property analysis, search, and user management.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class PropertyType(Enum):
    """Property types supported by the platform"""
    PRIMARY_RESIDENCE = "primary-residence"
    FIX_FLIP = "fix-flip"
    RENTAL_PROPERTY = "rental-property"
    MULTI_FAMILY = "multi-family"
    QUICK_DEALS = "quick-deals"
    COMMERCIAL = "commercial"
    LAND = "land"


class InvestmentStrategy(Enum):
    """Investment strategies supported by the platform"""
    BUY_AND_HOLD = "buy-and-hold"
    FIX_AND_FLIP = "fix-and-flip"
    WHOLESALE = "wholesale"
    BRRRR = "brrrr"
    LIVE_IN_FLIP = "live-in-flip"
    RENTAL = "rental"


@dataclass
class Property:
    """Enhanced property data structure with dual pricing"""
    id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[float] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    
    # Dual pricing system
    listing_price: Optional[float] = None  # From ATTOM API (market/assessed value)
    fair_value_estimate: Optional[float] = None  # From AI analysis engine
    ai_confidence: Optional[str] = None  # AI confidence level (high/medium/low)
    ai_reasoning: Optional[str] = None  # AI analysis reasoning
    
    # Additional ATTOM data
    zestimate: Optional[float] = None
    rent_estimate: Optional[float] = None
    tax_assessment: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[str] = None
    days_on_market: Optional[int] = None
    hoa_fee: Optional[float] = None
    property_taxes: Optional[float] = None
    insurance_estimate: Optional[float] = None


class ATTOMSearchCriteria(BaseModel):
    """Search criteria for ATTOM API property search"""
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    min_baths: Optional[float] = None
    max_baths: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    property_types: Optional[List[str]] = None
    max_results: Optional[int] = 10


class PropertySearchResult(BaseModel):
    """Result from property search operations"""
    property: Property
    match_score: Optional[float] = None
    distance_miles: Optional[float] = None
    market_context: Optional[Dict[str, Any]] = None


class PropertySearchResponse(BaseModel):
    """Response from property search API"""
    results: List[PropertySearchResult]
    total_found: int
    search_criteria: ATTOMSearchCriteria
    execution_time_ms: Optional[float] = None
    message: Optional[str] = None


class MarketAnalysis(BaseModel):
    """Market analysis data for a specific area"""
    area_name: str
    median_home_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    average_rent: Optional[float] = None
    rent_to_price_ratio: Optional[float] = None
    cap_rate_estimate: Optional[float] = None
    appreciation_rate: Optional[float] = None
    inventory_level: Optional[str] = None
    days_on_market_avg: Optional[int] = None
    price_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    rental_yield: Optional[float] = None
    last_updated: Optional[datetime] = None


class PropertyAnalysis(BaseModel):
    """Comprehensive analysis of a property investment"""
    property: Property
    market_analysis: Optional[MarketAnalysis] = None
    investment_metrics: Optional[Dict[str, Any]] = None
    cash_flow_projection: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    analysis_date: Optional[datetime] = None


class QuickAnalysisResponse(BaseModel):
    """Quick analysis response for property evaluation"""
    property_id: str
    address: str
    estimated_value: Optional[float] = None
    rent_estimate: Optional[float] = None
    cap_rate: Optional[float] = None
    cash_on_cash_return: Optional[float] = None
    monthly_cash_flow: Optional[float] = None
    investment_grade: Optional[str] = None  # "A", "B", "C", "D", "F"
    key_insights: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None


class UserProfile(BaseModel):
    """User profile and preferences"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    investment_experience: Optional[str] = None  # "beginner", "intermediate", "advanced"
    preferred_strategies: Optional[List[InvestmentStrategy]] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_locations: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None  # "low", "medium", "high"
    time_horizon: Optional[str] = None  # "short", "medium", "long"
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
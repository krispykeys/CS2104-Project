"""
Clean Property Analysis Engine
=============================

A focused analysis engine using Gemini 2.5 Pro to estimate fair property values
based on property characteristics, market conditions, and comparable sales data.
"""

import google.generativeai as genai
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class PropertyForAnalysis:
    """Property data structure for analysis"""
    address: str
    city: str
    state: str
    zip_code: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[float] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    listing_price: Optional[float] = None
    zestimate: Optional[float] = None
    rent_estimate: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[str] = None
    property_taxes: Optional[float] = None
    hoa_fee: Optional[float] = None


@dataclass 
class FairValueEstimate:
    """Fair value estimate result"""
    estimated_value: float
    confidence_level: str  # "high", "medium", "low"
    analysis_factors: List[str]
    market_comparison: Optional[str] = None
    reasoning: Optional[str] = None


class PropertyAnalysisEngine:
    """Clean analysis engine using Gemini 2.5 Pro for property valuation"""
    
    def __init__(self):
        """Initialize the analysis engine"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Configure Gemini 2.5 Pro
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        logger.info("✅ Property Analysis Engine initialized with Gemini 2.0 Flash")
    
    async def estimate_fair_value(self, property_data: PropertyForAnalysis) -> FairValueEstimate:
        """
        Estimate fair market value of a property using AI analysis
        
        Args:
            property_data: Property information to analyze
            
        Returns:
            FairValueEstimate with estimated value and analysis
        """
        try:
            # Build comprehensive analysis prompt
            analysis_prompt = self._build_analysis_prompt(property_data)
            
            # Get AI analysis
            response = await self._get_gemini_analysis(analysis_prompt)
            
            # Parse and validate response
            estimate = self._parse_analysis_response(response, property_data)
            
            logger.info(f"✅ Generated fair value estimate: ${estimate.estimated_value:,.0f} for {property_data.address}")
            
            return estimate
            
        except Exception as e:
            logger.error(f"❌ Error estimating fair value for {property_data.address}: {e}")
            
            # Return fallback estimate
            fallback_value = self._get_fallback_estimate(property_data)
            return FairValueEstimate(
                estimated_value=fallback_value,
                confidence_level="low",
                analysis_factors=["Fallback estimate due to analysis error"],
                reasoning=f"Unable to complete full analysis: {str(e)}"
            )
    
    def _build_analysis_prompt(self, prop: PropertyForAnalysis) -> str:
        """Build comprehensive analysis prompt for Gemini"""
        
        # Calculate property age
        current_year = datetime.now().year
        property_age = current_year - prop.year_built if prop.year_built else "Unknown"
        
        # Build price context
        price_context = []
        if prop.listing_price:
            price_context.append(f"Current listing price: ${prop.listing_price:,.0f}")
        if prop.zestimate:
            price_context.append(f"Zillow estimate: ${prop.zestimate:,.0f}")
        if prop.last_sale_price:
            price_context.append(f"Last sale: ${prop.last_sale_price:,.0f} on {prop.last_sale_date or 'unknown date'}")
        
        prompt = f"""
You are a professional real estate appraiser with 20+ years of experience. Analyze this property and provide a fair market value estimate.

PROPERTY DETAILS:
📍 Address: {prop.address}, {prop.city}, {prop.state} {prop.zip_code}
🏠 Type: {prop.property_type or 'Unknown'}
🛏️ Bedrooms: {prop.bedrooms or 'Unknown'}
🛁 Bathrooms: {prop.bathrooms or 'Unknown'}
📐 Square Feet: {prop.square_feet or 'Unknown'}
📏 Lot Size: {prop.lot_size or 'Unknown'} sqft
📅 Year Built: {prop.year_built or 'Unknown'} (Age: {property_age} years)

FINANCIAL DATA:
{chr(10).join(price_context) if price_context else "No pricing data available"}
💰 Property Taxes: ${prop.property_taxes or 0:,.0f}/year
🏢 HOA Fee: ${prop.hoa_fee or 0:,.0f}/month
💵 Rent Estimate: ${prop.rent_estimate or 0:,.0f}/month

ANALYSIS REQUIREMENTS:
1. Consider location desirability and market trends in {prop.city}, {prop.state}
2. Evaluate property condition based on age and typical maintenance
3. Compare to similar properties in the {prop.zip_code} area
4. Factor in current market conditions (interest rates, inventory, demand)
5. Assess investment potential and rental income capability

Please provide your analysis in this EXACT JSON format:
{{
    "estimated_value": [your fair market value estimate as number],
    "confidence_level": "[high/medium/low]",
    "analysis_factors": [
        "Factor 1 that influenced your estimate",
        "Factor 2 that influenced your estimate", 
        "Factor 3 that influenced your estimate"
    ],
    "market_comparison": "Brief comparison to similar properties in the area",
    "reasoning": "Your detailed reasoning for this valuation in 2-3 sentences"
}}

Focus on providing a realistic, market-based valuation that reflects current conditions and comparable sales.
"""
        
        return prompt
    
    async def _get_gemini_analysis(self, prompt: str) -> str:
        """Get analysis from Gemini 2.5 Pro"""
        try:
            # Use async generation if available, otherwise use sync
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=1000,
                    temperature=0.3  # Lower temperature for more consistent valuations
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting Gemini analysis: {e}")
            raise
    
    def _parse_analysis_response(self, response: str, property_data: PropertyForAnalysis) -> FairValueEstimate:
        """Parse and validate Gemini response"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            analysis_data = json.loads(json_str)
            
            # Validate and clean the data
            estimated_value = float(analysis_data.get('estimated_value', 0))
            
            # Sanity check the estimate
            if estimated_value < 10000 or estimated_value > 50000000:
                logger.warning(f"Unusual estimate: ${estimated_value:,.0f}, applying fallback")
                estimated_value = self._get_fallback_estimate(property_data)
            
            return FairValueEstimate(
                estimated_value=estimated_value,
                confidence_level=analysis_data.get('confidence_level', 'medium'),
                analysis_factors=analysis_data.get('analysis_factors', ['AI analysis completed']),
                market_comparison=analysis_data.get('market_comparison'),
                reasoning=analysis_data.get('reasoning')
            )
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            
            # Try to extract a number from the response as fallback
            import re
            numbers = re.findall(r'\$?[\d,]+', response)
            if numbers:
                try:
                    # Take the largest reasonable number
                    values = [float(n.replace('$', '').replace(',', '')) for n in numbers]
                    reasonable_values = [v for v in values if 10000 <= v <= 10000000]
                    if reasonable_values:
                        estimated_value = max(reasonable_values)
                        return FairValueEstimate(
                            estimated_value=estimated_value,
                            confidence_level="low",
                            analysis_factors=["Extracted from partial AI response"],
                            reasoning="Partial analysis due to parsing error"
                        )
                except:
                    pass
            
            # Ultimate fallback
            fallback_value = self._get_fallback_estimate(property_data)
            return FairValueEstimate(
                estimated_value=fallback_value,
                confidence_level="low", 
                analysis_factors=["Fallback calculation due to parsing error"],
                reasoning="Unable to parse AI analysis response"
            )
    
    def _get_fallback_estimate(self, prop: PropertyForAnalysis) -> float:
        """Generate fallback estimate when AI analysis fails"""
        
        # Use available price data as fallback
        if prop.zestimate and prop.zestimate > 0:
            return prop.zestimate
        
        if prop.listing_price and prop.listing_price > 0:
            return prop.listing_price * 0.95  # Assume 5% below listing
        
        if prop.last_sale_price and prop.last_sale_price > 0:
            # Adjust for appreciation (assume 3% per year)
            if prop.last_sale_date:
                try:
                    sale_year = int(prop.last_sale_date[:4])
                    years_since_sale = datetime.now().year - sale_year
                    appreciation_factor = (1.03 ** years_since_sale)
                    return prop.last_sale_price * appreciation_factor
                except:
                    pass
            return prop.last_sale_price
        
        # Calculate based on square footage if available
        if prop.square_feet and prop.square_feet > 0:
            # Use rough price per sqft based on location
            if prop.state in ['CA', 'NY', 'MA']:
                price_per_sqft = 300
            elif prop.state in ['TX', 'FL', 'GA', 'NC']:
                price_per_sqft = 150  
            elif prop.state in ['VA', 'MD', 'DC']:
                price_per_sqft = 200
            else:
                price_per_sqft = 120
            
            return prop.square_feet * price_per_sqft
        
        # Last resort: use rent estimate with cap rate
        if prop.rent_estimate and prop.rent_estimate > 0:
            annual_rent = prop.rent_estimate * 12
            # Assume 6% cap rate
            return annual_rent / 0.06
        
        # Absolute fallback
        return 250000


# Export main class for use
__all__ = ['PropertyAnalysisEngine', 'PropertyForAnalysis', 'FairValueEstimate']
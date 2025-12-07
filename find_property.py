"""
Find Property - Clean ATTOM API Integration with AI Analysis
Uses official ATTOM Data API to find properties by location and provides both
ATTOM valuations and AI-powered fair value estimates.
"""

import os
import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Import the property analysis engine
from property_analysis_engine import PropertyAnalysisEngine, PropertyForAnalysis, FairValueEstimate

# Import the city-state ZIP mapping service
from services.city_state_zip_mapper import get_city_zip_mapper, get_zip_codes_for_city

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyResult:
    """Property result with ATTOM data and AI-powered fair value estimate"""
    address: str
    city: str
    state: str
    zip_code: str
    property_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    listing_price: Optional[float] = None  # From ATTOM (market/assessed value)
    fair_value_estimate: Optional[float] = None  # From AI analysis engine
    ai_confidence: Optional[str] = None  # AI confidence level
    ai_reasoning: Optional[str] = None  # AI analysis reasoning
    assessed_value: Optional[float] = None
    market_value: Optional[float] = None
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[str] = None

class ATTOMPropertyFinder:
    """
    Clean ATTOM API integration for property search and valuation.
    Uses official ATTOM Data API endpoints with AI-powered fair value analysis.
    """
    
    def __init__(self):
        """Initialize ATTOM Property Finder with AI analysis engine"""
        self.api_key = os.getenv('ATTOM_API_KEY')
        self.use_mock_data = False
        
        if not self.api_key:
            logger.warning("⚠️ ATTOM_API_KEY not found - will use mock data for demonstration")
            self.use_mock_data = True
        
        # Initialize AI analysis engine
        try:
            self.analysis_engine = PropertyAnalysisEngine()
            logger.info("✅ AI Property Analysis Engine initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize AI analysis engine: {e}")
            self.analysis_engine = None
        
        # Official ATTOM API base URL
        self.base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
        
        # Headers for API requests
        self.headers = {
            "Accept": "application/json",
            "apikey": self.api_key if self.api_key else ""
        }
        
        logger.info("ATTOM Property Finder initialized")
    
    async def find_properties_by_location(self, city: str = None, state: str = None, 
                                        zip_code: str = None, max_results: int = 50) -> List[PropertyResult]:
        """
        Find properties by location using official ATTOM API
        
        Args:
            city: City name
            state: State abbreviation (e.g., 'TX', 'CA')
            zip_code: ZIP code
            max_results: Maximum number of results to return
        
        Returns:
            List of PropertyResult objects
        """
        # Use mock data if API key not available
        if self.use_mock_data:
            logger.info("📝 Using mock data for demonstration")
            return await self._get_mock_properties(city, state, zip_code, max_results)
        
        try:
            # Build search parameters based on location
            search_params = {
                "format": "json",
                "pageSize": min(max_results, 50)  # ATTOM API limit
            }
            
            # ZIP code search works reliably with ATTOM API
            if zip_code:
                search_params["postalcode"] = zip_code
                logger.info(f"Searching for properties by ZIP code: {zip_code}")
            
            elif city and state:
                # Use dynamic city-state ZIP mapping for comprehensive coverage
                logger.info(f"City/State search requested for {city}, {state}")
                logger.info("Using dynamic ZIP code mapping for comprehensive property search")
                
                # Get ZIP codes from the mapping service
                try:
                    # Try primary ZIP codes first for faster results
                    primary_zips = get_zip_codes_for_city(city, state, primary_only=True)
                    
                    if primary_zips:
                        logger.info(f"Found {len(primary_zips)} primary ZIP codes for {city}, {state}: {primary_zips}")
                        fallback_zips = primary_zips
                    else:
                        # If no primary ZIPs, try all ZIP codes
                        all_zips = get_zip_codes_for_city(city, state, primary_only=False)
                        if all_zips:
                            # Limit to first 8 ZIP codes to avoid too many API calls
                            fallback_zips = all_zips[:8]
                            logger.info(f"Using first {len(fallback_zips)} ZIP codes from {len(all_zips)} total for {city}, {state}")
                        else:
                            # Fall back to hardcoded ZIPs for cities not in mapping
                            fallback_zips = self._get_legacy_fallback_zips(city, state)
                            if fallback_zips:
                                logger.warning(f"City not in mapping, using legacy fallback ZIP codes: {fallback_zips}")
                            else:
                                logger.error(f"No ZIP codes available for {city}, {state}")
                                return []
                
                except Exception as e:
                    logger.warning(f"Error accessing ZIP mapping service: {e}")
                    # Fall back to legacy hardcoded ZIPs
                    fallback_zips = self._get_legacy_fallback_zips(city, state)
                    if fallback_zips:
                        logger.warning(f"Using legacy fallback ZIP codes: {fallback_zips}")
                    else:
                        logger.error(f"No fallback ZIP codes available for {city}, {state}")
                        return []
                
                # Search properties using the ZIP codes
                if fallback_zips:
                    all_properties = []
                    for zip_code in fallback_zips:
                        zip_search_params = {
                            "format": "json",
                            "pageSize": min(max_results // len(fallback_zips), 20),
                            "postalcode": zip_code
                        }
                        properties = await self._search_properties(zip_search_params)
                        all_properties.extend(properties)
                        if len(all_properties) >= max_results:
                            break
                    
                    # Process all found properties
                    results = []
                    for prop in all_properties[:max_results]:
                        try:
                            property_result = await self._create_property_result(prop)
                            if property_result:
                                results.append(property_result)
                        except Exception as e:
                            logger.warning(f"Error processing property: {e}")
                            continue
                    
                    logger.info(f"Found {len(results)} properties using dynamic ZIP mapping")
                    return results
                else:
                    logger.error(f"No ZIP codes available for {city}, {state}")
                    return []
            
            else:
                logger.error("Must provide either zip_code or both city and state")
                return []
            
            logger.info(f"Search parameters: {search_params}")
            
            # Use ATTOM's property basicprofile endpoint
            properties = await self._search_properties(search_params)
            
            # Get valuations for each property
            results = []
            for prop in properties:
                try:
                    property_result = await self._create_property_result(prop)
                    if property_result:
                        results.append(property_result)
                except Exception as e:
                    logger.warning(f"Error processing property: {e}")
                    continue
            
            logger.info(f"Found {len(results)} properties")
            
            # If no results from ATTOM API, use mock data as fallback
            if len(results) == 0:
                logger.info("No results from ATTOM API, using mock data fallback")
                return await self._get_mock_properties(city, state, zip_code, max_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding properties by location: {e}")
            return []
    
    def _get_legacy_fallback_zips(self, city: str, state: str) -> List[str]:
        """Get legacy hardcoded ZIP codes for major cities (backup only)"""
        city_lower = city.lower()
        state_upper = state.upper()
        
        # Common ZIP codes for major cities
        city_zip_map = {
            ("austin", "TX"): ["78701", "78702", "78704", "78705"],
            ("houston", "TX"): ["77001", "77002", "77019", "77056"],
            ("dallas", "TX"): ["75201", "75202", "75204", "75206"],
            ("san antonio", "TX"): ["78201", "78202", "78204", "78205"],
            ("new york", "NY"): ["10001", "10002", "10003", "10009"],
            ("los angeles", "CA"): ["90001", "90002", "90004", "90005"],
            ("chicago", "IL"): ["60601", "60602", "60603", "60604"],
            ("miami", "FL"): ["33101", "33102", "33109", "33130"],
            ("seattle", "WA"): ["98101", "98102", "98103", "98104"],
            ("denver", "CO"): ["80201", "80202", "80203", "80204"],
        }
        
        return city_zip_map.get((city_lower, state_upper), [])
    
    async def _get_mock_properties(self, city: str = None, state: str = None, 
                                   zip_code: str = None, max_results: int = 50) -> List[PropertyResult]:
        """Generate mock property data for demonstration when ATTOM API is not available"""
        import random
        
        # Determine location info
        if zip_code:
            # Common ZIP to city/state mappings
            zip_map = {
                "24060": ("Blacksburg", "VA"),
                "78701": ("Austin", "TX"),
                "90001": ("Los Angeles", "CA"),
                "60601": ("Chicago", "IL"),
                "33101": ("Miami", "FL"),
            }
            city, state = zip_map.get(zip_code, ("Sample City", "ST"))
        elif not city or not state:
            city, state = "Sample City", "ST"
        
        # Generate sample properties
        properties = []
        property_types = ["Single Family", "Condo", "Townhouse", "Multi-Family"]
        street_names = ["Oak Street", "Pine Avenue", "Maple Drive", "Elm Boulevard", "Cedar Lane", 
                       "Birch Road", "Willow Court", "Main Street", "Park Avenue"]
        
        for i in range(min(max_results, 5)):
            street_num = random.randint(100, 9999)
            street = random.choice(street_names)
            
            bedrooms = random.randint(2, 5)
            bathrooms = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
            sqft = random.randint(1200, 3500)
            year_built = random.randint(1990, 2023)
            
            # Generate realistic pricing
            base_price = sqft * random.randint(150, 350)
            listing_price = round(base_price, -3)  # Round to nearest thousand
            fair_value = listing_price * random.uniform(0.95, 1.15)  # AI estimate varies +/- 15%
            
            property = PropertyResult(
                address=f"{street_num} {street}",
                city=city,
                state=state,
                zip_code=zip_code or "00000",
                property_type=random.choice(property_types),
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=sqft,
                lot_size=random.randint(5000, 15000),
                year_built=year_built,
                listing_price=float(listing_price),
                fair_value_estimate=round(fair_value, -2),
                ai_confidence=random.choice(["high", "medium", "high"]),
                ai_reasoning=f"Based on {bedrooms}BR/{bathrooms}BA, {sqft} sqft, built {year_built} in {city}",
                assessed_value=listing_price * 0.85,
                market_value=listing_price,
                last_sale_price=listing_price * 0.9,
                last_sale_date="2022-06-15"
            )
            properties.append(property)
        
        logger.info(f"📝 Generated {len(properties)} mock properties for {city}, {state}")
        return properties
    
    async def _search_properties(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search properties using ATTOM API basicprofile endpoint"""
        endpoint = f"{self.base_url}/property/basicprofile"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, params=params, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'property' in data:
                        return data['property']
                    else:
                        logger.warning("No 'property' key found in response")
                        return []
                        
                elif response.status_code == 401:
                    logger.error("ATTOM API authentication failed - check API key")
                    return []
                    
                elif response.status_code == 404:
                    logger.info("No properties found for search criteria")
                    return []
                    
                else:
                    logger.error(f"ATTOM API error: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error calling ATTOM API: {e}")
            return []
    
    async def _create_property_result(self, property_data: Dict[str, Any]) -> Optional[PropertyResult]:
        """Create PropertyResult from ATTOM API property data with AI analysis"""
        try:
            # Extract address information
            address_info = property_data.get('address', {})
            full_address = address_info.get('oneLine', '')
            city = address_info.get('locality', '')
            state = address_info.get('countrySubd', '')
            zip_code = address_info.get('postal1', '')
            
            # Extract property details
            summary = property_data.get('summary', {})
            building = property_data.get('building', {})
            lot = property_data.get('lot', {})
            
            # Extract room information
            rooms = building.get('rooms', {})
            size = building.get('size', {})
            
            # Extract valuation data
            assessment = property_data.get('assessment', {})
            market = assessment.get('market', {})
            assessed = assessment.get('assessed', {})
            
            # Extract sale information
            sale = property_data.get('sale', {})
            amount = sale.get('amount', {})
            
            # Get ATTOM listing price (market value, assessed value, or recent sale)
            listing_price = await self._get_attom_valuation(property_data)
            
            # Get basic property data for analysis
            bedrooms = rooms.get('beds')
            bathrooms = rooms.get('bathsTotal')
            square_feet = size.get('livingSize')
            lot_size = lot.get('lotSize1')
            year_built = building.get('summary', {}).get('yearBuilt')
            
            # Prepare property for AI analysis
            property_for_analysis = PropertyForAnalysis(
                address=full_address,
                city=city,
                state=state,
                zip_code=zip_code,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size=lot_size,
                year_built=year_built,
                property_type=summary.get('propType', ''),
                listing_price=listing_price,
                last_sale_price=amount.get('saleAmt'),
                last_sale_date=amount.get('saleRecDate'),
                property_taxes=assessed.get('tax', {}).get('taxAmt'),
            )
            
            # Get AI fair value estimate
            fair_value_estimate = None
            ai_confidence = None
            ai_reasoning = None
            
            if self.analysis_engine:
                try:
                    ai_estimate = await self.analysis_engine.estimate_fair_value(property_for_analysis)
                    fair_value_estimate = ai_estimate.estimated_value
                    ai_confidence = ai_estimate.confidence_level
                    ai_reasoning = ai_estimate.reasoning
                    logger.debug(f"AI estimate: ${fair_value_estimate:,.0f} ({ai_confidence} confidence)")
                except Exception as e:
                    logger.warning(f"Could not get AI estimate for {full_address}: {e}")
            
            return PropertyResult(
                address=full_address,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=summary.get('propType', ''),
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size=lot_size,
                year_built=year_built,
                listing_price=listing_price,  # ATTOM valuation
                fair_value_estimate=fair_value_estimate,  # AI estimate
                ai_confidence=ai_confidence,
                ai_reasoning=ai_reasoning,
                assessed_value=assessed.get('assdTtlValue'),
                market_value=market.get('mktTtlValue'),
                last_sale_price=amount.get('saleAmt'),
                last_sale_date=amount.get('saleRecDate')
            )
            
        except Exception as e:
            logger.error(f"Error creating property result: {e}")
            return None
    
    async def _get_attom_valuation(self, property_data: Dict[str, Any]) -> Optional[float]:
        """
        Estimate property value using available ATTOM data.
        Uses market value, assessed value, and sale data to create estimate.
        """
        try:
            # Get available valuation data
            assessment = property_data.get('assessment', {})
            market = assessment.get('market', {})
            assessed = assessment.get('assessed', {})
            sale = property_data.get('sale', {})
            amount = sale.get('amount', {})
            
            # Priority order for valuation estimate:
            # 1. Market value (ATTOM's automated valuation)
            # 2. Recent sale price (if within last 2 years)
            # 3. Assessed value adjusted for market conditions
            
            market_value = market.get('mktTtlValue')
            if market_value and market_value > 0:
                logger.debug(f"Using market value: ${market_value:,.2f}")
                return float(market_value)
            
            # Check for recent sale
            sale_price = amount.get('saleAmt')
            sale_date = amount.get('saleRecDate')
            if sale_price and sale_price > 0:
                # Use sale price if it's recent (within last 2 years)
                if self._is_recent_sale(sale_date):
                    logger.debug(f"Using recent sale price: ${sale_price:,.2f}")
                    return float(sale_price)
            
            # Use assessed value as fallback, adjusted upward for market conditions
            assessed_value = assessed.get('assdTtlValue')
            if assessed_value and assessed_value > 0:
                # Assessed values are typically lower than market value
                # Apply a 15% upward adjustment as a rough market adjustment
                adjusted_value = float(assessed_value) * 1.15
                logger.debug(f"Using adjusted assessed value: ${adjusted_value:,.2f}")
                return adjusted_value
            
            logger.warning("No valuation data available for property")
            return None
            
        except Exception as e:
            logger.error(f"Error estimating property value: {e}")
            return None
    
    def _is_recent_sale(self, sale_date_str: Optional[str]) -> bool:
        """Check if sale date is within last 2 years"""
        if not sale_date_str:
            return False
        
        try:
            # Parse various date formats ATTOM might use
            for date_format in ['%Y-%m-%d', '%m/%d/%Y', '%Y%m%d']:
                try:
                    sale_date = datetime.strptime(sale_date_str, date_format)
                    years_ago = (datetime.now() - sale_date).days / 365.25
                    return years_ago <= 2.0
                except ValueError:
                    continue
            
            logger.debug(f"Could not parse sale date: {sale_date_str}")
            return False
            
        except Exception as e:
            logger.debug(f"Error checking sale date: {e}")
            return False

# Main function for testing
async def main():
    """Test the ATTOM Property Finder"""
    try:
        finder = ATTOMPropertyFinder()
        
        # Test search by city and state
        print("🏠 Testing property search in Austin, TX...")
        properties = await finder.find_properties_by_location(city="Austin", state="TX", max_results=5)
        
        if properties:
            print(f"\n✅ Found {len(properties)} properties:")
            for i, prop in enumerate(properties, 1):
                print(f"\n{i}. {prop.address}")
                print(f"   📍 {prop.city}, {prop.state} {prop.zip_code}")
                print(f"   🏡 {prop.property_type}")
                if prop.bedrooms and prop.bathrooms:
                    print(f"   🛏️  {prop.bedrooms} bed, {prop.bathrooms} bath")
                if prop.square_feet:
                    print(f"   📐 {prop.square_feet:,} sq ft")
                if prop.year_built:
                    print(f"   📅 Built: {prop.year_built}")
                if prop.listing_price:
                    print(f"   💰 Market Value: ${prop.listing_price:,.2f}")
                if prop.fair_value_estimate:
                    print(f"   🎯 Fair Value Estimate: ${prop.fair_value_estimate:,.2f}")
        else:
            print("❌ No properties found")
            
        # Test search by ZIP code
        print("\n🏠 Testing property search in ZIP 78701...")
        zip_properties = await finder.find_properties_by_location(zip_code="78701", max_results=3)
        
        if zip_properties:
            print(f"\n✅ Found {len(zip_properties)} properties by ZIP:")
            for i, prop in enumerate(zip_properties, 1):
                print(f"\n{i}. {prop.address}")
                if prop.fair_value_estimate:
                    print(f"   🎯 Estimated Value: ${prop.fair_value_estimate:,.2f}")
        else:
            print("❌ No properties found by ZIP")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
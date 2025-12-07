"""
City-State to ZIP Code Mapping Service

This service loads and provides lookup functionality for the city2zip.json mapping data.
Supports the comprehensive JSON schema with metadata, FIPS codes, centroids, and aliases.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CityInfo:
    """Information about a city from the mapping data"""
    city: str
    state: str
    zip_codes: List[str]
    place_type: Optional[str] = None
    county_names: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    fips_state: Optional[str] = None
    fips_counties: Optional[List[str]] = None
    fips_place: Optional[str] = None

    @property
    def city_state_key(self) -> str:
        """Return standardized 'City, ST' key format"""
        return f"{self.city}, {self.state}"

    @property
    def primary_zips(self) -> List[str]:
        """Return first few ZIP codes as 'primary' for faster searches"""
        return self.zip_codes[:5]  # First 5 ZIPs as primary

    @property
    def all_zips(self) -> List[str]:
        """Return all ZIP codes for comprehensive searches"""
        return self.zip_codes


class CityStateZipMapper:
    """
    Service for mapping city/state combinations to ZIP codes
    
    Loads the city2zip.json schema and provides fast lookup functionality
    for converting city/state to ZIP codes for property searches.
    """
    
    def __init__(self, mapping_file_path: str = None):
        """
        Initialize the mapper with JSON data
        
        Args:
            mapping_file_path: Path to the city2zip data file
        """
        self.mapping_file = mapping_file_path or "city2zip_data.json"
        self.cities: Dict[str, CityInfo] = {}
        self.aliases: Dict[str, str] = {}  # alias -> canonical city_state key
        self.loaded = False
        
    def load_mapping_data(self) -> bool:
        """
        Load the city/ZIP mapping data from JSON file
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            mapping_path = Path(self.mapping_file)
            if not mapping_path.exists():
                logger.error(f"Mapping file not found: {mapping_path}")
                return False
                
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate basic schema structure
            if 'metadata' not in data or 'records' not in data:
                logger.error("Invalid schema: missing 'metadata' or 'records'")
                return False
                
            # Log metadata
            metadata = data.get('metadata', {})
            logger.info(f"Loading city mapping: {metadata.get('title', 'Unknown')}")
            logger.info(f"Version: {metadata.get('version', 'Unknown')}")
            
            # Load city records
            records = data.get('records', [])
            cities_loaded = 0
            
            for record in records:
                try:
                    city_info = self._parse_city_record(record)
                    if city_info:
                        # Add main city entry
                        self.cities[city_info.city_state_key] = city_info
                        cities_loaded += 1
                        
                        # Add alias entries
                        if city_info.aliases:
                            for alias in city_info.aliases:
                                alias_key = f"{alias}, {city_info.state}"
                                self.aliases[alias_key] = city_info.city_state_key
                                
                except Exception as e:
                    logger.warning(f"Error parsing city record: {e}")
                    continue
                    
            self.loaded = True
            logger.info(f"Loaded {cities_loaded} cities and {len(self.aliases)} aliases")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load mapping data: {e}")
            return False
            
    def _parse_city_record(self, record: Dict) -> Optional[CityInfo]:
        """Parse a single city record from the JSON data"""
        try:
            # Required fields
            city = record.get('city')
            state = record.get('state')
            zip_codes = record.get('zip_codes', [])
            
            if not city or not state or not zip_codes:
                logger.warning(f"Missing required fields in record: {record}")
                return None
                
            # Optional fields
            place_type = record.get('place_type')
            county_names = record.get('county_names')
            aliases = record.get('aliases')
            
            # Centroid coordinates
            centroid = record.get('centroid', {})
            centroid_lat = centroid.get('lat')
            centroid_lon = centroid.get('lon')
            
            # FIPS codes
            fips = record.get('fips', {})
            fips_state = fips.get('state_fips')
            fips_counties = fips.get('county_fips')
            fips_place = fips.get('place_fips')
            
            return CityInfo(
                city=city,
                state=state,
                zip_codes=zip_codes,
                place_type=place_type,
                county_names=county_names,
                aliases=aliases,
                centroid_lat=centroid_lat,
                centroid_lon=centroid_lon,
                fips_state=fips_state,
                fips_counties=fips_counties,
                fips_place=fips_place
            )
            
        except Exception as e:
            logger.error(f"Error parsing city record: {e}")
            return None
            
    def get_zip_codes(self, city: str, state: str, 
                     primary_only: bool = False) -> List[str]:
        """
        Get ZIP codes for a city/state combination
        
        Args:
            city: City name
            state: State abbreviation (e.g., 'TX', 'CA')
            primary_only: If True, return only primary ZIP codes for faster searches
            
        Returns:
            List of ZIP codes, empty list if not found
        """
        if not self.loaded:
            logger.warning("Mapping data not loaded, attempting to load...")
            if not self.load_mapping_data():
                return []
                
        # Try exact match first
        city_state_key = f"{city}, {state}"
        city_info = self.cities.get(city_state_key)
        
        # Try alias lookup if exact match fails
        if not city_info:
            canonical_key = self.aliases.get(city_state_key)
            if canonical_key:
                city_info = self.cities.get(canonical_key)
                
        # Try case-insensitive lookup
        if not city_info:
            city_state_key_lower = city_state_key.lower()
            for key, info in self.cities.items():
                if key.lower() == city_state_key_lower:
                    city_info = info
                    break
                    
        if city_info:
            return city_info.primary_zips if primary_only else city_info.all_zips
        else:
            logger.warning(f"No ZIP codes found for {city}, {state}")
            return []
            
    def get_city_info(self, city: str, state: str) -> Optional[CityInfo]:
        """
        Get complete city information
        
        Args:
            city: City name
            state: State abbreviation
            
        Returns:
            CityInfo object or None if not found
        """
        if not self.loaded:
            if not self.load_mapping_data():
                return None
                
        city_state_key = f"{city}, {state}"
        city_info = self.cities.get(city_state_key)
        
        # Try alias lookup
        if not city_info:
            canonical_key = self.aliases.get(city_state_key)
            if canonical_key:
                city_info = self.cities.get(canonical_key)
                
        return city_info
        
    def search_cities(self, partial_name: str, state: str = None) -> List[CityInfo]:
        """
        Search for cities by partial name
        
        Args:
            partial_name: Partial city name to search for
            state: Optional state filter
            
        Returns:
            List of matching CityInfo objects
        """
        if not self.loaded:
            if not self.load_mapping_data():
                return []
                
        matches = []
        partial_lower = partial_name.lower()
        
        for city_info in self.cities.values():
            if partial_lower in city_info.city.lower():
                if state is None or city_info.state == state:
                    matches.append(city_info)
                    
        return matches
        
    def get_available_cities(self, state: str = None) -> List[str]:
        """
        Get list of available cities
        
        Args:
            state: Optional state filter
            
        Returns:
            List of city names
        """
        if not self.loaded:
            if not self.load_mapping_data():
                return []
                
        cities = []
        for city_info in self.cities.values():
            if state is None or city_info.state == state:
                cities.append(city_info.city_state_key)
                
        return sorted(cities)
        
    def get_statistics(self) -> Dict[str, int]:
        """Get mapping statistics"""
        if not self.loaded:
            if not self.load_mapping_data():
                return {}
                
        total_cities = len(self.cities)
        total_aliases = len(self.aliases)
        total_zips = sum(len(city.zip_codes) for city in self.cities.values())
        
        states = set(city.state for city in self.cities.values())
        
        return {
            "total_cities": total_cities,
            "total_aliases": total_aliases,
            "total_zip_codes": total_zips,
            "unique_states": len(states),
            "loaded": self.loaded
        }


# Global instance for easy access
_global_mapper = None

def get_city_zip_mapper() -> CityStateZipMapper:
    """Get the global city ZIP mapper instance"""
    global _global_mapper
    if _global_mapper is None:
        _global_mapper = CityStateZipMapper()
        _global_mapper.load_mapping_data()
    return _global_mapper


# Convenience functions
def get_zip_codes_for_city(city: str, state: str, primary_only: bool = False) -> List[str]:
    """Convenience function to get ZIP codes for a city"""
    mapper = get_city_zip_mapper()
    return mapper.get_zip_codes(city, state, primary_only)


def search_cities_by_name(partial_name: str, state: str = None) -> List[str]:
    """Convenience function to search cities"""
    mapper = get_city_zip_mapper()
    matches = mapper.search_cities(partial_name, state)
    return [match.city_state_key for match in matches]


if __name__ == "__main__":
    """Test the mapping service"""
    logging.basicConfig(level=logging.INFO)
    
    # Test the mapper
    mapper = CityStateZipMapper()
    
    if mapper.load_mapping_data():
        print("✅ Mapping data loaded successfully")
        
        # Print statistics
        stats = mapper.get_statistics()
        print(f"📊 Statistics: {stats}")
        
        # Test some lookups
        test_cities = [
            ("Austin", "TX"),
            ("New York", "NY"),
            ("Los Angeles", "CA"),
            ("Chicago", "IL")
        ]
        
        for city, state in test_cities:
            zips = mapper.get_zip_codes(city, state)
            primary_zips = mapper.get_zip_codes(city, state, primary_only=True)
            
            print(f"\n🏙️  {city}, {state}:")
            print(f"   Primary ZIPs: {primary_zips}")
            print(f"   Total ZIPs: {len(zips)}")
            
            city_info = mapper.get_city_info(city, state)
            if city_info and city_info.centroid_lat:
                print(f"   📍 Centroid: {city_info.centroid_lat:.4f}, {city_info.centroid_lon:.4f}")
                
    else:
        print("❌ Failed to load mapping data")
        print("Make sure city2zip.json exists and contains actual city data")
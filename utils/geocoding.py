"""
Geocoding utilities for location search.
"""
import logging
from typing import Any, Optional, Tuple

from geopy.geocoders import ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)


def search_location(
    query: str,
    user_agent: str = "property_claim_mapper"
) -> Optional[Tuple[float, float, str]]:
    """
    Search for a location using ArcGIS geocoding service.
    
    Args:
        query: Address or location search string
        user_agent: User agent string for the geocoder
        
    Returns:
        Tuple of (latitude, longitude, address) if found, None otherwise
        
    Raises:
        GeocoderTimedOut: If the geocoding request times out
        GeocoderServiceError: If there's a service error
    """
    if not query or not query.strip():
        logger.warning("Empty search query provided")
        return None
    
    try:
        geolocator = ArcGIS(user_agent=user_agent)
        location = geolocator.geocode(query)
        
        if location:
            logger.info(f"Found location: {location.address}")
            return (location.latitude, location.longitude, location.address)
        else:
            logger.info(f"No location found for query: {query}")
            return None
            
    except GeocoderTimedOut as e:
        logger.error(f"Geocoding timed out for query '{query}': {e}")
        raise
    except GeocoderServiceError as e:
        logger.error(f"Geocoding service error for query '{query}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during geocoding: {e}")
        raise

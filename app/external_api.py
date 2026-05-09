"""
External API integration for weather data.

WHY THIS FILE EXISTS:
- Centralizes external API calls
- Separates API integration from routes
- Makes external dependencies mockable for testing
- Handles API errors gracefully

EXTERNAL API EXPLANATION:
External APIs are services provided by other companies/projects.

EXAMPLE: WeatherAPI.com
- Provides real-time weather data
- We send HTTP request with location
- They respond with weather information

WHY INTEGRATE:
- Adds value to our service
- Don't need to collect weather data ourselves
- Typical in real applications

ERROR HANDLING:
- Network might be down
- API might be rate-limited
- Invalid parameters might be sent
- We need to handle all cases gracefully
"""

import httpx
from typing import Optional, Dict, Any
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


class WeatherService:
    """
    Service for integrating with Weather API.
    
    NOTE: Uses weatherapi.com - free tier available
    Sign up at: https://www.weatherapi.com/
    """
    
    BASE_URL = "https://api.weatherapi.com/v1"
    
    @staticmethod
    async def get_current_weather(city: str) -> Optional[Dict[str, Any]]:
        """
        Get current weather for a city.
        
        API ENDPOINT:
        GET https://api.weatherapi.com/v1/current.json
        
        PARAMETERS:
        - key: API key (from environment)
        - q: location (city name or coordinates)
        - aqi: air quality data (yes/no)
        
        RESPONSE EXAMPLE:
        {
            "current": {
                "temp_c": 15.2,
                "temp_f": 59.4,
                "condition": {
                    "text": "Partly cloudy",
                    "icon": "..."
                }
            }
        }
        
        ARGS:
            city: city name or location
        
        RETURNS:
            Weather data dictionary if successful, None if error
        """
        if not settings.weather_api_key:
            logger.warning("Weather API key not configured")
            return None
        
        try:
            # Build URL with parameters
            url = f"{WeatherService.BASE_URL}/current.json"
            params = {
                "key": settings.weather_api_key,
                "q": city,
                "aqi": "yes",  # Include air quality data
            }
            
            # Make HTTP request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            logger.info(f"Successfully fetched weather for: {city}")
            
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Weather API HTTP error: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Weather API request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return None
    
    @staticmethod
    async def get_forecast(city: str, days: int = 3) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a city.
        
        ARGS:
            city: city name or location
            days: number of forecast days (1-10)
        
        RETURNS:
            Forecast data if successful, None if error
        """
        if not settings.weather_api_key:
            logger.warning("Weather API key not configured")
            return None
        
        try:
            # Validate days parameter
            days = max(1, min(days, 10))
            
            url = f"{WeatherService.BASE_URL}/forecast.json"
            params = {
                "key": settings.weather_api_key,
                "q": city,
                "days": days,
                "aqi": "yes",
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched forecast for: {city}")
            
            return data
        
        except Exception as e:
            logger.error(f"Forecast API error: {str(e)}")
            return None


class CryptoService:
    """
    Service for cryptocurrency price data.
    
    Uses CoinGecko API (free, no key required).
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    @staticmethod
    async def get_crypto_price(crypto_id: str, vs_currency: str = "usd") -> Optional[Dict[str, Any]]:
        """
        Get cryptocurrency current price.
        
        CRYPTO IDS: bitcoin, ethereum, cardano, ripple, etc.
        
        ARGS:
            crypto_id: cryptocurrency ID
            vs_currency: currency to compare against (default: usd)
        
        RETURNS:
            Price data if successful, None if error
        """
        try:
            url = f"{CryptoService.BASE_URL}/simple/price"
            params = {
                "ids": crypto_id,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_change": "true",
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched price for: {crypto_id}")
            
            return data
        
        except Exception as e:
            logger.error(f"Crypto API error: {str(e)}")
            return None
    
    @staticmethod
    async def get_top_cryptos(limit: int = 10, vs_currency: str = "usd") -> Optional[list]:
        """
        Get top cryptocurrencies by market cap.
        
        ARGS:
            limit: number of top cryptos to return
            vs_currency: currency to compare against
        
        RETURNS:
            List of crypto data if successful, None if error
        """
        try:
            url = f"{CryptoService.BASE_URL}/coins/markets"
            params = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False,
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched top {limit} cryptos")
            
            return data
        
        except Exception as e:
            logger.error(f"Top cryptos API error: {str(e)}")
            return None

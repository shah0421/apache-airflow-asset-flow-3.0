import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


# Pydantic models for OpenWeatherMap API response
class WeatherInfo(BaseModel):
    """Validated weather information"""
    city: str
    country: str
    temperature: float
    weather_description: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for XCom compatibility"""
        return self.model_dump()


class OpenWeatherMapClient:
    """Client for interacting with OpenWeatherMap API"""
    def __init__(self, api_key: str, api_url: str, timeout: int = 10, units: str = 'metric'):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.units = units

    def get_weather(self, city: str, country_code: str) -> Optional[Dict]:
        """
        Fetch weather data for a specific city

        Returns weather dict if successful, None if failed
        """
        try:
            params = {
                'q': f"{city},{country_code}",
                'appid': self.api_key,
                'units': self.units
            }

            response = requests.get(self.api_url, params=params, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                # Build minimal WeatherInfo using Pydantic
                weather_info = WeatherInfo(
                    city=city,
                    country=country_code,
                    temperature=data["main"]["temp"],
                    weather_description=data["weather"][0]["description"]
                )

                logger.info(f"Successfully retrieved weather for {city}")
                return weather_info.model_dump()

            elif response.status_code == 404:
                logger.warning(f"City not found in API: {city}, {country_code}")
                return None

            elif response.status_code == 401:
                logger.error("API authentication failed. Check your API key.")
                raise ValueError("Invalid API key")

            else:
                logger.warning(f"API error for {city}: Status {response.status_code}")
                return None

        except ValidationError as e:
            logger.error(f"Failed to parse API response for {city}: {e}")
            return None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout calling API for {city}")
            return None

        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error for {city}")
            return None

        except Exception as e:
            logger.warning(f"Unexpected error for {city}: {str(e)}")
            return None

    def get_weather_bulk(self, cities: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Fetch weather data for multiple cities

        Args:
            cities: List of dicts with 'city' and 'country' keys

        Returns:
            Tuple of (weather_data list, failed_cities list)
        """
        logger.info(f"Calling weather API for {len(cities)} cities")
        weather_data = []
        failed_cities = []

        for city_info in cities:
            city_name = city_info['city']
            country_code = city_info['country']

            weather_info = self.get_weather(city_name, country_code)

            if weather_info:
                weather_data.append(weather_info)
            else:
                failed_cities.append(city_name)

        logger.info(f"Successfully retrieved weather data for {len(weather_data)} cities")
        if failed_cities:
            logger.warning(f"Failed to get weather for {len(failed_cities)} cities: {failed_cities}")

        return weather_data, failed_cities



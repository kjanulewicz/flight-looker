"""
Module for searching flights from various sources
"""
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import airline scrapers
try:
    from .airline_scrapers import search_airlines, MultiAirlineScraper
    SCRAPERS_AVAILABLE = True
except ImportError:
    SCRAPERS_AVAILABLE = False
    logger.warning("Airline scrapers not available. Install aiohttp: pip install aiohttp")


class FlightSearcher:
    """Searches for flights using various APIs and sources"""

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, use_scrapers: bool = True):
        self.api_key = api_key or os.getenv('AMADEUS_API_KEY')
        self.use_scrapers = use_scrapers and SCRAPERS_AVAILABLE
        self.api_secret = api_secret or os.getenv('AMADEUS_API_SECRET')
        self.access_token = None
        self.token_expires_at = None

    def _get_access_token(self, proxies: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Gets access token for Amadeus API"""
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token

        if not self.api_key or not self.api_secret:
            logger.warning("Missing Amadeus API keys. Using demo mode.")
            return None

        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            }

            response = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=15)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data['expires_in']
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            logger.info("Obtained Amadeus API access token")
            return self.access_token

        except Exception as e:
            logger.error(f"Error during token retrieval: {e}")
            return None

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        currency: str = "PLN",
        proxies: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Searches for flights

        Args:
            origin: IATA airport code for departure (e.g., 'POZ' for Poznań)
            destination: IATA airport code for destination (e.g., 'AMS' for Amsterdam)
            departure_date: Departure date in YYYY-MM-DD format
            adults: Number of adult passengers
            currency: Currency code (PLN, EUR, USD, TRY, ALL)
            proxies: Optional proxy configuration for requests

        Returns:
            List of dictionaries with flight information
        """
        all_flights = []

        # Search Amadeus API
        token = self._get_access_token(proxies)
        if token:
            amadeus_flights = self._search_amadeus(origin, destination, departure_date, adults, currency, proxies)
            all_flights.extend(amadeus_flights)
        else:
            # Demo mode - returns sample data
            demo_flights = self._generate_demo_data(origin, destination, departure_date, currency)
            all_flights.extend(demo_flights)

        return all_flights

    def search_with_scrapers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None,
        airlines: List[str] = None
    ) -> List[Dict]:
        """
        Search flights using airline website scrapers

        Args:
            origin: IATA airport code for departure
            destination: IATA airport code for destination
            departure_date: Departure date in YYYY-MM-DD format
            adults: Number of adult passengers
            country_code: ISO country code for price perspective (e.g., 'PL', 'GB')
            airlines: List of airlines to search (default: all)

        Returns:
            List of flights from airline websites
        """
        if not SCRAPERS_AVAILABLE:
            logger.warning("Scrapers not available")
            return []

        try:
            flights = search_airlines(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                adults=adults,
                airlines=airlines,
                country_code=country_code
            )
            return flights
        except Exception as e:
            logger.error(f"Error searching with scrapers: {e}")
            return []

    def search_all_sources(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        currency: str = "PLN",
        country_code: str = None,
        proxies: Optional[Dict[str, str]] = None,
        airlines: List[str] = None
    ) -> List[Dict]:
        """
        Search flights from ALL sources: Amadeus API + airline scrapers

        Returns:
            Combined list of flights from all sources
        """
        all_flights = []

        # 1. Search Amadeus API
        amadeus_flights = self.search_flights(
            origin, destination, departure_date, adults, currency, proxies
        )
        all_flights.extend(amadeus_flights)

        # 2. Search airline scrapers (if enabled)
        if self.use_scrapers and SCRAPERS_AVAILABLE:
            scraper_flights = self.search_with_scrapers(
                origin, destination, departure_date, adults, country_code, airlines
            )
            all_flights.extend(scraper_flights)

        # Remove duplicates based on flight number and price
        seen = set()
        unique_flights = []
        for flight in all_flights:
            key = (flight.get('flight_number', ''), flight.get('price', 0), flight.get('airline', ''))
            if key not in seen:
                seen.add(key)
                unique_flights.append(flight)

        return unique_flights

    def _search_amadeus(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int,
        currency: str,
        proxies: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """Searches for flights via Amadeus API"""
        try:
            url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "currencyCode": currency,
                "max": 10
            }

            response = requests.get(url, headers=headers, params=params, proxies=proxies, timeout=30)
            response.raise_for_status()

            data = response.json()
            flights = []

            for offer in data.get('data', []):
                price = float(offer['price']['total'])
                itineraries = offer.get('itineraries', [])

                if itineraries:
                    first_segment = itineraries[0]['segments'][0]
                    last_segment = itineraries[0]['segments'][-1]

                    flight_info = {
                        'price': price,
                        'currency': currency,
                        'departure_time': first_segment['departure']['at'],
                        'arrival_time': last_segment['arrival']['at'],
                        'airline': first_segment['carrierCode'],
                        'stops': len(itineraries[0]['segments']) - 1,
                        'duration': itineraries[0]['duration']
                    }
                    flights.append(flight_info)

            logger.info(f"Found {len(flights)} flights via Amadeus API")
            return flights

        except Exception as e:
            logger.error(f"Error searching via Amadeus: {e}")
            return self._generate_demo_data(origin, destination, departure_date, currency)

    def _generate_demo_data(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        currency: str
    ) -> List[Dict]:
        """Generates sample data for testing (when API is unavailable)"""
        import random

        # Various prices depending on currency
        base_prices = {
            'PLN': (400, 1200),
            'EUR': (90, 280),
            'USD': (100, 300),
            'TRY': (3000, 9000),
            'ALL': (10000, 30000)
        }

        price_range = base_prices.get(currency, (100, 500))

        flights = []
        for i in range(5):
            price = random.uniform(*price_range)
            flights.append({
                'price': round(price, 2),
                'currency': currency,
                'departure_time': f"{departure_date}T{random.randint(6,20):02d}:{random.choice(['00','30'])}:00",
                'arrival_time': f"{departure_date}T{random.randint(8,23):02d}:{random.choice(['00','30'])}:00",
                'airline': random.choice(['LO', 'W6', 'FR', 'LH', 'KL']),
                'stops': random.choice([0, 0, 0, 1, 1, 2]),
                'duration': f"PT{random.randint(2,5)}H{random.randint(0,55):02d}M",
                'source': 'DEMO'
            })

        logger.info(f"Generated {len(flights)} sample flights (demo mode)")
        return flights

    def get_cheapest_flight(self, flights: List[Dict]) -> Optional[Dict]:
        """Returns the cheapest flight from the list"""
        if not flights:
            return None
        return min(flights, key=lambda x: x['price'])


class MultiCountryFlightSearcher:
    """Searches for flights from the perspective of different countries"""

    def __init__(self, vpn_manager, flight_searcher: FlightSearcher):
        self.vpn_manager = vpn_manager
        self.flight_searcher = flight_searcher

    def search_from_countries(
        self,
        countries: List[str],
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1
    ) -> Dict[str, List[Dict]]:
        """
        Searches for flights from the perspective of different countries

        Args:
            countries: List of countries (e.g., ['poland', 'turkey', 'albania'])
            origin: IATA airport code for departure
            destination: IATA airport code for destination
            departure_date: Departure date
            adults: Number of passengers

        Returns:
            Dictionary: {country: list_of_flights}
        """
        results = {}

        # Country to currency mapping
        country_currency = {
            # Europe
            'poland': 'PLN',
            'germany': 'EUR',
            'united_kingdom': 'GBP',
            'france': 'EUR',
            'spain': 'EUR',
            'italy': 'EUR',
            'netherlands': 'EUR',
            'belgium': 'EUR',
            'austria': 'EUR',
            'switzerland': 'CHF',
            'sweden': 'SEK',
            'norway': 'NOK',
            'denmark': 'DKK',
            'finland': 'EUR',
            'portugal': 'EUR',
            'greece': 'EUR',
            'czech': 'CZK',
            'hungary': 'HUF',
            'romania': 'RON',
            'bulgaria': 'BGN',
            'croatia': 'EUR',
            'slovakia': 'EUR',
            'ireland': 'EUR',
            'ukraine': 'UAH',
            'albania': 'ALL',
            'turkey': 'TRY',
            # Americas
            'usa': 'USD',
            'canada': 'CAD',
            'mexico': 'MXN',
            'brazil': 'BRL',
            'argentina': 'ARS',
            # Asia & Middle East
            'japan': 'JPY',
            'south_korea': 'KRW',
            'china': 'CNY',
            'india': 'INR',
            'thailand': 'THB',
            'singapore': 'SGD',
            'malaysia': 'MYR',
            'indonesia': 'IDR',
            'vietnam': 'VND',
            'philippines': 'PHP',
            'uae': 'AED',
            'israel': 'ILS',
            'saudi_arabia': 'SAR',
            # Oceania & Africa
            'australia': 'AUD',
            'new_zealand': 'NZD',
            'south_africa': 'ZAR',
            'egypt': 'EGP',
            'morocco': 'MAD'
        }

        # Country to ISO code mapping
        country_to_iso = {
            'poland': 'PL', 'germany': 'DE', 'united_kingdom': 'GB', 'france': 'FR',
            'spain': 'ES', 'italy': 'IT', 'netherlands': 'NL', 'belgium': 'BE',
            'austria': 'AT', 'switzerland': 'CH', 'sweden': 'SE', 'norway': 'NO',
            'denmark': 'DK', 'finland': 'FI', 'portugal': 'PT', 'greece': 'GR',
            'czech': 'CZ', 'hungary': 'HU', 'romania': 'RO', 'bulgaria': 'BG',
            'croatia': 'HR', 'slovakia': 'SK', 'ireland': 'IE', 'ukraine': 'UA',
            'albania': 'AL', 'turkey': 'TR', 'usa': 'US', 'canada': 'CA',
            'mexico': 'MX', 'brazil': 'BR', 'argentina': 'AR', 'japan': 'JP',
            'south_korea': 'KR', 'china': 'CN', 'india': 'IN', 'thailand': 'TH',
            'singapore': 'SG', 'malaysia': 'MY', 'indonesia': 'ID', 'vietnam': 'VN',
            'philippines': 'PH', 'uae': 'AE', 'israel': 'IL', 'saudi_arabia': 'SA',
            'australia': 'AU', 'new_zealand': 'NZ', 'south_africa': 'ZA',
            'egypt': 'EG', 'morocco': 'MA'
        }

        for country in countries:
            logger.info(f"\n{'='*50}")
            logger.info(f"Searching for flights from the perspective of: {country.upper()}")
            logger.info(f"{'='*50}")

            # Get currency and ISO code for the country
            currency = country_currency.get(country.lower(), 'EUR')
            country_code = country_to_iso.get(country.lower(), 'GB')

            # Try to connect to VPN/proxy (optional - for real geo-location)
            proxy_config = None
            location = None

            if self.vpn_manager.use_nordvpn:
                # Only use proxy/VPN if explicitly enabled
                if self.vpn_manager.connect_to_country(country):
                    proxy_config = self.vpn_manager.get_current_proxy()
                    if proxy_config:
                        location = self.vpn_manager.get_current_location(use_proxy=True)

            # Search for flights - use all sources if scrapers enabled
            if self.flight_searcher.use_scrapers:
                flights = self.flight_searcher.search_all_sources(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    adults=adults,
                    currency=currency,
                    country_code=country_code,
                    proxies=proxy_config
                )
            else:
                flights = self.flight_searcher.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    adults=adults,
                    currency=currency,
                    proxies=proxy_config
                )

            results[country] = {
                'flights': flights,
                'currency': currency,
                'location': location,
                'proxy': self.vpn_manager.current_proxy if proxy_config else None,
                'country_code': country_code
            }

            if flights:
                cheapest = self.flight_searcher.get_cheapest_flight(flights)
                logger.info(f"Found {len(flights)} flights. Cheapest: {cheapest['price']} {currency}")

        # Disconnect VPN/proxy
        self.vpn_manager.disconnect()

        return results

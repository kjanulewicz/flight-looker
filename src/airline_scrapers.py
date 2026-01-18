"""
Airline website scrapers for real price comparison
Uses Playwright for browser automation
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirlineScraper(ABC):
    """Base class for airline scrapers"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context = None
        self.name = "Unknown"

    @abstractmethod
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> List[Dict]:
        """Search for flights on airline website"""
        pass

    async def init_browser(self, headless: bool = True, country_code: str = None):
        """Initialize browser with fresh context (no cookies)"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install")

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)

        # Create fresh context - this ensures no cookies from previous sessions
        # Set locale and timezone based on country for more realistic simulation
        locale_map = {
            'PL': ('pl-PL', 'Europe/Warsaw'),
            'DE': ('de-DE', 'Europe/Berlin'),
            'GB': ('en-GB', 'Europe/London'),
            'FR': ('fr-FR', 'Europe/Paris'),
            'ES': ('es-ES', 'Europe/Madrid'),
            'IT': ('it-IT', 'Europe/Rome'),
            'TR': ('tr-TR', 'Europe/Istanbul'),
            'US': ('en-US', 'America/New_York'),
            'JP': ('ja-JP', 'Asia/Tokyo'),
            'IN': ('en-IN', 'Asia/Kolkata'),
        }

        locale, timezone = locale_map.get(country_code, ('en-GB', 'Europe/London'))

        self.context = await self.browser.new_context(
            locale=locale,
            timezone_id=timezone,
            # Block tracking
            extra_http_headers={
                'DNT': '1',
                'Sec-GPC': '1',
            },
            # Fresh context = no cookies
            storage_state=None,
        )

        return self.browser

    async def clear_cookies(self):
        """Clear all cookies from current context"""
        if self.context:
            await self.context.clear_cookies()
            logger.debug(f"{self.name}: Cleared all cookies")

    async def new_page(self) -> Page:
        """Create new page with fresh state"""
        if not self.context:
            raise RuntimeError("Browser context not initialized")

        # Clear cookies before creating new page
        await self.clear_cookies()

        page = await self.context.new_page()

        # Block unnecessary resources to speed up
        await page.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2}", lambda route: route.abort())
        await page.route("**/analytics**", lambda route: route.abort())
        await page.route("**/tracking**", lambda route: route.abort())
        await page.route("**/google-analytics**", lambda route: route.abort())
        await page.route("**/facebook**", lambda route: route.abort())

        return page

    async def close_browser(self):
        """Close browser and clear all data"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        self.context = None
        self.browser = None


class RyanairScraper(AirlineScraper):
    """Scraper for Ryanair website"""

    # Ryanair country-specific domains
    COUNTRY_DOMAINS = {
        'PL': 'https://www.ryanair.com/pl/pl',
        'DE': 'https://www.ryanair.com/de/de',
        'GB': 'https://www.ryanair.com/gb/en',
        'FR': 'https://www.ryanair.com/fr/fr',
        'ES': 'https://www.ryanair.com/es/es',
        'IT': 'https://www.ryanair.com/it/it',
        'NL': 'https://www.ryanair.com/nl/nl',
        'BE': 'https://www.ryanair.com/be/nl',
        'AT': 'https://www.ryanair.com/at/de',
        'IE': 'https://www.ryanair.com/ie/en',
        'PT': 'https://www.ryanair.com/pt/pt',
        'TR': 'https://www.ryanair.com/tr/tr',
        'US': 'https://www.ryanair.com/us/en',
    }

    # Language codes for API
    COUNTRY_LANG = {
        'PL': 'pl-pl', 'DE': 'de-de', 'GB': 'en-gb', 'FR': 'fr-fr',
        'ES': 'es-es', 'IT': 'it-it', 'NL': 'nl-nl', 'BE': 'nl-be',
        'AT': 'de-at', 'IE': 'en-ie', 'PT': 'pt-pt', 'TR': 'tr-tr',
        'US': 'en-us',
    }

    def __init__(self):
        super().__init__()
        self.name = "Ryanair"
        self.base_url = "https://www.ryanair.com"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> List[Dict]:
        """Search Ryanair flights - uses country-specific API endpoint"""
        flights = []
        country_code = country_code or 'GB'
        lang = self.COUNTRY_LANG.get(country_code, 'en-gb')

        try:
            import aiohttp

            # Country-specific API endpoint - this is what gives different prices!
            url = (
                f"https://www.ryanair.com/api/booking/v4/{lang}/availability"
                f"?ADT={adults}&CHD=0&DateIn=&DateOut={departure_date}"
                f"&Destination={destination}&Disc=0&INF=0&Origin={origin}"
                f"&TEEN=0&promoCode=&IncludeConnectingFlights=false&FlexDaysBeforeOut=0"
                f"&FlexDaysOut=0&FlexDaysBeforeIn=0&FlexDaysIn=0&RoundTrip=false&ToUs=AGREED"
            )

            # Create session without cookies
            jar = aiohttp.CookieJar()
            jar.clear()

            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': lang.replace('-', '_'),
                }

                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        currency = data.get('currency', 'EUR')

                        trips = data.get('trips', [])
                        for trip in trips:
                            dates = trip.get('dates', [])
                            for date_info in dates:
                                flight_list = date_info.get('flights', [])
                                for flight in flight_list:
                                    if flight.get('faresLeft', 0) > 0:
                                        regular_fare = flight.get('regularFare', {})
                                        fares = regular_fare.get('fares', [])

                                        for fare in fares:
                                            price = fare.get('amount', 0)
                                            if price > 0:
                                                flights.append({
                                                    'price': price,
                                                    'currency': currency,
                                                    'airline': 'FR',
                                                    'airline_name': 'Ryanair',
                                                    'departure_time': flight.get('time', [''])[0],
                                                    'arrival_time': flight.get('time', ['', ''])[1] if len(flight.get('time', [])) > 1 else '',
                                                    'flight_number': flight.get('flightNumber', ''),
                                                    'stops': 0,
                                                    'source': f'ryanair_{country_code.lower()}'
                                                })

                        logger.info(f"Ryanair ({country_code}): Found {len(flights)} flights in {currency}")
                    else:
                        logger.warning(f"Ryanair API ({country_code}) returned status {response.status}")

        except Exception as e:
            logger.error(f"Ryanair scraping error ({country_code}): {e}")

        return flights


class WizzairScraper(AirlineScraper):
    """Scraper for Wizzair website"""

    # Wizzair country-specific API versions and languages
    COUNTRY_CONFIG = {
        'PL': {'lang': 'pl-PL', 'market': 'pl-pl'},
        'DE': {'lang': 'de-DE', 'market': 'de-de'},
        'GB': {'lang': 'en-GB', 'market': 'en-gb'},
        'HU': {'lang': 'hu-HU', 'market': 'hu-hu'},
        'RO': {'lang': 'ro-RO', 'market': 'ro-ro'},
        'BG': {'lang': 'bg-BG', 'market': 'bg-bg'},
        'IT': {'lang': 'it-IT', 'market': 'it-it'},
        'ES': {'lang': 'es-ES', 'market': 'es-es'},
        'AT': {'lang': 'de-AT', 'market': 'de-at'},
        'UA': {'lang': 'uk-UA', 'market': 'uk-ua'},
    }

    def __init__(self):
        super().__init__()
        self.name = "Wizzair"
        self.base_url = "https://wizzair.com"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> List[Dict]:
        """Search Wizzair flights using their API with country-specific settings"""
        flights = []
        country_code = country_code or 'GB'
        config = self.COUNTRY_CONFIG.get(country_code, {'lang': 'en-GB', 'market': 'en-gb'})

        try:
            import aiohttp

            # First get API version from metadata
            metadata_url = "https://be.wizzair.com/buildnumber"

            jar = aiohttp.CookieJar()
            jar.clear()

            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                # Get current API version
                try:
                    async with session.get(metadata_url, timeout=10) as resp:
                        if resp.status == 200:
                            api_version = (await resp.text()).strip()
                        else:
                            api_version = "13.8.0"  # fallback
                except:
                    api_version = "13.8.0"

                # Wizzair API endpoint with version
                url = f"https://be.wizzair.com/{api_version}/Api/search/search"

                payload = {
                    "flightList": [
                        {
                            "departureStation": origin,
                            "arrivalStation": destination,
                            "departureDate": departure_date
                        }
                    ],
                    "adultCount": adults,
                    "childCount": 0,
                    "infantCount": 0,
                    "wdc": False,
                    "isRescueFare": False
                }

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Content-Type': 'application/json;charset=UTF-8',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': config['lang'],
                    'Origin': 'https://wizzair.com',
                    'Referer': f"https://wizzair.com/{config['market']}/",
                }

                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        outbound = data.get('outboundFlights', [])
                        for flight in outbound:
                            fares = flight.get('fares', [])
                            for fare in fares:
                                price_info = fare.get('fullBasePrice') or fare.get('basePrice', {})
                                price = price_info.get('amount', 0)
                                currency = price_info.get('currencyCode', 'EUR')

                                if price > 0:
                                    flights.append({
                                        'price': price,
                                        'currency': currency,
                                        'airline': 'W6',
                                        'airline_name': 'Wizzair',
                                        'departure_time': flight.get('departureDateTime', ''),
                                        'arrival_time': flight.get('arrivalDateTime', ''),
                                        'flight_number': flight.get('flightNumber', ''),
                                        'stops': 0,
                                        'source': f'wizzair_{country_code.lower()}'
                                    })

                        logger.info(f"Wizzair ({country_code}): Found {len(flights)} flights")
                    else:
                        logger.warning(f"Wizzair API ({country_code}) returned status {response.status}")

        except Exception as e:
            logger.error(f"Wizzair scraping error ({country_code}): {e}")

        return flights


class LOTScraper(AirlineScraper):
    """Scraper for LOT Polish Airlines website"""

    COUNTRY_CONFIG = {
        'PL': {'lang': 'pl', 'currency': 'PLN'},
        'DE': {'lang': 'de', 'currency': 'EUR'},
        'GB': {'lang': 'en', 'currency': 'GBP'},
        'US': {'lang': 'en', 'currency': 'USD'},
    }

    def __init__(self):
        super().__init__()
        self.name = "LOT"
        self.base_url = "https://www.lot.com"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> List[Dict]:
        """Search LOT flights"""
        flights = []
        country_code = country_code or 'PL'
        config = self.COUNTRY_CONFIG.get(country_code, {'lang': 'en', 'currency': 'EUR'})

        try:
            import aiohttp

            jar = aiohttp.CookieJar()
            jar.clear()

            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                # LOT booking API
                url = f"https://www.lot.com/{config['lang']}/booking/search"

                params = {
                    'origin': origin,
                    'destination': destination,
                    'departureDate': departure_date,
                    'adults': adults,
                    'children': 0,
                    'infants': 0,
                    'cabinClass': 'ECONOMY',
                    'tripType': 'ONE_WAY',
                    'currency': config['currency']
                }

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': f"{config['lang']}-{country_code}",
                }

                async with session.get(url, params=params, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        for offer in data.get('offers', data.get('flights', [])):
                            price = offer.get('price', {}).get('amount', offer.get('totalPrice', 0))
                            currency = offer.get('price', {}).get('currency', config['currency'])

                            if price > 0:
                                flights.append({
                                    'price': price,
                                    'currency': currency,
                                    'airline': 'LO',
                                    'airline_name': 'LOT Polish Airlines',
                                    'departure_time': offer.get('departureTime', ''),
                                    'arrival_time': offer.get('arrivalTime', ''),
                                    'flight_number': offer.get('flightNumber', ''),
                                    'stops': offer.get('stops', 0),
                                    'source': f'lot_{country_code.lower()}'
                                })

                        logger.info(f"LOT ({country_code}): Found {len(flights)} flights")
                    else:
                        logger.debug(f"LOT API ({country_code}) returned status {response.status}")

        except Exception as e:
            logger.debug(f"LOT scraping ({country_code}): {e}")

        return flights


class EasyJetScraper(AirlineScraper):
    """Scraper for EasyJet website"""

    COUNTRY_CONFIG = {
        'GB': {'domain': 'www.easyjet.com', 'lang': 'en', 'currency': 'GBP'},
        'DE': {'domain': 'www.easyjet.com/de', 'lang': 'de', 'currency': 'EUR'},
        'FR': {'domain': 'www.easyjet.com/fr', 'lang': 'fr', 'currency': 'EUR'},
        'ES': {'domain': 'www.easyjet.com/es', 'lang': 'es', 'currency': 'EUR'},
        'IT': {'domain': 'www.easyjet.com/it', 'lang': 'it', 'currency': 'EUR'},
        'NL': {'domain': 'www.easyjet.com/nl', 'lang': 'nl', 'currency': 'EUR'},
        'CH': {'domain': 'www.easyjet.com/ch-de', 'lang': 'de', 'currency': 'CHF'},
    }

    def __init__(self):
        super().__init__()
        self.name = "EasyJet"
        self.base_url = "https://www.easyjet.com"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> List[Dict]:
        """Search EasyJet flights"""
        flights = []
        country_code = country_code or 'GB'
        config = self.COUNTRY_CONFIG.get(country_code, self.COUNTRY_CONFIG['GB'])

        try:
            import aiohttp

            jar = aiohttp.CookieJar()
            jar.clear()

            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                url = f"https://{config['domain']}/api/flights/search"

                params = {
                    'origin': origin,
                    'destination': destination,
                    'outboundDate': departure_date,
                    'adults': adults,
                    'children': 0,
                    'infants': 0,
                    'currency': config['currency']
                }

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Language': f"{config['lang']}-{country_code}",
                }

                async with session.get(url, params=params, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        for flight in data.get('flights', data.get('outbound', [])):
                            price = flight.get('price', flight.get('lowestPrice', 0))
                            currency = flight.get('currency', config['currency'])

                            if price > 0:
                                flights.append({
                                    'price': price,
                                    'currency': currency,
                                    'airline': 'U2',
                                    'airline_name': 'EasyJet',
                                    'departure_time': flight.get('departureTime', ''),
                                    'arrival_time': flight.get('arrivalTime', ''),
                                    'flight_number': flight.get('flightNumber', ''),
                                    'stops': 0,
                                    'source': f'easyjet_{country_code.lower()}'
                                })

                        logger.info(f"EasyJet ({country_code}): Found {len(flights)} flights")
                    else:
                        logger.debug(f"EasyJet API ({country_code}) returned status {response.status}")

        except Exception as e:
            logger.debug(f"EasyJet scraping ({country_code}): {e}")

        return flights


class LufthansaScraper(AirlineScraper):
    """Scraper for Lufthansa website"""

    COUNTRY_CONFIG = {
        'DE': {'lang': 'de', 'country': 'de', 'currency': 'EUR'},
        'GB': {'lang': 'en', 'country': 'gb', 'currency': 'GBP'},
        'US': {'lang': 'en', 'country': 'us', 'currency': 'USD'},
        'AT': {'lang': 'de', 'country': 'at', 'currency': 'EUR'},
        'CH': {'lang': 'de', 'country': 'ch', 'currency': 'CHF'},
        'PL': {'lang': 'pl', 'country': 'pl', 'currency': 'PLN'},
    }

    def __init__(self):
        super().__init__()
        self.name = "Lufthansa"
        self.base_url = "https://www.lufthansa.com"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> List[Dict]:
        """Search Lufthansa flights"""
        flights = []
        country_code = country_code or 'DE'
        config = self.COUNTRY_CONFIG.get(country_code, self.COUNTRY_CONFIG['DE'])

        try:
            import aiohttp

            jar = aiohttp.CookieJar()
            jar.clear()

            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                # Lufthansa booking search
                url = f"https://www.lufthansa.com/{config['country']}/{config['lang']}/flight/search"

                payload = {
                    "flightQuery": {
                        "origin": origin,
                        "destination": destination,
                        "departureDate": departure_date,
                        "cabinClass": "economy",
                        "travelers": {"adults": adults, "children": 0, "infants": 0},
                        "tripType": "ONE_WAY"
                    },
                    "currency": config['currency']
                }

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Accept-Language': f"{config['lang']}-{country_code}",
                }

                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()

                        for offer in data.get('offers', data.get('flights', [])):
                            price = offer.get('price', {}).get('amount', offer.get('totalPrice', 0))
                            currency = offer.get('price', {}).get('currency', config['currency'])

                            if price > 0:
                                flights.append({
                                    'price': price,
                                    'currency': currency,
                                    'airline': 'LH',
                                    'airline_name': 'Lufthansa',
                                    'departure_time': offer.get('departureTime', ''),
                                    'arrival_time': offer.get('arrivalTime', ''),
                                    'flight_number': offer.get('flightNumber', ''),
                                    'stops': offer.get('stops', 0),
                                    'source': f'lufthansa_{country_code.lower()}'
                                })

                        logger.info(f"Lufthansa ({country_code}): Found {len(flights)} flights")
                    else:
                        logger.debug(f"Lufthansa API ({country_code}) returned status {response.status}")

        except Exception as e:
            logger.debug(f"Lufthansa scraping ({country_code}): {e}")

        return flights


class MultiAirlineScraper:
    """Manages multiple airline scrapers for multi-country comparison"""

    SCRAPERS = {
        'ryanair': RyanairScraper,
        'wizzair': WizzairScraper,
        'lot': LOTScraper,
        'easyjet': EasyJetScraper,
        'lufthansa': LufthansaScraper,
    }

    def __init__(self, airlines: List[str] = None):
        """
        Initialize multi-airline scraper

        Args:
            airlines: List of airlines to scrape (default: all)
        """
        if airlines is None:
            airlines = list(self.SCRAPERS.keys())

        self.scrapers = {}
        for airline in airlines:
            if airline.lower() in self.SCRAPERS:
                self.scrapers[airline.lower()] = self.SCRAPERS[airline.lower()]()

    async def search_all_airlines(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> Dict[str, List[Dict]]:
        """
        Search all configured airlines from a specific country perspective

        Args:
            country_code: ISO country code for price perspective (e.g., 'PL', 'GB')

        Returns:
            Dict with airline name as key and list of flights as value
        """
        results = {}

        # Run all scrapers concurrently
        tasks = []
        for name, scraper in self.scrapers.items():
            task = asyncio.create_task(
                scraper.search_flights(origin, destination, departure_date, adults, country_code)
            )
            tasks.append((name, task))

        # Gather results
        for name, task in tasks:
            try:
                flights = await task
                results[name] = flights
            except Exception as e:
                logger.error(f"Error searching {name}: {e}")
                results[name] = []

        return results

    async def search_from_multiple_countries(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        countries: List[str],
        adults: int = 1
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Search all airlines from multiple country perspectives

        Returns:
            Nested dict: {country: {airline: [flights]}}
        """
        results = {}

        for country_code in countries:
            logger.info(f"Searching airlines from {country_code} perspective...")
            country_results = await self.search_all_airlines(
                origin, destination, departure_date, adults, country_code
            )
            results[country_code] = country_results

        return results

    def search_all_airlines_sync(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        country_code: str = None
    ) -> Dict[str, List[Dict]]:
        """Synchronous wrapper for search_all_airlines"""
        return asyncio.run(self.search_all_airlines(
            origin, destination, departure_date, adults, country_code
        ))

    def search_from_multiple_countries_sync(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        countries: List[str],
        adults: int = 1
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """Synchronous wrapper for search_from_multiple_countries"""
        return asyncio.run(self.search_from_multiple_countries(
            origin, destination, departure_date, countries, adults
        ))


def search_airlines(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    airlines: List[str] = None,
    country_code: str = None
) -> List[Dict]:
    """
    Convenience function to search multiple airlines

    Args:
        country_code: ISO country code for price perspective

    Returns:
        Combined list of all flights from all airlines
    """
    scraper = MultiAirlineScraper(airlines)
    results = scraper.search_all_airlines_sync(
        origin, destination, departure_date, adults, country_code
    )

    # Combine all results
    all_flights = []
    for airline, flights in results.items():
        all_flights.extend(flights)

    return all_flights


def search_airlines_multi_country(
    origin: str,
    destination: str,
    departure_date: str,
    countries: List[str],
    adults: int = 1,
    airlines: List[str] = None
) -> Dict[str, List[Dict]]:
    """
    Search airlines from multiple countries and combine results

    Returns:
        Dict with country as key and list of all flights as value
    """
    scraper = MultiAirlineScraper(airlines)
    results = scraper.search_from_multiple_countries_sync(
        origin, destination, departure_date, countries, adults
    )

    # Flatten airline results per country
    country_flights = {}
    for country, airline_results in results.items():
        all_flights = []
        for airline, flights in airline_results.items():
            all_flights.extend(flights)
        country_flights[country] = all_flights

    return country_flights

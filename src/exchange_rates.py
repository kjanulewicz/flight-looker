"""
Exchange rate fetcher using NBP (Narodowy Bank Polski) API
Provides real-time currency exchange rates to PLN
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExchangeRateFetcher:
    """Fetches and caches exchange rates from NBP API"""

    NBP_API_BASE = "https://api.nbp.pl/api/exchangerates/rates/a"
    CACHE_FILE = ".exchange_rates_cache.json"

    # NBP publishes rates once daily around 11:45-12:00 CET
    # Cache is valid until next NBP publication (next day at noon)

    # Fallback rates if API is unavailable
    FALLBACK_RATES = {
        'PLN': 1.0,
        # Europe
        'EUR': 4.3,
        'GBP': 5.1,
        'CHF': 4.6,
        'SEK': 0.38,
        'NOK': 0.37,
        'DKK': 0.58,
        'CZK': 0.17,
        'HUF': 0.011,
        'RON': 0.86,
        'BGN': 2.2,
        'UAH': 0.097,
        'ALL': 0.042,
        'TRY': 0.12,
        # Americas
        'USD': 4.0,
        'CAD': 2.9,
        'MXN': 0.23,
        'BRL': 0.78,
        'ARS': 0.004,
        # Asia & Middle East
        'JPY': 0.027,
        'KRW': 0.0029,
        'CNY': 0.55,
        'INR': 0.048,
        'THB': 0.12,
        'SGD': 3.0,
        'MYR': 0.9,
        'IDR': 0.00025,
        'VND': 0.00016,
        'PHP': 0.07,
        'AED': 1.09,
        'ILS': 1.1,
        'SAR': 1.07,
        # Oceania & Africa
        'AUD': 2.6,
        'NZD': 2.4,
        'ZAR': 0.22,
        'EGP': 0.08,
        'MAD': 0.4
    }

    # Currency codes supported by NBP API
    NBP_SUPPORTED_CURRENCIES = [
        'EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'CZK', 'HUF', 'RON',
        'BGN', 'TRY', 'CAD', 'AUD', 'NZD', 'JPY', 'CNY', 'INR', 'THB', 'SGD',
        'MYR', 'IDR', 'PHP', 'ZAR', 'BRL', 'MXN', 'ILS', 'KRW', 'AED'
    ]

    def __init__(self):
        self.cache = self._load_cache()

    def _is_cache_valid(self, cache_time: datetime) -> bool:
        """
        Check if cache is still valid based on NBP publication schedule

        NBP publishes rates once per day around 11:45-12:00 CET.
        Cache is valid if:
        - It's from today and current time is before 13:00 (NBP hasn't published new rates yet)
        - It's from today and was fetched after 12:00 (already has today's rates)
        """
        now = datetime.now()
        cache_date = cache_time.date()
        today = now.date()

        # Cache is invalid if it's from yesterday or earlier and it's past noon
        if cache_date < today and now.hour >= 12:
            return False

        # Cache is valid if it's from today
        if cache_date == today:
            return True

        # Cache from yesterday is valid only if it's before noon today (NBP hasn't published yet)
        if cache_date == today - timedelta(days=1) and now.hour < 12:
            return True

        return False

    def _load_cache(self) -> Dict:
        """Load cached exchange rates from file"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    cache_time = datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))

                    if self._is_cache_valid(cache_time):
                        logger.info(f"Using cached exchange rates from {cache_time.strftime('%Y-%m-%d %H:%M')}")
                        return cache
                    else:
                        logger.info(f"Cache expired (from {cache_time.strftime('%Y-%m-%d %H:%M')}), will fetch fresh rates")
            except Exception as e:
                logger.debug(f"Failed to load cache: {e}")
        return {}

    def _save_cache(self, rates: Dict, source: str = "NBP API"):
        """Save exchange rates to cache file"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'source': source,
                'rates': rates,
                'nbp_table_date': datetime.now().strftime('%Y-%m-%d')
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.debug("Exchange rates cached successfully")
        except Exception as e:
            logger.debug(f"Failed to save cache: {e}")

    def _fetch_rate_from_nbp(self, currency: str) -> Optional[float]:
        """Fetch single currency rate from NBP API"""
        if currency == 'PLN':
            return 1.0

        if currency not in self.NBP_SUPPORTED_CURRENCIES:
            logger.debug(f"Currency {currency} not supported by NBP API, using fallback")
            return None

        try:
            url = f"{self.NBP_API_BASE}/{currency.lower()}/?format=json"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                rate = data['rates'][0]['mid']
                logger.debug(f"Fetched {currency} rate from NBP: {rate}")
                return rate
            else:
                logger.debug(f"NBP API returned status {response.status_code} for {currency}")
                return None

        except Exception as e:
            logger.debug(f"Error fetching {currency} from NBP: {e}")
            return None

    def get_all_rates(self, force_refresh: bool = False) -> Dict[str, float]:
        """
        Get all exchange rates to PLN

        Args:
            force_refresh: If True, bypass cache and fetch fresh rates

        Returns:
            Dictionary with currency codes as keys and exchange rates as values
        """
        # Check cache first
        if not force_refresh and self.cache and 'rates' in self.cache:
            return self.cache['rates']

        logger.info("Fetching fresh exchange rates from NBP API...")
        rates = {'PLN': 1.0}
        successful_fetches = 0

        # Fetch rates from NBP
        for currency in self.NBP_SUPPORTED_CURRENCIES:
            rate = self._fetch_rate_from_nbp(currency)
            if rate:
                rates[currency] = rate
                successful_fetches += 1

        # Add currencies not supported by NBP from fallback
        for currency, rate in self.FALLBACK_RATES.items():
            if currency not in rates:
                rates[currency] = rate

        # If we successfully fetched at least some rates, save to cache
        if successful_fetches > 0:
            logger.info(f"Successfully fetched {successful_fetches} exchange rates from NBP API")
            logger.info(f"Exchange rates effective date: {datetime.now().strftime('%Y-%m-%d')}")
            self._save_cache(rates, source="NBP API")
        else:
            logger.warning("Failed to fetch rates from NBP API, using fallback rates")
            rates = self.FALLBACK_RATES.copy()
            self._save_cache(rates, source="Fallback")

        return rates

    def get_rate(self, currency: str) -> float:
        """
        Get exchange rate for a specific currency

        Args:
            currency: Currency code (e.g., 'USD', 'EUR')

        Returns:
            Exchange rate to PLN
        """
        rates = self.get_all_rates()
        return rates.get(currency, self.FALLBACK_RATES.get(currency, 1.0))

    def refresh_rates(self) -> Dict[str, float]:
        """Force refresh all exchange rates"""
        return self.get_all_rates(force_refresh=True)

    def get_rates_info(self) -> Dict:
        """Get information about current exchange rates"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    cache = json.load(f)
                    return {
                        'timestamp': cache.get('timestamp'),
                        'source': cache.get('source', 'Unknown'),
                        'date': cache.get('nbp_table_date', 'Unknown'),
                        'is_valid': self._is_cache_valid(
                            datetime.fromisoformat(cache.get('timestamp', '2000-01-01'))
                        ) if cache.get('timestamp') else False
                    }
            except:
                pass
        return {
            'timestamp': None,
            'source': 'Not cached',
            'date': 'Unknown',
            'is_valid': False
        }


# Global instance for easy access
_fetcher = None


def get_exchange_rate_fetcher() -> ExchangeRateFetcher:
    """Get singleton instance of ExchangeRateFetcher"""
    global _fetcher
    if _fetcher is None:
        _fetcher = ExchangeRateFetcher()
    return _fetcher

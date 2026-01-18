"""
Module for comparing flight prices from various countries
"""
import logging
from typing import Dict, List
import pandas as pd
from datetime import datetime
from .exchange_rates import get_exchange_rate_fetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceComparator:
    """Compares flight prices from various countries"""

    def __init__(self, use_live_rates: bool = True):
        """
        Initialize PriceComparator

        Args:
            use_live_rates: If True, fetch live rates from NBP API. If False, use fallback rates.
        """
        self.results = {}
        self.use_live_rates = use_live_rates
        self.exchange_rate_fetcher = get_exchange_rate_fetcher() if use_live_rates else None

        if use_live_rates:
            # Fetch rates on initialization
            self.exchange_rates = self.exchange_rate_fetcher.get_all_rates()
        else:
            # Use fallback rates
            from .exchange_rates import ExchangeRateFetcher
            self.exchange_rates = ExchangeRateFetcher.FALLBACK_RATES.copy()

    def add_results(self, country: str, flights_data: Dict):
        """
        Adds search results for a country

        Args:
            country: Country name
            flights_data: Data from search (flights, currency, location)
        """
        self.results[country] = flights_data

    def convert_to_pln(self, amount: float, currency: str) -> float:
        """
        Converts price to PLN using live exchange rates from NBP API

        Args:
            amount: Amount in source currency
            currency: Currency code (e.g., 'USD', 'EUR')

        Returns:
            Amount converted to PLN
        """
        rate = self.exchange_rates.get(currency, 1.0)
        return round(amount * rate, 2)

    def refresh_exchange_rates(self):
        """Force refresh exchange rates from NBP API"""
        if self.exchange_rate_fetcher:
            self.exchange_rates = self.exchange_rate_fetcher.refresh_rates()
            logger.info("Exchange rates refreshed from NBP API")

    def get_cheapest_by_country(self) -> Dict[str, Dict]:
        """
        Returns the cheapest flight for each country

        Returns:
            Dictionary: {country: {flight_info, price_pln}}
        """
        cheapest = {}

        for country, data in self.results.items():
            flights = data.get('flights', [])
            currency = data.get('currency', 'EUR')

            if flights:
                min_flight = min(flights, key=lambda x: x['price'])
                price_pln = self.convert_to_pln(min_flight['price'], currency)

                cheapest[country] = {
                    'flight': min_flight,
                    'price_pln': price_pln,
                    'original_price': min_flight['price'],
                    'currency': currency
                }
            else:
                cheapest[country] = None

        return cheapest

    def get_price_comparison_df(self) -> pd.DataFrame:
        """
        Creates a DataFrame with price comparison

        Returns:
            pandas DataFrame with prices in various currencies and PLN
        """
        data = []

        for country, info in self.results.items():
            flights = info.get('flights', [])
            currency = info.get('currency', 'EUR')

            for flight in flights:
                data.append({
                    'Country': country.capitalize(),
                    'Price': flight['price'],
                    'Currency': currency,
                    'Price PLN': self.convert_to_pln(flight['price'], currency),
                    'Airline': flight.get('airline', 'N/A'),
                    'Stops': flight.get('stops', 0),
                    'Departure': flight.get('departure_time', 'N/A'),
                    'Arrival': flight.get('arrival_time', 'N/A')
                })

        if data:
            df = pd.DataFrame(data)
            return df.sort_values('Price PLN')
        else:
            return pd.DataFrame()

    def get_statistics(self) -> Dict:
        """
        Returns price comparison statistics

        Returns:
            Dictionary with statistics
        """
        df = self.get_price_comparison_df()

        if df.empty:
            return {}

        stats = {
            'total_flights_found': len(df),
            'countries_searched': df['Country'].nunique(),
            'min_price_pln': df['Price PLN'].min(),
            'max_price_pln': df['Price PLN'].max(),
            'avg_price_pln': df['Price PLN'].mean(),
            'price_difference': df['Price PLN'].max() - df['Price PLN'].min(),
            'best_country': df.loc[df['Price PLN'].idxmin(), 'Country'],
            'worst_country': df.loc[df['Price PLN'].idxmax(), 'Country']
        }

        return stats

    def print_comparison(self):
        """Displays price comparison in console"""
        print("\n" + "="*80)
        print("FLIGHT PRICE COMPARISON FROM VARIOUS COUNTRIES")
        print("="*80 + "\n")

        cheapest = self.get_cheapest_by_country()

        for country, data in cheapest.items():
            if data:
                print(f"[{country.upper()}]")
                print(f"   Cheapest flight: {data['original_price']} {data['currency']}")
                print(f"   In PLN: {data['price_pln']} PLN")
                print(f"   Airline: {data['flight'].get('airline', 'N/A')}")
                print(f"   Stops: {data['flight'].get('stops', 0)}")
                print(f"   Departure: {data['flight'].get('departure_time', 'N/A')}")
                print()
            else:
                print(f"[{country.upper()}]")
                print(f"   No flights available")
                print()

        stats = self.get_statistics()
        if stats:
            print("="*80)
            print("STATISTICS")
            print("="*80)
            print(f"Flights found: {stats['total_flights_found']}")
            print(f"Countries searched: {stats['countries_searched']}")
            print(f"Cheapest flight: {stats['min_price_pln']:.2f} PLN ({stats['best_country']})")
            print(f"Most expensive flight: {stats['max_price_pln']:.2f} PLN ({stats['worst_country']})")
            print(f"Average price: {stats['avg_price_pln']:.2f} PLN")
            print(f"Price difference: {stats['price_difference']:.2f} PLN")
            print(f"Savings: {(stats['price_difference']/stats['max_price_pln']*100):.1f}%")
            print("="*80 + "\n")

    def save_to_csv(self, filename: str = 'flight_comparison.csv'):
        """Saves results to CSV file"""
        df = self.get_price_comparison_df()
        if not df.empty:
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"Results saved to file: {filename}")
        else:
            logger.warning("No data to save")

#!/usr/bin/env python3
"""
Top Deals Finder - Analyzes flight prices from 30 countries and shows top 5 cheapest
"""

import sys
from datetime import datetime, timedelta
from src.vpn_manager import VPNManager
from src.flight_search import FlightSearcher, MultiCountryFlightSearcher
from src.price_comparator import PriceComparator
from src.visualizer import FlightVisualizer
import argparse
import logging

logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)

# Set of 30 diverse countries for price comparison
DEFAULT_COUNTRIES = [
    # Europe (15 countries)
    'poland', 'germany', 'france', 'spain', 'italy',
    'netherlands', 'belgium', 'austria', 'switzerland', 'sweden',
    'portugal', 'greece', 'czech', 'hungary', 'romania',
    # Eastern Europe & Turkey (3 countries)
    'bulgaria', 'croatia', 'turkey',
    # Americas (4 countries)
    'usa', 'canada', 'mexico', 'brazil',
    # Asia (5 countries)
    'japan', 'india', 'thailand', 'singapore', 'uae',
    # Oceania & Africa (3 countries)
    'australia', 'south_africa', 'egypt'
]


def print_header():
    """Print application header"""
    print("\n" + "="*80)
    print("  TOP FLIGHT DEALS FINDER".center(80))
    print("  Analyzing prices from 30 countries worldwide".center(80))
    print("="*80 + "\n")


def print_top_deals(comparator: PriceComparator, top_n: int = 5):
    """Print top N cheapest deals"""

    # Get all countries with their cheapest flights
    countries_data = []

    for country in comparator.results.keys():
        flights = comparator.results[country]['flights']
        currency = comparator.results[country].get('currency', 'EUR')

        if flights:
            cheapest = min(flights, key=lambda x: x['price'])
            price_pln = comparator.convert_to_pln(cheapest['price'], currency)

            countries_data.append({
                'country': country,
                'price_pln': price_pln,
                'price_original': cheapest['price'],
                'currency': currency,
                'airline': cheapest.get('airline', 'N/A'),
                'stops': cheapest.get('stops', 0),
                'departure': cheapest.get('departure_time', 'N/A'),
                'arrival': cheapest.get('arrival_time', 'N/A')
            })

    # Sort by price PLN
    countries_data.sort(key=lambda x: x['price_pln'])

    if not countries_data:
        print("❌ No flight data available")
        return

    print("\n" + "="*80)
    print(f"  🏆 TOP {top_n} CHEAPEST COUNTRIES TO BUY FROM".center(80))
    print("="*80 + "\n")

    # Show top N
    for i, data in enumerate(countries_data[:top_n], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        country_name = data['country'].upper().replace('_', ' ')

        print(f"{medal} {country_name}")
        print(f"   💰 Price: {data['price_pln']:.2f} PLN ({data['price_original']:.2f} {data['currency']})")
        print(f"   ✈️  Airline: {data['airline']} | Stops: {data['stops']}")
        print(f"   🕐 Departure: {data['departure']}")
        print()

    # Show savings statistics
    cheapest = countries_data[0]['price_pln']
    most_expensive = countries_data[-1]['price_pln']
    average = sum(d['price_pln'] for d in countries_data) / len(countries_data)
    savings = most_expensive - cheapest
    savings_pct = (savings / most_expensive) * 100

    print("="*80)
    print("  📊 PRICE STATISTICS".center(80))
    print("="*80 + "\n")
    print(f"Countries analyzed: {len(countries_data)}")
    print(f"Cheapest price: {cheapest:.2f} PLN ({countries_data[0]['country'].upper()})")
    print(f"Most expensive: {most_expensive:.2f} PLN ({countries_data[-1]['country'].upper()})")
    print(f"Average price: {average:.2f} PLN")
    print(f"Maximum savings: {savings:.2f} PLN ({savings_pct:.1f}%)")
    print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Find top flight deals from 30 countries worldwide'
    )
    parser.add_argument('-o', '--origin', required=True,
                       help='Origin airport IATA code (e.g., POZ, WAW)')
    parser.add_argument('-d', '--destination', required=True,
                       help='Destination airport IATA code (e.g., AMS, BCN)')
    parser.add_argument('--date',
                       help='Departure date YYYY-MM-DD (default: 30 days from now)')
    parser.add_argument('-a', '--adults', type=int, default=1,
                       help='Number of passengers (default: 1)')
    parser.add_argument('-n', '--top', type=int, default=5,
                       help='Number of top deals to show (default: 5)')
    parser.add_argument('--countries', nargs='+',
                       help='Custom list of countries (default: 30 predefined countries)')
    parser.add_argument('--save-csv', action='store_true',
                       help='Save results to CSV file')
    parser.add_argument('--no-charts', action='store_true',
                       help='Skip chart generation')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output (show search progress)')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Set departure date
    if args.date:
        departure_date = args.date
    else:
        departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    # Select countries
    countries = args.countries if args.countries else DEFAULT_COUNTRIES

    # Print header
    print_header()

    print(f"Route: {args.origin.upper()} → {args.destination.upper()}")
    print(f"Date: {departure_date}")
    print(f"Passengers: {args.adults}")
    print(f"Countries to analyze: {len(countries)}")
    print(f"\nSearching flights... (this may take a few minutes)")
    print()

    # Initialize components
    vpn_manager = VPNManager(use_nordvpn=False)
    flight_searcher = FlightSearcher()
    multi_searcher = MultiCountryFlightSearcher(vpn_manager, flight_searcher)

    # Search flights
    results = multi_searcher.search_from_countries(
        countries=countries,
        origin=args.origin.upper(),
        destination=args.destination.upper(),
        departure_date=departure_date,
        adults=args.adults
    )

    # Create comparison
    comparator = PriceComparator()
    for country, data in results.items():
        comparator.add_results(country, data)

    # Display exchange rate info
    if comparator.exchange_rate_fetcher:
        rates_info = comparator.exchange_rate_fetcher.get_rates_info()
        if rates_info['source'] != 'Not cached':
            print(f"📊 Exchange rates: {rates_info['source']} (date: {rates_info['date']})")
            print()

    # Display top deals
    print_top_deals(comparator, top_n=args.top)

    # Save to CSV if requested
    if args.save_csv:
        filename = f"top_deals_{args.origin}_{args.destination}_{departure_date}.csv"
        comparator.save_to_csv(filename)
        print(f"✅ Results saved to: {filename}\n")

    # Create charts if requested
    if not args.no_charts:
        print("Creating visualizations...")
        visualizer = FlightVisualizer(output_dir='charts/top_deals')
        route = f"{args.origin.upper()} → {args.destination.upper()}"
        charts = visualizer.create_all_visualizations(comparator, route)
        print(f"✅ Created {len(charts)} charts in charts/top_deals/\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Search cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

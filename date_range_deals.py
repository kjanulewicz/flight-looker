#!/usr/bin/env python3
"""
Date Range Deals Finder - Analyzes flight prices across multiple dates
Finds the best date to fly for a given route
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


def print_header():
    """Print application header"""
    print("\n" + "="*80)
    print("  DATE RANGE DEALS FINDER".center(80))
    print("  Find the best date to fly for your route".center(80))
    print("="*80 + "\n")


def generate_date_range(center_date: str, days_before: int, days_after: int):
    """Generate list of dates around center date"""
    center = datetime.strptime(center_date, '%Y-%m-%d')
    dates = []

    for i in range(-days_before, days_after + 1):
        date = center + timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))

    return dates


def print_date_comparison(results_by_date: dict, origin: str, destination: str):
    """Print comparison of prices across dates"""

    # Prepare data
    date_data = []
    for date_str, comparator in results_by_date.items():
        if not comparator.results:
            continue

        # Get cheapest price across all countries for this date
        cheapest_price = float('inf')
        cheapest_country = None

        for country in comparator.results.keys():
            flights = comparator.results[country]['flights']
            currency = comparator.results[country].get('currency', 'EUR')

            if flights:
                flight = min(flights, key=lambda x: x['price'])
                price_pln = comparator.convert_to_pln(flight['price'], currency)

                if price_pln < cheapest_price:
                    cheapest_price = price_pln
                    cheapest_country = country

        if cheapest_country:
            date_data.append({
                'date': date_str,
                'price': cheapest_price,
                'country': cheapest_country,
                'day_of_week': datetime.strptime(date_str, '%Y-%m-%d').strftime('%A')
            })

    # Sort by price
    date_data.sort(key=lambda x: x['price'])

    if not date_data:
        print("❌ No flight data available")
        return

    print("\n" + "="*80)
    print(f"  🗓️  BEST DATES TO FLY: {origin.upper()} → {destination.upper()}".center(80))
    print("="*80 + "\n")

    # Show top 5 cheapest dates
    for i, data in enumerate(date_data[:5], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")

        print(f"{medal} {data['date']} ({data['day_of_week']})")
        print(f"   💰 Price: {data['price']:.2f} PLN")
        print(f"   🌍 Country: {data['country'].upper().replace('_', ' ')}")
        print()

    # Show statistics
    prices = [d['price'] for d in date_data]
    cheapest = min(prices)
    most_expensive = max(prices)
    average = sum(prices) / len(prices)
    savings = most_expensive - cheapest

    print("="*80)
    print("  📊 DATE COMPARISON STATISTICS".center(80))
    print("="*80 + "\n")
    print(f"Dates analyzed: {len(date_data)}")
    print(f"Cheapest date: {date_data[0]['date']} ({date_data[0]['day_of_week']}) - {cheapest:.2f} PLN")
    print(f"Most expensive date: {date_data[-1]['date']} ({date_data[-1]['day_of_week']}) - {most_expensive:.2f} PLN")
    print(f"Average price: {average:.2f} PLN")
    print(f"Maximum savings: {savings:.2f} PLN ({(savings/most_expensive)*100:.1f}%)")
    print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Find best dates to fly by analyzing price range'
    )
    parser.add_argument('-o', '--origin', required=True,
                       help='Origin airport IATA code (e.g., POZ, WAW)')
    parser.add_argument('-d', '--destination', required=True,
                       help='Destination airport IATA code (e.g., AMS, BCN)')
    parser.add_argument('--date', required=True,
                       help='Center date YYYY-MM-DD')
    parser.add_argument('--days-before', type=int, default=3,
                       help='Number of days before center date (default: 3)')
    parser.add_argument('--days-after', type=int, default=3,
                       help='Number of days after center date (default: 3)')
    parser.add_argument('-a', '--adults', type=int, default=1,
                       help='Number of passengers (default: 1)')
    parser.add_argument('--countries', nargs='+',
                       default=['poland', 'germany', 'france', 'spain', 'italy'],
                       help='Countries to compare (default: poland germany france spain italy)')
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

    # Generate date range
    dates = generate_date_range(args.date, args.days_before, args.days_after)

    # Print header
    print_header()

    print(f"Route: {args.origin.upper()} → {args.destination.upper()}")
    print(f"Center date: {args.date}")
    print(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} dates)")
    print(f"Countries: {', '.join(args.countries)}")
    print(f"Passengers: {args.adults}")
    print(f"\nSearching flights across {len(dates)} dates...")
    print(f"This will take approximately {len(dates) * len(args.countries) * 2} seconds\n")

    # Initialize components
    vpn_manager = VPNManager(use_nordvpn=False)  # Use demo mode for speed
    flight_searcher = FlightSearcher()
    multi_searcher = MultiCountryFlightSearcher(vpn_manager, flight_searcher)

    # Search flights for each date
    results_by_date = {}

    for i, date_str in enumerate(dates, 1):
        print(f"\n[{i}/{len(dates)}] Searching {date_str}...")

        results = multi_searcher.search_from_countries(
            countries=args.countries,
            origin=args.origin.upper(),
            destination=args.destination.upper(),
            departure_date=date_str,
            adults=args.adults
        )

        # Create comparison for this date
        comparator = PriceComparator()
        for country, data in results.items():
            comparator.add_results(country, data)

        results_by_date[date_str] = comparator

    # Display results
    print_date_comparison(results_by_date, args.origin, args.destination)

    # Save to CSV if requested
    if args.save_csv:
        # Combine all results into one CSV
        all_data = []
        for date_str, comparator in results_by_date.items():
            for country in comparator.results.keys():
                flights = comparator.results[country]['flights']
                currency = comparator.results[country].get('currency', 'EUR')

                for flight in flights:
                    all_data.append({
                        'Date': date_str,
                        'Country': country,
                        'Price': flight['price'],
                        'Currency': currency,
                        'Price PLN': comparator.convert_to_pln(flight['price'], currency),
                        'Airline': flight.get('airline', 'N/A'),
                        'Stops': flight.get('stops', 0),
                        'Departure': flight.get('departure_time', 'N/A')
                    })

        if all_data:
            import pandas as pd
            df = pd.DataFrame(all_data)
            filename = f"date_range_{args.origin}_{args.destination}_{dates[0]}_to_{dates[-1]}.csv"
            df.to_csv(filename, index=False)
            print(f"✅ Results saved to: {filename}\n")

    # Create charts if requested
    if not args.no_charts:
        print("Creating date comparison chart...")

        # Prepare data for visualization
        date_prices = []
        for date_str, comparator in results_by_date.items():
            for country in comparator.results.keys():
                flights = comparator.results[country]['flights']
                currency = comparator.results[country].get('currency', 'EUR')

                if flights:
                    cheapest = min(flights, key=lambda x: x['price'])
                    price_pln = comparator.convert_to_pln(cheapest['price'], currency)
                    date_prices.append({
                        'Date': date_str,
                        'Price PLN': price_pln,
                        'Country': country
                    })

        if date_prices:
            import pandas as pd
            import matplotlib.pyplot as plt
            import seaborn as sns

            df = pd.DataFrame(date_prices)

            # Create line chart showing price trends across dates
            plt.figure(figsize=(14, 6))

            # Get cheapest price per date
            cheapest_by_date = df.groupby('Date')['Price PLN'].min().reset_index()
            cheapest_by_date = cheapest_by_date.sort_values('Date')

            plt.plot(cheapest_by_date['Date'], cheapest_by_date['Price PLN'],
                    marker='o', linewidth=2, markersize=8, color='#2ecc71')

            plt.title(f'Price Trend: {args.origin.upper()} → {args.destination.upper()}',
                     fontsize=14, fontweight='bold', pad=20)
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Price (PLN)', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3, linestyle='--')
            plt.tight_layout()

            import os
            os.makedirs('charts/date_range', exist_ok=True)
            chart_path = f'charts/date_range/price_trend_{args.origin}_{args.destination}.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()

            print(f"✅ Chart saved to: {chart_path}\n")


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

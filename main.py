#!/usr/bin/env python3
"""
Flight Price Comparison Tool
Compares flight prices from various countries using VPN

Author: Flight Looker
"""
import argparse
import sys
from datetime import datetime, timedelta
from src.vpn_manager import VPNManager
from src.flight_search import FlightSearcher, MultiCountryFlightSearcher
from src.price_comparator import PriceComparator
from src.visualizer import FlightVisualizer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Compare flight prices from various countries using VPN',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:

  # Compare prices Poznań → Amsterdam from 3 countries (demo mode)
  python main.py --origin POZ --destination AMS --countries poland turkey albania

  # Compare with specific date
  python main.py --origin POZ --destination AMS --date 2026-03-15 --countries poland germany

  # Use VPN (requires NordVPN CLI)
  python main.py --origin POZ --destination AMS --countries poland turkey --use-vpn

  # Save results to CSV
  python main.py --origin POZ --destination AMS --countries poland turkey --save-csv

Airport codes (IATA):
  POZ - Poznań        AMS - Amsterdam      WAW - Warsaw
  KRK - Kraków        LHR - London         BCN - Barcelona
  GDN - Gdańsk        CDG - Paris          FCO - Rome

Available countries:
  poland, turkey, albania, germany, united_kingdom, usa
        """
    )

    parser.add_argument(
        '--origin', '-o',
        required=True,
        help='IATA airport code for departure (e.g., POZ for Poznań)'
    )

    parser.add_argument(
        '--destination', '-d',
        required=True,
        help='IATA airport code for destination (e.g., AMS for Amsterdam)'
    )

    parser.add_argument(
        '--date',
        help='Departure date in YYYY-MM-DD format (default: in 30 days)',
        default=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    )

    parser.add_argument(
        '--countries', '-c',
        nargs='+',
        default=['poland', 'turkey', 'albania'],
        help='List of countries to compare (e.g., poland turkey albania)'
    )

    parser.add_argument(
        '--adults', '-a',
        type=int,
        default=1,
        help='Number of adult passengers (default: 1)'
    )

    parser.add_argument(
        '--use-vpn',
        action='store_true',
        help='Use VPN (requires installed NordVPN CLI)'
    )

    parser.add_argument(
        '--save-csv',
        action='store_true',
        help='Save results to CSV file'
    )

    parser.add_argument(
        '--no-charts',
        action='store_true',
        help='Do not create charts'
    )

    parser.add_argument(
        '--no-scrape',
        action='store_true',
        help='Disable scraping airline websites (use only Amadeus API)'
    )

    parser.add_argument(
        '--airlines',
        nargs='+',
        default=None,
        help='Airlines to scrape (e.g., ryanair wizzair lot). Default: all'
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "="*80)
    print("  FLIGHT PRICE COMPARISON TOOL")
    print("  Flight price comparison from various countries")
    print("="*80 + "\n")

    print(f"Route: {args.origin} -> {args.destination}")
    print(f"Departure date: {args.date}")
    print(f"Passengers: {args.adults}")
    print(f"Countries: {', '.join([c.capitalize() for c in args.countries])}")
    print(f"VPN mode: {'YES' if args.use_vpn else 'NO'}")
    print(f"Scrape airlines: {'NO' if args.no_scrape else 'YES'}")
    if not args.no_scrape and args.airlines:
        print(f"Airlines: {', '.join(args.airlines)}")
    print()

    if args.use_vpn:
        print("WARNING: VPN mode requires installed and configured NordVPN")
        print("   If you don't have NordVPN, the application will use API-only mode\n")

    if args.no_scrape:
        print("INFO: Scraping disabled - using only Amadeus API\n")
    else:
        print("INFO: Scraping airline websites for real geo-based prices")
        print("   This may take longer but gives more accurate price differences\n")

    try:
        # Initialize components
        vpn_manager = VPNManager(use_nordvpn=args.use_vpn)
        flight_searcher = FlightSearcher(use_scrapers=not args.no_scrape)
        multi_searcher = MultiCountryFlightSearcher(vpn_manager, flight_searcher)

        # Search for flights from different countries
        print("Starting flight search...\n")
        results = multi_searcher.search_from_countries(
            countries=args.countries,
            origin=args.origin,
            destination=args.destination,
            departure_date=args.date,
            adults=args.adults
        )

        # Compare prices
        print("\nAnalyzing results...\n")
        comparator = PriceComparator()

        for country, data in results.items():
            comparator.add_results(country, data)

        # Display comparison
        comparator.print_comparison()

        # Save to CSV if required
        if args.save_csv:
            filename = f'flight_comparison_{args.origin}_{args.destination}_{args.date}.csv'
            comparator.save_to_csv(filename)
            print(f"Results saved to: {filename}\n")

        # Create charts if required
        if not args.no_charts:
            print("Creating charts...")
            visualizer = FlightVisualizer()
            route = f"{args.origin} -> {args.destination}"
            charts = visualizer.create_all_visualizations(comparator, route)

            if charts:
                print(f"\nCreated {len(charts)} charts:")
                for chart in charts:
                    print(f"   - {chart}")
            print()

        print("="*80)
        print("ANALYSIS COMPLETED")
        print("="*80 + "\n")

        # Savings summary
        stats = comparator.get_statistics()
        if stats:
            savings = stats.get('price_difference', 0)
            if savings > 0:
                print(f"You can save up to {savings:.2f} PLN")
                print(f"   by buying a ticket in {stats.get('best_country', 'N/A')} instead of {stats.get('worst_country', 'N/A')}!")
                print()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Example usage of Flight Price Comparison Tool

This script shows how to use the library programmatically
"""

from src.vpn_manager import VPNManager
from src.flight_search import FlightSearcher, MultiCountryFlightSearcher
from src.price_comparator import PriceComparator
from src.visualizer import FlightVisualizer
from datetime import datetime, timedelta


def example_basic_search():
    """Example of basic search without VPN"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic search (demo mode)")
    print("="*60 + "\n")

    # Initialize
    searcher = FlightSearcher()

    # Search for flights Poznań → Amsterdam in 30 days
    departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    print(f"Searching for flights POZ → AMS on {departure_date}\n")

    flights = searcher.search_flights(
        origin='POZ',
        destination='AMS',
        departure_date=departure_date,
        adults=1,
        currency='PLN'
    )

    # Display results
    print(f"Found {len(flights)} flights:\n")
    for i, flight in enumerate(flights[:3], 1):
        print(f"{i}. {flight['price']} {flight['currency']} - {flight['airline']}")
        print(f"   Departure: {flight['departure_time']}")
        print(f"   Stops: {flight['stops']}")
        print()


def example_multi_country_comparison():
    """Example of price comparison from different countries"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Price comparison from different countries")
    print("="*60 + "\n")

    # Initialize (without real VPN for demo)
    vpn_manager = VPNManager(use_nordvpn=False)
    flight_searcher = FlightSearcher()
    multi_searcher = MultiCountryFlightSearcher(vpn_manager, flight_searcher)

    # Search parameters
    countries = ['poland', 'turkey', 'albania']
    origin = 'POZ'
    destination = 'AMS'
    departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    print(f"Comparing flight prices {origin} → {destination}")
    print(f"Date: {departure_date}")
    print(f"Countries: {', '.join(countries)}\n")

    # Search for flights
    results = multi_searcher.search_from_countries(
        countries=countries,
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        adults=1
    )

    # Create comparison
    comparator = PriceComparator()
    for country, data in results.items():
        comparator.add_results(country, data)

    # Display results
    comparator.print_comparison()

    return comparator


def example_with_visualization():
    """Example with visualization"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Complete analysis with charts")
    print("="*60 + "\n")

    # Execute search (using the previous example)
    comparator = example_multi_country_comparison()

    # Create visualizations
    print("\nCreating charts...")
    visualizer = FlightVisualizer(output_dir='charts/example')

    charts = visualizer.create_all_visualizations(
        comparator,
        route="POZ → AMS"
    )

    print(f"\nCreated {len(charts)} charts:")
    for chart in charts:
        print(f"   - {chart}")

    # Save to CSV
    comparator.save_to_csv('data/example_comparison.csv')


def example_custom_analysis():
    """Example of custom data analysis"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom data analysis")
    print("="*60 + "\n")

    # Get data
    vpn_manager = VPNManager(use_nordvpn=False)
    flight_searcher = FlightSearcher()
    multi_searcher = MultiCountryFlightSearcher(vpn_manager, flight_searcher)

    departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    results = multi_searcher.search_from_countries(
        countries=['poland', 'turkey', 'albania', 'germany'],
        origin='WAW',
        destination='BCN',
        departure_date=departure_date,
        adults=2
    )

    # Custom analysis
    comparator = PriceComparator()
    for country, data in results.items():
        comparator.add_results(country, data)

    # Get DataFrame
    df = comparator.get_price_comparison_df()

    print("DataFrame statistics:")
    print(df.describe())
    print("\nCheapest flights:")
    print(df.nsmallest(5, 'Price PLN')[['Country', 'Price PLN', 'Airline', 'Stops']])

    # Analysis by airline
    print("\nAverage prices by airline:")
    airline_avg = df.groupby('Airline')['Price PLN'].mean().sort_values()
    print(airline_avg)


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("FLIGHT PRICE COMPARISON - USAGE EXAMPLES")
    print("="*60)

    # Run examples
    example_basic_search()

    input("\nPress Enter to continue to example 2...")
    example_multi_country_comparison()

    input("\nPress Enter to continue to example 3...")
    example_with_visualization()

    input("\nPress Enter to continue to example 4...")
    example_custom_analysis()

    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED")
    print("="*60 + "\n")


if __name__ == '__main__':
    # You can run a specific example or all of them
    import sys

    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num == '1':
            example_basic_search()
        elif example_num == '2':
            example_multi_country_comparison()
        elif example_num == '3':
            example_with_visualization()
        elif example_num == '4':
            example_custom_analysis()
        else:
            print("Usage: python example.py [1|2|3|4]")
    else:
        main()

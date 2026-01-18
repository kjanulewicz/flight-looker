"""
Module for visualizing flight price comparison
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import logging
from typing import Dict, List
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Settings for Polish characters
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class FlightVisualizer:
    """Creates charts comparing flight prices"""

    def __init__(self, output_dir: str = 'charts'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Style settings
        sns.set_style("whitegrid")
        self.colors = sns.color_palette("husl", 8)

    def plot_price_comparison(
        self,
        comparator,
        title: str = "Flight price comparison from various countries"
    ) -> str:
        """
        Creates a bar chart comparing the cheapest prices from each country

        Args:
            comparator: PriceComparator object with data
            title: Chart title

        Returns:
            Path to the saved chart
        """
        cheapest = comparator.get_cheapest_by_country()

        countries = []
        prices_pln = []
        original_prices = []
        currencies = []

        for country, data in cheapest.items():
            if data:
                countries.append(country.capitalize())
                prices_pln.append(data['price_pln'])
                original_prices.append(data['original_price'])
                currencies.append(data['currency'])

        if not countries:
            logger.warning("No data for visualization")
            return ""

        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))

        bars = ax.bar(countries, prices_pln, color=self.colors[:len(countries)])

        # Add price labels
        for i, (bar, price, orig, curr) in enumerate(zip(bars, prices_pln, original_prices, currencies)):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{price:.0f} PLN\n({orig:.0f} {curr})',
                ha='center',
                va='bottom',
                fontsize=9
            )

        ax.set_ylabel('Price (PLN)', fontsize=12)
        ax.set_xlabel('Country', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')

        # Add grid
        ax.yaxis.grid(True, alpha=0.3)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # Save chart
        filename = os.path.join(self.output_dir, 'price_comparison_bar.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Chart saved: {filename}")
        return filename

    def plot_all_flights_distribution(
        self,
        comparator,
        title: str = "Distribution of prices of all available flights"
    ) -> str:
        """
        Creates a box plot showing the distribution of prices for each country

        Returns:
            Path to the saved chart
        """
        df = comparator.get_price_comparison_df()

        if df.empty:
            logger.warning("No data for visualization")
            return ""

        fig, ax = plt.subplots(figsize=(12, 6))

        # Box plot
        sns.boxplot(data=df, x='Country', y='Price PLN', palette=self.colors, ax=ax)

        # Add points for all flights
        sns.swarmplot(data=df, x='Country', y='Price PLN', color='black', alpha=0.5, size=4, ax=ax)

        ax.set_ylabel('Price (PLN)', fontsize=12)
        ax.set_xlabel('Country', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        filename = os.path.join(self.output_dir, 'price_distribution_box.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Chart saved: {filename}")
        return filename

    def plot_price_by_airline(
        self,
        comparator,
        title: str = "Prices by airline"
    ) -> str:
        """
        Creates a chart comparing prices by airline

        Returns:
            Path to the saved chart
        """
        df = comparator.get_price_comparison_df()

        if df.empty:
            logger.warning("No data for visualization")
            return ""

        fig, ax = plt.subplots(figsize=(12, 6))

        # Group by airline and country
        pivot_data = df.pivot_table(
            values='Price PLN',
            index='Airline',
            columns='Country',
            aggfunc='min'
        )

        pivot_data.plot(kind='bar', ax=ax, color=self.colors[:len(pivot_data.columns)])

        ax.set_ylabel('Price (PLN)', fontsize=12)
        ax.set_xlabel('Airline', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(title='Country', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        filename = os.path.join(self.output_dir, 'price_by_airline.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Chart saved: {filename}")
        return filename

    def plot_savings_comparison(
        self,
        comparator,
        title: str = "Potential savings when buying from different countries"
    ) -> str:
        """
        Creates a chart showing savings compared to the most expensive option

        Returns:
            Path to the saved chart
        """
        cheapest = comparator.get_cheapest_by_country()

        countries = []
        prices_pln = []

        for country, data in cheapest.items():
            if data:
                countries.append(country.capitalize())
                prices_pln.append(data['price_pln'])

        if not countries:
            logger.warning("No data for visualization")
            return ""

        max_price = max(prices_pln)
        savings = [max_price - price for price in prices_pln]
        savings_percent = [(s/max_price)*100 for s in savings]

        # Create chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Chart 1: Savings in PLN
        bars1 = ax1.barh(countries, savings, color=self.colors[:len(countries)])
        ax1.set_xlabel('Savings (PLN)', fontsize=12)
        ax1.set_title('Savings in PLN', fontsize=12, fontweight='bold')

        for i, (bar, saving) in enumerate(zip(bars1, savings)):
            width = bar.get_width()
            ax1.text(
                width,
                bar.get_y() + bar.get_height()/2.,
                f'{saving:.0f} PLN',
                ha='left',
                va='center',
                fontsize=9
            )

        # Chart 2: Savings in percentage
        bars2 = ax2.barh(countries, savings_percent, color=self.colors[:len(countries)])
        ax2.set_xlabel('Savings (%)', fontsize=12)
        ax2.set_title('Savings in percentage', fontsize=12, fontweight='bold')

        for i, (bar, percent) in enumerate(zip(bars2, savings_percent)):
            width = bar.get_width()
            ax2.text(
                width,
                bar.get_y() + bar.get_height()/2.,
                f'{percent:.1f}%',
                ha='left',
                va='center',
                fontsize=9
            )

        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()

        filename = os.path.join(self.output_dir, 'savings_comparison.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Chart saved: {filename}")
        return filename

    def create_all_visualizations(self, comparator, route: str = "") -> List[str]:
        """
        Creates all charts

        Args:
            comparator: PriceComparator object
            route: Route description (e.g., "POZ → AMS")

        Returns:
            List of paths to saved charts
        """
        logger.info("Creating visualizations...")

        charts = []

        # Chart 1: Comparison of cheapest prices
        if route:
            title1 = f"Flight price comparison {route}"
        else:
            title1 = "Flight price comparison from various countries"
        chart1 = self.plot_price_comparison(comparator, title1)
        if chart1:
            charts.append(chart1)

        # Chart 2: Distribution of all prices
        chart2 = self.plot_all_flights_distribution(comparator)
        if chart2:
            charts.append(chart2)

        # Chart 3: Prices by airline
        chart3 = self.plot_price_by_airline(comparator)
        if chart3:
            charts.append(chart3)

        # Chart 4: Savings
        chart4 = self.plot_savings_comparison(comparator)
        if chart4:
            charts.append(chart4)

        logger.info(f"Created {len(charts)} charts in directory: {self.output_dir}")
        return charts

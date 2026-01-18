# Flight Price Comparison Tool 🛫

A tool for comparing flight prices from different countries via VPN. Check if purchasing a ticket from another country's perspective can save you money.

## 🎯 Project Description

This application performs flight searches by simulating access from different countries (using VPN or proxy) and compares prices. Often, the same flight can cost differently depending on which country you're purchasing from.

### Example Use Case

Compare flight prices from Poznań → Amsterdam from the perspective of:
- 🇵🇱 Polish website
- 🇹🇷 Turkish website
- 🇦🇱 Albanian website

## ✨ Features

- 🌍 **Multi-country search** - simulates access from selected countries via VPN
- 📅 **Date range analysis** - find the best date to fly by comparing prices across multiple days
- 💰 **Price comparison** - converts all prices to PLN for easy comparison
- 📊 **Data visualization** - creates comparison charts in Python
- 💾 **CSV export** - saves results to CSV file
- 📈 **Savings statistics** - shows how much you can save
- 🎨 **Multiple chart types**:
  - Bar chart for price comparison
  - Box plot for price distribution
  - Comparison by airlines
  - Savings visualization
  - Date range price trends

## 🚀 Installation

### Two Installation Methods

**Method 1: Docker (Recommended for VPN support)**
- Works on macOS, Linux, Windows
- Includes NordVPN CLI
- No Python setup required
- See [DOCKER.md](DOCKER.md) for full guide

**Method 2: Native Python**
- Direct installation
- No VPN support on macOS
- VPN works on Linux only

---

### Method 1: Docker Installation (Recommended)

#### Requirements
- Docker Desktop

#### Quick Start
```bash
git clone https://github.com/yourusername/flight-looker.git
cd flight-looker
./docker-run.sh top-deals --origin WAW --destination BCN
```

See [DOCKER.md](DOCKER.md) for complete Docker usage guide.

---

### Method 2: Native Python Installation

#### Requirements

- Python 3.8 or newer
- pip (Python package manager)
- (Optional) NordVPN CLI for real VPN connections (Linux only)

#### Step 1: Clone the repository

```bash
git clone https://github.com/yourusername/flight-looker.git
cd flight-looker
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configuration (optional)

Copy `.env.example` to `.env` and fill in the data:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys (optional):

```env
AMADEUS_API_KEY=your_api_key_here
AMADEUS_API_SECRET=your_api_secret_here

# For VPN functionality (optional)
NORDVPN_TOKEN=your_nordvpn_token_here
```

**Note**:
- The application works without API keys in demo mode with sample data
- For VPN: Generate token at [Nord Account](https://my.nordaccount.com) (Services > NordVPN > Access tokens)

## 📖 Usage

### Quick Start: Top Deals Finder 🏆

**NEW!** Find the best deals by analyzing 30 countries worldwide:

```bash
python top_deals.py --origin WAW --destination BCN --date 2026-03-15
```

This will automatically search 30 countries and show you the top 5 cheapest options with detailed statistics.

**Custom analysis:**
```bash
# Analyze specific countries
python top_deals.py --origin POZ --destination AMS --countries poland germany france spain italy

# Show top 10 instead of top 5
python top_deals.py --origin WAW --destination LHR --top 10

# Save results to CSV
python top_deals.py --origin KRK --destination BCN --save-csv
```

### Date Range Deals Finder 📅

**NEW!** Find the best date to fly by analyzing price variations across multiple dates:

```bash
python date_range_deals.py --origin WAW --destination BCN --date 2026-03-15
```

This will search ±3 days around your target date and show you which dates have the cheapest flights, revealing dynamic pricing patterns.

**Custom date range:**
```bash
# Wider search: ±7 days
python date_range_deals.py --origin POZ --destination AMS --date 2026-03-20 --days-before 7 --days-after 7

# Specific countries only
python date_range_deals.py --origin WAW --destination LHR --date 2026-04-10 --countries poland germany france

# Save results and skip charts
python date_range_deals.py --origin KRK --destination BCN --date 2026-05-15 --save-csv --no-charts

# With VPN (requires NordVPN CLI)
python date_range_deals.py --origin WAW --destination BCN --date 2026-03-15 --use-vpn
```

**Example output:**
```
📅 Best dates to fly: WAW → BCN

🥇 2026-03-15 (Saturday) - 426.74 PLN
🥈 2026-03-14 (Friday)   - 433.16 PLN
🥉 2026-03-13 (Thursday) - 439.12 PLN
4. 2026-03-16 (Sunday)   - 441.53 PLN
5. 2026-03-12 (Wednesday)- 449.90 PLN

Maximum savings: 105.52 PLN (19.8%) by choosing the right date
```

### Basic usage

Simplest way - compare flights in demo mode (without VPN):

```bash
python main.py --origin POZ --destination AMS --countries poland turkey albania
```

### Advanced options

```bash
# With specific departure date
python main.py --origin POZ --destination AMS --date 2026-03-15 --countries poland germany

# With VPN (requires NordVPN CLI)
python main.py --origin WAW --destination BCN --countries poland turkey --use-vpn

# Save results to CSV
python main.py --origin GDN --destination LHR --countries poland turkey albania --save-csv

# Multiple passengers
python main.py --origin KRK --destination AMS --adults 2 --countries poland germany
```

### Available parameters

```
--origin, -o          IATA airport code for departure (e.g. POZ)
--destination, -d     IATA airport code for arrival (e.g. AMS)
--date               Departure date YYYY-MM-DD (default: 30 days from now)
--countries, -c      List of countries to compare
--adults, -a         Number of passengers (default: 1)
--use-vpn           Use real VPN (requires NordVPN CLI)
--save-csv          Save results to CSV file
--no-charts         Don't create charts
```

### Airport codes (IATA)

Major Polish airports:
- `POZ` - Poznań
- `WAW` - Warsaw
- `KRK` - Kraków
- `GDN` - Gdańsk
- `WRO` - Wrocław
- `KTW` - Katowice

Popular destinations:
- `AMS` - Amsterdam
- `LHR` - London Heathrow
- `BCN` - Barcelona
- `CDG` - Paris
- `FCO` - Rome
- `DXB` - Dubai

### Available countries (48 total)

**Europe (26):**
- `poland`, `germany`, `france`, `spain`, `italy`, `netherlands`, `belgium`
- `austria`, `switzerland`, `sweden`, `norway`, `denmark`, `finland`
- `portugal`, `greece`, `czech`, `hungary`, `romania`, `bulgaria`
- `croatia`, `slovakia`, `ireland`, `ukraine`, `albania`, `turkey`, `united_kingdom`

**Americas (5):**
- `usa`, `canada`, `mexico`, `brazil`, `argentina`

**Asia & Middle East (12):**
- `japan`, `south_korea`, `china`, `india`, `thailand`, `singapore`
- `malaysia`, `indonesia`, `vietnam`, `philippines`, `uae`, `israel`, `saudi_arabia`

**Oceania & Africa (5):**
- `australia`, `new_zealand`, `south_africa`, `egypt`, `morocco`

## 📊 Results & Chart Examples

### Example results from Top Deals Finder

Warsaw (WAW) → Barcelona (BCN), March 10, 2026:

```
🥇 SWEDEN      - 426.74 PLN (1,123.00 SEK)
🥈 CZECH       - 433.16 PLN (2,548.00 CZK)
🥉 SOUTH AFRICA - 439.12 PLN (1,996.00 ZAR)
4. POLAND      - 441.53 PLN
5. HUNGARY     - 449.90 PLN (40,900.00 HUF)

Maximum savings: 205.52 PLN (32.5%) compared to most expensive country
```

### Chart types

The application creates 4 types of charts:

1. **Cheapest price comparison** - bar chart showing the lowest price from each country
2. **Price distribution** - box plot showing distribution of all available flights
3. **Prices by airline** - comparison of different carriers
4. **Savings** - visualization of potential savings

Charts are saved in the `charts/` directory (or `charts/top_deals/` for top deals finder).

## 💻 Programmatic Usage

You can use the library directly in your Python code:

```python
from src.vpn_manager import VPNManager
from src.flight_search import FlightSearcher, MultiCountryFlightSearcher
from src.price_comparator import PriceComparator
from src.visualizer import FlightVisualizer

# Initialize
vpn_manager = VPNManager(use_nordvpn=False)
flight_searcher = FlightSearcher()
multi_searcher = MultiCountryFlightSearcher(vpn_manager, flight_searcher)

# Search flights
results = multi_searcher.search_from_countries(
    countries=['poland', 'turkey', 'albania'],
    origin='POZ',
    destination='AMS',
    departure_date='2026-03-15',
    adults=1
)

# Compare prices
comparator = PriceComparator()
for country, data in results.items():
    comparator.add_results(country, data)

# Display results
comparator.print_comparison()

# Create charts
visualizer = FlightVisualizer()
charts = visualizer.create_all_visualizations(comparator, "POZ → AMS")
```

See `example.py` for more examples.

## 🔧 VPN Integration

### NordVPN CLI (Linux/Mac)

1. Install NordVPN CLI:

**Ubuntu/Debian:**
```bash
sudo apt install nordvpn
```

**Mac:**
```bash
brew install nordvpn
```

2. Login:
```bash
nordvpn login
```

3. Run the application with `--use-vpn` flag:
```bash
python main.py --origin POZ --destination AMS --countries poland turkey --use-vpn
```

### Mode without VPN (Demo)

If you don't have VPN, the application works in demo mode using:
- Sample flight data
- Simulation of different prices in different currencies
- All visualization features

## 📁 Project Structure

```
flight-looker/
├── src/
│   ├── __init__.py
│   ├── vpn_manager.py          # VPN/proxy management (48 countries)
│   ├── flight_search.py        # Flight search via Amadeus API
│   ├── price_comparator.py     # Price comparison & conversion
│   ├── exchange_rates.py       # Live NBP API exchange rates
│   ├── visualizer.py           # Chart creation
│   └── airline_scrapers.py     # Direct airline scraping
├── charts/                     # Generated charts
│   ├── top_deals/             # Charts from top_deals.py
│   └── date_range/            # Charts from date_range_deals.py
├── main.py                     # Main application (custom countries)
├── top_deals.py               # Top deals finder (30 countries analysis)
├── date_range_deals.py        # Date range comparison (find best date)
├── example.py                  # Programmatic usage examples
├── requirements.txt            # Dependencies
├── .env.example               # Example configuration
└── README.md                  # This file
```

## 🔑 Amadeus API (optional)

For real flight data you can register at:
https://developers.amadeus.com

1. Create an account
2. Create an application (Self-Service)
3. Copy API Key and API Secret
4. Paste into `.env` file

**Note**: Amadeus offers a free tier with limitations.

## ⚠️ Important Information

1. **Legality**: Use VPN in accordance with the law and airline service terms
2. **Rate limiting**: Don't make too many requests in a short time
3. **Prices**: Prices are indicative and may differ from final prices
4. **Exchange rates**: ✅ Live rates from NBP API (Narodowy Bank Polski)
   - Automatically fetched and cached daily
   - NBP publishes rates once per day (around 11:45-12:00 CET)
   - Cache automatically refreshes when new rates are available
   - Fallback to static rates if NBP API is unavailable

## 🤝 Contributing

Pull requests are welcome! Areas for development:

- [ ] Support for more flight APIs
- [x] ✅ Automatic currency exchange rate updates (NBP API integration)
- [x] ✅ Date range comparison (find best date to fly)
- [ ] Support for return flights
- [ ] Price alerts
- [ ] Support for more VPN providers
- [ ] Web application
- [ ] Support for hotels and car rentals

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Flight Looker Team

## 🐛 Bug Reporting

If you find a bug or have a suggestion, open an issue on GitHub.

## 📚 Useful Links

- [Amadeus for Developers](https://developers.amadeus.com)
- [NordVPN](https://nordvpn.com)
- [IATA Airport Codes](https://www.iata.org/en/publications/directories/code-search/)
- [matplotlib Documentation](https://matplotlib.org)

---

**Happy flight hunting! ✈️**

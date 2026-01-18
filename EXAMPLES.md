# Flight Looker - Usage Examples

This file contains practical examples of using the Flight Looker tool.

## Quick Start

### 1. Top Deals Finder - Analyze 30 Countries

Find the cheapest countries to buy your flight from:

```bash
# Basic usage - searches 30 countries automatically
python top_deals.py --origin WAW --destination BCN --date 2026-03-15

# Save results to CSV
python top_deals.py --origin POZ --destination AMS --save-csv

# Show top 10 instead of top 5
python top_deals.py --origin KRK --destination LHR --top 10

# Specific departure date
python top_deals.py --origin GDN --destination CDG --date 2026-04-20
```

### 2. Custom Country Comparison

Compare specific countries you're interested in:

```bash
# Compare 3 countries
python main.py --origin POZ --destination AMS --countries poland germany turkey

# European comparison
python main.py --origin WAW --destination BCN --countries poland germany france spain italy

# Worldwide comparison
python main.py --origin KRK --destination DXB --countries poland usa uae india japan
```

## Real-World Scenarios

### Scenario 1: Planning European Vacation

Find cheapest way to book Barcelona from Warsaw:

```bash
python top_deals.py --origin WAW --destination BCN --date 2026-06-15 --save-csv
```

**Example output:**
```
🥇 SWEDEN      - 426.74 PLN
🥈 CZECH       - 433.16 PLN
🥉 SOUTH AFRICA - 439.12 PLN
```

### Scenario 2: Family Trip (Multiple Passengers)

Family of 4 going to London:

```bash
python top_deals.py --origin KRK --destination LHR --date 2026-07-01 --adults 4 --top 10
```

### Scenario 3: Compare Neighboring Countries

Check if buying from neighboring countries is cheaper:

```bash
python main.py --origin POZ --destination AMS --countries poland germany czech slovakia
```

### Scenario 4: Long-haul Flight Comparison

Compare prices for Dubai flight:

```bash
python top_deals.py --origin WAW --destination DXB --date 2026-12-20 --top 10
```

### Scenario 5: Budget Analysis

Find absolute cheapest options worldwide:

```bash
python top_deals.py --origin POZ --destination AMS --save-csv --top 10
# Then check the CSV file for detailed price breakdown
```

## Advanced Usage

### Custom Country Set

Analyze specific regions:

```bash
# Eastern Europe
python top_deals.py --origin WAW --destination BCN \
  --countries poland czech hungary slovakia romania bulgaria croatia

# Western Europe
python top_deals.py --origin POZ --destination LHR \
  --countries germany france netherlands belgium switzerland austria

# Scandinavia
python top_deals.py --origin GDN --destination AMS \
  --countries sweden norway denmark finland

# Asia
python top_deals.py --origin WAW --destination BKK \
  --countries india thailand singapore malaysia vietnam japan
```

### Programmatic Usage

Use the library in your own Python scripts:

```python
from src.vpn_manager import VPNManager
from src.flight_search import FlightSearcher, MultiCountryFlightSearcher
from src.price_comparator import PriceComparator

# Initialize
vpn = VPNManager(use_nordvpn=False)
searcher = FlightSearcher()
multi = MultiCountryFlightSearcher(vpn, searcher)

# Search
results = multi.search_from_countries(
    countries=['poland', 'germany', 'france'],
    origin='WAW',
    destination='BCN',
    departure_date='2026-03-15',
    adults=1
)

# Analyze
comparator = PriceComparator()
for country, data in results.items():
    comparator.add_results(country, data)

# Display results
comparator.print_comparison()

# Save to CSV
comparator.save_to_csv('my_comparison.csv')
```

## Popular Routes

### From Poland

```bash
# Poznań to Amsterdam
python top_deals.py --origin POZ --destination AMS

# Warsaw to Barcelona
python top_deals.py --origin WAW --destination BCN

# Kraków to London
python top_deals.py --origin KRK --destination LHR

# Gdańsk to Paris
python top_deals.py --origin GDN --destination CDG

# Wrocław to Rome
python top_deals.py --origin WRO --destination FCO
```

### From Major European Cities

```bash
# London to New York
python top_deals.py --origin LHR --destination JFK --top 10

# Paris to Tokyo
python top_deals.py --origin CDG --destination NRT --top 10

# Berlin to Dubai
python top_deals.py --origin TXL --destination DXB --top 10
```

## Tips & Tricks

### 1. Best Time to Search
- Search 2-3 months in advance for best prices
- Use `--date` parameter with flexible dates

### 2. Maximum Savings
- Use `top_deals.py` with default 30 countries for maximum coverage
- Check the statistics section for potential savings percentage

### 3. CSV Export for Analysis
Always save to CSV for deeper analysis:
```bash
python top_deals.py --origin WAW --destination BCN --save-csv
```

Then open in Excel/Google Sheets to:
- Sort by price
- Filter by airline
- Analyze by stops

### 4. Combining with VPN (Advanced)
If you have NordVPN CLI installed:
```bash
python main.py --origin POZ --destination AMS --countries poland germany --use-vpn
```

### 5. Skip Charts for Faster Results
If you only need CSV data:
```bash
python top_deals.py --origin WAW --destination BCN --save-csv --no-charts
```

## Common Airport Codes

### Poland
- POZ - Poznań
- WAW - Warsaw
- KRK - Kraków
- GDN - Gdańsk
- WRO - Wrocław
- KTW - Katowice

### Europe Popular
- AMS - Amsterdam
- LHR - London Heathrow
- BCN - Barcelona
- CDG - Paris Charles de Gaulle
- FCO - Rome Fiumicino
- MAD - Madrid
- VIE - Vienna
- PRG - Prague
- BUD - Budapest

### Worldwide Popular
- JFK - New York
- DXB - Dubai
- NRT - Tokyo Narita
- SIN - Singapore
- BKK - Bangkok
- SYD - Sydney

Full list: https://www.iata.org/en/publications/directories/code-search/

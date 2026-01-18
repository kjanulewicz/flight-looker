# Docker Usage Guide

This guide explains how to run Flight Looker in Docker with full NordVPN CLI support.

## Prerequisites

1. **Docker Desktop** installed on macOS
   ```bash
   brew install --cask docker
   ```

2. **NordVPN Account** (required for VPN features)

## Quick Start

### 1. Build the Docker Image

```bash
docker build -t flight-looker:latest .
```

Or use the helper script:
```bash
./docker-run.sh shell  # This will build automatically
```

### 2. Configure NordVPN Authentication

**Method 1: Access Token (Recommended - Most Secure)**

Generate a token at [Nord Account](https://my.nordaccount.com):
1. Login to Nord Account
2. Go to Services > NordVPN > Access tokens
3. Click "Generate new token"
4. Choose "Non-expiring token" (recommended for automation)
5. Copy the token

Add to `.env`:
```env
NORDVPN_TOKEN=your_generated_token_here
```

The application will automatically login when using `--use-vpn` flag.

**Method 2: Username/Password (Fallback)**

If you prefer username/password, add to `.env`:
```env
NORDVPN_USERNAME=your_nordvpn_email@example.com
NORDVPN_PASSWORD=your_nordvpn_password
```

Note: Token authentication is preferred as it's more secure and doesn't require storing your password.

**Method 3: Manual login (Interactive)**

```bash
./docker-run.sh login
```

Follow the prompts to authenticate with your NordVPN account. This session persists in the container.

### 3. Run the Application

**Using top_deals.py (30 countries analysis):**
```bash
./docker-run.sh top-deals --origin WAW --destination BCN --date 2026-03-15
```

**Using main.py with VPN:**
```bash
./docker-run.sh main --origin POZ --destination AMS --countries poland germany turkey --use-vpn
```

## Helper Script Commands

The `docker-run.sh` script provides convenient commands:

| Command | Description | Example |
|---------|-------------|---------|
| `login` | Login to NordVPN | `./docker-run.sh login` |
| `shell` | Interactive bash shell | `./docker-run.sh shell` |
| `top-deals` | Run top_deals.py | `./docker-run.sh top-deals --origin WAW --destination BCN` |
| `main` | Run main.py | `./docker-run.sh main --origin POZ --destination AMS --use-vpn` |

## Manual Docker Commands

If you prefer not to use the helper script:

**Build:**
```bash
docker build -t flight-looker:latest .
```

**Run with VPN:**
```bash
docker run -it --rm \
  --cap-add=NET_ADMIN \
  --device /dev/net/tun \
  -v "$(pwd)/.env:/app/.env:ro" \
  -v "$(pwd)/charts:/app/charts" \
  -v "$(pwd)/data:/app/data" \
  flight-looker:latest \
  python3 main.py --origin WAW --destination BCN --use-vpn
```

**Interactive shell:**
```bash
docker run -it --rm \
  --cap-add=NET_ADMIN \
  --device /dev/net/tun \
  -v "$(pwd)/.env:/app/.env:ro" \
  -v "$(pwd)/charts:/app/charts" \
  flight-looker:latest \
  /bin/bash
```

## Using Docker Compose

Start the container:
```bash
docker-compose up -d
```

Execute commands:
```bash
docker-compose exec flight-looker python3 top_deals.py --origin WAW --destination BCN
```

Stop the container:
```bash
docker-compose down
```

## Volumes Explained

The Docker setup mounts several directories:

- `.env` - Your API credentials (read-only)
- `charts/` - Generated charts are saved here
- `data/` - CSV exports are saved here
- `.exchange_rates_cache.json` - NBP exchange rate cache

All generated files will appear in your local directories automatically.

## NordVPN Inside Docker

The container includes NordVPN CLI with full functionality:

**Check VPN status:**
```bash
./docker-run.sh shell
# Inside container:
nordvpn status
```

**Connect to specific country:**
```bash
nordvpn connect Poland
```

**Disconnect:**
```bash
nordvpn disconnect
```

## Troubleshooting

### Permission Denied

Make sure the script is executable:
```bash
chmod +x docker-run.sh
```

### Docker Not Running

Start Docker Desktop application before running commands.

### VPN Connection Fails

1. Make sure you've logged in: `./docker-run.sh login`
2. Check NordVPN account is active
3. Try reconnecting: `nordvpn disconnect && nordvpn connect`

### Missing Charts/Data

Make sure the directories exist:
```bash
mkdir -p charts data
```

## Examples

### Find cheapest flights from 30 countries:
```bash
./docker-run.sh top-deals --origin WAW --destination LHR --date 2026-04-15 --top 10
```

### Compare specific countries with VPN:
```bash
./docker-run.sh main --origin POZ --destination BCN \
  --countries poland germany france spain italy \
  --use-vpn --save-csv
```

### Custom analysis with 2 passengers:
```bash
./docker-run.sh top-deals --origin KRK --destination AMS \
  --adults 2 --date 2026-05-20 --save-csv
```

## Notes

- The container runs Ubuntu 22.04 with Python 3
- All Python dependencies are pre-installed
- NordVPN CLI is fully configured
- Exchange rate cache is shared with host
- Generated files appear immediately in local directories

## Advanced: Building for Different Platforms

For ARM64 (Apple Silicon):
```bash
docker build --platform linux/arm64 -t flight-looker:latest .
```

For AMD64 (Intel):
```bash
docker build --platform linux/amd64 -t flight-looker:latest .
```

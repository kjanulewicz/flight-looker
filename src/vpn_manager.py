"""
VPN and proxy management module for different countries
"""
import subprocess
import time
import requests
import os
from typing import Optional, Dict, List
import logging
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyFetcher:
    """Fetches free proxies from various sources"""

    PROXY_SOURCES = [
        # Free proxy APIs
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country={country}&ssl=yes",
        "https://www.proxy-list.download/api/v1/get?type=http&country={country}",
    ]

    # Backup proxies (free public proxies - may be slow/unreliable)
    BACKUP_PROXIES = {
        'PL': ['91.202.230.104:8080', '185.238.228.243:8080'],
        'DE': ['138.201.198.164:8080', '5.161.105.105:80'],
        'GB': ['178.62.103.98:8080', '167.71.142.195:8080'],
        'FR': ['91.121.208.136:8080', '163.172.182.165:8080'],
        'US': ['155.94.241.133:1994', '38.154.227.167:5868'],
        'TR': ['31.28.8.74:1923', '185.15.172.212:3128'],
        'NL': ['185.217.137.216:1337', '45.140.143.77:8080'],
        'ES': ['161.49.215.28:8080', '45.167.253.225:999'],
        'IT': ['146.196.110.136:55443', '93.188.161.148:80'],
        'JP': ['43.134.68.153:3128', '43.153.207.93:3128'],
        'IN': ['103.159.96.141:8080', '103.169.130.42:8080'],
        'AU': ['103.152.112.162:80', '43.154.134.238:50001'],
    }

    @classmethod
    def get_proxies_for_country(cls, country_code: str, limit: int = 5) -> List[str]:
        """
        Fetches working proxies for a specific country

        Args:
            country_code: ISO country code (e.g., 'PL', 'US')
            limit: Maximum number of proxies to return

        Returns:
            List of proxy addresses in format 'ip:port'
        """
        proxies = []

        # Try to fetch from APIs
        for source in cls.PROXY_SOURCES:
            try:
                url = source.format(country=country_code)
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    text = response.text.strip()
                    if text:
                        new_proxies = [p.strip() for p in text.split('\n') if p.strip()]
                        proxies.extend(new_proxies[:limit])
                        if len(proxies) >= limit:
                            break
            except Exception as e:
                logger.debug(f"Failed to fetch from {source}: {e}")
                continue

        # Use backup proxies if none found
        if not proxies:
            proxies = cls.BACKUP_PROXIES.get(country_code, [])

        return proxies[:limit]

    @classmethod
    def test_proxy(cls, proxy: str, timeout: int = 5) -> bool:
        """Tests if a proxy is working"""
        try:
            proxies = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(
                'https://httpbin.org/ip',
                proxies=proxies,
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False


class VPNManager:
    """Manages VPN connections to different countries"""

    COUNTRY_CODES = {
        # Europe
        'poland': 'PL',
        'germany': 'DE',
        'united_kingdom': 'GB',
        'france': 'FR',
        'spain': 'ES',
        'italy': 'IT',
        'netherlands': 'NL',
        'belgium': 'BE',
        'austria': 'AT',
        'switzerland': 'CH',
        'sweden': 'SE',
        'norway': 'NO',
        'denmark': 'DK',
        'finland': 'FI',
        'portugal': 'PT',
        'greece': 'GR',
        'czech': 'CZ',
        'hungary': 'HU',
        'romania': 'RO',
        'bulgaria': 'BG',
        'croatia': 'HR',
        'slovakia': 'SK',
        'ireland': 'IE',
        'ukraine': 'UA',
        'albania': 'AL',
        'turkey': 'TR',
        # Americas
        'usa': 'US',
        'canada': 'CA',
        'mexico': 'MX',
        'brazil': 'BR',
        'argentina': 'AR',
        # Asia & Middle East
        'japan': 'JP',
        'south_korea': 'KR',
        'china': 'CN',
        'india': 'IN',
        'thailand': 'TH',
        'singapore': 'SG',
        'malaysia': 'MY',
        'indonesia': 'ID',
        'vietnam': 'VN',
        'philippines': 'PH',
        'uae': 'AE',
        'israel': 'IL',
        'saudi_arabia': 'SA',
        # Oceania & Africa
        'australia': 'AU',
        'new_zealand': 'NZ',
        'south_africa': 'ZA',
        'egypt': 'EG',
        'morocco': 'MA'
    }

    def __init__(self, use_nordvpn: bool = True, use_proxy: bool = False):
        self.use_nordvpn = use_nordvpn
        self.use_proxy = use_proxy or not use_nordvpn
        self.current_country = None
        self.current_proxy = None
        self.proxy_cache: Dict[str, List[str]] = {}
        self.is_logged_in = False

        # Get NordVPN credentials from environment (token preferred, fallback to username/password)
        self.nordvpn_token = os.getenv('NORDVPN_TOKEN')
        self.nordvpn_username = os.getenv('NORDVPN_USERNAME')
        self.nordvpn_password = os.getenv('NORDVPN_PASSWORD')

        # Auto-login if credentials are provided and using NordVPN
        if self.use_nordvpn:
            has_token = self.nordvpn_token and self.nordvpn_token != 'your_nordvpn_token_here'
            has_credentials = self.nordvpn_username and self.nordvpn_password and \
                            self.nordvpn_username != 'your_nordvpn_email@example.com'

            if (has_token or has_credentials) and not self._is_nordvpn_logged_in():
                self._login_nordvpn()

    def connect_to_country(self, country: str) -> bool:
        """
        Connects to VPN/proxy in the selected country

        Args:
            country: Country name (e.g. 'poland', 'turkey')

        Returns:
            bool: True if connection succeeded
        """
        country_code = self.COUNTRY_CODES.get(country.lower())
        if not country_code:
            logger.error(f"Unknown country: {country}")
            return False

        if self.use_nordvpn:
            return self._connect_nordvpn(country_code)
        else:
            return self._connect_proxy(country_code)

    def _connect_nordvpn(self, country_code: str) -> bool:
        """Connects via NordVPN CLI (supports Windows and Linux)"""
        import platform

        if platform.system() == 'Windows':
            return self._connect_nordvpn_windows(country_code)
        else:
            return self._connect_nordvpn_linux(country_code)

    def _connect_nordvpn_windows(self, country_code: str) -> bool:
        """Connects via NordVPN on Windows"""
        # NordVPN Windows paths
        nordvpn_paths = [
            r"C:\Program Files\NordVPN\nordvpn.exe",
            r"C:\Program Files (x86)\NordVPN\nordvpn.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\NordVPN\nordvpn.exe"),
        ]

        nordvpn_exe = None
        for path in nordvpn_paths:
            if os.path.exists(path):
                nordvpn_exe = path
                break

        if not nordvpn_exe:
            logger.warning("NordVPN not found on Windows, falling back to proxy mode")
            self.use_nordvpn = False
            return self._connect_proxy(country_code)

        try:
            # Disconnect current connection
            subprocess.run([nordvpn_exe, '-d'],
                         capture_output=True, timeout=10, shell=True)
            time.sleep(2)

            # Connect to selected country
            result = subprocess.run(
                [nordvpn_exe, '-c', '-g', country_code],
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )

            # NordVPN Windows doesn't always return proper exit codes
            time.sleep(5)  # Wait for connection

            # Verify connection by checking IP
            location = self.get_current_location(use_proxy=False)
            if location and location.get('countryCode') == country_code:
                logger.info(f"Connected to VPN: {country_code} ({location.get('country')})")
                self.current_country = country_code
                return True
            else:
                logger.warning(f"VPN connection may have failed for {country_code}")
                self.current_country = country_code
                return True  # Continue anyway

        except subprocess.TimeoutExpired:
            logger.error("Timeout while connecting to VPN")
            return False
        except Exception as e:
            logger.error(f"VPN connection error: {e}")
            self.use_nordvpn = False
            return self._connect_proxy(country_code)

    def _is_nordvpn_logged_in(self) -> bool:
        """Check if NordVPN is already logged in"""
        try:
            result = subprocess.run(
                ['nordvpn', 'account'],
                capture_output=True,
                text=True,
                timeout=10
            )
            # If account command succeeds, user is logged in
            return result.returncode == 0 and 'logged in' not in result.stdout.lower() or 'Email' in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _login_nordvpn(self) -> bool:
        """
        Login to NordVPN using token (preferred) or username/password from .env

        Token-based authentication is more secure and recommended for automation.
        Generate token at: https://my.nordaccount.com
        """
        # Method 1: Token-based login (preferred)
        if self.nordvpn_token and self.nordvpn_token != 'your_nordvpn_token_here':
            try:
                logger.info("Logging in to NordVPN using access token...")
                # Auto-respond to privacy policy question with 'n' (essential data only)
                result = subprocess.run(
                    f"echo 'n' | nordvpn login --token {self.nordvpn_token}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 or 'logged in' in result.stdout.lower() or 'Welcome' in result.stdout:
                    logger.info("Successfully logged in to NordVPN via token")
                    self.is_logged_in = True
                    return True
                else:
                    logger.warning(f"Token login failed: {result.stderr}")
                    # Fall through to try username/password

            except subprocess.TimeoutExpired:
                logger.error("Timeout while logging in with token")
                return False
            except Exception as e:
                logger.warning(f"Token login error: {e}, trying username/password...")

        # Method 2: Username/Password login (fallback)
        if self.nordvpn_username and self.nordvpn_password and \
           self.nordvpn_username != 'your_nordvpn_email@example.com':
            try:
                logger.info("Logging in to NordVPN using username/password...")
                # Auto-respond to privacy policy question with 'n' (essential data only)
                result = subprocess.run(
                    f"echo 'n' | nordvpn login --username {self.nordvpn_username} --password {self.nordvpn_password}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0 or 'logged in' in result.stdout.lower():
                    logger.info("Successfully logged in to NordVPN via username/password")
                    self.is_logged_in = True
                    return True
                else:
                    logger.error(f"NordVPN login failed: {result.stderr}")
                    return False

            except subprocess.TimeoutExpired:
                logger.error("Timeout while logging in to NordVPN")
                return False
            except Exception as e:
                logger.error(f"NordVPN login error: {e}")
                return False

        # No valid credentials found
        logger.warning("No valid NordVPN credentials found in .env file")
        logger.info("Please set NORDVPN_TOKEN (recommended) or NORDVPN_USERNAME + NORDVPN_PASSWORD")
        return False

    def _connect_nordvpn_linux(self, country_code: str) -> bool:
        """Connects via NordVPN CLI on Linux"""
        try:
            # Ensure we're logged in
            if not self.is_logged_in and not self._is_nordvpn_logged_in():
                if not self._login_nordvpn():
                    logger.warning("Not logged in to NordVPN, falling back to proxy mode")
                    self.use_nordvpn = False
                    return self._connect_proxy(country_code)

            # Disconnect current connection
            subprocess.run(['nordvpn', 'disconnect'],
                         capture_output=True, timeout=10)
            time.sleep(2)

            # Connect to selected country
            result = subprocess.run(
                ['nordvpn', 'connect', country_code],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Connected to VPN: {country_code}")
                self.current_country = country_code
                time.sleep(3)  # Wait for connection to stabilize
                return True
            else:
                logger.error(f"VPN connection error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Timeout while connecting to VPN")
            return False
        except FileNotFoundError:
            logger.warning("NordVPN CLI not found, falling back to proxy mode")
            self.use_nordvpn = False
            return self._connect_proxy(country_code)

    def _connect_proxy(self, country_code: str) -> bool:
        """Connects via free proxy"""
        logger.info(f"Finding proxy for country: {country_code}")

        # Check cache first
        if country_code not in self.proxy_cache:
            self.proxy_cache[country_code] = ProxyFetcher.get_proxies_for_country(country_code)

        proxies = self.proxy_cache.get(country_code, [])

        if proxies:
            # Try to find a working proxy
            for proxy in proxies:
                logger.debug(f"Testing proxy: {proxy}")
                if ProxyFetcher.test_proxy(proxy):
                    self.current_proxy = proxy
                    self.current_country = country_code
                    logger.info(f"Connected via proxy: {proxy} ({country_code})")
                    return True

            # If no proxy works, use first one anyway (API doesn't need real geo-location)
            self.current_proxy = proxies[0]
            self.current_country = country_code
            logger.warning(f"Using untested proxy: {proxies[0]} ({country_code})")
            return True
        else:
            # No proxy available - continue without proxy (API will still work with currency)
            logger.warning(f"No proxy available for {country_code}, continuing without proxy")
            self.current_country = country_code
            self.current_proxy = None
            return True

    def get_current_proxy(self) -> Optional[Dict[str, str]]:
        """Returns current proxy configuration for requests"""
        if self.current_proxy:
            return {
                'http': f'http://{self.current_proxy}',
                'https': f'http://{self.current_proxy}'
            }
        return None

    def disconnect(self):
        """Disconnects VPN/proxy"""
        if self.use_nordvpn:
            try:
                subprocess.run(['nordvpn', 'disconnect'],
                             capture_output=True, timeout=10)
                logger.info("Disconnected VPN")
            except Exception as e:
                logger.debug(f"VPN disconnect: {e}")

        self.current_country = None
        self.current_proxy = None

    def get_current_ip(self, use_proxy: bool = True) -> Optional[str]:
        """Gets current public IP address"""
        try:
            proxies = self.get_current_proxy() if use_proxy else None
            response = requests.get('https://api.ipify.org?format=json',
                                   proxies=proxies, timeout=10)
            return response.json()['ip']
        except Exception as e:
            logger.debug(f"Cannot get IP: {e}")
            return None

    def get_current_location(self, use_proxy: bool = True) -> Optional[Dict]:
        """Gets current location based on IP"""
        try:
            ip = self.get_current_ip(use_proxy)
            if ip:
                response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
                data = response.json()
                logger.info(f"Current location: {data.get('country')}, {data.get('city')}")
                return data
        except Exception as e:
            logger.debug(f"Cannot get location: {e}")
        return None

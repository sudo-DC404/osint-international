#!/usr/bin/env python3
"""
International OSINT Tool - Phone Numbers & People Search
For non-US focused OSINT operations
"""

import sqlite3
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote, urlparse
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
import whois
import dns.resolver
import dns.reversename
import hashlib
import base64

# Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Database
DB_PATH = Path.home() / '.osint_international.db'
RESULTS_DIR = Path.home() / 'osint_results'
RESULTS_DIR.mkdir(exist_ok=True)

class OSINTDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Phone number lookups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS phone_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                country TEXT,
                carrier TEXT,
                line_type TEXT,
                location TEXT,
                timezone TEXT,
                valid BOOLEAN,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # People/username searches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                platform TEXT,
                url TEXT,
                found BOOLEAN,
                additional_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Search sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_type TEXT,
                query TEXT,
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Domain lookups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domain_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                registrar TEXT,
                creation_date TEXT,
                expiration_date TEXT,
                name_servers TEXT,
                dns_records TEXT,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Breach data searches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS breach_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                breaches_found INTEGER,
                breach_names TEXT,
                paste_count INTEGER,
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Image searches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                image_hash TEXT,
                search_engine TEXT,
                results_found BOOLEAN,
                results_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Dark web searches
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS darkweb_searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                search_engine TEXT,
                results_count INTEGER,
                results_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def save_phone_lookup(self, data: Dict):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO phone_lookups
            (phone_number, country, carrier, line_type, location, timezone, valid, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('phone_number'),
            data.get('country'),
            data.get('carrier'),
            data.get('line_type'),
            data.get('location'),
            data.get('timezone'),
            data.get('valid'),
            json.dumps(data.get('raw_data', {}))
        ))
        self.conn.commit()
        return cursor.lastrowid

    def save_username_search(self, username: str, platform: str, url: str, found: bool, info: str = ""):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO people_searches
            (username, platform, url, found, additional_info)
            VALUES (?, ?, ?, ?, ?)
        """, (username, platform, url, found, info))
        self.conn.commit()

    def get_recent_searches(self, limit: int = 10):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM search_sessions
            ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

class PhoneOSINT:
    """International phone number OSINT"""

    def __init__(self, db: OSINTDatabase):
        self.db = db

    def lookup_phone(self, phone_number: str, default_country: str = None) -> Dict:
        """
        Lookup phone number information
        Supports international format (+country_code)
        """
        print(f"\n{Colors.CYAN}[*] Analyzing phone number: {phone_number}{Colors.END}")

        results = {
            'phone_number': phone_number,
            'valid': False,
            'country': None,
            'carrier': None,
            'line_type': None,
            'location': None,
            'timezone': None,
            'raw_data': {}
        }

        try:
            # Parse phone number
            if default_country:
                parsed = phonenumbers.parse(phone_number, default_country)
            else:
                parsed = phonenumbers.parse(phone_number, None)

            # Validate
            is_valid = phonenumbers.is_valid_number(parsed)
            results['valid'] = is_valid

            if is_valid:
                # Get country
                country = geocoder.description_for_number(parsed, "en")
                results['country'] = country

                # Get carrier
                carrier_name = carrier.name_for_number(parsed, "en")
                results['carrier'] = carrier_name

                # Get line type
                number_type = phonenumbers.number_type(parsed)
                type_map = {
                    0: 'Fixed Line',
                    1: 'Mobile',
                    2: 'Fixed Line or Mobile',
                    3: 'Toll Free',
                    4: 'Premium Rate',
                    5: 'Shared Cost',
                    6: 'VoIP',
                    7: 'Personal Number',
                    8: 'Pager',
                    9: 'UAN',
                    10: 'Voicemail',
                    99: 'Unknown'
                }
                results['line_type'] = type_map.get(number_type, 'Unknown')

                # Get location
                results['location'] = geocoder.description_for_number(parsed, "en")

                # Get timezone
                timezones = timezone.time_zones_for_number(parsed)
                results['timezone'] = ', '.join(timezones) if timezones else 'Unknown'

                # Format international and national
                international_format = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                national_format = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.NATIONAL
                )

                results['raw_data'] = {
                    'international_format': international_format,
                    'national_format': national_format,
                    'country_code': parsed.country_code,
                    'national_number': parsed.national_number
                }

                print(f"{Colors.GREEN}[+] Valid number!{Colors.END}")
                print(f"{Colors.BLUE}Country:{Colors.END} {country}")
                print(f"{Colors.BLUE}Carrier:{Colors.END} {carrier_name or 'Unknown'}")
                print(f"{Colors.BLUE}Line Type:{Colors.END} {results['line_type']}")
                print(f"{Colors.BLUE}Location:{Colors.END} {results['location']}")
                print(f"{Colors.BLUE}Timezone:{Colors.END} {results['timezone']}")
                print(f"{Colors.BLUE}International Format:{Colors.END} {international_format}")
                print(f"{Colors.BLUE}National Format:{Colors.END} {national_format}")

            else:
                print(f"{Colors.RED}[-] Invalid phone number{Colors.END}")

        except phonenumbers.NumberParseException as e:
            print(f"{Colors.RED}[-] Error parsing number: {e}{Colors.END}")
            results['raw_data']['error'] = str(e)

        # Save to database
        self.db.save_phone_lookup(results)

        return results

    def batch_lookup(self, phone_numbers: List[str], country: str = None):
        """Lookup multiple phone numbers"""
        results = []
        for phone in phone_numbers:
            result = self.lookup_phone(phone.strip(), country)
            results.append(result)
        return results

class PeopleOSINT:
    """International people/username search"""

    # International platforms (non-US focused)
    PLATFORMS = {
        'VK': 'https://vk.com/{}',
        'OK': 'https://ok.ru/{}',
        'Telegram': 'https://t.me/{}',
        'WeChat': None,  # No direct URL
        'Line': None,  # No direct URL
        'Weibo': 'https://weibo.com/{}',
        'Douyin': None,  # TikTok China
        'QQ': None,  # Requires app
        'Baidu': 'https://tieba.baidu.com/home/main?un={}',
        'Yandex': None,  # Search engine
        'Mail.ru': None,  # Email service
        'Viber': None,  # App only
        'WhatsApp': None,  # App only
        'Skype': 'https://web.skype.com/{}',
        '500px': 'https://500px.com/p/{}',
        'AboutMe': 'https://about.me/{}',
        'DeviantArt': 'https://www.deviantart.com/{}',
        'Flickr': 'https://www.flickr.com/people/{}',
        'GitHub': 'https://github.com/{}',
        'GitLab': 'https://gitlab.com/{}',
        'Instagram': 'https://www.instagram.com/{}',
        'LinkedIn': 'https://www.linkedin.com/in/{}',
        'Medium': 'https://medium.com/@{}',
        'Pinterest': 'https://www.pinterest.com/{}',
        'Reddit': 'https://www.reddit.com/user/{}',
        'Snapchat': 'https://www.snapchat.com/add/{}',
        'SoundCloud': 'https://soundcloud.com/{}',
        'Spotify': 'https://open.spotify.com/user/{}',
        'Steam': 'https://steamcommunity.com/id/{}',
        'Telegram': 'https://t.me/{}',
        'TikTok': 'https://www.tiktok.com/@{}',
        'Twitch': 'https://www.twitch.tv/{}',
        'Twitter': 'https://twitter.com/{}',
        'Vimeo': 'https://vimeo.com/{}',
        'YouTube': 'https://www.youtube.com/@{}',
        'Behance': 'https://www.behance.net/{}',
        'Dribbble': 'https://dribbble.com/{}',
        'Tumblr': 'https://{}.tumblr.com',
        'WordPress': 'https://{}.wordpress.com',
    }

    def __init__(self, db: OSINTDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_username(self, username: str, platform: str, url_template: str) -> Dict:
        """Check if username exists on platform"""
        if not url_template:
            return {'platform': platform, 'found': False, 'url': None, 'reason': 'No URL check available'}

        # Sanitize username for URL safety
        safe_username = quote(username, safe='')
        url = url_template.format(safe_username)

        try:
            response = self.session.get(url, timeout=5, allow_redirects=True)

            # Platform-specific detection
            found = False
            reason = ""

            if response.status_code == 200:
                # Additional checks for false positives
                text_lower = response.text.lower()

                # Common "not found" indicators
                not_found_indicators = [
                    'page not found',
                    'user not found',
                    'profile not found',
                    'account not found',
                    'doesn\'t exist',
                    'not available',
                    'sorry, this page isn\'t available',
                    'the page you requested was not found'
                ]

                if any(indicator in text_lower for indicator in not_found_indicators):
                    found = False
                    reason = "Profile page indicates user not found"
                else:
                    found = True
                    reason = f"HTTP {response.status_code} - Likely exists"

            elif response.status_code == 404:
                found = False
                reason = "HTTP 404 - Not found"

            else:
                found = False
                reason = f"HTTP {response.status_code}"

            return {
                'platform': platform,
                'found': found,
                'url': url,
                'status_code': response.status_code,
                'reason': reason
            }

        except requests.RequestException as e:
            return {
                'platform': platform,
                'found': False,
                'url': url,
                'reason': f"Error: {str(e)}"
            }

    def search_username(self, username: str, platforms: List[str] = None):
        """Search for username across multiple platforms"""
        print(f"\n{Colors.CYAN}[*] Searching for username: {username}{Colors.END}\n")

        if platforms is None:
            platforms = list(self.PLATFORMS.keys())

        results = []
        found_count = 0

        for platform in platforms:
            if platform not in self.PLATFORMS:
                continue

            url_template = self.PLATFORMS[platform]

            if url_template is None:
                print(f"{Colors.YELLOW}[-] {platform}: No URL check available{Colors.END}")
                continue

            print(f"{Colors.BLUE}[*] Checking {platform}...{Colors.END}", end=' ')

            result = self.check_username(username, platform, url_template)
            results.append(result)

            if result['found']:
                print(f"{Colors.GREEN}FOUND!{Colors.END}")
                print(f"    {Colors.CYAN}{result['url']}{Colors.END}")
                found_count += 1
                self.db.save_username_search(username, platform, result['url'], True, result['reason'])
            else:
                print(f"{Colors.RED}Not found{Colors.END}")
                self.db.save_username_search(username, platform, result.get('url', ''), False, result['reason'])

        print(f"\n{Colors.GREEN}[+] Found on {found_count}/{len(results)} platforms{Colors.END}")
        return results

    def search_email(self, email: str):
        """Search for email across various services"""
        print(f"\n{Colors.CYAN}[*] Searching for email: {email}{Colors.END}")
        print(f"{Colors.YELLOW}[!] Email search requires external tools{Colors.END}")
        print(f"{Colors.BLUE}Suggested tools:{Colors.END}")
        print(f"  - holehe (https://github.com/megadose/holehe)")
        print(f"  - h8mail (https://github.com/khast3x/h8mail)")
        print(f"  - GHunt (for Gmail)")

class DomainOSINT:
    """Domain OSINT - WHOIS and DNS lookups"""

    def __init__(self, db: OSINTDatabase):
        self.db = db

    def lookup_domain(self, domain: str) -> Dict:
        """Perform WHOIS and DNS lookup on domain"""
        print(f"\n{Colors.CYAN}[*] Analyzing domain: {domain}{Colors.END}\n")

        results = {
            'domain': domain,
            'whois_data': {},
            'dns_records': {},
            'success': False
        }

        # WHOIS Lookup
        try:
            print(f"{Colors.BLUE}[*] Performing WHOIS lookup...{Colors.END}")
            w = whois.query(domain)

            whois_data = {
                'registrar': w.registrar if hasattr(w, 'registrar') else None,
                'creation_date': str(w.creation_date) if hasattr(w, 'creation_date') else None,
                'expiration_date': str(w.expiration_date) if hasattr(w, 'expiration_date') else None,
                'updated_date': str(w.updated_date) if hasattr(w, 'updated_date') else None,
                'name_servers': w.name_servers if hasattr(w, 'name_servers') else None,
                'status': w.status if hasattr(w, 'status') else None,
                'emails': w.emails if hasattr(w, 'emails') else None,
                'org': w.org if hasattr(w, 'org') else None,
                'country': w.country if hasattr(w, 'country') else None,
            }

            results['whois_data'] = whois_data
            results['success'] = True

            print(f"{Colors.GREEN}[+] WHOIS data retrieved{Colors.END}")
            if whois_data.get('registrar'):
                print(f"  {Colors.BLUE}Registrar:{Colors.END} {whois_data['registrar']}")
            if whois_data.get('creation_date'):
                print(f"  {Colors.BLUE}Created:{Colors.END} {whois_data['creation_date']}")
            if whois_data.get('expiration_date'):
                print(f"  {Colors.BLUE}Expires:{Colors.END} {whois_data['expiration_date']}")
            if whois_data.get('org'):
                print(f"  {Colors.BLUE}Organization:{Colors.END} {whois_data['org']}")

        except Exception as e:
            print(f"{Colors.RED}[-] WHOIS lookup failed: {e}{Colors.END}")
            results['whois_data']['error'] = str(e)

        # DNS Lookup
        try:
            print(f"\n{Colors.BLUE}[*] Performing DNS lookups...{Colors.END}")
            dns_data = {}

            # A Records
            try:
                answers = dns.resolver.resolve(domain, 'A')
                dns_data['A'] = [str(rdata) for rdata in answers]
                print(f"  {Colors.GREEN}A Records:{Colors.END} {', '.join(dns_data['A'])}")
            except:
                dns_data['A'] = []

            # AAAA Records (IPv6)
            try:
                answers = dns.resolver.resolve(domain, 'AAAA')
                dns_data['AAAA'] = [str(rdata) for rdata in answers]
                print(f"  {Colors.GREEN}AAAA Records:{Colors.END} {', '.join(dns_data['AAAA'])}")
            except:
                dns_data['AAAA'] = []

            # MX Records
            try:
                answers = dns.resolver.resolve(domain, 'MX')
                dns_data['MX'] = [str(rdata.exchange) for rdata in answers]
                print(f"  {Colors.GREEN}MX Records:{Colors.END} {', '.join(dns_data['MX'])}")
            except:
                dns_data['MX'] = []

            # NS Records
            try:
                answers = dns.resolver.resolve(domain, 'NS')
                dns_data['NS'] = [str(rdata) for rdata in answers]
                print(f"  {Colors.GREEN}NS Records:{Colors.END} {', '.join(dns_data['NS'])}")
            except:
                dns_data['NS'] = []

            # TXT Records
            try:
                answers = dns.resolver.resolve(domain, 'TXT')
                dns_data['TXT'] = [str(rdata) for rdata in answers]
                print(f"  {Colors.GREEN}TXT Records:{Colors.END} Found {len(dns_data['TXT'])} records")
            except:
                dns_data['TXT'] = []

            results['dns_records'] = dns_data

        except Exception as e:
            print(f"{Colors.RED}[-] DNS lookup failed: {e}{Colors.END}")
            results['dns_records']['error'] = str(e)

        # Save to database
        self.save_to_db(results)

        return results

    def save_to_db(self, data: Dict):
        """Save domain lookup to database"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO domain_lookups
            (domain, registrar, creation_date, expiration_date, name_servers, dns_records, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['domain'],
            data['whois_data'].get('registrar'),
            data['whois_data'].get('creation_date'),
            data['whois_data'].get('expiration_date'),
            json.dumps(data['whois_data'].get('name_servers')),
            json.dumps(data['dns_records']),
            json.dumps(data)
        ))
        self.db.conn.commit()

class BreachDataOSINT:
    """Breach data checking using HaveIBeenPwned API"""

    HIBP_API_BASE = "https://haveibeenpwned.com/api/v3"

    def __init__(self, db: OSINTDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OSINT-International-Tool'
        })

    def check_breaches(self, email: str, api_key: str = None) -> Dict:
        """Check if email appears in data breaches"""
        print(f"\n{Colors.CYAN}[*] Checking breaches for: {email}{Colors.END}\n")

        results = {
            'email': email,
            'breaches': [],
            'breach_count': 0,
            'paste_count': 0,
            'found': False
        }

        if not api_key:
            print(f"{Colors.YELLOW}[!] No API key provided{Colors.END}")
            print(f"{Colors.BLUE}HaveIBeenPwned requires an API key for automated checks{Colors.END}")
            print(f"{Colors.BLUE}Get one at:{Colors.END} https://haveibeenpwned.com/API/Key")
            print(f"\n{Colors.YELLOW}Alternative: Check manually at:{Colors.END}")
            print(f"  https://haveibeenpwned.com/")
            print(f"\n{Colors.BLUE}Other breach checkers:{Colors.END}")
            print(f"  - DeHashed: https://dehashed.com/")
            print(f"  - LeakCheck: https://leakcheck.io/")
            print(f"  - IntelX: https://intelx.io/")
            return results

        # Check breaches with API
        try:
            url = f"{self.HIBP_API_BASE}/breachedaccount/{quote(email)}"
            headers = {'hibp-api-key': api_key}

            response = self.session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                breaches = response.json()
                results['breaches'] = breaches
                results['breach_count'] = len(breaches)
                results['found'] = True

                print(f"{Colors.RED}[!] Email found in {len(breaches)} breaches!{Colors.END}\n")
                for breach in breaches[:10]:  # Show first 10
                    print(f"  {Colors.YELLOW}•{Colors.END} {breach['Name']}")
                    print(f"    Date: {breach.get('BreachDate', 'Unknown')}")
                    print(f"    Data: {', '.join(breach.get('DataClasses', []))}")
                    print()

                if len(breaches) > 10:
                    print(f"  {Colors.CYAN}... and {len(breaches) - 10} more{Colors.END}\n")

            elif response.status_code == 404:
                print(f"{Colors.GREEN}[+] Email not found in any breaches{Colors.END}")
                results['found'] = False
            else:
                print(f"{Colors.RED}[-] API returned status {response.status_code}{Colors.END}")

        except Exception as e:
            print(f"{Colors.RED}[-] Error checking breaches: {e}{Colors.END}")

        # Save to database
        self.save_to_db(results)

        return results

    def save_to_db(self, data: Dict):
        """Save breach check to database"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO breach_searches
            (email, breaches_found, breach_names, paste_count, raw_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['email'],
            data['breach_count'],
            json.dumps([b.get('Name') for b in data['breaches']]),
            data['paste_count'],
            json.dumps(data)
        ))
        self.db.conn.commit()

class ReverseImageOSINT:
    """Reverse image search"""

    def __init__(self, db: OSINTDatabase):
        self.db = db

    def calculate_image_hash(self, image_path: str) -> str:
        """Calculate hash of image file"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return f"Error: {e}"

    def search_image(self, image_path: str) -> Dict:
        """Perform reverse image search"""
        print(f"\n{Colors.CYAN}[*] Reverse image search for: {image_path}{Colors.END}\n")

        results = {
            'image_path': image_path,
            'image_hash': self.calculate_image_hash(image_path),
            'searches': {}
        }

        # Manual search URLs
        print(f"{Colors.YELLOW}[!] Automated reverse image search requires API keys{Colors.END}\n")
        print(f"{Colors.BLUE}Manual search options:{Colors.END}\n")

        search_engines = {
            'Google Images': f'https://www.google.com/searchbyimage (Upload: {image_path})',
            'Yandex Images': f'https://yandex.com/images/ (Upload: {image_path})',
            'TinEye': f'https://tineye.com/ (Upload: {image_path})',
            'Bing Visual Search': f'https://www.bing.com/visualsearch (Upload: {image_path})',
            'PimEyes (Faces)': f'https://pimeyes.com/ (Upload: {image_path})',
        }

        for engine, url in search_engines.items():
            print(f"  {Colors.GREEN}•{Colors.END} {Colors.BOLD}{engine}{Colors.END}")
            print(f"    {url}\n")

        print(f"\n{Colors.BLUE}Automated tools:{Colors.END}")
        print(f"  - search-that-hash (CLI)")
        print(f"  - GHunt (for Google profile pics)")
        print(f"  - Social Mapper (social media)")

        print(f"\n{Colors.CYAN}Image hash:{Colors.END} {results['image_hash']}")

        # Save to database
        self.save_to_db(results)

        return results

    def save_to_db(self, data: Dict):
        """Save image search to database"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO image_searches
            (image_path, image_hash, search_engine, results_found, results_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['image_path'],
            data['image_hash'],
            'Manual',
            False,
            json.dumps(data)
        ))
        self.db.conn.commit()

class DarkWebOSINT:
    """Dark web search using Ahmia and other Tor search engines"""

    def __init__(self, db: OSINTDatabase):
        self.db = db

    def search_ahmia(self, query: str) -> Dict:
        """Search Ahmia.fi (clearnet Tor search engine)"""
        print(f"\n{Colors.CYAN}[*] Searching dark web for: {query}{Colors.END}\n")

        results = {
            'query': query,
            'search_engine': 'ahmia',
            'results': [],
            'count': 0
        }

        try:
            print(f"{Colors.BLUE}[*] Searching Ahmia.fi...{Colors.END}")

            url = f"https://ahmia.fi/search/?q={quote(query)}"
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                # Simple parsing - look for .onion links
                onion_pattern = r'http[s]?://[a-z2-7]{16,56}\.onion[^\s<>"]*'
                found_onions = list(set(re.findall(onion_pattern, response.text)))

                results['results'] = found_onions
                results['count'] = len(found_onions)

                print(f"{Colors.GREEN}[+] Found {len(found_onions)} .onion results{Colors.END}\n")

                for i, onion in enumerate(found_onions[:10], 1):
                    print(f"  {i}. {onion}")

                if len(found_onions) > 10:
                    print(f"\n  {Colors.CYAN}... and {len(found_onions) - 10} more{Colors.END}")

            else:
                print(f"{Colors.RED}[-] Search returned status {response.status_code}{Colors.END}")

        except Exception as e:
            print(f"{Colors.RED}[-] Error searching: {e}{Colors.END}")

        print(f"\n{Colors.YELLOW}[!] To access .onion sites, you need Tor Browser{Colors.END}")
        print(f"{Colors.BLUE}Download:{Colors.END} https://www.torproject.org/")

        print(f"\n{Colors.BLUE}Other dark web search engines:{Colors.END}")
        print(f"  - Ahmia: https://ahmia.fi/")
        print(f"  - DarkSearch: https://darksearch.io/")
        print(f"  - Tor66: http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/")
        print(f"  - Haystak: http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/")

        # Save to database
        self.save_to_db(results)

        return results

    def save_to_db(self, data: Dict):
        """Save dark web search to database"""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO darkweb_searches
            (query, search_engine, results_count, results_data)
            VALUES (?, ?, ?, ?)
        """, (
            data['query'],
            data['search_engine'],
            data['count'],
            json.dumps(data)
        ))
        self.db.conn.commit()

class OSINTInternational:
    """Main OSINT tool"""

    def __init__(self):
        self.db = OSINTDatabase()
        self.phone_osint = PhoneOSINT(self.db)
        self.people_osint = PeopleOSINT(self.db)
        self.domain_osint = DomainOSINT(self.db)
        self.breach_osint = BreachDataOSINT(self.db)
        self.image_osint = ReverseImageOSINT(self.db)
        self.darkweb_osint = DarkWebOSINT(self.db)

    def banner(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔════════════════════════════════════════════╗")
        print("║   INTERNATIONAL OSINT TOOL v2.0            ║")
        print("║   Advanced Intelligence Gathering          ║")
        print("║   Multi-Source OSINT Platform              ║")
        print("╚════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")

    def main_menu(self):
        while True:
            print(f"\n{Colors.BOLD}Main Menu:{Colors.END}")
            print(f"\n{Colors.CYAN}  Core Modules:{Colors.END}")
            print(f"  {Colors.GREEN}1.{Colors.END} Phone Number Lookup")
            print(f"  {Colors.GREEN}2.{Colors.END} Username/People Search")
            print(f"  {Colors.GREEN}3.{Colors.END} Email Search")
            print(f"\n{Colors.CYAN}  Advanced Modules:{Colors.END}")
            print(f"  {Colors.GREEN}4.{Colors.END} Domain OSINT (WHOIS/DNS)")
            print(f"  {Colors.GREEN}5.{Colors.END} Breach Data Check")
            print(f"  {Colors.GREEN}6.{Colors.END} Reverse Image Search")
            print(f"  {Colors.GREEN}7.{Colors.END} Dark Web Search")
            print(f"\n{Colors.CYAN}  Utilities:{Colors.END}")
            print(f"  {Colors.GREEN}8.{Colors.END} View Recent Searches")
            print(f"  {Colors.GREEN}9.{Colors.END} Export Results")
            print(f"  {Colors.GREEN}0.{Colors.END} Country Selection Guide")
            print(f"  {Colors.GREEN}q.{Colors.END} Quit")

            choice = input(f"\n{Colors.CYAN}Select option:{Colors.END} ").strip().lower()

            if choice == '1':
                self.phone_menu()
            elif choice == '2':
                self.username_menu()
            elif choice == '3':
                self.email_menu()
            elif choice == '4':
                self.domain_menu()
            elif choice == '5':
                self.breach_menu()
            elif choice == '6':
                self.image_menu()
            elif choice == '7':
                self.darkweb_menu()
            elif choice == '8':
                self.view_recent()
            elif choice == '9':
                self.export_results()
            elif choice == '0':
                self.country_guide()
            elif choice == 'q':
                print(f"\n{Colors.GREEN}Goodbye!{Colors.END}\n")
                break

    def phone_menu(self):
        print(f"\n{Colors.BOLD}Phone Number Lookup{Colors.END}")
        print(f"{Colors.YELLOW}Format: +[country_code][number] (e.g., +44 7700 900000){Colors.END}")

        phone = input(f"\n{Colors.CYAN}Enter phone number (or 'back'):{Colors.END} ").strip()

        if phone.lower() == 'back':
            return

        # Ask for default country if not in international format
        if not phone.startswith('+'):
            print(f"\n{Colors.YELLOW}Number doesn't start with +. Specify country code:{Colors.END}")
            print("Common codes: GB (UK), DE (Germany), FR (France), IN (India), CN (China)")
            print("              RU (Russia), BR (Brazil), AU (Australia), etc.")
            country = input(f"{Colors.CYAN}Country code (2 letters, or Enter to detect):{Colors.END} ").strip().upper()
            country = country if country else None
        else:
            country = None

        self.phone_osint.lookup_phone(phone, country)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def username_menu(self):
        print(f"\n{Colors.BOLD}Username/People Search{Colors.END}")

        username = input(f"\n{Colors.CYAN}Enter username:{Colors.END} ").strip()

        if not username:
            return

        print(f"\n{Colors.YELLOW}Platform options:{Colors.END}")
        print(f"  1. All platforms")
        print(f"  2. International only (VK, Telegram, Weibo, etc.)")
        print(f"  3. Social media only")
        print(f"  4. Developer platforms (GitHub, GitLab, etc.)")

        choice = input(f"\n{Colors.CYAN}Select [1]:{Colors.END} ").strip() or '1'

        if choice == '1':
            platforms = None  # All
        elif choice == '2':
            platforms = ['VK', 'OK', 'Telegram', 'Weibo', 'Baidu', 'Skype']
        elif choice == '3':
            platforms = ['Instagram', 'Twitter', 'TikTok', 'Facebook', 'Snapchat', 'VK']
        elif choice == '4':
            platforms = ['GitHub', 'GitLab', 'Stack Overflow', 'Behance', 'Dribbble']
        else:
            platforms = None

        self.people_osint.search_username(username, platforms)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def email_menu(self):
        print(f"\n{Colors.BOLD}Email Search{Colors.END}")
        email = input(f"\n{Colors.CYAN}Enter email:{Colors.END} ").strip()

        if email:
            self.people_osint.search_email(email)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def domain_menu(self):
        print(f"\n{Colors.BOLD}Domain OSINT - WHOIS & DNS Lookup{Colors.END}")
        domain = input(f"\n{Colors.CYAN}Enter domain (e.g., example.com):{Colors.END} ").strip()

        if domain:
            # Remove http:// or https:// if present
            domain = domain.replace('http://', '').replace('https://', '').split('/')[0]
            self.domain_osint.lookup_domain(domain)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def breach_menu(self):
        print(f"\n{Colors.BOLD}Breach Data Check{Colors.END}")
        email = input(f"\n{Colors.CYAN}Enter email to check:{Colors.END} ").strip()

        if email:
            print(f"\n{Colors.YELLOW}Do you have a HaveIBeenPwned API key?{Colors.END}")
            print(f"  1. Yes (enter key)")
            print(f"  2. No (show manual options)")

            choice = input(f"\n{Colors.CYAN}Select [2]:{Colors.END} ").strip() or '2'

            api_key = None
            if choice == '1':
                api_key = input(f"\n{Colors.CYAN}Enter API key:{Colors.END} ").strip()

            self.breach_osint.check_breaches(email, api_key)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def image_menu(self):
        print(f"\n{Colors.BOLD}Reverse Image Search{Colors.END}")
        image_path = input(f"\n{Colors.CYAN}Enter image file path:{Colors.END} ").strip()

        if image_path:
            # Expand ~ to home directory
            from os.path import expanduser
            image_path = expanduser(image_path)

            self.image_osint.search_image(image_path)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def darkweb_menu(self):
        print(f"\n{Colors.BOLD}Dark Web Search{Colors.END}")
        print(f"{Colors.RED}[!] For authorized research only{Colors.END}")

        query = input(f"\n{Colors.CYAN}Enter search query:{Colors.END} ").strip()

        if query:
            self.darkweb_osint.search_ahmia(query)

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def view_recent(self):
        print(f"\n{Colors.BOLD}Recent Searches{Colors.END}")
        searches = self.db.get_recent_searches(20)

        if not searches:
            print(f"{Colors.YELLOW}No searches yet{Colors.END}")
        else:
            for s in searches:
                print(f"\n{Colors.CYAN}{s['created_at']}{Colors.END}")
                print(f"  Type: {s['search_type']}")
                print(f"  Query: {s['query']}")
                print(f"  Results: {s['results_count']}")

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def export_results(self):
        print(f"\n{Colors.BOLD}Export Results{Colors.END}")
        print(f"{Colors.YELLOW}Export options:{Colors.END}")
        print(f"  1. Phone lookups (JSON)")
        print(f"  2. Username searches (JSON)")
        print(f"  3. Full report (Markdown)")

        choice = input(f"\n{Colors.CYAN}Select:{Colors.END} ").strip()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if choice == '1':
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT * FROM phone_lookups ORDER BY created_at DESC")
            data = [dict(row) for row in cursor.fetchall()]

            filepath = RESULTS_DIR / f'phone_lookups_{timestamp}.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            print(f"{Colors.GREEN}[+] Exported to: {filepath}{Colors.END}")

        elif choice == '2':
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT * FROM people_searches ORDER BY created_at DESC")
            data = [dict(row) for row in cursor.fetchall()]

            filepath = RESULTS_DIR / f'username_searches_{timestamp}.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            print(f"{Colors.GREEN}[+] Exported to: {filepath}{Colors.END}")

        elif choice == '3':
            filepath = RESULTS_DIR / f'osint_report_{timestamp}.md'

            with open(filepath, 'w') as f:
                f.write("# International OSINT Report\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Phone lookups
                f.write("## Phone Number Lookups\n\n")
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT * FROM phone_lookups ORDER BY created_at DESC LIMIT 50")
                phones = cursor.fetchall()

                for p in phones:
                    f.write(f"### {p['phone_number']}\n")
                    f.write(f"- **Valid:** {p['valid']}\n")
                    f.write(f"- **Country:** {p['country']}\n")
                    f.write(f"- **Carrier:** {p['carrier']}\n")
                    f.write(f"- **Line Type:** {p['line_type']}\n")
                    f.write(f"- **Location:** {p['location']}\n")
                    f.write(f"- **Timezone:** {p['timezone']}\n")
                    f.write(f"- **Date:** {p['created_at']}\n\n")

                # Username searches
                f.write("## Username Searches\n\n")
                cursor.execute("""
                    SELECT username, COUNT(*) as total,
                           SUM(CASE WHEN found THEN 1 ELSE 0 END) as found_count
                    FROM people_searches
                    GROUP BY username
                    ORDER BY created_at DESC
                """)
                usernames = cursor.fetchall()

                for u in usernames:
                    f.write(f"### {u['username']}\n")
                    f.write(f"- **Found on:** {u['found_count']} / {u['total']} platforms\n\n")

                    cursor.execute("""
                        SELECT platform, url FROM people_searches
                        WHERE username = ? AND found = 1
                    """, (u['username'],))

                    platforms = cursor.fetchall()
                    if platforms:
                        f.write("**Profiles found:**\n")
                        for p in platforms:
                            f.write(f"- [{p['platform']}]({p['url']})\n")
                        f.write("\n")

            print(f"{Colors.GREEN}[+] Exported report to: {filepath}{Colors.END}")

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def country_guide(self):
        print(f"\n{Colors.BOLD}Country Selection Guide{Colors.END}\n")

        countries = {
            'Europe': {
                'GB': 'United Kingdom (+44)',
                'DE': 'Germany (+49)',
                'FR': 'France (+33)',
                'IT': 'Italy (+39)',
                'ES': 'Spain (+34)',
                'RU': 'Russia (+7)',
                'PL': 'Poland (+48)',
                'UA': 'Ukraine (+380)',
            },
            'Asia': {
                'CN': 'China (+86)',
                'IN': 'India (+91)',
                'JP': 'Japan (+81)',
                'KR': 'South Korea (+82)',
                'PK': 'Pakistan (+92)',
                'ID': 'Indonesia (+62)',
                'TH': 'Thailand (+66)',
                'VN': 'Vietnam (+84)',
            },
            'Americas': {
                'BR': 'Brazil (+55)',
                'MX': 'Mexico (+52)',
                'AR': 'Argentina (+54)',
                'CO': 'Colombia (+57)',
                'CA': 'Canada (+1)',
            },
            'Other': {
                'AU': 'Australia (+61)',
                'ZA': 'South Africa (+27)',
                'EG': 'Egypt (+20)',
                'SA': 'Saudi Arabia (+966)',
            }
        }

        for region, codes in countries.items():
            print(f"{Colors.CYAN}{region}:{Colors.END}")
            for code, name in codes.items():
                print(f"  {Colors.GREEN}{code}{Colors.END} - {name}")
            print()

        input(f"{Colors.BLUE}Press Enter to continue...{Colors.END}")

    def run(self):
        self.banner()
        self.main_menu()

if __name__ == '__main__':
    try:
        tool = OSINTInternational()
        tool.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}[!] Interrupted by user{Colors.END}\n")
    except Exception as e:
        print(f"\n{Colors.RED}[!] Error: {e}{Colors.END}\n")

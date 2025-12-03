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
from urllib.parse import quote
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

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

class OSINTInternational:
    """Main OSINT tool"""

    def __init__(self):
        self.db = OSINTDatabase()
        self.phone_osint = PhoneOSINT(self.db)
        self.people_osint = PeopleOSINT(self.db)

    def banner(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔════════════════════════════════════════════╗")
        print("║   INTERNATIONAL OSINT TOOL                 ║")
        print("║   Phone Numbers & People Search            ║")
        print("║   Non-US Focused                           ║")
        print("╚════════════════════════════════════════════╝")
        print(f"{Colors.END}\n")

    def main_menu(self):
        while True:
            print(f"\n{Colors.BOLD}Main Menu:{Colors.END}")
            print(f"  {Colors.GREEN}1.{Colors.END} Phone Number Lookup")
            print(f"  {Colors.GREEN}2.{Colors.END} Username/People Search")
            print(f"  {Colors.GREEN}3.{Colors.END} Email Search")
            print(f"  {Colors.GREEN}4.{Colors.END} View Recent Searches")
            print(f"  {Colors.GREEN}5.{Colors.END} Export Results")
            print(f"  {Colors.GREEN}6.{Colors.END} Country Selection Guide")
            print(f"  {Colors.GREEN}q.{Colors.END} Quit")

            choice = input(f"\n{Colors.CYAN}Select option:{Colors.END} ").strip().lower()

            if choice == '1':
                self.phone_menu()
            elif choice == '2':
                self.username_menu()
            elif choice == '3':
                self.email_menu()
            elif choice == '4':
                self.view_recent()
            elif choice == '5':
                self.export_results()
            elif choice == '6':
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

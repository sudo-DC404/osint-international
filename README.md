

<img width="1536" height="1024" alt="5F68FEB7-F855-4D92-B2BA-AAC4A34AECD1" src="https://github.com/user-attachments/assets/3f2eead4-bb97-43b2-8578-0fdd05138f17" />



# 🌍 International OSINT Tool v2.0

A comprehensive OSINT platform for **advanced intelligence gathering** with focus on **international targets** and **multi-source data collection**.

## Features

### 📱 Phone Number OSINT
- International phone number validation (100+ countries)
- Country and region detection
- Carrier identification
- Line type detection (Mobile, Fixed Line, VoIP, Toll Free, etc.)
- Geographic location and timezone information
- Multiple format support (international and national)

### 👤 Username/People Search
- Search across **30+ platforms**
- International platform focus:
  - VK (Russia)
  - OK.ru (Russia)
  - Telegram
  - Weibo (China)
  - Baidu Tieba (China)
- Global platforms: Instagram, Twitter, GitHub, LinkedIn, TikTok, and more
- Targeted search categories (International, Social Media, Developer platforms)
- Direct profile URLs for found accounts

### 🌐 Domain OSINT **[NEW]**
- WHOIS lookups (registrar, creation date, expiration, organization)
- DNS record enumeration (A, AAAA, MX, NS, TXT)
- Name server identification
- Domain registration history
- Automated data collection and storage

### 💥 Breach Data Integration **[NEW]**
- HaveIBeenPwned API integration
- Email breach checking
- Password paste detection
- Alternative breach databases (DeHashed, LeakCheck, IntelX)
- Manual and API-based checking

### 🖼️ Reverse Image Search **[NEW]**
- Image hash calculation (SHA-256)
- Multiple search engine support:
  - Google Images
  - Yandex Images
  - TinEye
  - Bing Visual Search
  - PimEyes (facial recognition)
- Local image file analysis
- Search URL generation

### 🕵️ Dark Web Search **[NEW]**
- Ahmia.fi integration (clearnet Tor search)
- .onion link discovery
- Dark web search engines directory
- Tor Browser integration guidance
- Multiple dark web search options

### 📊 Data Management
- SQLite database for all searches
- 7 specialized data tables
- Search history tracking
- Export to JSON or Markdown reports
- Timestamp tracking for all activities

## Installation

### Prerequisites
```bash
# Debian/Ubuntu/Kali
sudo apt install python3 python3-phonenumbers python3-whois python3-dnspython

# Or via pip (if using virtual environment)
pip install phonenumbers requests python-whois dnspython
```

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/osint-international.git
cd osint-international

# Make executable
chmod +x osint_international.py

# Create symlink (optional)
ln -s $(pwd)/osint_international.py ~/.local/bin/osint

# Run
./osint_international.py
# or
osint
```

## Quick Start

### Launch Tool
```bash
osint
```

### Phone Number Lookup
```bash
osint → 1 → +44 7700 900000
```

**Output:**
```
[+] Valid number!
Country: United Kingdom
Carrier: Vodafone
Line Type: Mobile
Location: United Kingdom
Timezone: Europe/London
```

### Username Search
```bash
osint → 2 → target_username → 1 (All platforms)
```

**Output:**
```
[*] Searching for username: target_username

[*] Checking VK... FOUND!
    https://vk.com/target_username
[*] Checking GitHub... FOUND!
    https://github.com/target_username
[*] Checking Instagram... Not found

[+] Found on 2/30 platforms
```

## Usage

### Main Menu Options

**Core Modules:**
1. **Phone Number Lookup** - Analyze international phone numbers
2. **Username/People Search** - Find profiles across platforms
3. **Email Search** - Get tool recommendations for email OSINT

**Advanced Modules:**
4. **Domain OSINT (WHOIS/DNS)** - Domain registration and DNS analysis
5. **Breach Data Check** - Email breach detection
6. **Reverse Image Search** - Find images across the web
7. **Dark Web Search** - Search Tor hidden services

**Utilities:**
8. **View Recent Searches** - Browse search history
9. **Export Results** - Export to JSON or Markdown
0. **Country Selection Guide** - Quick country code reference
q. **Quit**

### Phone Number Format

Always use international format:
```
+[country_code][number]
```

Examples:
```
+44 7700 900000        # UK
+49 151 12345678       # Germany
+91 98765 43210        # India
+86 138 0013 8000      # China
+7 495 123 4567        # Russia
+55 11 91234 5678      # Brazil
```

### Platform Search Categories

**1. All Platforms (30+)**
- Comprehensive search across all platforms
- ~60 seconds

**2. International Only (6 platforms)**
- VK, OK.ru, Telegram, Weibo, Baidu, Skype
- ~15 seconds
- Best for non-US targets

**3. Social Media (8 platforms)**
- Instagram, Twitter, TikTok, Snapchat, etc.
- ~20 seconds

**4. Developer Platforms (5 platforms)**
- GitHub, GitLab, Behance, Dribbble
- ~10 seconds

### NEW FEATURE Examples

#### Domain OSINT
```bash
osint → 4 → google.com
```

**Output:**
```
[*] Performing WHOIS lookup...
[+] WHOIS data retrieved
  Registrar: MarkMonitor Inc.
  Created: 1997-09-15
  Expires: 2028-09-14

[*] Performing DNS lookups...
  A Records: 142.250.185.46
  MX Records: smtp.google.com
  NS Records: ns1.google.com, ns2.google.com
```

#### Breach Data Check
```bash
osint → 5 → email@example.com
```

**Output:**
```
[!] Email found in 3 breaches!

• Collection #1
  Date: 2019-01-07
  Data: Email addresses, Passwords

• LinkedIn
  Date: 2021-06-22
  Data: Email addresses, Names, Phone numbers
```

#### Reverse Image Search
```bash
osint → 6 → /path/to/image.jpg
```

**Output:**
```
Manual search options:

• Google Images
  https://www.google.com/searchbyimage

• Yandex Images
  https://yandex.com/images/

• PimEyes (Faces)
  https://pimeyes.com/

Image hash: a3f5e9c2b1d4...
```

#### Dark Web Search
```bash
osint → 7 → hacking forums
```

**Output:**
```
[*] Searching Ahmia.fi...
[+] Found 15 .onion results

  1. http://example123456789abc.onion/forums
  2. http://darknet987654321xyz.onion/community
  ...

[!] To access .onion sites, you need Tor Browser
```

## Supported Platforms

### International Focus
- VK (Russia)
- OK.ru (Russia)
- Telegram
- Weibo (China)
- Baidu Tieba (China)
- Skype

### Social Media
Instagram, Twitter, TikTok, Snapchat, LinkedIn, Reddit, Pinterest, Medium, Tumblr, WordPress

### Developer
GitHub, GitLab, Behance, Dribbble, DeviantArt

### Content
YouTube, Twitch, Vimeo, SoundCloud, Spotify, 500px, Flickr

### Gaming
Steam

## Country Coverage

### Europe
GB (+44), DE (+49), FR (+33), RU (+7), IT (+39), ES (+34), PL (+48), UA (+380)

### Asia
CN (+86), IN (+91), JP (+81), KR (+82), PK (+92), ID (+62), TH (+66), VN (+84)

### Americas
BR (+55), MX (+52), AR (+54), CO (+57), CA (+1)

### Other
AU (+61), ZA (+27), EG (+20), SA (+966)

## Data Storage

### Database
```
~/.osint_international.db
```

### Tables
- `phone_lookups` - Phone number search history
- `people_searches` - Username search results
- `search_sessions` - Session tracking

### Results Directory
```
~/osint_results/
├── phone_lookups_[timestamp].json
├── username_searches_[timestamp].json
└── osint_report_[timestamp].md
```

## Export Options

### 1. Phone Lookups (JSON)
```json
{
  "phone_number": "+44 7700 900000",
  "country": "United Kingdom",
  "carrier": "Vodafone",
  "line_type": "Mobile",
  "valid": true
}
```

### 2. Username Searches (JSON)
```json
{
  "username": "target_user",
  "platform": "VK",
  "url": "https://vk.com/target_user",
  "found": true
}
```

### 3. Full Markdown Report
Professional markdown report with all phone and username searches.

## Security

### Implemented Security Measures
- ✅ SQL Injection Protection (parameterized queries)
- ✅ URL Encoding for usernames
- ✅ Input validation via phonenumbers library
- ✅ HTTP timeout protection (5 seconds)
- ✅ Exception handling for all operations
- ✅ No command execution vulnerabilities
- ✅ Local data storage only (no cloud sync)

### Ethical Use
- ⚠️ For authorized investigations only
- ⚠️ Respect privacy laws in your jurisdiction
- ⚠️ Use for legitimate purposes only
- ⚠️ Educational, security research, and authorized testing

### Rate Limiting
- 5-second timeout per HTTP request
- Respectful of target websites
- Session reuse for connection pooling

## Legal & Ethical Considerations

This tool is for **authorized use only**:
- ✅ Security research
- ✅ Authorized penetration testing
- ✅ OSINT training and education
- ✅ Personal investigations (lawful)
- ❌ Unauthorized surveillance
- ❌ Stalking or harassment
- ❌ Illegal activities

**Users are responsible for complying with local laws.**

## Requirements

- Python 3.7+
- phonenumbers library
- requests library
- sqlite3 (built-in)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## Roadmap

Future enhancements:
- [ ] Facial recognition integration
- [ ] Reverse image search
- [ ] Domain OSINT (WHOIS, DNS)
- [ ] Breach data integration
- [ ] Dark web search
- [ ] Automated PDF reporting
- [ ] API support

## Related Tools

### Complementary OSINT Tools
- **PhoneInfoga** - Advanced phone OSINT
- **Sherlock** - Username search (300+ sites)
- **Holehe** - Email verification (120+ sites)
- **GHunt** - Gmail specific OSINT
- **Maigret** - Advanced username enumeration

## Performance

- Phone lookup: ~1 second
- Username search (all platforms): 30-60 seconds
- Username search (targeted): 5-15 seconds
- Export: <5 seconds

## Troubleshooting

### "Invalid phone number"
Use international format: `+[country_code][number]`

### Slow searches
Use targeted platform categories instead of "All platforms"

### Database locked
Close other instances: `killall python3`

## License

MIT License - See LICENSE file for details

## Author

Built for international OSINT operations with focus on non-US platforms.

## Acknowledgments

- phonenumbers library by Google
- OSINT community
- Security researchers worldwide

---

**For educational and authorized use only. Users are responsible for compliance with applicable laws.**

## Contact

For issues, feature requests, or contributions, please open an issue on GitHub.

---

**International OSINT. Phone + Username. 30+ Platforms. 100+ Countries. 🌍**

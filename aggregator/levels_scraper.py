"""
Levels.fyi scraper for new grad salary data
"""

import re
import json
import requests
from typing import Optional, Tuple
from functools import lru_cache


class LevelsScraper:
    """Scrape salary data from levels.fyi"""

    BASE_URL = "https://www.levels.fyi/companies/{company}/salaries/software-engineer"

    # Company name aliases (job listing name -> levels.fyi slug)
    COMPANY_ALIASES = {
        # Big tech variants
        "tiktok": "bytedance",
        "tik tok": "bytedance",
        "bytedance": "bytedance",
        "facebook": "meta",
        "instagram": "meta",
        "whatsapp": "meta",
        "oculus": "meta",
        "google llc": "google",
        "alphabet": "google",
        "youtube": "google",
        "deepmind": "google",
        "amazon.com": "amazon",
        "aws": "amazon",
        "amazon web services": "amazon",
        "twitch": "twitch",
        "ring": "amazon",
        "microsoft corporation": "microsoft",
        "github": "microsoft",
        "linkedin": "microsoft",
        "azure": "microsoft",

        # Finance
        "citadel securities": "citadel",
        "citadel llc": "citadel",
        "two sigma investments": "two-sigma",
        "two sigma securities": "two-sigma",
        "jane street capital": "jane-street",
        "goldman sachs group": "goldman-sachs",
        "goldman sachs & co": "goldman-sachs",
        "morgan stanley": "morgan-stanley",
        "jp morgan": "jpmorgan-chase",
        "jpmorgan": "jpmorgan-chase",
        "jpmorgan chase": "jpmorgan-chase",
        "capital one": "capital-one",
        "capital one financial": "capital-one",
        "bank of america": "bank-of-america",
        "bofa": "bank-of-america",
        "wells fargo": "wells-fargo",
        "american express": "american-express",
        "amex": "american-express",
        "visa inc": "visa",
        "mastercard": "mastercard",
        "blackrock": "blackrock",
        "fidelity": "fidelity-investments",
        "fidelity investments": "fidelity-investments",
        "charles schwab": "charles-schwab",
        "robinhood markets": "robinhood",
        "sofi": "sofi",
        "chime": "chime",
        "affirm": "affirm",
        "citigroup": "citi",
        "citibank": "citi",
        "citi group": "citi",
        "interactive brokers": "interactive-brokers",
        "ibkr": "interactive-brokers",
        "pnc bank": "pnc",
        "pnc financial": "pnc",
        "susquehanna international group": "susquehanna-international-group",
        "sig": "susquehanna-international-group",
        "susquehanna": "susquehanna-international-group",
        "imc trading": "imc",
        "jump trading": "jump-trading",
        "drw holdings": "drw",
        "drw trading": "drw",
        "chicago trading company": "chicago-trading-company",
        "akuna capital": "akuna-capital",
        "hudson river trading": "hudson-river-trading",
        "hrt": "hudson-river-trading",
        "optiver": "optiver",
        "flow traders": "flow-traders",
        "virtu financial": "virtu-financial",

        # Tech companies
        "apple inc": "apple",
        "nvidia corporation": "nvidia",
        "intel corporation": "intel",
        "amd": "amd",
        "qualcomm": "qualcomm",
        "broadcom": "broadcom",
        "salesforce": "salesforce",
        "salesforce.com": "salesforce",
        "oracle corporation": "oracle",
        "ibm": "ibm",
        "cisco systems": "cisco",
        "cisco": "cisco",
        "vmware": "vmware",
        "dell technologies": "dell",
        "hp inc": "hp",
        "hewlett packard": "hp",
        "hewlett-packard": "hp",
        "hpe": "hpe",
        "hewlett packard enterprise": "hpe",
        "servicenow": "servicenow",
        "workday": "workday",
        "splunk": "splunk",
        "atlassian": "atlassian",
        "zendesk": "zendesk",
        "hubspot": "hubspot",
        "twilio": "twilio",
        "okta": "okta",
        "crowdstrike": "crowdstrike",
        "palo alto networks": "palo-alto-networks",
        "zscaler": "zscaler",
        "fortinet": "fortinet",
        "mongodb": "mongodb",
        "elastic": "elastic",
        "snowflake": "snowflake",
        "databricks": "databricks",
        "confluent": "confluent",
        "hashicorp": "hashicorp",
        "intuit": "intuit",
        "adobe": "adobe",
        "adobe inc": "adobe",
        "autodesk": "autodesk",
        "synopsys": "synopsys",
        "cadence": "cadence-design-systems",
        "cadence design systems": "cadence-design-systems",
        "applied materials": "applied-materials",
        "lam research": "lam-research",
        "kla": "kla",
        "kla corporation": "kla",
        "microchip technology": "microchip-technology",
        "microchip": "microchip-technology",
        "marvell": "marvell",
        "marvell technology": "marvell",
        "analog devices": "analog-devices",
        "texas instruments": "texas-instruments",
        "ti": "texas-instruments",
        "micron": "micron",
        "micron technology": "micron",
        "western digital": "western-digital",
        "seagate": "seagate",

        # Consumer tech
        "uber technologies": "uber",
        "lyft inc": "lyft",
        "doordash": "doordash",
        "instacart": "instacart",
        "airbnb": "airbnb",
        "booking.com": "booking",
        "booking holdings": "booking",
        "expedia": "expedia",
        "tripadvisor": "tripadvisor",
        "zillow": "zillow",
        "zillow group": "zillow",
        "redfin": "redfin",
        "opendoor": "opendoor",
        "compass real estate": "compass",
        "yelp": "yelp",
        "grubhub": "grubhub",
        "postmates": "uber",
        "etsy": "etsy",
        "ebay": "ebay",
        "wayfair": "wayfair",
        "shopify": "shopify",
        "squarespace": "squarespace",
        "wix": "wix",

        # Social/Entertainment
        "snap inc": "snap",
        "snapchat": "snap",
        "twitter": "x",
        "x corp": "x",
        "pinterest": "pinterest",
        "reddit": "reddit",
        "discord": "discord",
        "spotify": "spotify",
        "netflix": "netflix",
        "roku": "roku",
        "hulu": "disney",
        "disney": "disney",
        "walt disney": "disney",
        "warner bros": "warner-bros-discovery",
        "paramount": "paramount",
        "sony": "sony",
        "electronic arts": "ea",
        "activision": "activision-blizzard",
        "blizzard": "activision-blizzard",
        "riot games": "riot-games",
        "epic games": "epic-games",
        "roblox": "roblox",
        "unity": "unity",

        # Payments/Fintech
        "stripe": "stripe",
        "square": "block",
        "block inc": "block",
        "paypal": "paypal",
        "venmo": "paypal",
        "brex": "brex",
        "ramp": "ramp",
        "plaid": "plaid",
        "marqeta": "marqeta",
        "checkout.com": "checkout",
        "adyen": "adyen",
        "klarna": "klarna",
        "afterpay": "afterpay",
        "bill.com": "billcom",
        "bill": "billcom",

        # Cloud/Enterprise
        "dropbox": "dropbox",
        "box": "box",
        "docusign": "docusign",
        "zoom": "zoom",
        "zoom video": "zoom",
        "slack": "salesforce",
        "asana": "asana",
        "monday.com": "monday",
        "notion": "notion",
        "figma": "figma",
        "canva": "canva",
        "miro": "miro",
        "airtable": "airtable",
        "webflow": "webflow",
        "pega": "pegasystems",
        "pegasystems": "pegasystems",

        # AI/ML
        "openai": "openai",
        "anthropic": "anthropic",
        "cohere": "cohere",
        "scale ai": "scale-ai",
        "hugging face": "hugging-face",
        "stability ai": "stability-ai",

        # Auto/Space
        "tesla": "tesla",
        "tesla motors": "tesla",
        "spacex": "spacex",
        "waymo": "waymo",
        "cruise": "cruise",
        "aurora": "aurora",
        "nuro": "nuro",
        "rivian": "rivian",
        "lucid motors": "lucid-motors",
        "gm": "general-motors",
        "general motors": "general-motors",
        "ford": "ford",
        "ford motor": "ford",
        "toyota": "toyota",
        "honda": "honda",
        "bmw": "bmw",
        "mercedes": "mercedes-benz",

        # Defense/Aerospace/Government contractors
        "boeing": "boeing",
        "the boeing company": "boeing",
        "lockheed martin": "lockheed-martin",
        "lockheed": "lockheed-martin",
        "northrop grumman": "northrop-grumman",
        "northrop": "northrop-grumman",
        "raytheon": "raytheon",
        "rtx": "raytheon",
        "raytheon technologies": "raytheon",
        "bae systems": "bae-systems",
        "bae": "bae-systems",
        "general dynamics": "general-dynamics-mission-systems",
        "general dynamics mission systems": "general-dynamics-mission-systems",
        "gdms": "general-dynamics-mission-systems",
        "general dynamics information technology": "general-dynamics-mission-systems",
        "gdit": "general-dynamics-mission-systems",
        "maxar": "maxar-technologies",
        "maxar technologies": "maxar-technologies",
        "l3harris": "l3harris",
        "l3harris technologies": "l3harris",
        "l3 harris": "l3harris",
        "leidos": "leidos",
        "saic": "saic",
        "booz allen hamilton": "booz-allen-hamilton",
        "booz allen": "booz-allen-hamilton",
        "caci": "caci-international",
        "caci international": "caci-international",
        "accenture federal services": "accenture",
        "accenture": "accenture",
        "deloitte": "deloitte",
        "kpmg": "kpmg",
        "ey": "ey",
        "ernst young": "ey",
        "ernst & young": "ey",
        "pwc": "pwc",
        "pricewaterhousecoopers": "pwc",
        "mckinsey": "mckinsey",
        "bcg": "bcg",
        "boston consulting group": "bcg",
        "bain": "bain",
        "bain & company": "bain",

        # Other tech
        "palantir": "palantir",
        "palantir technologies": "palantir",
        "datadog": "datadog",
        "new relic": "new-relic",
        "sumo logic": "sumo-logic",
        "dynatrace": "dynatrace",
        "grafana": "grafana-labs",
        "cloudflare": "cloudflare",
        "fastly": "fastly",
        "akamai": "akamai",
        "veeva": "veeva-systems",
        "veeva systems": "veeva-systems",
        "epic systems": "epic-systems",
        "cerner": "cerner",
        "bloomberg": "bloomberg",
        "bloomberg lp": "bloomberg",
        "thomson reuters": "thomson-reuters",
        "factset": "factset",
        "morningstar": "morningstar",
        "ge healthcare": "ge-healthcare",
        "ge": "ge-healthcare",
        "general electric": "ge-healthcare",

        # Enterprise Storage/Infrastructure
        "nutanix": "nutanix",
        "pure storage": "pure-storage",
        "purestorage": "pure-storage",
        "netapp": "netapp",
        "net app": "netapp",
        "rubrik": "rubrik",
        "cohesity": "cohesity",
        "commvault": "commvault",
        "dell emc": "dell",
        "emc": "dell",

        # More tech
        "thales": "thales",
        "thales group": "thales",
        "ciena": "ciena",
        "juniper networks": "juniper-networks",
        "juniper": "juniper-networks",
        "arista networks": "arista-networks",
        "arista": "arista-networks",
        "f5 networks": "f5-networks",
        "f5": "f5-networks",
        "citrix": "citrix",
        "vmware": "vmware",
    }

    # Entry level mappings for different companies
    ENTRY_LEVELS = {
        "google": "l3",
        "meta": "e3",
        "facebook": "e3",
        "apple": "ice2",
        "amazon": "sde1",
        "microsoft": "59",
        "netflix": "l3",
        "nvidia": "new-grad",
        "salesforce": "amts",
        "adobe": "e3",
        "uber": "e3",
        "lyft": "l3",
        "airbnb": "l3",
        "stripe": "l1",
        "doordash": "e3",
        "coinbase": "l3",
        "robinhood": "l3",
        "databricks": "l3",
        "snowflake": "entry-level",
        "palantir": "software-engineer",
        "datadog": "new-grad",
        "dropbox": "e3",
        "pinterest": "l3",
        "snap": "l3",
        "linkedin": "l3",
        "reddit": "e3",
        "discord": "l3",
        "figma": "l3",
        "notion": "e3",
        "plaid": "l3",
        "ramp": "l1",
        "square": "l3",
        "block": "l3",
        "paypal": "e3",
        "intuit": "swe1",
        "oracle": "ic1",
        "cisco": "i-7",
        "intel": "grade-3",
        "bloomberg": "l3",
        "capital-one": "associate",
        "goldman-sachs": "analyst",
        "citadel": "l3",
        "two-sigma": "l3",
        "jane-street": "junior-trader",
        "openai": "l3",
        "anthropic": "l3",
        "spacex": "l1",
        "tesla": "l2",
        "waymo": "l3",
        "bytedance": "e3",
        "jpmorgan-chase": "analyst",
        "morgan-stanley": "analyst",
        "bank-of-america": "analyst",
        "x": "l3",
    }

    CACHE_FILE = ".levels_salary_cache.json"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        # Cache for companies not found on levels.fyi (confirmed 404s)
        self._not_found_cache = set()
        # Cache for successful salary lookups
        self._salary_cache = {}
        # Load cache from file
        self._load_cache()

    def _load_cache(self):
        """Load salary cache from file"""
        import os
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self._salary_cache = {k: tuple(v) for k, v in data.get('found', {}).items()}
                    self._not_found_cache = set(data.get('not_found', []))
                    print(f"  [Cache] Loaded {len(self._salary_cache)} cached salaries, {len(self._not_found_cache)} not-found", file=__import__('sys').stderr)
            except Exception as e:
                print(f"  [Cache] Error loading cache: {e}", file=__import__('sys').stderr)

    def _save_cache(self):
        """Save salary cache to file"""
        try:
            data = {
                'found': {k: list(v) for k, v in self._salary_cache.items()},
                'not_found': list(self._not_found_cache)
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"  [Cache] Error saving cache: {e}", file=__import__('sys').stderr)

    # Common suffixes to strip from company names
    COMPANY_SUFFIXES = [
        ' inc', ' inc.', ' incorporated', ' corp', ' corp.', ' corporation',
        ' llc', ' llc.', ' ltd', ' ltd.', ' limited', ' co', ' co.',
        ' company', ' companies', ' technologies', ' technology', ' tech',
        ' solutions', ' software', ' systems', ' services', ' group',
        ' holdings', ' international', ' global', ' worldwide',
        ', inc', ', inc.', ', llc', ', corp', ', ltd',
    ]

    # Common prefixes to strip
    COMPANY_PREFIXES = ['the ']

    def _normalize_company(self, name: str) -> str:
        """Normalize company name to levels.fyi slug using aliases"""
        name_lower = name.lower().strip()

        # Check exact match in aliases first
        if name_lower in self.COMPANY_ALIASES:
            return self.COMPANY_ALIASES[name_lower]

        # Strip common suffixes and prefixes, then check again
        name_stripped = name_lower
        for prefix in self.COMPANY_PREFIXES:
            if name_stripped.startswith(prefix):
                name_stripped = name_stripped[len(prefix):]
        for suffix in self.COMPANY_SUFFIXES:
            if name_stripped.endswith(suffix):
                name_stripped = name_stripped[:-len(suffix)]
        name_stripped = name_stripped.strip()

        # Check stripped name in aliases
        if name_stripped in self.COMPANY_ALIASES:
            return self.COMPANY_ALIASES[name_stripped]

        # Check if stripped name slugified matches an alias
        name_slug = re.sub(r'[^a-z0-9]+', '-', name_stripped).strip('-')
        if name_slug in self.COMPANY_ALIASES:
            return self.COMPANY_ALIASES[name_slug]

        # Check if full name contains a known alias (for multi-word matches)
        # Only match if the alias is a significant part of the name (>50% length or >3 words match)
        best_match = None
        best_match_len = 0
        for alias, slug in self.COMPANY_ALIASES.items():
            # Skip very short aliases to avoid false positives
            if len(alias) < 4:
                continue
            # Check if alias is contained as a word boundary match
            if alias in name_lower:
                # Prefer longer matches
                if len(alias) > best_match_len:
                    best_match = slug
                    best_match_len = len(alias)

        if best_match and best_match_len >= len(name_stripped) * 0.5:
            return best_match

        # Fallback to basic slugify
        return name_slug

    def _slugify(self, name: str) -> str:
        """Convert company name to URL slug (legacy, use _normalize_company)"""
        return self._normalize_company(name)

    def get_salary(self, company: str, title: str = "software engineer",
                   location: str = None) -> Tuple[Optional[int], Optional[int]]:
        """
        Get salary range for a company/title/location combination.

        Returns (min_salary, max_salary) or (None, None) if not found.
        """
        company_slug = self._normalize_company(company)

        # Check not-found cache first (only for confirmed 404s)
        if company_slug in self._not_found_cache:
            return (None, None)

        # Check positive salary cache
        if company_slug in self._salary_cache:
            return self._salary_cache[company_slug]

        # Fetch from levels.fyi with rate limiting
        result = self._fetch_salary(company_slug)

        # Cache the result appropriately
        if result != (None, None):
            self._salary_cache[company_slug] = result

        return result

    def _fetch_salary(self, company_slug: str) -> Tuple[Optional[int], Optional[int]]:
        """Fetch salary from levels.fyi with rate limiting and retry logic"""
        import time

        url = self.BASE_URL.format(company=company_slug)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Rate limiting - small delay between requests
                time.sleep(0.05)

                resp = self.session.get(url, timeout=10)

                # Handle rate limiting
                if resp.status_code in (429, 405, 503):
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return (None, None)

                # Company not found - add to not_found_cache
                if resp.status_code == 404:
                    self._not_found_cache.add(company_slug)
                    return (None, None)

                if resp.status_code != 200:
                    return (None, None)

                # Extract __NEXT_DATA__ JSON
                match = re.search(
                    r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
                    resp.text
                )
                if not match:
                    self._not_found_cache.add(company_slug)
                    return (None, None)

                data = json.loads(match.group(1))
                page_props = data.get('props', {}).get('pageProps', {})
                averages = page_props.get('averages', [])

                if not averages:
                    self._not_found_cache.add(company_slug)
                    return (None, None)

                # Find entry level data
                entry_level = self.ENTRY_LEVELS.get(company_slug)
                entry_data = None

                for avg in averages:
                    level = avg.get('level', '').lower()
                    # Check if this is entry level
                    if entry_level and level == entry_level:
                        entry_data = avg
                        break
                    # Fallback: look for common entry level indicators
                    if not entry_data and any(x in level for x in ['l3', 'e3', 'sde1', 'new-grad', 'entry', 'junior', '1', 'i']):
                        entry_data = avg

                if not entry_data:
                    # Use first level as fallback (usually entry)
                    entry_data = averages[0] if averages else None

                if not entry_data:
                    return (None, None)

                # Get salary from samples
                samples = entry_data.get('samples', [])

                if samples:
                    # Get min/max from samples
                    comps = [s.get('totalCompensation') for s in samples if s.get('totalCompensation')]
                    if comps:
                        # Return 25th and 75th percentile for range
                        comps.sort()
                        n = len(comps)
                        return (comps[n // 4], comps[3 * n // 4])

                # Fallback to averages
                total = entry_data.get('total') or entry_data.get('rawValues', {}).get('total')
                if total:
                    # Return ±15% range around average
                    return (int(total * 0.85), int(total * 1.15))

                return (None, None)

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return (None, None)

        return (None, None)

    def enrich_jobs(self, jobs: list) -> int:
        """
        Enrich jobs with salary data from levels.fyi.
        Only enriches jobs that don't already have salary data.

        Returns count of enriched jobs.
        """
        import sys
        enriched = 0
        total = len(jobs)

        # Track unique companies to avoid redundant lookups
        seen_companies = set()

        for i, job in enumerate(jobs):
            # Progress output every 500 jobs
            if i > 0 and i % 500 == 0:
                print(f"    Enriching... {i}/{total} jobs ({enriched} enriched)", file=sys.stderr)
                sys.stderr.flush()

            # Skip if already has salary
            if job.salary_min or job.salary_max:
                continue

            # Skip if we've already looked up this company
            company_key = job.company.lower().strip()
            if company_key in seen_companies:
                # Get cached result
                salary_min, salary_max = self.get_salary(job.company, job.title, job.location)
                if salary_min and salary_max:
                    job.salary_min = salary_min
                    job.salary_max = salary_max
                    enriched += 1
                continue

            seen_companies.add(company_key)

            # Try to get salary
            salary_min, salary_max = self.get_salary(
                job.company,
                job.title,
                job.location
            )

            if salary_min and salary_max:
                job.salary_min = salary_min
                job.salary_max = salary_max
                enriched += 1

        # Save cache to file for future runs
        self._save_cache()

        return enriched


# Singleton instance for caching
_scraper = None

def get_scraper() -> LevelsScraper:
    global _scraper
    if _scraper is None:
        _scraper = LevelsScraper()
    return _scraper


if __name__ == "__main__":
    # Test the scraper
    scraper = LevelsScraper()

    test_companies = ["google", "meta", "stripe", "openai", "jane street"]

    for company in test_companies:
        min_sal, max_sal = scraper.get_salary(company)
        if min_sal and max_sal:
            print(f"{company}: ${min_sal:,} - ${max_sal:,}")
        else:
            print(f"{company}: No data")

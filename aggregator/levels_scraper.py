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
        "twitch": "amazon",
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
        "vmware": "vmware",
        "dell technologies": "dell",
        "hp inc": "hp",
        "hewlett packard": "hp",
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
        "ea": "ea",
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

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        # Cache for companies not found on levels.fyi
        self._not_found_cache = set()

    def _normalize_company(self, name: str) -> str:
        """Normalize company name to levels.fyi slug using aliases"""
        name_lower = name.lower().strip()

        # Check exact match in aliases
        if name_lower in self.COMPANY_ALIASES:
            return self.COMPANY_ALIASES[name_lower]

        # Check if any alias is contained in the name
        for alias, slug in self.COMPANY_ALIASES.items():
            if alias in name_lower or name_lower in alias:
                return slug

        # Fallback to basic slugify
        return re.sub(r'[^a-z0-9]+', '-', name_lower).strip('-')

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

        # Check not-found cache first
        if company_slug in self._not_found_cache:
            return (None, None)

        # Check salary cache
        result = self._get_salary_cached(company_slug)
        if result == (None, None):
            self._not_found_cache.add(company_slug)
        return result

    @lru_cache(maxsize=500)
    def _get_salary_cached(self, company_slug: str) -> Tuple[Optional[int], Optional[int]]:
        """Cached salary lookup by normalized slug"""
        try:
            url = self.BASE_URL.format(company=company_slug)
            resp = self.session.get(url, timeout=10)

            if resp.status_code != 200:
                return (None, None)

            # Extract __NEXT_DATA__ JSON
            match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
                resp.text
            )
            if not match:
                return (None, None)

            data = json.loads(match.group(1))
            page_props = data.get('props', {}).get('pageProps', {})
            averages = page_props.get('averages', [])

            if not averages:
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
            return (None, None)

    def enrich_jobs(self, jobs: list) -> int:
        """
        Enrich jobs with salary data from levels.fyi.
        Only enriches jobs that don't already have salary data.

        Returns count of enriched jobs.
        """
        enriched = 0

        for job in jobs:
            # Skip if already has salary
            if job.salary_min or job.salary_max:
                continue

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

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
        "capital one": "associate",
        "goldman sachs": "analyst",
        "citadel": "l3",
        "two sigma": "l3",
        "jane street": "junior-trader",
        "openai": "l3",
        "anthropic": "l3",
        "spacex": "l1",
        "tesla": "l2",
        "waymo": "l3",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def _slugify(self, name: str) -> str:
        """Convert company name to URL slug"""
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    @lru_cache(maxsize=500)
    def get_salary(self, company: str, title: str = "software engineer",
                   location: str = None) -> Tuple[Optional[int], Optional[int]]:
        """
        Get salary range for a company/title/location combination.

        Returns (min_salary, max_salary) or (None, None) if not found.
        """
        company_slug = self._slugify(company)

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

            # Get salary from samples filtered by location if specified
            samples = entry_data.get('samples', [])

            if location and samples:
                # Filter by location
                location_lower = location.lower()
                filtered = [s for s in samples if location_lower in s.get('location', '').lower()]
                if filtered:
                    samples = filtered

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

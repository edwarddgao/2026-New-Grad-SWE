"""
Levels.fyi scraper for new grad salary data
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('aggregator.levels_scraper')

# Path to company config file (relative to this module)
CONFIG_FILE = Path(__file__).parent / "company_config.json"


def _load_company_config() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Load company aliases and entry levels from config file.

    Returns:
        Tuple of (aliases_dict, entry_levels_dict)
    """
    aliases = {}
    entry_levels = {}

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                aliases = data.get('aliases', {})
                entry_levels = data.get('entry_levels', {})
                logger.debug(f"  [Config] Loaded {len(aliases)} aliases, {len(entry_levels)} entry levels")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"  [Config] Error loading {CONFIG_FILE}: {e}")
    else:
        logger.warning(f"  [Config] Config file not found: {CONFIG_FILE}")

    return aliases, entry_levels


# Load config at module import time
_COMPANY_ALIASES, _ENTRY_LEVELS = _load_company_config()


class LevelsScraper:
    """Scrape salary data from levels.fyi"""

    # Use the software-engineer specific URL for better level breakdown
    BASE_URL = "https://www.levels.fyi/companies/{company}/salaries/software-engineer"

    # Maximum years of experience to consider as "new grad"
    MAX_NEW_GRAD_YOE = 2

    # Company name aliases loaded from config file (job listing name -> levels.fyi slug)
    COMPANY_ALIASES = _COMPANY_ALIASES

    # Entry level mappings loaded from config file (company slug -> entry-level title)
    ENTRY_LEVELS = _ENTRY_LEVELS

    CACHE_FILE = ".levels_salary_cache.json"
    # Different expiry times for different failure reasons
    EXPIRY_DAYS = {
        "404": 30,           # Company page doesn't exist - wait longer
        "no_swe_data": 14,   # Company exists but no SWE salary data
        "no_entry_level": 7, # Has SWE data but no entry-level samples
    }

    # Common entry-level patterns that should be recognized regardless of company-specific slugs
    ENTRY_LEVEL_PATTERNS = {
        # Explicit entry-level titles
        'new-grad', 'newgrad', 'entry-level', 'entry', 'junior', 'jr',
        'associate', 'graduate', 'grad',
        # SWE level 1 variants
        'software-engineer-i', 'software-engineer-1', 'software-engineer-one',
        'swe-i', 'swe-1', 'swe1', 'swe-one',
        'sde-i', 'sde-1', 'sde1', 'sde-one',
        'se-i', 'se-1', 'se1',
        # Generic level numbers (used by Meta, Google, Uber, etc.)
        'l1', 'l2', 'l3',
        'e1', 'e2', 'e3',
        't1', 't2', 't3',
        # Apple style
        'ic1', 'ic2', 'ice1', 'ice2',
        # P-levels (some companies)
        'p1', 'p2',
        # Roman numerals
        'i', 'ii',
        # Microsoft levels
        '59', '60', '61',
    }

    # Suffixes that indicate entry-level when combined with a base slug
    ENTRY_LEVEL_SUFFIXES = ('-i', '-1', '-one', '1', '-I')

    # Maximum sample count for fallback to median.commonRange
    MAX_FALLBACK_SAMPLE_COUNT = 5

    def __init__(self):
        self.session = requests.Session()
        # Full browser headers required - levels.fyi returns 405 with incomplete headers
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })
        # Cache for companies not found on levels.fyi (with timestamps and reasons)
        # Format: {company_slug: {"date": "YYYY-MM-DD", "reason": "404|no_data|insufficient"}}
        self._not_found_cache = {}
        # Cache for successful salary lookups
        self._salary_cache = {}
        # Load cache from file
        self._load_cache()

    def _load_cache(self):
        """Load salary cache from file, expiring old not_found entries based on reason."""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self._salary_cache = {k: tuple(v) for k, v in data.get('found', {}).items()}

                    # Load not_found entries, expiring old ones
                    not_found_data = data.get('not_found', {})
                    today = datetime.now()
                    expired_count = 0
                    for company, info in not_found_data.items():
                        if not isinstance(info, dict):
                            continue
                        date_str = info.get("date", "")
                        reason = info.get("reason", "no_swe_data")
                        expiry_days = self.EXPIRY_DAYS.get(reason, 7)
                        cutoff = (today - timedelta(days=expiry_days)).strftime("%Y-%m-%d")
                        if date_str >= cutoff:
                            self._not_found_cache[company] = info
                        else:
                            expired_count += 1
                    if expired_count > 0:
                        logger.debug(f"  [Cache] Expired {expired_count} not-found entries")

                    logger.info(f"  [Cache] Loaded {len(self._salary_cache)} cached salaries, {len(self._not_found_cache)} not-found")
            except (json.JSONDecodeError, IOError, KeyError) as e:
                logger.error(f"  [Cache] Error loading cache: {e}")

    def _add_not_found(self, company_slug: str, reason: str):
        """Add a company to the not_found cache with reason."""
        self._not_found_cache[company_slug] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reason": reason
        }

    def _save_cache(self):
        """Save salary cache to file"""
        try:
            data = {
                'found': {k: list(v) for k, v in self._salary_cache.items()},
                'not_found': self._not_found_cache
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(data, f)
        except (IOError, OSError) as e:
            logger.error(f"  [Cache] Error saving cache: {e}")

    def _is_entry_level(self, level: str, entry_level_slugs: set) -> bool:
        """
        Check if a level string represents an entry-level position.

        Uses multiple matching strategies:
        1. Exact match against entry_level_slugs from levels.fyi
        2. Match against hardcoded ENTRY_LEVEL_PATTERNS
        3. Prefix matching (e.g., 'sde-i' matches if 'sde' is in entry_level_slugs)
        4. Suffix matching (e.g., anything ending in '-i' or '-1')

        Args:
            level: The level string from averages data (e.g., 'sde-i', 'l3', 'p2')
            entry_level_slugs: Set of entry-level slugs from the company's levels data

        Returns:
            True if this level should be considered entry-level
        """
        level_lower = level.lower().strip()

        # 1. Exact match against company-specific entry-level slugs
        if level_lower in entry_level_slugs:
            return True

        # 2. Match against hardcoded entry-level patterns
        if level_lower in self.ENTRY_LEVEL_PATTERNS:
            return True

        # 3. Prefix matching: 'sde-i' matches if 'sde' is in entry_level_slugs
        for slug in entry_level_slugs:
            # Check if level starts with the slug followed by a separator or number
            if level_lower.startswith(slug + '-') or level_lower.startswith(slug + '1'):
                # Make sure it's entry-level suffix, not senior (e.g., sde-iii)
                remainder = level_lower[len(slug):]
                if remainder in ('-i', '-1', '-one', '1', '-I'):
                    return True
            # Also check if level is slug + single digit 1
            if level_lower == slug + '1':
                return True

        # 4. Check for entry-level suffixes on common base patterns
        # e.g., 'software-engineer-i' should match even without explicit slug
        for suffix in self.ENTRY_LEVEL_SUFFIXES:
            if level_lower.endswith(suffix):
                # Extract base and verify it's not a senior level (iii, iv, 3, 4, etc.)
                base = level_lower[:-len(suffix)]
                # Skip if this looks like a senior level (roman numerals ii+, numbers 3+)
                if suffix == '-i' and not base.endswith('i'):  # Avoid matching '-ii', '-iii'
                    return True
                if suffix == '-1' and not any(base.endswith(str(n)) for n in range(2, 10)):
                    return True
                if suffix == '1' and base and not base[-1].isdigit():
                    return True

        return False

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

    def get_salary(self, company: str, title: str = "software engineer",
                   location: str = None) -> Tuple[Optional[int], Optional[int]]:
        """
        Get salary range for a company/title/location combination.

        Returns (min_salary, max_salary) or (None, None) if not found.
        """
        company_slug = self._normalize_company(company)

        # Check not-found cache
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
        """Fetch salary from levels.fyi with rate limiting and retry logic."""
        url = self.BASE_URL.format(company=company_slug)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # Rate limiting - 0.5s base delay to avoid 405/429 errors
                time.sleep(0.5)

                resp = self.session.get(url, timeout=10)

                # Handle rate limiting with exponential backoff
                # Note: levels.fyi returns 405 when rate limited (not just 429)
                if resp.status_code in (405, 429, 503):
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2.0  # 2s, 4s, 8s backoff
                        logger.warning(f"    [Levels] {company_slug}: {resp.status_code}, retry {attempt+1}")
                        time.sleep(wait_time)
                        continue
                    logger.warning(f"    [Levels] {company_slug}: {resp.status_code} after {max_retries} retries")
                    return (None, None)

                # Company not found - cache for 30 days
                if resp.status_code == 404:
                    self._add_not_found(company_slug, "404")
                    return (None, None)

                if resp.status_code != 200:
                    logger.warning(f"    [Levels] {company_slug}: HTTP {resp.status_code}")
                    return (None, None)

                # Extract __NEXT_DATA__ JSON
                match = re.search(
                    r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>',
                    resp.text
                )
                if not match:
                    self._add_not_found(company_slug, "no_swe_data")
                    return (None, None)

                data = json.loads(match.group(1))
                page_props = data.get('props', {}).get('pageProps', {})

                # Get all samples from averages
                averages = page_props.get('averages', [])
                median = page_props.get('median') or {}

                # If averages is empty, try fallback to median for small sample sizes
                if not averages:
                    # Fallback: use median.commonRange for small sample sizes
                    sample_count = median.get('count', 0)
                    common_start = median.get('commonRangeStart', 0)
                    common_end = median.get('commonRangeEnd', 0)

                    if (sample_count > 0 and
                        sample_count <= self.MAX_FALLBACK_SAMPLE_COUNT and
                        common_start > 0):
                        return (common_start, common_end)

                    self._add_not_found(company_slug, "no_swe_data")
                    return (None, None)

                # Get levels info to find entry level (order: 0 = entry)
                levels_info = page_props.get('levels', {})
                levels_list = levels_info.get('levels', [])

                # Find entry level title slugs (order 0 is entry level)
                entry_level_slugs = set()
                for level in levels_list:
                    if level.get('order') == 0:
                        entry_level_slugs.update(slug.lower() for slug in level.get('titleSlugs', []))

                # Also check our manual ENTRY_LEVELS mapping
                manual_entry = self.ENTRY_LEVELS.get(company_slug)
                if manual_entry:
                    entry_level_slugs.add(manual_entry.lower())

                # Collect new grad compensation from entry-level samples only
                new_grad_comps = []

                for avg in averages:
                    level = avg.get('level', '')
                    samples = avg.get('samples', [])

                    # Check if this level is entry level using fuzzy matching
                    if not self._is_entry_level(level, entry_level_slugs):
                        continue

                    for sample in samples:
                        yoe = sample.get('yearsOfExperience')
                        tc = sample.get('totalCompensation')

                        if tc is None:
                            continue

                        # Additional filter: only include samples with low YoE for entry level
                        if yoe is None or yoe <= self.MAX_NEW_GRAD_YOE:
                            new_grad_comps.append(tc)

                # No entry-level samples found
                if not new_grad_comps:
                    self._add_not_found(company_slug, "no_entry_level")
                    return (None, None)

                # Calculate salary range
                new_grad_comps.sort()
                n = len(new_grad_comps)
                if n == 1:
                    return (new_grad_comps[0], new_grad_comps[0])
                elif n == 2:
                    return (new_grad_comps[0], new_grad_comps[1])
                else:
                    # 25th and 75th percentile
                    return (new_grad_comps[n // 4], new_grad_comps[3 * n // 4])

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"    [Levels] {company_slug}: {type(e).__name__}, retry {attempt+1}")
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f"    [Levels] {company_slug}: {type(e).__name__} after {max_retries} retries: {e}")
                return (None, None)

        return (None, None)

    def enrich_jobs(self, jobs: List) -> int:
        """
        Enrich jobs with salary data from levels.fyi.
        Only enriches jobs that don't already have salary data.

        Args:
            jobs: List of Job objects to enrich with salary data.

        Returns:
            Count of enriched jobs.
        """
        enriched = 0
        total = len(jobs)

        # Track unique companies to avoid redundant lookups
        seen_companies = set()

        for i, job in enumerate(jobs):
            # Progress output every 500 jobs
            if i > 0 and i % 500 == 0:
                logger.info(f"    Enriching... {i}/{total} jobs ({enriched} enriched)")

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
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # Test the scraper
    scraper = LevelsScraper()

    test_companies = ["google", "meta", "stripe", "openai", "jane street"]

    for company in test_companies:
        min_sal, max_sal = scraper.get_salary(company)
        if min_sal and max_sal:
            logger.info(f"{company}: ${min_sal:,} - ${max_sal:,}")
        else:
            logger.info(f"{company}: No data")

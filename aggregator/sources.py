"""
Job Aggregator - Data Sources Module
Pulls job listings from multiple free sources
"""

import html
import json
import os
import re
import requests
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .filters import filter_jobs
from .levels_scraper import get_scraper
from .utils import slugify

@dataclass
class Job:
    """Unified job listing format"""
    id: str
    title: str
    company: str
    company_slug: str
    location: str
    url: str
    source: str
    date_posted: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    sponsorship: Optional[str] = None
    remote: Optional[bool] = None
    description: Optional[str] = None
    experience_level: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class SimplifySource:
    """Pull jobs from SimplifyJobs GitHub repos"""

    SOURCES = [
        {
            "name": "New-Grad-Positions",
            "url": "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json",
            "type": "new_grad"
        }
    ]

    def fetch(self) -> List[Job]:
        jobs = []
        for source in self.SOURCES:
            try:
                resp = requests.get(source["url"], timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data:
                        if not item.get("active", True):
                            continue
                        job = Job(
                            id=f"simplify_{item.get('id', '')}",
                            title=item.get("title", ""),
                            company=item.get("company_name", ""),
                            company_slug=slugify(item.get("company_name", "")),
                            location=", ".join(item.get("locations", [])),
                            url=item.get("url", ""),
                            source=f"simplify_{source['type']}",
                            date_posted=self._format_date(item.get("date_posted")),
                            sponsorship=item.get("sponsorship"),
                            experience_level=source["type"]
                        )
                        jobs.append(job)
                    print(f"  [Simplify] {source['name']}: {len(data)} jobs")
            except Exception as e:
                print(f"  [Simplify] {source['name']}: Error - {e}")
        return jobs

    def _format_date(self, timestamp: int) -> Optional[str]:
        """Convert Unix timestamp to YYYY-MM-DD date string."""
        if timestamp:
            try:
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            except (ValueError, OSError, OverflowError):
                pass
        return None


class SpeedyApplySource:
    """Pull jobs from speedyapply/2026-SWE-College-Jobs GitHub repo"""

    URL = "https://raw.githubusercontent.com/speedyapply/2026-SWE-College-Jobs/main/NEW_GRAD_USA.md"

    def fetch(self) -> List[Job]:
        jobs = []
        try:
            resp = requests.get(self.URL, timeout=60)
            if resp.status_code == 200:
                # Parse markdown table with HTML links
                # Format: | <a href="company_url"><strong>Company</strong></a> | Position | Location | Salary | <a href="job_url">...</a> | Age |
                # Or without salary: | <a href="company_url"><strong>Company</strong></a> | Position | Location | <a href="job_url">...</a> | Age |

                # Pattern for rows with salary column
                pattern_with_salary = re.compile(
                    r'\|\s*<a href="[^"]*"><strong>([^<]+)</strong></a>\s*\|\s*'  # Company
                    r'([^|]+)\|\s*'  # Position
                    r'([^|]+)\|\s*'  # Location
                    r'(\$[^|]+)\|\s*'  # Salary (starts with $)
                    r'<a href="([^"]+)"[^|]+\|\s*'  # Job URL
                    r'(\d+)d\s*\|'  # Age in days
                )

                # Pattern for rows without salary column
                pattern_no_salary = re.compile(
                    r'\|\s*<a href="[^"]*"><strong>([^<]+)</strong></a>\s*\|\s*'  # Company
                    r'([^|]+)\|\s*'  # Position
                    r'([^|]+)\|\s*'  # Location
                    r'<a href="([^"]+)"[^|]+\|\s*'  # Job URL
                    r'(\d+)d\s*\|'  # Age in days
                )

                seen_urls = set()

                # First try pattern with salary
                for match in pattern_with_salary.finditer(resp.text):
                    company, title, location, salary, job_url, age_days = match.groups()

                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    # Parse salary
                    salary_min, salary_max = self._parse_salary(salary.strip())

                    job = Job(
                        id=f"speedyapply_{hash(job_url) % 10**8}",
                        title=title.strip(),
                        company=company.strip(),
                        company_slug=slugify(company),
                        location=location.strip(),
                        url=job_url,
                        source="speedyapply",
                        date_posted=self._parse_age(int(age_days)),
                        salary_min=salary_min,
                        salary_max=salary_max,
                        experience_level="new_grad"
                    )
                    jobs.append(job)

                # Then try pattern without salary for remaining rows
                for match in pattern_no_salary.finditer(resp.text):
                    company, title, location, job_url, age_days = match.groups()

                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    job = Job(
                        id=f"speedyapply_{hash(job_url) % 10**8}",
                        title=title.strip(),
                        company=company.strip(),
                        company_slug=slugify(company),
                        location=location.strip(),
                        url=job_url,
                        source="speedyapply",
                        date_posted=self._parse_age(int(age_days)),
                        experience_level="new_grad"
                    )
                    jobs.append(job)

                print(f"  [SpeedyApply] Parsed: {len(jobs)} jobs")
        except Exception as e:
            print(f"  [SpeedyApply] Error: {e}")
        return jobs

    def _parse_age(self, days: int) -> Optional[str]:
        """Convert age in days to YYYY-MM-DD date string."""
        try:
            return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return None

    def _parse_salary(self, salary_str: str) -> tuple:
        """Parse salary string like '$172k/yr' or '$62/hr' to (min, max) integers."""
        if not salary_str:
            return None, None
        try:
            # Remove $ and whitespace
            salary_str = salary_str.replace('$', '').replace(',', '').strip()

            # Handle hourly rate (convert to annual assuming 2080 hours/year)
            if '/hr' in salary_str:
                hourly = float(salary_str.replace('/hr', '').replace('k', ''))
                if 'k' in salary_str.replace('/hr', ''):
                    hourly *= 1000
                annual = int(hourly * 2080)
                return annual, annual

            # Handle annual salary
            if '/yr' in salary_str:
                salary_str = salary_str.replace('/yr', '')

            if 'k' in salary_str.lower():
                val = float(salary_str.lower().replace('k', '')) * 1000
                return int(val), int(val)

            val = float(salary_str)
            return int(val), int(val)
        except (ValueError, TypeError):
            return None, None


class BuiltInSource:
    """Pull jobs from Built In (NYC, SF, etc.)"""

    BASE_URL = "https://builtin.com"

    # City-specific paths
    CITIES = {
        "nyc": "/jobs/new-york/dev-engineering/entry-level",
        "sf": "/jobs/san-francisco/dev-engineering/entry-level",
        "la": "/jobs/los-angeles/dev-engineering/entry-level",
    }

    def __init__(self):
        self.available = True
        try:
            from bs4 import BeautifulSoup
            self.BeautifulSoup = BeautifulSoup
        except ImportError:
            print("  [BuiltIn] BeautifulSoup not installed. Run: pip install beautifulsoup4")
            self.available = False

    def fetch(self, cities: List[str] = None, max_pages: int = 10, cached_jobs: Dict[str, dict] = None) -> List[Job]:
        """
        Fetch jobs from Built In.

        Args:
            cities: List of city codes to scrape (nyc, sf, la)
            max_pages: Maximum pages to scrape per city
            cached_jobs: Dictionary of url -> job_dict for preserving original posted dates
        """
        if not self.available:
            return []

        if cities is None:
            cities = ["nyc"]

        if cached_jobs is None:
            cached_jobs = {}

        jobs = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        for city in cities:
            if city not in self.CITIES:
                continue

            seen_ids = set()
            city_jobs = 0

            # Fetch multiple pages
            for page in range(1, max_pages + 1):
                try:
                    url = f"{self.BASE_URL}{self.CITIES[city]}"
                    if page > 1:
                        url += f"?page={page}"

                    resp = requests.get(url, headers=headers, timeout=60)

                    if resp.status_code != 200:
                        break

                    soup = self.BeautifulSoup(resp.text, 'html.parser')

                    # Find job cards by data-id attribute
                    job_cards = soup.find_all('div', {'data-id': 'job-card'})

                    page_jobs = 0
                    for card in job_cards:
                        # Get job ID from card id attribute (e.g., "job-card-8019048")
                        card_id = card.get('id', '')
                        job_id_match = re.search(r'job-card-(\d+)', card_id)
                        if not job_id_match:
                            continue

                        job_id = job_id_match.group(1)
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        # Get job title from data-id="job-card-title"
                        title_link = card.find('a', {'data-id': 'job-card-title'})
                        if not title_link:
                            continue

                        title = title_link.get_text(strip=True)
                        job_url = title_link.get('href', '')
                        if not title or not job_url:
                            continue

                        # Get company from data-id="company-title"
                        company_link = card.find('a', {'data-id': 'company-title'})
                        company = "Unknown"
                        if company_link:
                            company_span = company_link.find('span')
                            if company_span:
                                company = company_span.get_text(strip=True)
                            else:
                                company = company_link.get_text(strip=True)

                        # Get location
                        location = self._extract_location(card, city)

                        # Build full URL for cache lookup
                        full_url = f"{self.BASE_URL}{job_url}"

                        # Use cached posted date if available, otherwise calculate from relative time
                        # This ensures the posted date stays stable across scrapes
                        cached_job = cached_jobs.get(full_url)
                        if cached_job and cached_job.get('date_posted'):
                            date_posted = cached_job['date_posted']
                        else:
                            # Only calculate date for NEW jobs we haven't seen before
                            date_posted = self._extract_date(card)

                        job = Job(
                            id=f"builtin_{job_id}",
                            title=title,
                            company=company,
                            company_slug=slugify(company),
                            location=location,
                            url=full_url,
                            source=f"builtin_{city}",
                            date_posted=date_posted,
                            experience_level="entry_level"
                        )
                        jobs.append(job)
                        page_jobs += 1
                        city_jobs += 1

                    # Stop if no new jobs found on this page
                    if page_jobs == 0:
                        break

                except Exception as e:
                    print(f"  [BuiltIn] {city.upper()} page {page} Error: {e}")
                    break

            print(f"  [BuiltIn] {city.upper()}: {city_jobs} jobs")

        return jobs

    def _extract_date(self, card) -> Optional[str]:
        """Extract posting date from job card"""
        # Look for text containing "Ago" or "Yesterday"
        text = card.get_text()
        today = datetime.now()

        # Match patterns like "7 Days Ago", "Reposted 3 Days Ago", "Yesterday", "29 Minutes Ago"
        if "yesterday" in text.lower():
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")

        days_match = re.search(r'(\d+)\s*days?\s*ago', text, re.IGNORECASE)
        if days_match:
            days = int(days_match.group(1))
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")

        # Hours or minutes ago = today
        if re.search(r'\d+\s*(hours?|minutes?)\s*ago', text, re.IGNORECASE):
            return today.strftime("%Y-%m-%d")

        return None

    def _extract_location(self, card, default_city: str) -> str:
        """Extract location from job card"""
        city_map = {"nyc": "New York, NY", "sf": "San Francisco, CA", "la": "Los Angeles, CA"}

        # Look for location text after fa-location-dot icon
        loc_icon = card.find('i', class_=re.compile(r'fa-location-dot'))
        if loc_icon:
            # Get text from next sibling or parent
            parent = loc_icon.parent
            if parent:
                next_span = parent.find_next_sibling('span') or parent.find('span')
                if next_span:
                    loc_text = next_span.get_text(strip=True)
                    if loc_text:
                        # Check if remote
                        if "remote" in card.get_text().lower():
                            return f"Remote, {loc_text}"
                        return loc_text

        # Fallback to default city
        return city_map.get(default_city, "US")


class HNHiringSource:
    """Pull jobs from Hacker News 'Who is hiring?' threads"""

    HN_API = "https://hacker-news.firebaseio.com/v0"

    # Monthly thread IDs (updated manually or auto-discovered)
    THREAD_IDS = {
        "2025-01": 42575537,  # January 2025
    }

    def __init__(self):
        self.available = True

    def fetch(self, max_jobs: int = 100) -> List[Job]:
        """Fetch jobs from the most recent Who is Hiring thread"""
        jobs = []

        # Get the most recent thread
        thread_id = self._get_latest_thread_id()
        if not thread_id:
            print("  [HN] Could not find Who is Hiring thread")
            return []

        try:
            # Fetch thread to get comment IDs
            resp = requests.get(f"{self.HN_API}/item/{thread_id}.json", timeout=30)
            if resp.status_code != 200:
                return []

            thread = resp.json()
            kids = thread.get("kids", [])[:max_jobs]  # Limit to first N comments

            # Fetch each job posting comment
            for kid_id in kids:
                try:
                    comment_resp = requests.get(f"{self.HN_API}/item/{kid_id}.json", timeout=10)
                    if comment_resp.status_code != 200:
                        continue

                    comment = comment_resp.json()
                    if not comment or comment.get("deleted") or not comment.get("text"):
                        continue

                    # Parse the job posting
                    job = self._parse_job(comment)
                    if job:
                        jobs.append(job)

                except Exception:
                    continue

            print(f"  [HN] Who is Hiring: {len(jobs)} jobs")

        except Exception as e:
            print(f"  [HN] Error: {e}")

        return jobs

    def _get_latest_thread_id(self) -> Optional[int]:
        """Get the most recent Who is Hiring thread ID"""
        # Use known thread ID for current month
        current = datetime.now().strftime("%Y-%m")
        if current in self.THREAD_IDS:
            return self.THREAD_IDS[current]

        # Fallback to most recent known
        if self.THREAD_IDS:
            return list(self.THREAD_IDS.values())[-1]

        return None

    def _parse_job(self, comment: dict) -> Optional[Job]:
        """Parse a job posting from HN comment format"""
        text = comment.get("text", "")
        if not text:
            return None

        # Unescape HTML entities
        text = html.unescape(text)

        # Format is typically: Company | Role | Location | REMOTE/ONSITE | URL
        # First line usually has the structured info
        first_line = text.split("<p>")[0].strip()

        # Split by pipe
        parts = [p.strip() for p in first_line.split("|")]
        if len(parts) < 2:
            return None

        company = self._strip_html(parts[0]) if parts else "Unknown"
        title = self._strip_html(parts[1]) if len(parts) > 1 else "Software Engineer"
        location = self._strip_html(parts[2]) if len(parts) > 2 else "Remote"

        # Extract URL from text
        url_match = re.search(r'href="([^"]+)"', text)
        url = url_match.group(1) if url_match else f"https://news.ycombinator.com/item?id={comment['id']}"

        # Check for remote
        remote = "remote" in text.lower()

        # Get date from timestamp
        timestamp = comment.get("time")
        date_posted = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d") if timestamp else None

        return Job(
            id=f"hn_{comment['id']}",
            title=title,
            company=company,
            company_slug=slugify(company),
            location=location,
            url=url,
            source="hn_hiring",
            date_posted=date_posted,
            remote=remote,
            experience_level=None
        )

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        return re.sub(r'<[^>]+>', '', text).strip()


class JobSpySource:
    """Pull jobs from Indeed/LinkedIn via JobSpy"""

    def __init__(self):
        self.available = False
        try:
            from jobspy import scrape_jobs
            self.scrape_jobs = scrape_jobs
            self.available = True
        except ImportError:
            print("  [JobSpy] Not installed. Run: pip install python-jobspy")

    def fetch(self, site: str = "indeed", search_term: str = "software engineer new grad",
              location: str = "United States", results: int = 50, hours_old: int = 72,
              cached_jobs: Dict[str, dict] = None) -> List[Job]:
        """
        Fetch jobs from Indeed/LinkedIn/Glassdoor via JobSpy.

        Args:
            cached_jobs: Dictionary of url -> job_dict for preserving original posted dates
        """
        if not self.available:
            return []

        if cached_jobs is None:
            cached_jobs = {}

        jobs = []
        try:
            kwargs = {
                "site_name": [site],
                "search_term": search_term,
                "location": location,
                "results_wanted": results,
                "hours_old": hours_old,
            }
            if site == "indeed":
                kwargs["country_indeed"] = "USA"
            if site == "linkedin":
                kwargs["linkedin_fetch_description"] = True

            results_df = self.scrape_jobs(**kwargs)

            for _, row in results_df.iterrows():
                # Only include jobs with direct URLs (actual company postings)
                job_url_direct = row.get("job_url_direct", "")
                if not job_url_direct or str(job_url_direct).lower() in ('nan', 'none', ''):
                    continue  # Skip jobs without direct URLs
                job_url = str(job_url_direct).split('?')[0]  # Remove tracking params

                # Use cached posted date if available, otherwise parse from source
                # This ensures the posted date stays stable across scrapes
                cached_job = cached_jobs.get(job_url)
                if cached_job and cached_job.get('date_posted'):
                    parsed_date = cached_job['date_posted']
                else:
                    # Parse actual posted date from source - do NOT default to today
                    # if no date is available to avoid confusing scrape date with posted date
                    parsed_date = self._parse_date(row.get("date_posted"))

                job = Job(
                    id=f"{site}_{row.get('id', hash(job_url) % 10**8)}",
                    title=row.get("title", ""),
                    company=row.get("company", ""),
                    company_slug=slugify(row.get("company", "")),
                    location=row.get("location", ""),
                    url=job_url,
                    source=site,
                    date_posted=parsed_date,
                    salary_min=self._parse_salary(row.get("min_amount")),
                    salary_max=self._parse_salary(row.get("max_amount")),
                    remote=row.get("is_remote", False),
                    description=row.get("description", "")[:500] if row.get("description") else None,
                    experience_level=None  # Mixed levels in search results
                )
                jobs.append(job)
            print(f"  [{site.capitalize()}] Scraped: {len(jobs)} jobs")
        except Exception as e:
            print(f"  [{site.capitalize()}] Error: {e}")
        return jobs

    def _parse_salary(self, val) -> Optional[int]:
        """Parse salary value, handling NaN and various formats."""
        if val and not str(val).lower() == 'nan':
            try:
                return int(float(val))
            except (ValueError, TypeError):
                pass
        return None

    def _parse_date(self, val) -> Optional[str]:
        """Parse date from JobSpy, handling NaT and various formats."""
        if val is None:
            return None
        # Convert to string and check for invalid values
        val_str = str(val).strip()
        if not val_str or val_str.lower() in ('nat', 'nan', 'none', ''):
            return None
        # Try to extract YYYY-MM-DD format
        try:
            # If it's already in ISO format, take first 10 chars
            if len(val_str) >= 10 and val_str[4] == '-' and val_str[7] == '-':
                return val_str[:10]
            # Try parsing as datetime
            import pandas as pd
            if pd.notna(val):
                dt = pd.to_datetime(val)
                return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
        return None


class JobAggregator:
    """Main aggregator that pulls from all sources"""

    # Sources that need caching (ephemeral scraped data)
    SCRAPED_SOURCES = {"linkedin", "builtin_nyc", "builtin_sf", "builtin_la", "hn_hiring"}
    CACHE_FILE = ".scraped_jobs_cache.json"
    CACHE_EXPIRY_DAYS = 30  # Remove jobs older than this

    def __init__(self):
        self.sources = {
            "simplify": SimplifySource(),
            "speedyapply": SpeedyApplySource(),  # SpeedyApply 2026 SWE Jobs
            "builtin": BuiltInSource(),  # Built In NYC/SF/LA
            "hn": HNHiringSource(),  # HN Who's Hiring
            "jobspy": JobSpySource(),  # For LinkedIn
        }
        self.jobs: List[Job] = []
        self._job_cache: Dict[str, dict] = {}  # url -> job dict
        self._load_job_cache()

    def _load_job_cache(self):
        """Load cached scraped jobs from file"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self._job_cache = data.get('jobs', {})
                    print(f"  [JobCache] Loaded {len(self._job_cache)} cached jobs")
            except Exception as e:
                print(f"  [JobCache] Error loading cache: {e}")
                self._job_cache = {}

    def _save_job_cache(self):
        """Save scraped jobs to cache file"""
        try:
            # Remove expired jobs
            cutoff = (datetime.now() - timedelta(days=self.CACHE_EXPIRY_DAYS)).strftime("%Y-%m-%d")
            valid_jobs = {}
            expired_count = 0
            for url, job_dict in self._job_cache.items():
                # Keep jobs that have no date or are newer than cutoff
                job_date = job_dict.get('date_posted')
                if not job_date or job_date >= cutoff:
                    valid_jobs[url] = job_dict
                else:
                    expired_count += 1

            with open(self.CACHE_FILE, 'w') as f:
                json.dump({'jobs': valid_jobs, 'updated': datetime.now().isoformat()}, f, indent=2)
            if expired_count > 0:
                print(f"  [JobCache] Removed {expired_count} expired jobs (>{self.CACHE_EXPIRY_DAYS} days old)")
            print(f"  [JobCache] Saved {len(valid_jobs)} jobs to cache")
        except Exception as e:
            print(f"  [JobCache] Error saving cache: {e}")

    def _cache_jobs(self, jobs: List[Job]):
        """Add scraped jobs to cache (only jobs that pass the filter)"""
        from .filters import is_new_grad_swe
        for job in jobs:
            if job.source in self.SCRAPED_SOURCES:
                if is_new_grad_swe(job.title, job.source):
                    self._job_cache[job.url] = job.to_dict()

    def _get_cached_jobs(self) -> List[Job]:
        """Get all cached jobs as Job objects"""
        jobs = []
        for job_dict in self._job_cache.values():
            try:
                jobs.append(Job(**job_dict))
            except Exception:
                pass  # Skip invalid cached entries
        return jobs

    def fetch_all(self, include_linkedin: bool = False, linkedin_limit: int = 50,
                  include_builtin: bool = False, builtin_cities: List[str] = None,
                  include_hn: bool = False, hn_limit: int = 100,
                  skip_enrichment: bool = False) -> List[Job]:
        """Fetch jobs from all sources"""
        print("\n=== Fetching jobs from all sources ===\n")

        all_jobs = []

        # Simplify (always)
        all_jobs.extend(self.sources["simplify"].fetch())

        # SpeedyApply (always)
        all_jobs.extend(self.sources["speedyapply"].fetch())

        # Built In (optional)
        # Pass cached jobs to preserve original posted dates across scrapes
        if include_builtin and self.sources["builtin"].available:
            all_jobs.extend(self.sources["builtin"].fetch(
                cities=builtin_cities or ["nyc"],
                cached_jobs=self._job_cache
            ))

        # HN Who's Hiring (optional)
        if include_hn and self.sources["hn"].available:
            all_jobs.extend(self.sources["hn"].fetch(max_jobs=hn_limit))

        # LinkedIn (optional, uses JobSpy scraping)
        # Pass cached jobs to preserve original posted dates across scrapes
        if include_linkedin and self.sources["jobspy"].available:
            # Search "new grad" - NYC and CA
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="linkedin", location="New York, NY", results=linkedin_limit // 4,
                cached_jobs=self._job_cache
            ))
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="linkedin", location="California", results=linkedin_limit // 4,
                cached_jobs=self._job_cache
            ))
            # Search "entry level" - NYC and CA
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="linkedin", search_term="software engineer entry level",
                location="New York, NY", results=linkedin_limit // 4,
                cached_jobs=self._job_cache
            ))
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="linkedin", search_term="software engineer entry level",
                location="California", results=linkedin_limit // 4,
                cached_jobs=self._job_cache
            ))

        # Cache newly scraped jobs before deduplication
        scraped_jobs = [j for j in all_jobs if j.source in self.SCRAPED_SOURCES]
        if scraped_jobs:
            self._cache_jobs(scraped_jobs)
            print(f"  [JobCache] Cached {len(scraped_jobs)} freshly scraped jobs")

        # Add previously cached jobs (will be deduped below)
        cached_jobs = self._get_cached_jobs()
        if cached_jobs:
            all_jobs.extend(cached_jobs)
            print(f"  [JobCache] Added {len(cached_jobs)} jobs from cache")

        # Deduplicate by URL (normalize URLs first to catch duplicates with query params)
        def normalize_url_for_dedup(url: str) -> str:
            """Normalize URL by removing query parameters, fragments, and standardizing hosts."""
            if not url:
                return ""
            # Remove query string and fragment
            url = url.split('?')[0].split('#')[0]
            # Remove trailing slashes
            url = url.rstrip('/')
            # Lowercase for consistency
            url = url.lower()
            # Normalize greenhouse.io URL variations
            url = url.replace('job-boards.greenhouse.io', 'boards.greenhouse.io')
            return url

        seen_urls = set()
        deduped_jobs = []
        for job in all_jobs:
            normalized_url = normalize_url_for_dedup(job.url)
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                deduped_jobs.append(job)

        dedup_count = len(all_jobs) - len(deduped_jobs)
        if dedup_count > 0:
            print(f"  [Deduped] Removed {dedup_count} duplicate jobs (same URL)")

        # Filter non-curated sources to only keep new grad/entry level SWE roles
        # This runs BEFORE enrichment to avoid wasting levels.fyi lookups on
        # non-SWE companies (e.g., civil engineering firms like Stantec)
        filtered_jobs, filtered_count = filter_jobs(deduped_jobs)
        if filtered_count > 0:
            print(f"  [Filtered] Removed {filtered_count} non-SWE/senior roles from non-curated sources")

        # Enrich with levels.fyi salary data
        if not skip_enrichment:
            scraper = get_scraper()
            enriched = scraper.enrich_jobs(filtered_jobs)
            if enriched > 0:
                print(f"  [Salary] Enriched {enriched} jobs with levels.fyi data")
        else:
            print(f"  [Salary] Enrichment skipped")

        self.jobs = filtered_jobs

        # Save job cache for persistence between runs
        self._save_job_cache()

        print(f"\n=== Total unique jobs: {len(filtered_jobs)} ===")
        return filtered_jobs

    def filter_location(self, regions: List[str] = None) -> List[Job]:
        """Filter jobs by location (NYC, California, etc.)"""
        if regions is None:
            regions = ["nyc", "california"]

        # Location patterns for each region
        location_patterns = {
            "nyc": [
                "new york", "nyc", "brooklyn, ny", "manhattan", "queens, ny",
                "bronx, ny", "staten island", ", ny,", ", ny"
            ],
            "california": [
                "california", ", ca,", ", ca ", ", ca", "san francisco", "los angeles",
                "san diego", "san jose", "oakland, ca", "palo alto",
                "mountain view", "sunnyvale", "cupertino", "menlo park",
                "redwood city", "santa clara", "irvine, ca", "pasadena, ca",
                "berkeley, ca", "fremont, ca", "sacramento", "santa monica",
                "venice, ca", "culver city", "burbank, ca", "glendale, ca"
            ],
            "remote": ["remote"]
        }

        # Build list of patterns to match
        patterns = []
        for region in regions:
            region_lower = region.lower()
            if region_lower in location_patterns:
                patterns.extend(location_patterns[region_lower])
            else:
                patterns.append(region_lower)

        # Exclusion patterns (to avoid Canada, etc.)
        exclude_patterns = ["canada", "ontario", "quebec", "british columbia", "alberta"]

        filtered = []
        for job in self.jobs:
            loc_lower = job.location.lower()
            # Must match a pattern AND not match any exclusion
            if any(pattern in loc_lower for pattern in patterns):
                if not any(excl in loc_lower for excl in exclude_patterns):
                    filtered.append(job)

        self.jobs = filtered
        print(f"  [Location] {len(filtered)} jobs in {', '.join(regions)}")
        return filtered

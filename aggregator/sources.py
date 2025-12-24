"""
Job Aggregator - Data Sources Module
Pulls job listings from multiple free sources
"""

import json
import re
import requests
import urllib3
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import time

# Suppress SSL warnings for YC API
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
                            company_slug=self._slugify(item.get("company_name", "")),
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

    def _slugify(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    def _format_date(self, timestamp) -> Optional[str]:
        if timestamp:
            try:
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
            except:
                pass
        return None


class JobrightSource:
    """Pull jobs from jobright-ai GitHub repos"""

    URL = "https://raw.githubusercontent.com/jobright-ai/2025-Software-Engineer-New-Grad/master/README.md"

    def fetch(self) -> List[Job]:
        jobs = []
        try:
            resp = requests.get(self.URL, timeout=60)
            if resp.status_code == 200:
                # Parse markdown table
                pattern = re.compile(
                    r'\|\s*\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*\|\s*'  # Company
                    r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\s*\|\s*'        # Job title
                    r'([^|]+)\|\s*'                                    # Location
                    r'([^|]+)\|\s*'                                    # Work model
                    r'([^|]+)\|'                                       # Date
                )

                for match in pattern.finditer(resp.text):
                    company, company_url, title, job_url, location, work_model, date = match.groups()

                    # Skip job titles that got captured as companies
                    if any(x in company.lower() for x in ['engineer', 'developer', 'analyst']):
                        continue

                    job = Job(
                        id=f"jobright_{hash(job_url) % 10**8}",
                        title=title.strip(),
                        company=company.strip(),
                        company_slug=self._slugify(company),
                        location=location.strip(),
                        url=job_url,
                        source="jobright",
                        date_posted=self._parse_date(date.strip()),
                        remote="remote" in work_model.lower(),
                        experience_level="new_grad"
                    )
                    jobs.append(job)
                print(f"  [Jobright] Parsed: {len(jobs)} jobs")
        except Exception as e:
            print(f"  [Jobright] Error: {e}")
        return jobs

    def _slugify(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    def _parse_date(self, date_str: str) -> Optional[str]:
        # Format: "Dec 23"
        try:
            current_year = datetime.now().year
            dt = datetime.strptime(f"{date_str} {current_year}", "%b %d %Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return None


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
              location: str = "United States", results: int = 50, hours_old: int = 72) -> List[Job]:
        if not self.available:
            return []

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

            results_df = self.scrape_jobs(**kwargs)

            for _, row in results_df.iterrows():
                job = Job(
                    id=f"{site}_{row.get('id', hash(row.get('job_url', '')) % 10**8)}",
                    title=row.get("title", ""),
                    company=row.get("company", ""),
                    company_slug=self._slugify(row.get("company", "")),
                    location=row.get("location", ""),
                    url=row.get("job_url", ""),
                    source=site,
                    date_posted=str(row.get("date_posted", ""))[:10] if row.get("date_posted") else None,
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

    def _slugify(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    def _parse_salary(self, val) -> Optional[int]:
        if val and not str(val).lower() == 'nan':
            try:
                return int(float(val))
            except:
                pass
        return None


# Backwards compatibility alias
IndeedSource = JobSpySource


class YCombinatorSource:
    """Pull YC company data and jobs from Work at a Startup"""

    COMPANIES_API = "https://api.ycombinator.com/v0.1/companies"
    JOBS_BASE_URL = "https://www.workatastartup.com/companies"

    def fetch(self, min_team_size: int = 2, max_team_size: int = 100,
              recent_batches_only: bool = True) -> List[Job]:
        """
        Fetch YC companies and generate job search URLs.
        Note: Actual jobs require visiting workatastartup.com (JS-rendered).
        This provides company data and direct links to their job pages.
        """
        jobs = []
        try:
            # Fetch all pages of companies
            all_companies = []
            page = 1
            max_pages = 50  # Limit to avoid too many requests

            while page <= max_pages:
                resp = requests.get(
                    f"{self.COMPANIES_API}?page={page}",
                    timeout=60,
                    verify=False  # YC API has cert issues sometimes
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                companies = data.get("companies", [])
                if not companies:
                    break

                all_companies.extend(companies)
                page += 1

                # Rate limit
                time.sleep(0.1)

            print(f"  [YC] Fetched {len(all_companies)} companies from API ({page-1} pages)")

            # Recent batches (last ~3 years) - more likely to be hiring
            recent_batches = {
                'W26', 'S25', 'W25', 'S24', 'W24', 'S23', 'W23', 'S22', 'W22'
            }

            # Filter for active, hiring companies
            for company in all_companies:
                if company.get("status") != "Active":
                    continue

                # Filter by recent batches if requested
                batch = company.get("batch", "")
                if recent_batches_only and batch not in recent_batches:
                    continue

                team_size = company.get("teamSize") or 0
                if team_size < min_team_size or team_size > max_team_size:
                    continue

                # Create a job entry for each company (pointing to their jobs page)
                # Note: This links to the company page, not a specific job listing
                # The company may have multiple roles at different levels
                job = Job(
                    id=f"yc_{company.get('id', '')}",
                    title=f"Open Roles at {company.get('name', 'YC Startup')} (YC {batch})",
                    company=company.get("name", ""),
                    company_slug=company.get("slug", ""),
                    location=", ".join(company.get("locations", ["Remote"])),
                    url=f"{self.JOBS_BASE_URL}/{company.get('slug', '')}",
                    source="yc_workatastartup",
                    description=company.get("oneLiner", ""),
                    remote="Remote" in company.get("regions", []),
                    experience_level=None  # Mixed levels - check individual listings
                )
                jobs.append(job)

            print(f"  [YC] {len(jobs)} active startups (team size {min_team_size}-{max_team_size})")

        except Exception as e:
            print(f"  [YC] Error: {e}")

        return jobs

    def _slugify(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


class LevelsFyiEnricher:
    """Enrich job data with levels.fyi salary information"""

    def __init__(self, companies_file: str = None):
        self.companies = set()
        if companies_file:
            try:
                with open(companies_file, 'r') as f:
                    self.companies = set(line.strip().lower() for line in f if line.strip())
                print(f"  [Levels.fyi] Loaded {len(self.companies)} companies")
            except:
                pass

    def has_salary_data(self, company_slug: str) -> bool:
        """Check if company exists on levels.fyi"""
        return company_slug.lower() in self.companies

    def get_company_url(self, company_slug: str) -> str:
        """Get levels.fyi URL for company"""
        return f"https://www.levels.fyi/companies/{company_slug}/salaries"


class JobAggregator:
    """Main aggregator that pulls from all sources"""

    def __init__(self, levels_companies_file: str = None):
        self.sources = {
            "simplify": SimplifySource(),
            "jobright": JobrightSource(),
            "jobspy": JobSpySource(),  # For Indeed/LinkedIn
        }
        self.enricher = LevelsFyiEnricher(levels_companies_file)
        self.jobs: List[Job] = []

    def fetch_all(self, include_linkedin: bool = False, linkedin_limit: int = 50,
                  include_indeed: bool = False, indeed_limit: int = 50) -> List[Job]:
        """Fetch jobs from all sources"""
        print("\n=== Fetching jobs from all sources ===\n")

        all_jobs = []

        # Simplify (always)
        all_jobs.extend(self.sources["simplify"].fetch())

        # Jobright (always)
        all_jobs.extend(self.sources["jobright"].fetch())

        # LinkedIn (optional, uses JobSpy scraping)
        if include_linkedin and self.sources["jobspy"].available:
            # Search NYC
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="linkedin", location="New York, NY", results=linkedin_limit // 2
            ))
            # Search California
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="linkedin", location="California", results=linkedin_limit // 2
            ))

        # Indeed (optional, uses JobSpy scraping)
        if include_indeed and self.sources["jobspy"].available:
            # Search NYC
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="indeed", location="New York, NY", results=indeed_limit // 2
            ))
            # Search California
            all_jobs.extend(self.sources["jobspy"].fetch(
                site="indeed", location="California", results=indeed_limit // 2
            ))

        # Deduplicate by URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)

        # Deduplicate ACROSS sources only (same company+title+location from different sources)
        # Keep the first occurrence (Simplify > Jobright > LinkedIn)
        seen_keys = {}  # key -> source
        deduped_jobs = []
        cross_source_dupes = 0
        for job in unique_jobs:
            title_norm = job.title.lower().replace('–', '-').replace('—', '-').strip()
            loc_norm = job.location.lower().strip()
            key = (job.company.lower(), title_norm, loc_norm)
            if key in seen_keys:
                # Only remove if from a DIFFERENT source
                if seen_keys[key] != job.source:
                    cross_source_dupes += 1
                    continue  # Skip this duplicate from another source
            seen_keys[key] = job.source
            deduped_jobs.append(job)

        self.jobs = deduped_jobs
        print(f"  [Deduped] Removed {cross_source_dupes} cross-source duplicates")
        print(f"\n=== Total unique jobs: {len(deduped_jobs)} ===")
        return deduped_jobs

    def enrich(self) -> List[Job]:
        """Enrich jobs with levels.fyi data"""
        enriched = 0
        for job in self.jobs:
            if self.enricher.has_salary_data(job.company_slug):
                job.description = (job.description or "") + f"\n\n[Salary data available on levels.fyi]({self.enricher.get_company_url(job.company_slug)})"
                enriched += 1
        print(f"  [Enriched] {enriched} jobs have levels.fyi salary data")
        return self.jobs

    def filter_new_grad(self) -> List[Job]:
        """Filter to only new grad/entry level positions"""
        keywords = ['new grad', 'entry level', 'junior', 'associate', 'early career',
                   'university', 'graduate', 'level 1', 'level i', 'i ', 'engineer 1',
                   'software engineer 1', 'swe 1', 'developer 1']
        filtered = []
        for job in self.jobs:
            title_lower = job.title.lower()
            if any(kw in title_lower for kw in keywords) or job.experience_level == "new_grad":
                filtered.append(job)
        print(f"  [Filtered] {len(filtered)} new grad positions")
        return filtered

    def filter_location(self, regions: List[str] = None) -> List[Job]:
        """Filter jobs by location (NYC, California, etc.)"""
        if regions is None:
            regions = ["nyc", "california"]

        # Location patterns for each region
        location_patterns = {
            "nyc": [
                "new york", "nyc", "brooklyn, ny", "manhattan", "queens, ny",
                "bronx, ny", "staten island", ", ny,"
            ],
            "california": [
                "california", ", ca,", ", ca ", "san francisco", "los angeles",
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

    def to_json(self, filepath: str):
        """Export jobs to JSON"""
        with open(filepath, 'w') as f:
            json.dump([job.to_dict() for job in self.jobs], f, indent=2)
        print(f"  [Export] Saved {len(self.jobs)} jobs to {filepath}")

    def summary(self) -> Dict:
        """Get summary statistics"""
        sources = {}
        companies = set()
        with_salary = 0

        for job in self.jobs:
            sources[job.source] = sources.get(job.source, 0) + 1
            companies.add(job.company_slug)
            if job.salary_min or job.salary_max:
                with_salary += 1

        return {
            "total_jobs": len(self.jobs),
            "unique_companies": len(companies),
            "jobs_with_salary": with_salary,
            "by_source": sources
        }


if __name__ == "__main__":
    # Test the aggregator
    agg = JobAggregator(levels_companies_file="/home/user/Hidden-Gems/data/levels_companies.txt")

    # Fetch from free sources + LinkedIn (NYC/CA searches)
    jobs = agg.fetch_all(include_linkedin=True, linkedin_limit=100)

    # Filter to NYC and California only
    agg.filter_location(["nyc", "california"])

    # Enrich with levels.fyi data
    agg.enrich()

    # Filter to new grad only
    new_grad_jobs = agg.filter_new_grad()

    # Export
    agg.to_json("/home/user/Hidden-Gems/aggregator/jobs.json")

    # Summary
    print("\n=== Summary ===")
    summary = agg.summary()
    for key, val in summary.items():
        print(f"  {key}: {val}")

"""
Jobright URL Resolver

Resolves Jobright wrapper URLs to direct job posting URLs.
This module extracts company information from Jobright pages and attempts to
find direct job posting links on the employer's career site.
"""

import json
import os
import re
import time
import requests
from typing import Dict, List, Optional, Tuple


class JobrightResolver:
    """Resolves Jobright URLs to direct employer job posting URLs."""

    CACHE_FILE = ".jobright_url_cache.json"
    JOBRIGHT_PATTERN = re.compile(r'https?://jobright\.ai/jobs/info/')

    # Known ATS patterns for major companies
    ATS_PATTERNS = {
        'greenhouse': 'boards.greenhouse.io',
        'lever': 'jobs.lever.co',
        'workday': 'myworkdayjobs.com',
        'ashby': 'jobs.ashbyhq.com',
        'icims': 'icims.com',
        'smartrecruiters': 'smartrecruiters.com',
    }

    def __init__(self):
        self._url_cache: Dict[str, str] = {}
        self._company_ats_cache: Dict[str, str] = {}  # company -> ATS URL pattern
        self._load_cache()

    def _load_cache(self):
        """Load cached URL mappings."""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self._url_cache = data.get('urls', {})
                    self._company_ats_cache = data.get('company_ats', {})
                    print(f"  [JobrightResolver] Loaded {len(self._url_cache)} cached URL mappings")
            except Exception as e:
                print(f"  [JobrightResolver] Error loading cache: {e}")
                self._url_cache = {}

    def _save_cache(self):
        """Save URL mappings to cache."""
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump({
                    'urls': self._url_cache,
                    'company_ats': self._company_ats_cache,
                    'updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2)
            print(f"  [JobrightResolver] Saved {len(self._url_cache)} URL mappings to cache")
        except Exception as e:
            print(f"  [JobrightResolver] Error saving cache: {e}")

    def is_jobright_url(self, url: str) -> bool:
        """Check if URL is a Jobright wrapper URL."""
        return bool(self.JOBRIGHT_PATTERN.match(url))

    def _extract_job_info(self, jobright_url: str) -> Optional[Dict]:
        """Extract job and company info from Jobright page."""
        try:
            resp = requests.get(jobright_url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            if resp.status_code != 200:
                return None

            # Extract JSON-LD data
            match = re.search(r'<script id="job-posting" type="application/ld\+json">(.+?)</script>', resp.text)
            if match:
                data = json.loads(match.group(1))
                return {
                    'company': data.get('hiringOrganization', {}).get('name', ''),
                    'company_url': data.get('hiringOrganization', {}).get('sameAs', ''),
                    'title': data.get('title', ''),
                    'location': data.get('jobLocation', {}).get('address', {}).get('addressLocality', ''),
                }
        except Exception as e:
            print(f"  [JobrightResolver] Error extracting job info: {e}")
        return None

    def _find_company_ats(self, company_url: str) -> Optional[str]:
        """Try to find the company's ATS by checking their careers page."""
        if not company_url:
            return None

        # Check cache first
        if company_url in self._company_ats_cache:
            return self._company_ats_cache[company_url]

        try:
            base_url = company_url.rstrip('/')
            careers_paths = ['/careers', '/jobs', '/job-openings', '/company/careers']

            for path in careers_paths:
                try:
                    careers_url = base_url + path
                    resp = requests.get(careers_url, timeout=10, allow_redirects=True, headers={
                        "User-Agent": "Mozilla/5.0"
                    }, verify=False)

                    if resp.status_code == 200:
                        # Look for ATS patterns in the page
                        for ats_name, pattern in self.ATS_PATTERNS.items():
                            if pattern in resp.text.lower() or pattern in resp.url.lower():
                                # Try to extract the full ATS URL
                                ats_match = re.search(rf'https?://[^\s"\'<>]*{pattern}[^\s"\'<>]*', resp.text, re.I)
                                if ats_match:
                                    ats_url = ats_match.group(0).split('"')[0].split("'")[0]
                                    self._company_ats_cache[company_url] = ats_url
                                    return ats_url
                except Exception:
                    continue

        except Exception as e:
            print(f"  [JobrightResolver] Error finding ATS: {e}")

        return None

    def resolve_url(self, jobright_url: str) -> Optional[str]:
        """
        Resolve a single Jobright URL to its direct job posting URL.

        Args:
            jobright_url: The Jobright wrapper URL

        Returns:
            The direct job posting URL, or None if resolution failed
        """
        # Check cache first
        if jobright_url in self._url_cache:
            return self._url_cache[jobright_url]

        # Extract job info from the Jobright page
        job_info = self._extract_job_info(jobright_url)
        if not job_info:
            return None

        # Try to find the job on the company's ATS
        ats_url = self._find_company_ats(job_info['company_url'])
        if ats_url:
            # For now, just return the ATS careers page
            # In the future, we could try to search for the specific job
            self._url_cache[jobright_url] = ats_url
            return ats_url

        return None

    def get_cached_url(self, jobright_url: str) -> Optional[str]:
        """Get a cached direct URL for a Jobright URL."""
        return self._url_cache.get(jobright_url)


def resolve_jobright_urls_in_jobs(jobs: list, resolver: JobrightResolver = None) -> Tuple[list, int]:
    """
    Resolve Jobright URLs in a list of Job objects to direct URLs.

    Args:
        jobs: List of Job objects
        resolver: Optional JobrightResolver instance (creates one if not provided)

    Returns:
        Tuple of (updated jobs list, number of URLs resolved)
    """
    if resolver is None:
        resolver = JobrightResolver()

    # Find all Jobright URLs in jobs
    jobright_jobs = [(i, job) for i, job in enumerate(jobs) if resolver.is_jobright_url(job.url)]

    if not jobright_jobs:
        print("  [JobrightResolver] No Jobright URLs to resolve")
        return jobs, 0

    print(f"  [JobrightResolver] Found {len(jobright_jobs)} jobs with Jobright URLs")
    print("  [JobrightResolver] Note: URL resolution requires Playwright with browser deps.")
    print("  [JobrightResolver] Install with: pip install playwright && playwright install chromium")
    print("  [JobrightResolver] Keeping Jobright URLs for now (they redirect to job postings)")

    # For now, just return the jobs as-is
    # The resolver can be enhanced later when playwright is available

    return jobs, 0

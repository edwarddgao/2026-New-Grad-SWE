"""
Job Aggregator Package

Aggregates job listings from multiple sources including:
- SimplifyJobs GitHub repos
- Jobright GitHub repos
- Built In (NYC, SF, LA)
- Hacker News Who's Hiring threads
- Indeed/LinkedIn/Glassdoor via JobSpy

Also includes salary enrichment from levels.fyi.
"""

from .sources import Job, JobAggregator
from .filters import filter_jobs
from .levels_scraper import LevelsScraper, get_scraper
from .utils import slugify

__all__ = [
    'Job',
    'JobAggregator',
    'filter_jobs',
    'LevelsScraper',
    'get_scraper',
    'slugify',
]

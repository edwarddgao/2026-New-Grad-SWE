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

import logging

# Configure package-level logger
logger = logging.getLogger('aggregator')

def configure_logging(level: int = logging.INFO, format_string: str = None):
    """Configure logging for the aggregator package.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = '%(message)s'

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format_string))

    logger.setLevel(level)
    logger.addHandler(handler)

    # Prevent duplicate logs if called multiple times
    logger.propagate = False

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
    'configure_logging',
    'logger',
]

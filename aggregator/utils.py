"""
Shared utility functions for the job aggregator
"""

import re


def slugify(name: str) -> str:
    """
    Convert a string to a URL-friendly slug.

    Args:
        name: The string to slugify (e.g., company name)

    Returns:
        A lowercase string with only alphanumeric characters and hyphens

    Examples:
        >>> slugify("Google Inc.")
        'google-inc'
        >>> slugify("Jane Street Capital")
        'jane-street-capital'
    """
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

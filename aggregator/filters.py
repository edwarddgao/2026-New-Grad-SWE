"""
Job filtering logic for new grad SWE roles
"""

# Sources that are already curated for new grad roles
CURATED_SOURCES = {"simplify_new_grad", "simplify_internship", "speedyapply"}

# Keywords indicating new grad/entry level positions
NEW_GRAD_KEYWORDS = [
    'new grad', 'new college grad', 'entry level', 'entry-level',
    'junior', 'associate', 'early career', 'university', 'graduate',
    'level 1', 'level i', 'engineer 1', 'engineer i', 'swe 1', 'swe i',
    'developer 1', 'developer i', '2025', '2026', 'rotational',
    'early in career', 'recent grad', 'college grad'
]

# Keywords indicating senior/staff level (should be filtered out)
SENIOR_KEYWORDS = [
    'senior', 'staff', 'principal', 'lead', 'manager', 'director',
    'architect', 'vp ', 'vice president', 'head of', 'chief',
    'sr ', 'sr.', ' iii', ' iv', ' 3', ' 4', ' 5',
    'founding', 'distinguished', 'fellow', 'phd'
]

# SWE-related keywords (must match at least one for non-curated sources)
SWE_KEYWORDS = [
    'software', 'swe', 'developer', 'frontend', 'backend', 'fullstack',
    'full-stack', 'full stack', 'web dev', 'mobile dev', 'ios dev',
    'android dev', 'data engineer', 'ml engineer', 'machine learning',
    'platform engineer', 'devops', 'site reliability', 'sre',
    'cloud engineer', 'infrastructure engineer', 'systems engineer',
    'application engineer', 'api engineer', 'integration engineer'
]

# Non-SWE engineering keywords to exclude
NON_SWE_KEYWORDS = [
    'structural engineer', 'civil engineer', 'mechanical engineer',
    'electrical engineer', 'chemical engineer', 'hardware engineer',
    'manufacturing engineer', 'process engineer', 'quality engineer',
    'test engineer', 'validation engineer', 'field engineer',
    'sales engineer', 'solutions engineer', 'support engineer',
    'network engineer', 'rf engineer', 'audio engineer'
]


def is_new_grad_swe(title: str, source: str) -> bool:
    """
    Check if a job should be kept based on title and source.

    Args:
        title: Job title
        source: Job source (e.g., 'simplify_new_grad', 'linkedin', 'hn_hiring')

    Returns:
        True if job should be kept, False if it should be filtered out
    """
    title_lower = title.lower()

    # Always filter out PhD positions regardless of source
    if 'phd' in title_lower:
        return False

    # Keep all jobs from curated sources (after PhD filter)
    if source in CURATED_SOURCES:
        return True

    # Reject if has senior keywords
    if any(kw in title_lower for kw in SENIOR_KEYWORDS):
        return False

    # Reject if explicitly non-SWE engineering
    if any(kw in title_lower for kw in NON_SWE_KEYWORDS):
        return False

    # Must have SWE-related keyword OR be generic "engineer" with new grad keyword
    has_swe = any(kw in title_lower for kw in SWE_KEYWORDS)
    has_new_grad = any(kw in title_lower for kw in NEW_GRAD_KEYWORDS)

    return has_swe or (has_new_grad and 'engineer' in title_lower)


def filter_jobs(jobs: list, verbose: bool = True) -> tuple:
    """
    Filter a list of jobs to only new grad SWE roles.

    Args:
        jobs: List of Job objects
        verbose: Whether to print filtering stats

    Returns:
        Tuple of (filtered_jobs, filtered_count)
    """
    filtered_jobs = []
    filtered_count = 0

    for job in jobs:
        if is_new_grad_swe(job.title, job.source):
            filtered_jobs.append(job)
        else:
            filtered_count += 1

    if verbose and filtered_count > 0:
        print(f"  [Filtered] Removed {filtered_count} non-matching roles from non-curated sources")

    return filtered_jobs, filtered_count

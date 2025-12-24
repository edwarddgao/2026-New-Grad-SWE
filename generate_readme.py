#!/usr/bin/env python3
"""
Generate README.md with job listings table (like Simplify/Jobright)
"""

from aggregator.sources import JobAggregator
from datetime import datetime, timedelta
from collections import defaultdict

def get_age(date_str: str) -> str:
    """Convert date to age string (e.g., '0d', '1w', '1mo')"""
    if not date_str:
        return ""
    try:
        posted = datetime.strptime(date_str, "%Y-%m-%d")
        days = (datetime.now() - posted).days
        if days <= 0:
            return "0d"
        elif days < 7:
            return f"{days}d"
        elif days < 30:
            return f"{days // 7}w"
        else:
            return f"{days // 30}mo"
    except:
        return ""

def generate_readme():
    # Fetch and filter jobs
    agg = JobAggregator()
    agg.fetch_all(include_linkedin=True, linkedin_limit=100)
    agg.filter_location(["nyc", "california"])

    # Group jobs by company
    by_company = defaultdict(list)
    for job in agg.jobs:
        by_company[job.company].append(job)

    # Sort companies alphabetically
    sorted_companies = sorted(by_company.keys(), key=str.lower)

    # Generate README content
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    readme = f"""# New Grad SWE Jobs - NYC & California

> Aggregated from [SimplifyJobs](https://github.com/SimplifyJobs/New-Grad-Positions) and [Jobright](https://github.com/jobright-ai/2025-Software-Engineer-New-Grad)

**Last updated:** {now}

**Total:** {len(agg.jobs)} jobs from {len(by_company)} companies

---

## Job Listings

| Company | Role | Location | Source | Posted |
|---------|------|----------|--------|--------|
"""

    # Add job rows
    for company in sorted_companies:
        jobs = by_company[company]
        for i, job in enumerate(jobs):
            # First job shows company name, subsequent jobs use arrow
            company_col = f"**{company}**" if i == 0 else "↳"

            # Format title as link
            title_col = f"[{job.title}]({job.url})"

            # Truncate location if too long
            loc = job.location
            if len(loc) > 40:
                loc = loc[:37] + "..."

            # Source badge
            source_map = {
                "simplify_new_grad": "Simplify",
                "simplify_internship": "Simplify",
                "jobright": "Jobright",
                "linkedin": "LinkedIn",
                "indeed": "Indeed"
            }
            source = source_map.get(job.source, job.source)

            # Age
            age = get_age(job.date_posted)

            readme += f"| {company_col} | {title_col} | {loc} | {source} | {age} |\n"

    readme += """
---

## About

This list aggregates new grad software engineering positions in NYC and California from multiple sources:

- **[SimplifyJobs](https://github.com/SimplifyJobs/New-Grad-Positions)** - Curated new grad job database
- **[Jobright](https://github.com/jobright-ai/2025-Software-Engineer-New-Grad)** - AI-powered job aggregator

### Usage

To regenerate this list:

```bash
python generate_readme.py
```

### Contributing

Found a job not listed? Open an issue or PR!
"""

    # Write README
    with open("README.md", "w") as f:
        f.write(readme)

    print(f"Generated README.md with {len(agg.jobs)} jobs from {len(by_company)} companies")

if __name__ == "__main__":
    generate_readme()

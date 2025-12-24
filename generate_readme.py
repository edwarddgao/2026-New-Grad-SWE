#!/usr/bin/env python3
"""
Generate README.md with job listings table (like Simplify/Jobright)
"""

from aggregator.sources import JobAggregator
from datetime import datetime, timedelta
from collections import defaultdict

def format_salary(salary_min: int, salary_max: int) -> str:
    """Format salary range as compact string (e.g., '$120k-150k')"""
    # Filter out zero/invalid salaries
    if not salary_min or salary_min < 10000:
        salary_min = None
    if not salary_max or salary_max < 10000:
        salary_max = None

    if not salary_min and not salary_max:
        return ""
    if salary_min and salary_max:
        return f"${salary_min // 1000}k-{salary_max // 1000}k"
    elif salary_min:
        return f"${salary_min // 1000}k+"
    else:
        return f"${salary_max // 1000}k"

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
    agg.fetch_all(include_linkedin=True, linkedin_limit=100, include_builtin=True, builtin_cities=["nyc", "sf", "la"], include_indeed=True, indeed_limit=50, include_glassdoor=True, glassdoor_limit=50, include_hn=True, hn_limit=100)
    agg.filter_location(["nyc", "california"])

    # Sort jobs by recency (most recent first)
    def sort_key(job):
        if not job.date_posted:
            return "0000-00-00"  # Jobs without dates go to end
        return job.date_posted

    sorted_jobs = sorted(agg.jobs, key=sort_key, reverse=True)

    # Count unique companies
    unique_companies = set(job.company for job in agg.jobs)

    # Generate README content
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    readme = f"""# New Grad SWE Jobs - NYC & California

> Aggregated from [SimplifyJobs](https://github.com/SimplifyJobs/New-Grad-Positions), [Jobright](https://github.com/jobright-ai/2025-Software-Engineer-New-Grad), [LinkedIn](https://linkedin.com/jobs), [Indeed](https://indeed.com), [Glassdoor](https://glassdoor.com), [Built In](https://builtin.com/jobs) (NYC, SF, LA), and [HN Who's Hiring](https://news.ycombinator.com/item?id=42575537)

**Last updated:** {now}

**Total:** {len(agg.jobs)} jobs from {len(unique_companies)} companies

---

## Job Listings

| Company | Role | Location | Comp | Source | Posted |
|---------|------|----------|------|--------|--------|
"""

    # Add job rows sorted by recency
    for job in sorted_jobs:
        # Escape pipe characters to prevent breaking markdown table
        company = job.company.replace("|", "\\|")
        title = job.title.replace("|", "\\|")
        loc = job.location.replace("|", "\\|")

        # Format company
        company_col = f"**{company}**"

        # Format title as link
        title_col = f"[{title}]({job.url})"

        # Truncate location if too long
        if len(loc) > 40:
            loc = loc[:37] + "..."

        # Source badge
        source_map = {
            "simplify_new_grad": "Simplify",
            "simplify_internship": "Simplify",
            "jobright": "Jobright",
            "linkedin": "LinkedIn",
            "indeed": "Indeed",
            "glassdoor": "Glassdoor",
            "builtin_nyc": "Built In NYC",
            "builtin_sf": "Built In SF",
            "builtin_la": "Built In LA",
            "hn_hiring": "HN Hiring"
        }
        source = source_map.get(job.source, job.source)

        # Age
        age = get_age(job.date_posted)

        # Compensation
        comp = format_salary(job.salary_min, job.salary_max)

        readme += f"| {company_col} | {title_col} | {loc} | {comp} | {source} | {age} |\n"

    readme += """
---

## About

This list aggregates new grad software engineering positions in NYC and California from multiple sources:

- **[SimplifyJobs](https://github.com/SimplifyJobs/New-Grad-Positions)** - Curated new grad job database
- **[Jobright](https://github.com/jobright-ai/2025-Software-Engineer-New-Grad)** - AI-powered job aggregator
- **[LinkedIn](https://linkedin.com/jobs)** - Professional job board (via JobSpy)
- **[Indeed](https://indeed.com)** - Job search engine (via JobSpy)
- **[Glassdoor](https://glassdoor.com)** - Job board with salary data (via JobSpy)
- **[Built In](https://builtin.com/jobs)** - Local tech job boards (NYC, SF, LA)
- **[HN Who's Hiring](https://news.ycombinator.com)** - Monthly Hacker News hiring thread

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

    print(f"Generated README.md with {len(agg.jobs)} jobs from {len(unique_companies)} companies")

if __name__ == "__main__":
    generate_readme()

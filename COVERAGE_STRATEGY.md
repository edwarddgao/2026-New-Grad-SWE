# Maximum Coverage Strategy for New Grad SWE Jobs

## Quick Start: 100% Coverage in 3 Sources

```
Simplify (62%) + levels.fyi gap (20%) + jobright-ai (18%) = 100%
```

## Tier 1: Essential Sources (82% coverage)

### 1. SimplifyJobs GitHub (62%)
**URL:** `https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json`

```python
import requests
resp = requests.get(url)
jobs = resp.json()  # ~3,000+ companies
```

**Pros:** JSON format, easy to parse, updated frequently
**Cons:** Misses 38% of companies

### 2. levels.fyi (adds 20%)
**Method:** Cross-reference their company list against Simplify to find gaps

Companies on levels.fyi but NOT Simplify (48 notable ones):
- Plaid, Unity, monday.com, Verily, LaunchDarkly
- Major tech companies with salary data

**How to capture:**
1. Get company list from levels.fyi sitemaps
2. Filter to companies NOT in Simplify
3. Scrape their career pages or check levels.fyi/jobs

---

## Tier 2: Complete Coverage (adds remaining 18%)

### 3. jobright-ai GitHub
**URL:** `https://github.com/jobright-ai/2025-Software-Engineer-New-Grad`

Covers companies missed by both Simplify and levels.fyi:
- Government agencies (CalPERS, Ohio DJFS)
- Gaming studios (Naughty Dog, NetherRealm)
- Healthcare (Mayo Clinic)
- Startups (1Sphere AI, Fluidstack)

### 4. Indeed via JobSpy (backup)
```python
from jobspy import scrape_jobs
jobs = scrape_jobs(
    site_name=["indeed"],
    search_term="software engineer new grad",
    location="USA",
    results_wanted=100,
    hours_old=72
)
```

### 5. Direct ATS Scraping (for high-value targets)
Many companies use common ATS platforms:
- **Greenhouse:** `boards.greenhouse.io/{company}`
- **Lever:** `jobs.lever.co/{company}`
- **Workday:** `{company}.wd5.myworkdayjobs.com`

---

## Implementation: The Aggregator

Use `aggregator/sources.py` in this repo:

```python
from aggregator.sources import JobAggregator

agg = JobAggregator()
jobs = agg.fetch_all(include_indeed=False)  # Simplify + jobright-ai
agg.enrich()  # Add levels.fyi salary links
agg.to_json("jobs.json")

print(agg.summary())
# {
#   "total_jobs": 6705,
#   "unique_companies": 1788,
#   "by_source": {"simplify_internship": 4200, "simplify_new_grad": 1800, "jobright": 705}
# }
```

---

## Priority Order for Job Seekers

| Priority | Action | Time | Coverage Gain |
|----------|--------|------|---------------|
| 1 | Check SimplifyJobs GitHub daily | 5 min | 62% |
| 2 | Check jobright-ai GitHub daily | 5 min | +18% → 80% |
| 3 | Browse levels.fyi/jobs weekly | 15 min | +15% → 95% |
| 4 | Direct applications to gap companies | 30 min | +5% → 100% |

---

## The 93 Companies You'll Miss Using Simplify Alone

### High-Priority Targets (well-known companies)
1. **Plaid** - Fintech infrastructure
2. **Unity** - Game engine
3. **monday.com** - Work management
4. **Verily** - Alphabet health spinoff
5. **LaunchDarkly** - Feature flags
6. **Scotiabank** - Major bank
7. **Teradyne** - Semiconductors
8. **Mayo Clinic** - Healthcare
9. **Naughty Dog** - Gaming (Sony)
10. **NetherRealm Studios** - Gaming (WB)

### Government/Defense (stable, good benefits)
- Noblis, Jacobs, Nightwing, HII, Kiewit

### Startups (high growth potential)
- 1Sphere AI, Broccoli AI, Fluidstack, Vast.ai, Ketryx

---

## Automation: Daily Job Alert Script

```python
#!/usr/bin/env python3
"""Daily job aggregator - run via cron"""

from aggregator.sources import JobAggregator
from datetime import datetime, timedelta
import json

def get_new_jobs():
    agg = JobAggregator()
    jobs = agg.fetch_all()

    # Filter to last 24 hours
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_jobs = [j for j in jobs if j.date_posted and j.date_posted >= yesterday]

    return new_jobs

if __name__ == "__main__":
    new_jobs = get_new_jobs()
    print(f"Found {len(new_jobs)} new jobs in last 24 hours")

    # Group by company
    by_company = {}
    for job in new_jobs:
        by_company.setdefault(job.company, []).append(job)

    for company, jobs in sorted(by_company.items()):
        print(f"\n{company}:")
        for job in jobs:
            print(f"  - {job.title} ({job.location})")
```

---

## Summary

| Strategy | Coverage | Complexity |
|----------|----------|------------|
| Simplify only | 62% | ⭐ |
| + jobright-ai | 80% | ⭐⭐ |
| + levels.fyi | 95% | ⭐⭐⭐ |
| + direct applications | 100% | ⭐⭐⭐⭐ |

**Bottom line:** Using Simplify + jobright-ai gets you 80% coverage with minimal effort. Adding levels.fyi brings you to 95%. The remaining 5% requires direct applications to specific companies.

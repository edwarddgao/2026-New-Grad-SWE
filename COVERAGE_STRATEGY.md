# Maximum Coverage Strategy for New Grad SWE Jobs

## Quick Start: Two Sources for Maximum Coverage

```
Simplify (950 companies) + Jobright (+166 unique) = ~1,100 companies
```

**Note:** These are complementary sources, not subsets. Each finds companies the other misses.

## Source Comparison

| Source | Companies | Jobs | Strength |
|--------|-----------|------|----------|
| **Simplify** | 950 | 2,544 | Largest curated database |
| **Jobright** | 249 | ~600 | Scrapes Indeed/LinkedIn/career pages |
| **Overlap** | ~83 | - | Both sources have this |
| **Combined** | ~1,100 | ~3,100 | Maximum coverage |

---

## Primary Source: Simplify

**URL:** `https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json`

```python
import requests
resp = requests.get(url)
jobs = resp.json()  # 2,544 active jobs from 950 companies
```

**What you get:**
- Major tech (Google, Meta, Amazon, Microsoft, Apple)
- Big banks (JPMorgan, Goldman Sachs, Capital One)
- Defense (Lockheed Martin, Northrop Grumman, RTX)
- Hundreds of startups and mid-size companies

---

## Complementary Source: Jobright

**URL:** `https://github.com/jobright-ai/2025-Software-Engineer-New-Grad`

**What it adds (~166 unique companies):**
- Gaming studios (Naughty Dog, NetherRealm, 2K)
- Fintech (Plaid, monday.com)
- Healthcare (Mayo Clinic, Brown University Health)
- Government (CalPERS, Ohio DJFS)
- Defense contractors (Noblis, Jacobs, HII)

---

## About levels.fyi

**NOT a job source.** It's a salary database with 49,981 companies.

**Correct usage:**
1. Find company career page URLs
2. Check their actual job board at levels.fyi/jobs
3. Use for salary research during negotiations

**Incorrect usage:**
- ❌ Treating it as a list of "companies hiring"
- ❌ Using it to calculate "coverage percentages"

---

## Implementation: The Aggregator

Use `aggregator/sources.py` in this repo:

```python
from aggregator.sources import JobAggregator

agg = JobAggregator()
jobs = agg.fetch_all()  # Combines Simplify + Jobright

print(agg.summary())
# {
#   "total_jobs": ~3100,
#   "unique_companies": ~1100,
#   "by_source": {"simplify_new_grad": 2544, "jobright": ~600}
# }
```

---

## Priority Order for Job Seekers

| Priority | Action | Companies |
|----------|--------|-----------|
| 1 | Check SimplifyJobs GitHub | 950 companies |
| 2 | Check jobright-ai GitHub | +166 additional |
| 3 | Direct applications to targets | Specific companies |

---

## Notable Companies Only on Jobright

These companies have active new grad postings but are NOT on Simplify:

### Tech
- **Plaid** - Fintech infrastructure
- **Unity** - Game engine
- **monday.com** - Work management
- **Verily** - Alphabet health spinoff
- **LaunchDarkly** - Feature flags

### Gaming
- **Naughty Dog** - Sony (Uncharted, Last of Us)
- **NetherRealm Studios** - WB Games (Mortal Kombat)
- **2K** - Sports/action games

### Healthcare
- **Mayo Clinic**
- **Brown University Health**

### Government/Defense
- Noblis, Jacobs, Nightwing, HII, Kiewit, CalPERS

### Startups
- 1Sphere AI, Broccoli AI, Fluidstack, Vast.ai, Ketryx

---

## Automation: Daily Job Alert Script

```python
#!/usr/bin/env python3
"""Daily job aggregator - run via cron"""

from aggregator.sources import JobAggregator
from datetime import datetime, timedelta

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

| Strategy | Companies | Notes |
|----------|-----------|-------|
| Simplify only | 950 | Miss ~166 from Jobright |
| Jobright only | 249 | Miss ~859 from Simplify |
| **Both sources** | ~1,100 | Maximum coverage |

**Bottom line:** Use both Simplify and Jobright. They're complementary, not competing sources.

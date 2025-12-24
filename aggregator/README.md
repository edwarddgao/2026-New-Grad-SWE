# Job Aggregator Architecture

## Overview

A multi-source job aggregator that pulls new grad/entry-level SWE positions from free sources and enriches them with salary data.

## Data Sources

### ✅ Working Sources (Free)

| Source | Jobs | Update Freq | Data Quality | Rate Limits |
|--------|------|-------------|--------------|-------------|
| **SimplifyJobs Internships** | 12,500+ | Daily | High | None |
| **SimplifyJobs New-Grad** | 7,600+ | Daily | High | None |
| **jobright-ai** | 400-600 | Daily | Medium | None |
| **levels.fyi sitemaps** | 50K companies | Weekly | High | None |

### ⚠️ Available but Limited

| Source | Status | Notes |
|--------|--------|-------|
| **Indeed (JobSpy)** | Works locally | May be blocked in some environments |
| **Adzuna API** | Free tier | Requires registration |
| **levels.fyi /jobs** | Scrapable | ~73K jobs, medium legal risk |

### ❌ Not Accessible

| Source | Reason |
|--------|--------|
| **LinkedIn** | API restricted, ToS prohibits scraping |
| **Glassdoor** | API closed since 2021 |
| **Crunchbase** | Paid API only |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Job Aggregator                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Simplify   │  │  Jobright   │  │   Indeed    │   Sources    │
│  │  (GitHub)   │  │  (GitHub)   │  │  (JobSpy)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│                  ┌───────────────┐                               │
│                  │   Normalizer  │  Unified Job format           │
│                  └───────┬───────┘                               │
│                          ▼                                       │
│                  ┌───────────────┐                               │
│                  │  Deduplicator │  Remove duplicates by URL     │
│                  └───────┬───────┘                               │
│                          ▼                                       │
│                  ┌───────────────┐                               │
│                  │   Enricher    │  Add levels.fyi salary links  │
│                  └───────┬───────┘                               │
│                          ▼                                       │
│                  ┌───────────────┐                               │
│                  │    Filter     │  New grad / entry level       │
│                  └───────┬───────┘                               │
│                          ▼                                       │
│                  ┌───────────────┐                               │
│                  │    Export     │  JSON / CSV / DB              │
│                  └───────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Unified Job Schema

```python
@dataclass
class Job:
    id: str                      # Unique ID (source_originalid)
    title: str                   # Job title
    company: str                 # Company name
    company_slug: str            # Normalized slug
    location: str                # Location(s)
    url: str                     # Application URL
    source: str                  # Data source
    date_posted: Optional[str]   # YYYY-MM-DD
    salary_min: Optional[int]    # Min salary (annual)
    salary_max: Optional[int]    # Max salary (annual)
    sponsorship: Optional[str]   # Visa sponsorship status
    remote: Optional[bool]       # Remote work available
    description: Optional[str]   # Job description
    experience_level: Optional[str]  # new_grad, internship, etc.
```

## Usage

```python
from sources import JobAggregator

# Initialize with levels.fyi data for enrichment
agg = JobAggregator(
    levels_companies_file="data/levels_companies.txt"
)

# Fetch from all free sources
jobs = agg.fetch_all(include_indeed=False)

# Enrich with salary data links
agg.enrich()

# Filter to new grad only
new_grad = agg.filter_new_grad()

# Export
agg.to_json("output/jobs.json")

# Get stats
print(agg.summary())
```

## Current Results

```
Total unique jobs: 6,705
Unique companies: 1,788
Jobs with levels.fyi salary data: 4,491 (67%)

By source:
  simplify_internship: 3,731
  simplify_new_grad: 2,540
  jobright: 434
```

## Enrichment Options

### Free (Current)
- **levels.fyi link**: Add salary page URL for companies with data

### Paid (Future)
- **Crunchbase API**: Company funding, valuation, size
- **Clearbit API**: Company logos, industry, tech stack
- **Adzuna API**: Additional job listings with salary data

## Adding New Sources

1. Create a source class in `sources.py`:

```python
class NewSource:
    def fetch(self) -> List[Job]:
        # Fetch and normalize jobs
        jobs = []
        # ... scraping/API logic ...
        return jobs
```

2. Add to aggregator sources dict:

```python
self.sources["newsource"] = NewSource()
```

## Legal Considerations

| Action | Risk Level | Notes |
|--------|------------|-------|
| GitHub repo parsing | ✅ Low | Public data, no ToS violation |
| levels.fyi sitemaps | ✅ Low | Public XML, standard crawling |
| Indeed via JobSpy | ⚠️ Medium | Scraping, but no auth bypass |
| Glassdoor scraping | ❌ High | ToS violation, legal precedent |
| LinkedIn scraping | ❌ High | ToS violation, active enforcement |

## Future Enhancements

1. **Caching**: Store fetched data to reduce API calls
2. **Scheduling**: Run daily via cron/GitHub Actions
3. **Dedup improvements**: Fuzzy matching for same job on multiple sources
4. **Email alerts**: Notify for new jobs matching criteria
5. **Web UI**: Simple frontend to browse aggregated jobs
6. **Salary estimation**: Use levels.fyi data to estimate salaries

---
Generated: 2024-12-24

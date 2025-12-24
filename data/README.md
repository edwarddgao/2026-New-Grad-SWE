# Company Comparison: Levels.fyi vs Simplify.jobs

## Summary

| Metric | Count |
|--------|-------|
| **Levels.fyi companies** | 49,981 |
| **Simplify.jobs companies** | 3,035 |
| **Companies matched (both)** | 2,786 (92% of Simplify) |
| **Companies ONLY on levels.fyi** | 34,316 |
| **Companies ONLY on simplify.jobs** | 249 |

## Matching Methodology

Companies are matched using:
1. Exact slug match
2. Normalized match (removing hyphens/special chars)
3. Prefix matching (same first 5-8 characters)
4. Word-based matching (shared distinctive 5+ char words)
5. Known aliases (e.g., `a16z` → `andreessen-horowitz`, `at-t` → `atandt`)

## Data Sources

### Levels.fyi
- **Source**: Sitemap files at `https://www.levels.fyi/sitemaps/companies-sitemap-{0-64}.xml`
- **Coverage**: Complete company database (~50,000 companies)

### Simplify.jobs
- **Source**: GitHub job listing repositories (JSON data files)
  - [Summer2026-Internships](https://github.com/SimplifyJobs/Summer2026-Internships) - `.github/scripts/listings.json`
  - [New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) - `.github/scripts/listings.json`
- **Coverage**: 3,035 unique companies with job postings
- **Note**: Simplify.jobs website blocks direct access (503/TLS errors)

## Files

| File | Description |
|------|-------------|
| `levels_companies.txt` | All 49,981 companies from levels.fyi |
| `simplify_companies.txt` | All 3,035 companies from Simplify |
| `only_on_levels.txt` | 34,316 companies only on levels.fyi |
| `only_on_simplify.txt` | 249 companies only on Simplify |
| `on_both.txt` | 2,786 matched companies |
| `summer2026_listings.json` | Raw internship data |
| `newgrad_listings.json` | Raw new-grad data |

## Key Findings

1. **92% of Simplify companies are also on levels.fyi** - Most companies in Simplify's job listings also have salary data on levels.fyi

2. **34,316 companies on levels.fyi aren't in Simplify's listings** - These are potential "hidden gems" for job seekers who only use Simplify

3. **Only 249 companies are unique to Simplify** - These are mostly smaller companies, regional organizations, or those with non-standard naming

## Usage

```bash
# Find companies with salary data not in Simplify's listings
cat data/only_on_levels.txt | head -100

# Check if a company is on both platforms
grep "company-name" data/on_both.txt
```

Generated: 2024-12-24

# Company Comparison: Levels.fyi vs Simplify.jobs

## Summary

| Metric | Count |
|--------|-------|
| **Levels.fyi companies** | 49,981 |
| **Simplify.jobs companies** | 1,486 |
| **Companies on BOTH** | 851 |
| **Companies ONLY on levels.fyi** | 49,130 |
| **Companies ONLY on simplify.jobs** | 635 |

## Data Sources

### Levels.fyi
- **Source**: Sitemap files at `https://www.levels.fyi/sitemaps/companies-sitemap-{0-64}.xml`
- **Coverage**: Complete company database (~50,000 companies)

### Simplify.jobs
- **Source**: GitHub job listing repositories
  - [Summer2026-Internships](https://github.com/SimplifyJobs/Summer2026-Internships)
  - [New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions)
- **Coverage**: Companies with active job postings in these repos (~1,500 companies)
- **Note**: Simplify.jobs claims to have 20,000+ companies on their platform, but their website blocks direct access. The data here is limited to companies appearing in their public GitHub job listing repos.

## Files

| File | Description |
|------|-------------|
| `levels_companies.txt` | All 49,981 companies from levels.fyi |
| `simplify_companies.txt` | All 1,486 companies from Simplify GitHub repos |
| `only_on_levels.txt` | 49,130 companies on levels.fyi but NOT in Simplify repos |
| `only_on_simplify.txt` | 635 companies in Simplify repos but NOT on levels.fyi |
| `on_both.txt` | 851 companies appearing on both platforms |

## Notes

1. **Company names are normalized**: lowercase, URL-slug format (e.g., "google", "meta", "amazon")

2. **Simplify data is incomplete**: We could only access company data from Simplify's public GitHub repositories, not their full platform (which is protected behind a web application that blocks automated access).

3. **The real "hidden gems"**: The 49,130 companies on levels.fyi but not in Simplify's GitHub repos represent potential opportunities that job seekers might miss if they only use Simplify's curated job lists.

## How to use

To find companies with salary data on levels.fyi that don't appear in Simplify's job listings:

```bash
# View the list
cat data/only_on_levels.txt

# Search for a specific company
grep "company-name" data/only_on_levels.txt

# Get a sample of larger companies (those more likely to have good data)
head -500 data/only_on_levels.txt
```

Generated: 2024-12-24

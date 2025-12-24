# Company Comparison: Levels.fyi vs Simplify.jobs

## Summary

| Metric | Count |
|--------|-------|
| **Levels.fyi companies** | 49,981 |
| **Simplify.jobs companies** | 3,247 |
| **Companies on BOTH** | 1,736 |
| **Companies ONLY on levels.fyi** | 48,245 |
| **Companies ONLY on simplify.jobs** | 1,511 |

## Data Sources

### Levels.fyi
- **Source**: Sitemap files at `https://www.levels.fyi/sitemaps/companies-sitemap-{0-64}.xml`
- **Coverage**: Complete company database (~50,000 companies)

### Simplify.jobs
- **Source**: GitHub job listing repositories (including structured JSON data files)
  - [Summer2026-Internships](https://github.com/SimplifyJobs/Summer2026-Internships) - `listings.json` (2,039 companies)
  - [New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) - `listings.json` (1,872 companies)
  - README markdown files with company links
- **Coverage**: 3,247 unique companies with job postings in these repos
- **Note**: Simplify.jobs claims 20,000+ companies on their platform, but their website blocks direct access (503 errors, TLS failures). The data here is from their public GitHub repositories.

## Files

| File | Description |
|------|-------------|
| `levels_companies.txt` | All 49,981 companies from levels.fyi |
| `simplify_companies.txt` | All 3,247 companies from Simplify GitHub repos |
| `simplify_all_companies.txt` | Same as above (combined from all sources) |
| `simplify_company_names.txt` | Company slugs with original names |
| `only_on_levels.txt` | 48,245 companies on levels.fyi but NOT on Simplify |
| `only_on_simplify.txt` | 1,511 companies on Simplify but NOT on levels.fyi |
| `on_both.txt` | 1,736 companies appearing on both platforms |
| `summer2026_listings.json` | Raw data from Summer2026-Internships repo |
| `newgrad_listings.json` | Raw data from New-Grad-Positions repo |

## Notes

1. **Company names are normalized**: lowercase, URL-slug format (e.g., "google", "meta", "amazon")

2. **Simplify data is incomplete**: We could only access company data from Simplify's public GitHub repositories, not their full platform (which blocks automated access with 503 errors).

3. **The real "hidden gems"**: The 48,245 companies on levels.fyi but not in Simplify's repos represent potential opportunities that job seekers might miss if they only use Simplify's curated job lists.

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

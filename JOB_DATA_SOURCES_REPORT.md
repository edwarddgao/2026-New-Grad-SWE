# Job Data Sources Research Report
**Date:** December 24, 2025
**Project:** Hidden-Gems Job Data Collection

## Executive Summary

This report documents research and testing of various programmatic job data sources. We successfully tested **4 sources** and found **3 sources with working data access**.

---

## 1. GitHub Repositories with Structured JSON Data

### ✅ SimplifyJobs/Summer2026-Internships

**Status:** ✅ **WORKING** - Currently in use

**Data Location:**
- URL: `https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json`
- Branch: `dev`
- Local file: `/home/user/Hidden-Gems/data/summer2026_listings.json`

**Data Statistics:**
- **Total Jobs:** 12,510 listings
- **File Size:** 8.9 MB
- **Update Frequency:** Updated regularly via GitHub commits

**Data Structure:**
```json
{
  "date_updated": 1751392325,
  "url": "https://jobs.lever.co/palantir/e27af7ab-41fc-40c9-b31d-02c6cb1c505c",
  "company_name": "Palantir",
  "title": "Software Engineer Intern",
  "locations": ["Palo Alto, CA"],
  "terms": ["Summer 2026"],
  "sponsorship": "Offers Sponsorship",
  "active": true,
  "source": "reddoy",
  "id": "8e89d029-fc69-4ceb-850c-bbfddd85468a",
  "date_posted": 1751392325,
  "company_url": "",
  "is_visible": true
}
```

**Available Fields:**
- `id`, `company_name`, `title`, `url`, `locations`, `terms`
- `sponsorship`, `active`, `is_visible`
- `date_posted`, `date_updated`
- `source`, `company_url`

**Fetch Method:**
```bash
curl -o summer2026_listings.json \
  "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json"
```

---

### ✅ SimplifyJobs/New-Grad-Positions

**Status:** ✅ **WORKING** - Currently in use

**Data Location:**
- URL: `https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json`
- Branch: `dev`
- Local file: `/home/user/Hidden-Gems/data/newgrad_listings.json`

**Data Statistics:**
- **Total Jobs:** 7,636 listings
- **File Size:** 4.8 MB
- **Update Frequency:** Updated regularly via GitHub commits

**Data Structure:**
```json
{
  "source": "Simplify",
  "company_name": "Adobe",
  "id": "20b0f992-16b4-4518-9bf8-cfc3e9b78596",
  "title": "University Graduate - Software Engineer",
  "active": false,
  "date_updated": 1745866852,
  "date_posted": 1745866852,
  "url": "https://adobe.wd5.myworkdayjobs.com/...",
  "locations": ["NYC"],
  "company_url": "https://simplify.jobs/c/Adobe",
  "is_visible": true,
  "sponsorship": "Other"
}
```

**Available Fields:**
- `id`, `company_name`, `title`, `url`, `locations`
- `sponsorship`, `active`, `is_visible`
- `date_posted`, `date_updated`
- `source`, `company_url`

**Fetch Method:**
```bash
curl -o newgrad_listings.json \
  "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"
```

---

### ✅ jobright-ai/2025-Software-Engineer-New-Grad

**Status:** ⚠️ **PARSABLE** - Markdown table format (no JSON file)

**Data Location:**
- URL: `https://raw.githubusercontent.com/jobright-ai/2025-Software-Engineer-New-Grad/master/README.md`
- Branch: `master`
- Format: **Markdown table** (not JSON)

**Data Statistics:**
- **Total Jobs:** 566 listings (as of Dec 24, 2025)
- **Update Frequency:** Daily
- **Retention:** Last 7 days only

**Data Structure:**
The data is in a markdown table format:
```markdown
| Company | Job Title | Location | Work Model | Date Posted |
| ----- | --------- | --------- | ---- | ------- |
| **[Milliman](http://www.milliman.com)** | **[Quantitative Developer](https://jobright.ai/jobs/...)** | Chicago, IL | Hybrid | Dec 23 |
```

**Parsed JSON Structure:**
```json
{
  "company": "Milliman",
  "company_url": "http://www.milliman.com",
  "title": "Quantitative Developer",
  "job_url": "https://jobright.ai/jobs/info/...",
  "location": "Chicago, IL",
  "work_model": "Hybrid",
  "date_posted": "Dec 23"
}
```

**Available Fields:**
- `company`, `company_url`, `title`, `job_url`
- `location`, `work_model`, `date_posted`

**Limitations:**
- Only contains jobs from last 7 days
- No JSON file - requires markdown parsing
- Date format is relative (e.g., "Dec 23") not timestamp
- Less metadata than SimplifyJobs

**Fetch Method:**
- Parser script created: `/home/user/Hidden-Gems/test_jobright_parser.py`
- Output saved to: `/home/user/Hidden-Gems/jobright_parsed_output.json`

**Usage:**
```bash
python3 test_jobright_parser.py
```

---

## 2. JobSpy - Python Library for Job Scraping

### ✅ JobSpy with Indeed

**Status:** ✅ **WORKING** - Indeed scraping functional

**Installation:**
```bash
pip install python-jobspy
```

**Data Statistics:**
- **Test Results:** Successfully scraped 5 jobs from Indeed
- **File Size:** 27 KB (5 jobs)
- **Rate Limiting:** No rate limiting observed on Indeed

**Data Structure:**
```json
{
  "id": "in-0c3621e3e66badb6",
  "site": "indeed",
  "job_url": "https://www.indeed.com/viewjob?jk=...",
  "job_url_direct": "https://careers.withwaymo.com/jobs/...",
  "title": "Senior Software Engineer, Robotics",
  "company": "Waymo",
  "location": "San Francisco, CA, US",
  "date_posted": 1766448000000,
  "job_type": "fulltime",
  "salary_source": "direct_data",
  "interval": "yearly",
  "min_amount": 204000.0,
  "max_amount": 259000.0,
  "currency": "USD",
  "is_remote": true,
  "description": "...",
  "company_url": "https://www.indeed.com/cmp/Waymo",
  "company_logo": "https://d2q79iu7y748jz.cloudfront.net/...",
  "company_url_direct": "http://www.waymo.com",
  "company_addresses": "Mountain View, CA",
  "company_description": "..."
}
```

**Available Fields (34 total):**
- Basic: `id`, `site`, `title`, `company`, `location`, `date_posted`
- URLs: `job_url`, `job_url_direct`, `company_url`, `company_url_direct`
- Salary: `salary_source`, `interval`, `min_amount`, `max_amount`, `currency`
- Job Details: `job_type`, `job_level`, `job_function`, `listing_type`, `is_remote`
- Description: `description`, `skills`, `experience_range`
- Company: `company_industry`, `company_logo`, `company_addresses`, `company_num_employees`, `company_revenue`, `company_description`, `company_rating`, `company_reviews_count`
- Other: `emails`, `vacancy_count`, `work_from_home_type`

**Supported Sites:**
- ✅ **Indeed** - Working
- ❌ **LinkedIn** - Error: 'NoneType' object has no attribute 'strip'
- ❌ **Glassdoor** - Error: 'NoneType' object has no attribute 'strip'
- ❌ **ZipRecruiter** - Error: 'NoneType' object has no attribute 'strip'

**Usage Example:**
```python
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed"],
    search_term="software engineer",
    location="San Francisco, CA",
    results_wanted=10,
    hours_old=72,  # Jobs posted in last 72 hours
    country_indeed='USA'
)

# Returns pandas DataFrame
print(f"Found {len(jobs)} jobs")
jobs.to_json('output.json', orient='records')
```

**Test Script:**
- Location: `/home/user/Hidden-Gems/test_jobspy.py`
- Multi-site test: `/home/user/Hidden-Gems/test_jobspy_multi.py`
- Output: `/home/user/Hidden-Gems/jobspy_indeed_output.json`

**Limitations:**
- Only Indeed currently working (other sites have errors)
- Scraping may be unstable - depends on website structure
- No official API - uses web scraping (may break if sites change)
- Unclear rate limits - use responsibly

**Advantages:**
- **Very rich data** - 34 fields including salary, company details, descriptions
- Full job descriptions included
- Salary data when available
- Company metadata (logo, description, etc.)
- No API key required
- Indeed reportedly has no rate limiting

---

## 3. Adzuna API

### ⚠️ Adzuna API

**Status:** ⚠️ **REQUIRES REGISTRATION** - Free tier available but not tested

**Registration:**
- URL: https://developer.adzuna.com/signup
- Free tier available
- Requires `app_id` and `app_key`

**API Documentation:**
- Base URL: `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}`
- Format: JSON, JSONP, or XML
- Authentication: Query parameters `app_id` and `app_key`

**Available Endpoints:**
1. **Job Search** - `/api/jobs/{country}/search/{page}`
2. **Categories** - `/api/jobs/{country}/categories`
3. **History** - Historical salary/job data
4. **Top Companies** - Top hiring companies
5. **Geodata** - Geographic job density data

**Search Parameters:**
- `what` - Job title/keyword search
- `what_exclude` - Keywords to exclude
- `where` - Location filtering
- `salary_min` - Minimum salary threshold
- `full_time` - Filter for full-time positions
- `permanent` - Filter for permanent contracts
- `sort_by` - Ordering method (e.g., salary)
- `results_per_page` - Result count per request (max 50)

**Expected Response Fields:**
- `title`, `description`, `id`
- `salary_min`, `salary_max`, `salary_is_predicted`
- `location` (with geographic hierarchy)
- `company` (display name)
- `contract_type`, `contract_time`
- `latitude`, `longitude`
- `created` (timestamp)
- `redirect_url` (direct link to job posting)
- `category` (label and tag)

**Supported Countries:**
- `us`, `gb`, `au`, `ca`, `de`, `fr`, `nl`, `nz`, `pl`, `br`, `in`, `za`, `at`, `ch`, `sg`

**Usage Example:**
```python
import requests

APP_ID = "your_app_id"
APP_KEY = "your_app_key"

url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
params = {
    'app_id': APP_ID,
    'app_key': APP_KEY,
    'results_per_page': 10,
    'what': 'software engineer',
    'where': 'san francisco'
}

response = requests.get(url, params=params)
data = response.json()

print(f"Found {data['count']} total jobs")
```

**Test Script:**
- Location: `/home/user/Hidden-Gems/test_adzuna_api.py`
- Not tested (requires API credentials)

**Limitations:**
- **Requires free registration** for API credentials
- Rate limits unknown (not documented on overview page)
- Not tested - no credentials available

**Advantages:**
- Official REST API (more stable than scraping)
- Multiple countries supported (15+)
- Additional endpoints (categories, history, geodata)
- Free tier available

---

## Summary Comparison

| Source | Status | Jobs Available | Format | Update Freq | Cost | Requires Auth |
|--------|--------|----------------|--------|-------------|------|---------------|
| **SimplifyJobs Summer2026** | ✅ Working | 12,510 | JSON | Regular | Free | No |
| **SimplifyJobs New-Grad** | ✅ Working | 7,636 | JSON | Regular | Free | No |
| **jobright-ai** | ⚠️ Parsable | 566 (7 days) | Markdown | Daily | Free | No |
| **JobSpy (Indeed)** | ✅ Working | Unlimited* | Python/JSON | Real-time | Free | No |
| **JobSpy (Others)** | ❌ Broken | - | - | - | Free | No |
| **Adzuna API** | ⚠️ Untested | Unlimited* | JSON/XML | Real-time | Free tier | Yes |

*Subject to rate limits and search constraints

---

## Recommendations

### For Current Use

1. **Continue using SimplifyJobs repos** - Most reliable, comprehensive, and well-structured
   - Already integrated and working
   - 20,000+ total jobs between both repos
   - Good metadata and regular updates

2. **Consider adding JobSpy for Indeed** - Valuable for real-time data
   - Rich data with 34 fields including salaries
   - Can supplement SimplifyJobs with recent postings
   - Good for tracking new jobs as they appear
   - Use cautiously to avoid overwhelming servers

3. **Skip jobright-ai for now** - Limited value
   - Only 7 days of data
   - Requires markdown parsing
   - Smaller dataset than other sources
   - Could be useful for very recent jobs only

4. **Adzuna API** - Good future option
   - Consider registering for API key if official API is preferred
   - More stable than web scraping
   - Better for long-term production use

### For Data Pipeline

**Recommended Architecture:**
```
Primary: SimplifyJobs (bulk historical data)
    └─> 20K+ curated internship and new-grad positions
    └─> Updated regularly via GitHub

Supplement: JobSpy + Indeed (real-time scraping)
    └─> Fresh jobs posted in last 24-72 hours
    └─> Rich salary and company data
    └─> Run daily or weekly

Future: Adzuna API (official data source)
    └─> Production-ready API
    └─> Multiple countries
    └─> Once free API key obtained
```

---

## Test Files Created

All test scripts are located in: `/home/user/Hidden-Gems/`

1. **test_jobspy.py** - JobSpy basic test with Indeed
2. **test_jobspy_multi.py** - JobSpy multi-site test
3. **test_adzuna_api.py** - Adzuna API test (requires credentials)
4. **test_jobright_parser.py** - Markdown table parser for jobright-ai

**Output Files:**
- `jobspy_indeed_output.json` - 5 sample jobs from Indeed
- `jobright_parsed_output.json` - 566 jobs from jobright-ai README
- `adzuna_output.json` - (will be created when API credentials available)

---

## Next Steps

1. ✅ **SimplifyJobs integration** - Already working, continue using
2. 🔄 **Consider JobSpy integration** - Add Indeed scraping for real-time data
3. ⏸️ **Hold on jobright-ai** - Only useful for very recent jobs
4. 📋 **Register for Adzuna API** - Get free API key for future use
5. 🧪 **Test Adzuna** - Once credentials obtained, validate data quality

---

## Resources

- **SimplifyJobs Summer 2026:** https://github.com/SimplifyJobs/Summer2026-Internships
- **SimplifyJobs New Grad:** https://github.com/SimplifyJobs/New-Grad-Positions
- **jobright-ai:** https://github.com/jobright-ai/2025-Software-Engineer-New-Grad
- **JobSpy:** https://pypi.org/project/python-jobspy/
- **Adzuna API:** https://developer.adzuna.com/
- **Adzuna Signup:** https://developer.adzuna.com/signup
- **Adzuna Docs:** https://developer.adzuna.com/docs/search

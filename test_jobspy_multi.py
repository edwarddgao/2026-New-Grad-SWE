#!/usr/bin/env python3
"""Test JobSpy library with multiple job sites."""

from jobspy import scrape_jobs
import json

print("Testing JobSpy with multiple job sites...")
print("=" * 80)

# Test different sites
sites_to_test = [
    ("indeed", "USA"),
    ("linkedin", "USA"),
    ("glassdoor", "USA"),
    ("zip_recruiter", "USA"),
]

for site, country in sites_to_test:
    print(f"\nTesting {site}...")
    try:
        jobs = scrape_jobs(
            site_name=[site],
            search_term="software engineer",
            location="San Francisco",
            results_wanted=5,
            country_indeed=country if site == 'indeed' else None
        )

        if len(jobs) > 0:
            print(f"  ✓ {site}: Found {len(jobs)} jobs")
            print(f"  Columns: {list(jobs.columns)}")

            # Show first job details
            first_job = jobs.iloc[0]
            print(f"  Sample: {first_job.get('title', 'N/A')} at {first_job.get('company', 'N/A')}")

            # Save successful results
            output_file = f'/home/user/Hidden-Gems/jobspy_{site}_output.json'
            jobs.to_json(output_file, orient='records', indent=2)
            print(f"  Saved to {output_file}")
        else:
            print(f"  ✗ {site}: No jobs found")
    except Exception as e:
        print(f"  ✗ {site}: Error - {str(e)}")

print("\n" + "=" * 80)
print("Testing complete")

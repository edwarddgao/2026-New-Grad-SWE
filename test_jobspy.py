#!/usr/bin/env python3
"""Test JobSpy library to scrape job data from Indeed."""

from jobspy import scrape_jobs
import json
import pandas as pd

# Test scraping Indeed for software engineering jobs
print("Testing JobSpy - scraping Indeed for 'Software Engineer' jobs...")
print("=" * 80)

try:
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term="software engineer",
        location="San Francisco, CA",
        results_wanted=10,
        hours_old=72,  # Jobs posted in last 72 hours
        country_indeed='USA'
    )

    print(f"\n✓ Successfully scraped {len(jobs)} jobs from Indeed")
    print(f"\nDataFrame columns: {list(jobs.columns)}")
    print(f"\nDataFrame shape: {jobs.shape}")

    # Display first job as sample
    if len(jobs) > 0:
        print("\n" + "=" * 80)
        print("SAMPLE JOB ENTRY:")
        print("=" * 80)
        first_job = jobs.iloc[0].to_dict()
        for key, value in first_job.items():
            print(f"{key}: {value}")

        # Save to JSON for inspection
        output_file = '/home/user/Hidden-Gems/test_jobspy_output.json'
        jobs_dict = jobs.to_dict('records')
        with open(output_file, 'w') as f:
            json.dump(jobs_dict, f, indent=2, default=str)
        print(f"\n✓ Saved full output to {output_file}")

        # Show data types and non-null counts
        print("\n" + "=" * 80)
        print("DATA STRUCTURE INFO:")
        print("=" * 80)
        print(jobs.info())

except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

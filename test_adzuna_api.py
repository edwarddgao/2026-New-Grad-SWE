#!/usr/bin/env python3
"""
Test Adzuna API for job search.

To use this script:
1. Register for free API credentials at: https://developer.adzuna.com/signup
2. Set your APP_ID and APP_KEY environment variables
3. Run the script

Example usage:
    export ADZUNA_APP_ID="your_app_id"
    export ADZUNA_APP_KEY="your_app_key"
    python3 test_adzuna_api.py
"""

import os
import requests
import json

# Get API credentials from environment
APP_ID = os.environ.get('ADZUNA_APP_ID', 'YOUR_APP_ID_HERE')
APP_KEY = os.environ.get('ADZUNA_APP_KEY', 'YOUR_APP_KEY_HERE')

def search_jobs(query="software engineer", location="san francisco", results_per_page=10, page=1, country="us"):
    """
    Search for jobs using Adzuna API.

    Args:
        query: Search keywords
        location: Location to search (use coordinates or location name)
        results_per_page: Number of results per page (max 50)
        page: Page number (1-indexed)
        country: Country code (us, gb, au, etc.)

    Returns:
        JSON response with job listings
    """
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

    params = {
        'app_id': APP_ID,
        'app_key': APP_KEY,
        'results_per_page': results_per_page,
        'what': query,
        'where': location,
        'content-type': 'application/json'
    }

    try:
        print(f"Searching Adzuna for: '{query}' in '{location}'...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()

        print(f"\n✓ Success! Found {data.get('count', 0)} total jobs")
        print(f"  Showing page {page} with {len(data.get('results', []))} results\n")

        # Display sample job
        if data.get('results'):
            print("=" * 80)
            print("SAMPLE JOB ENTRY:")
            print("=" * 80)
            sample = data['results'][0]
            for key, value in sample.items():
                if key != 'description':  # Skip long description
                    print(f"{key}: {value}")

            # Show available fields
            print("\n" + "=" * 80)
            print("AVAILABLE FIELDS:")
            print("=" * 80)
            print(list(data['results'][0].keys()))

            # Save to file
            output_file = '/home/user/Hidden-Gems/adzuna_output.json'
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n✓ Saved full output to {output_file}")

        return data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("\n✗ Authentication failed!")
            print("  Please register at https://developer.adzuna.com/signup")
            print("  Then set ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables")
        else:
            print(f"\n✗ HTTP Error: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")

    return None

def get_categories(country="us"):
    """Get available job categories."""
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/categories"

    params = {
        'app_id': APP_ID,
        'app_key': APP_KEY
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting categories: {e}")
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("ADZUNA API TEST")
    print("=" * 80)

    # Check if credentials are set
    if APP_ID == 'YOUR_APP_ID_HERE' or APP_KEY == 'YOUR_APP_KEY_HERE':
        print("\n⚠️  Warning: Using placeholder credentials")
        print("   To test with real data:")
        print("   1. Register at: https://developer.adzuna.com/signup")
        print("   2. Set environment variables:")
        print("      export ADZUNA_APP_ID='your_id'")
        print("      export ADZUNA_APP_KEY='your_key'")
        print("\n   Attempting API call anyway...\n")

    # Test job search
    result = search_jobs(
        query="software engineer",
        location="san francisco",
        results_per_page=5,
        page=1,
        country="us"
    )

    if result:
        print("\n" + "=" * 80)
        print("API ENDPOINT INFORMATION:")
        print("=" * 80)
        print("Base URL: https://api.adzuna.com/v1/api/jobs/{country}/search/{page}")
        print("Available countries: us, gb, au, ca, de, fr, nl, nz, pl, br, in, za, at, ch, sg")
        print("Max results per page: 50")
        print("Authentication: app_id and app_key parameters")
        print("\nOther endpoints:")
        print("  - /categories - Get job categories")
        print("  - /history - Historical salary/job data")
        print("  - /top_companies - Top hiring companies")
        print("  - /geodata - Geographic job density data")

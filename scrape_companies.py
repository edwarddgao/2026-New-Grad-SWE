#!/usr/bin/env python3
"""
Script to extract company lists from levels.fyi and simplify.jobs
and find companies on levels.fyi not on simplify.jobs
"""

import requests
import re
import time
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_levels_companies():
    """Extract all company names from levels.fyi sitemaps"""
    companies = set()
    base_url = "https://www.levels.fyi/sitemaps/companies-sitemap-{}.xml"

    # Pattern to match company URLs like /companies/company-name (not /salaries, /benefits, etc.)
    pattern = re.compile(r'https://www\.levels\.fyi/companies/([^/<"]+)</loc>')

    def fetch_sitemap(i):
        local_companies = set()
        url = base_url.format(i)
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                matches = pattern.findall(resp.text)
                for match in matches:
                    # Filter out subpages
                    if '/' not in match:
                        local_companies.add(match.lower())
        except Exception as e:
            print(f"Error fetching sitemap {i}: {e}")
        return local_companies

    print("Fetching levels.fyi company sitemaps (0-64)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_sitemap, i) for i in range(65)]
        for future in as_completed(futures):
            companies.update(future.result())

    print(f"Found {len(companies)} companies on levels.fyi")
    return companies

def get_simplify_companies():
    """Extract all company names from simplify.jobs company directory"""
    companies = set()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    # Try different URL patterns for simplify.jobs company directory
    patterns_to_try = [
        "https://simplify.jobs/companies?letter={}",
        "https://simplify.jobs/companies/{}",
        "https://simplify.jobs/c/{}",
        "https://simplify.jobs/company/letter/{}",
    ]

    # First, try to find the sitemap
    print("Trying to find simplify.jobs sitemap...")
    sitemap_urls = [
        "https://simplify.jobs/sitemap.xml",
        "https://simplify.jobs/sitemap-index.xml",
        "https://simplify.jobs/sitemaps/sitemap.xml",
    ]

    for sitemap_url in sitemap_urls:
        try:
            resp = requests.get(sitemap_url, headers=headers, timeout=30)
            print(f"  {sitemap_url}: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  Content preview: {resp.text[:500]}")
        except Exception as e:
            print(f"  {sitemap_url}: Error - {e}")

    # Try the company directory pages
    print("\nTrying company directory patterns...")
    for pattern in patterns_to_try:
        test_url = pattern.format('a')
        try:
            resp = requests.get(test_url, headers=headers, timeout=30, allow_redirects=True)
            print(f"  {test_url}: {resp.status_code} (final URL: {resp.url})")
            if resp.status_code == 200 and len(resp.text) > 1000:
                print(f"  Found working pattern! Content length: {len(resp.text)}")
                # Try to extract company links
                company_pattern = re.compile(r'href="[^"]*?/c/([^/"]+)"')
                matches = company_pattern.findall(resp.text)
                if matches:
                    print(f"  Found {len(matches)} company matches with /c/ pattern")
                    break
        except Exception as e:
            print(f"  {test_url}: Error - {e}")

    # Try fetching the main companies page
    print("\nTrying main companies page...")
    try:
        resp = requests.get("https://simplify.jobs/companies", headers=headers, timeout=30, allow_redirects=True)
        print(f"  Status: {resp.status_code}, URL: {resp.url}")
        if resp.status_code == 200:
            # Look for company links
            patterns = [
                re.compile(r'href="/c/([^"/?]+)"'),
                re.compile(r'href="/companies/([^"/?]+)"'),
                re.compile(r'"slug":"([^"]+)"'),
                re.compile(r'"companySlug":"([^"]+)"'),
            ]
            for p in patterns:
                matches = p.findall(resp.text)
                if matches:
                    print(f"  Pattern {p.pattern}: found {len(matches)} matches")
                    companies.update(m.lower() for m in matches)
    except Exception as e:
        print(f"  Error: {e}")

    return companies

if __name__ == "__main__":
    print("=" * 60)
    print("Starting company comparison: levels.fyi vs simplify.jobs")
    print("=" * 60)

    # Get levels.fyi companies
    levels_companies = get_levels_companies()

    print("\n" + "=" * 60)

    # Get simplify.jobs companies
    simplify_companies = get_simplify_companies()

    print(f"\nTotal simplify.jobs companies found: {len(simplify_companies)}")

    if simplify_companies:
        # Find companies on levels but not on simplify
        only_on_levels = levels_companies - simplify_companies
        print(f"\nCompanies on levels.fyi but NOT on simplify.jobs: {len(only_on_levels)}")

        # Save results
        with open("/home/user/Hidden-Gems/data/levels_companies.txt", "w") as f:
            for c in sorted(levels_companies):
                f.write(c + "\n")

        with open("/home/user/Hidden-Gems/data/simplify_companies.txt", "w") as f:
            for c in sorted(simplify_companies):
                f.write(c + "\n")

        with open("/home/user/Hidden-Gems/data/only_on_levels.txt", "w") as f:
            for c in sorted(only_on_levels):
                f.write(c + "\n")

        print("\nResults saved to /home/user/Hidden-Gems/data/")

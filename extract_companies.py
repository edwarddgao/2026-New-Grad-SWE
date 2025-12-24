#!/usr/bin/env python3
"""
Extract and compare company lists from levels.fyi and simplify.jobs
"""

import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

DATA_DIR = "/home/user/Hidden-Gems/data"

def normalize_company_name(name):
    """Normalize company name for comparison"""
    # Remove common suffixes and special chars
    name = name.lower().strip()
    # Replace common separators with nothing
    name = re.sub(r'[-_\s]+', '', name)
    return name

def get_levels_companies():
    """Extract all company names from levels.fyi sitemaps"""
    companies = set()
    base_url = "https://www.levels.fyi/sitemaps/companies-sitemap-{}.xml"

    # Pattern to match company URLs - base company page only
    pattern = re.compile(r'<loc>https://www\.levels\.fyi/companies/([^/<]+)</loc>')

    def fetch_sitemap(i):
        local_companies = set()
        url = base_url.format(i)
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                matches = pattern.findall(resp.text)
                for match in matches:
                    local_companies.add(match.lower())
        except Exception as e:
            print(f"Error fetching sitemap {i}: {e}")
        return local_companies

    print("Fetching levels.fyi company sitemaps (0-64)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_sitemap, i) for i in range(65)]
        for future in as_completed(futures):
            companies.update(future.result())

    print(f"Found {len(companies)} unique companies on levels.fyi")
    return companies

def extract_simplify_companies_from_markdown(filepath):
    """Extract company slugs from simplify.jobs/c/ links in markdown files"""
    companies = set()

    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return companies

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match simplify.jobs/c/CompanySlug
    pattern = re.compile(r'simplify\.jobs/c/([^"/?&\s\)]+)')
    matches = pattern.findall(content)

    for match in matches:
        # Clean up the slug
        slug = match.strip().lower()
        # Skip if it's just tracking params
        if slug and not slug.startswith('utm_') and len(slug) > 1:
            companies.add(slug)

    print(f"  Found {len(companies)} companies in {os.path.basename(filepath)}")
    return companies

def get_simplify_companies():
    """Get all companies from simplify.jobs GitHub repos and other sources"""
    all_companies = set()

    print("Extracting companies from Simplify GitHub repos...")

    # Files to parse
    files_to_check = [
        f"{DATA_DIR}/simplify_newgrad_readme.md",
        f"{DATA_DIR}/simplify_internships_readme.md",
    ]

    for filepath in files_to_check:
        companies = extract_simplify_companies_from_markdown(filepath)
        all_companies.update(companies)

    # Also try to fetch additional company lists
    additional_urls = [
        "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/main/README.md",
        "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md",
    ]

    print("Fetching additional Simplify sources...")
    for url in additional_urls:
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                # Save and extract
                filename = url.split('/')[-1] + "_" + url.split('/')[4] + ".md"
                temp_path = f"{DATA_DIR}/{filename}"
                with open(temp_path, 'w') as f:
                    f.write(resp.text)
                companies = extract_simplify_companies_from_markdown(temp_path)
                all_companies.update(companies)
        except Exception as e:
            print(f"  Error fetching {url}: {e}")

    print(f"\nTotal unique Simplify companies found: {len(all_companies)}")
    return all_companies

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=" * 70)
    print("Company Comparison: levels.fyi vs simplify.jobs")
    print("=" * 70)
    print()

    # Get levels.fyi companies
    levels_companies = get_levels_companies()

    print()
    print("-" * 70)
    print()

    # Get simplify.jobs companies
    simplify_companies = get_simplify_companies()

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    # Calculate differences
    only_on_levels = levels_companies - simplify_companies
    only_on_simplify = simplify_companies - levels_companies
    on_both = levels_companies & simplify_companies

    print(f"\nLevels.fyi companies: {len(levels_companies)}")
    print(f"Simplify.jobs companies: {len(simplify_companies)}")
    print(f"Companies on BOTH: {len(on_both)}")
    print(f"Companies ONLY on levels.fyi: {len(only_on_levels)}")
    print(f"Companies ONLY on simplify.jobs: {len(only_on_simplify)}")

    # Save results
    print("\nSaving results...")

    with open(f"{DATA_DIR}/levels_companies.txt", "w") as f:
        for c in sorted(levels_companies):
            f.write(c + "\n")
    print(f"  Saved {len(levels_companies)} levels.fyi companies")

    with open(f"{DATA_DIR}/simplify_companies.txt", "w") as f:
        for c in sorted(simplify_companies):
            f.write(c + "\n")
    print(f"  Saved {len(simplify_companies)} simplify.jobs companies")

    with open(f"{DATA_DIR}/only_on_levels.txt", "w") as f:
        for c in sorted(only_on_levels):
            f.write(c + "\n")
    print(f"  Saved {len(only_on_levels)} companies only on levels.fyi")

    with open(f"{DATA_DIR}/only_on_simplify.txt", "w") as f:
        for c in sorted(only_on_simplify):
            f.write(c + "\n")
    print(f"  Saved {len(only_on_simplify)} companies only on simplify.jobs")

    with open(f"{DATA_DIR}/on_both.txt", "w") as f:
        for c in sorted(on_both):
            f.write(c + "\n")
    print(f"  Saved {len(on_both)} companies on both")

    # Print sample of companies only on levels.fyi
    print("\n" + "=" * 70)
    print("Sample of companies on levels.fyi but NOT on simplify.jobs:")
    print("=" * 70)
    sample = sorted(only_on_levels)[:100]
    for i, company in enumerate(sample):
        print(f"  {i+1}. {company}")
    if len(only_on_levels) > 100:
        print(f"  ... and {len(only_on_levels) - 100} more")

    print("\n" + "=" * 70)
    print(f"All results saved to {DATA_DIR}/")
    print("=" * 70)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Extract company names from SimplifyJobs sources with proper filtering
"""

import json
import re
import os

DATA_DIR = "/home/user/Hidden-Gems/data"

def normalize_slug(name):
    """Convert company name to slug format for comparison"""
    name = name.lower().strip()
    # Replace special chars with hyphens
    name = re.sub(r'[^a-z0-9]+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    return name

def is_valid_company_slug(slug):
    """Check if a slug looks like a company name, not a UUID or garbage"""
    if not slug or len(slug) < 2:
        return False
    # Filter out UUIDs
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-', slug):
        return False
    # Filter out pure numbers
    if re.match(r'^[0-9]+$', slug):
        return False
    # Filter out very short slugs that are just numbers
    if len(slug) <= 3 and re.match(r'^[0-9a-z]+$', slug):
        return False
    return True

def extract_companies_from_json(filepath):
    """Extract unique company names from a listings.json file"""
    companies = {}  # slug -> original name

    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return companies

    with open(filepath, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  Unexpected data type: {type(data)}")
        return companies

    for item in data:
        if isinstance(item, dict) and 'company_name' in item:
            name = item['company_name']
            if name and isinstance(name, str):
                slug = normalize_slug(name)
                if is_valid_company_slug(slug):
                    companies[slug] = name

    return companies

def extract_companies_from_markdown(filepath):
    """Extract company slugs from /c/ links in markdown files"""
    companies = set()

    if not os.path.exists(filepath):
        print(f"  File not found: {filepath}")
        return companies

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Only match /c/ URLs (company pages), not /p/ (job postings)
    pattern = re.compile(r'simplify\.jobs/c/([^"/?&\s\)]+)')
    matches = pattern.findall(content)

    for match in matches:
        slug = match.strip().lower()
        if is_valid_company_slug(slug):
            companies.add(slug)

    return companies

def main():
    all_companies = {}  # slug -> name
    all_slugs = set()

    print("="*60)
    print("Extracting Simplify companies (fixed)")
    print("="*60)

    # Process JSON files
    json_files = [
        f"{DATA_DIR}/summer2026_listings.json",
        f"{DATA_DIR}/newgrad_listings.json",
    ]

    for filepath in json_files:
        print(f"\nProcessing {os.path.basename(filepath)}...")
        companies = extract_companies_from_json(filepath)
        print(f"  Found {len(companies)} valid companies")
        all_companies.update(companies)

    # Process markdown files - only /c/ links
    md_files = [
        f"{DATA_DIR}/simplify_newgrad_readme.md",
        f"{DATA_DIR}/simplify_internships_readme.md",
        f"{DATA_DIR}/README.md_Summer2026-Internships.md",
    ]

    for filepath in md_files:
        if os.path.exists(filepath):
            print(f"\nProcessing {os.path.basename(filepath)}...")
            companies = extract_companies_from_markdown(filepath)
            print(f"  Found {len(companies)} valid companies")
            all_slugs.update(companies)

    # Combine JSON slugs and markdown slugs
    all_slugs.update(all_companies.keys())
    print(f"\nTotal unique Simplify companies: {len(all_slugs)}")

    # Save
    with open(f"{DATA_DIR}/simplify_all_companies.txt", 'w') as f:
        for slug in sorted(all_slugs):
            f.write(slug + "\n")

    with open(f"{DATA_DIR}/simplify_companies.txt", 'w') as f:
        for slug in sorted(all_slugs):
            f.write(slug + "\n")

    # Now compare with levels.fyi
    with open(f"{DATA_DIR}/levels_companies.txt", 'r') as f:
        levels = set(line.strip().lower() for line in f if line.strip())

    print(f"\nLevels.fyi companies: {len(levels)}")

    # Calculate differences
    only_levels = levels - all_slugs
    only_simplify = all_slugs - levels
    on_both = levels & all_slugs

    print(f"Companies on BOTH: {len(on_both)}")
    print(f"Companies ONLY on levels.fyi: {len(only_levels)}")
    print(f"Companies ONLY on simplify.jobs: {len(only_simplify)}")

    # Check what's in only_simplify
    print(f"\nSample of 'only on Simplify' (should be real companies):")
    for slug in sorted(only_simplify)[:20]:
        print(f"  {slug}")

    # Save results
    with open(f"{DATA_DIR}/only_on_levels.txt", 'w') as f:
        for c in sorted(only_levels):
            f.write(c + "\n")

    with open(f"{DATA_DIR}/only_on_simplify.txt", 'w') as f:
        for c in sorted(only_simplify):
            f.write(c + "\n")

    with open(f"{DATA_DIR}/on_both.txt", 'w') as f:
        for c in sorted(on_both):
            f.write(c + "\n")

    print(f"\nResults saved.")

if __name__ == "__main__":
    main()

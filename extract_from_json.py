#!/usr/bin/env python3
"""
Extract company names from SimplifyJobs listings.json files
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

def extract_companies_from_json(filepath):
    """Extract unique company names from a listings.json file"""
    companies = {}  # slug -> original name

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return companies

    with open(filepath, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Unexpected data type: {type(data)}")
        return companies

    for item in data:
        if isinstance(item, dict) and 'company_name' in item:
            name = item['company_name']
            slug = normalize_slug(name)
            if slug and len(slug) > 1:
                companies[slug] = name

    return companies

def main():
    all_companies = {}

    # Process all listings.json files
    json_files = [
        f"{DATA_DIR}/summer2026_listings.json",
        f"{DATA_DIR}/newgrad_listings.json",
    ]

    for filepath in json_files:
        print(f"Processing {os.path.basename(filepath)}...")
        companies = extract_companies_from_json(filepath)
        print(f"  Found {len(companies)} unique companies")
        all_companies.update(companies)

    print(f"\nTotal unique companies from JSON files: {len(all_companies)}")

    # Also combine with previously extracted companies from README
    prev_companies = set()
    prev_file = f"{DATA_DIR}/simplify_companies.txt"
    if os.path.exists(prev_file):
        with open(prev_file, 'r') as f:
            prev_companies = set(line.strip().lower() for line in f if line.strip())
        print(f"Previously extracted from README: {len(prev_companies)}")

    # Merge
    all_slugs = set(all_companies.keys()) | prev_companies
    print(f"Combined total unique companies: {len(all_slugs)}")

    # Save combined list
    output_file = f"{DATA_DIR}/simplify_all_companies.txt"
    with open(output_file, 'w') as f:
        for slug in sorted(all_slugs):
            f.write(slug + "\n")
    print(f"Saved to {output_file}")

    # Also save with original names
    output_file_names = f"{DATA_DIR}/simplify_company_names.txt"
    with open(output_file_names, 'w') as f:
        for slug in sorted(all_companies.keys()):
            f.write(f"{slug}\t{all_companies[slug]}\n")
    print(f"Saved names to {output_file_names}")

    return all_slugs

if __name__ == "__main__":
    companies = main()

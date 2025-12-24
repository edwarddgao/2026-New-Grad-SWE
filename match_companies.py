#!/usr/bin/env python3
"""
Better company matching with fuzzy logic and known aliases
"""

import re
import os

DATA_DIR = "/home/user/Hidden-Gems/data"

# Known aliases/abbreviations
ALIASES = {
    'a16z': 'andreessen-horowitz',
    'abnormal-security': 'abnormal-ai',
    'accenture-fs': 'accenture',
    'fb': 'facebook',
    'meta': 'facebook',
    'goog': 'google',
    'msft': 'microsoft',
    'amzn': 'amazon',
    'aws': 'amazon',
    'ibm': 'international-business-machines',
    'hp': 'hewlett-packard',
    'jpmc': 'jpmorgan-chase',
    'jpm': 'jpmorgan-chase',
    'baml': 'bank-of-america',
    'bofa': 'bank-of-america',
    'gs': 'goldman-sachs',
    'ms': 'morgan-stanley',
    'ubs': 'ubs',
    'citi': 'citigroup',
    'wfc': 'wells-fargo',
    'cap1': 'capital-one',
}

def normalize(name):
    """Normalize for comparison"""
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9]', '', name)  # Remove all non-alphanumeric
    return name

def get_base_name(slug):
    """Get base company name without suffixes like -fs, -labs, etc."""
    # Remove common suffixes
    slug = re.sub(r'-(inc|llc|corp|co|labs|ai|io|tech|technologies|software|solutions|group|holdings|fs|federal|services|global|international)$', '', slug)
    return slug

def main():
    # Load companies
    with open(f"{DATA_DIR}/levels_companies.txt", 'r') as f:
        levels_raw = [line.strip().lower() for line in f if line.strip()]
    levels = set(levels_raw)

    with open(f"{DATA_DIR}/simplify_all_companies.txt", 'r') as f:
        simplify_raw = [line.strip().lower() for line in f if line.strip()]
    simplify = set(simplify_raw)

    # Create lookup tables for fuzzy matching
    levels_normalized = {normalize(l): l for l in levels}
    levels_base = {get_base_name(l): l for l in levels}

    # Find matches
    matched = set()
    truly_only_simplify = set()

    for s in simplify:
        # Exact match
        if s in levels:
            matched.add(s)
            continue

        # Check aliases
        if s in ALIASES and ALIASES[s] in levels:
            matched.add(s)
            continue

        # Normalized match (remove hyphens)
        s_norm = normalize(s)
        if s_norm in levels_normalized:
            matched.add(s)
            continue

        # Base name match
        s_base = get_base_name(s)
        if s_base in levels_base:
            matched.add(s)
            continue

        # Check if simplify name is a prefix of any levels name
        for l in levels:
            if l.startswith(s) or s.startswith(l):
                if len(s) > 3 and len(l) > 3:  # Avoid short matches
                    matched.add(s)
                    break
        else:
            truly_only_simplify.add(s)

    truly_only_levels = levels - matched - {ALIASES.get(s, s) for s in simplify}
    # Recalculate only_levels more accurately
    simplify_and_aliases = set()
    for s in simplify:
        simplify_and_aliases.add(s)
        simplify_and_aliases.add(normalize(s))
        simplify_and_aliases.add(get_base_name(s))
        if s in ALIASES:
            simplify_and_aliases.add(ALIASES[s])

    truly_only_levels = set()
    for l in levels:
        if l in simplify:
            continue
        if normalize(l) in {normalize(s) for s in simplify}:
            continue
        if get_base_name(l) in {get_base_name(s) for s in simplify}:
            continue
        truly_only_levels.add(l)

    print("="*60)
    print("IMPROVED MATCHING RESULTS")
    print("="*60)
    print(f"Levels.fyi companies: {len(levels)}")
    print(f"Simplify.jobs companies: {len(simplify)}")
    print(f"Matched (exact + fuzzy): {len(matched)}")
    print(f"Only on Simplify (after fuzzy matching): {len(truly_only_simplify)}")
    print(f"Only on Levels (after fuzzy matching): {len(truly_only_levels)}")

    print(f"\nSample of truly unique to Simplify:")
    for s in sorted(truly_only_simplify)[:30]:
        print(f"  {s}")

    # Save updated results
    with open(f"{DATA_DIR}/only_on_simplify.txt", 'w') as f:
        for c in sorted(truly_only_simplify):
            f.write(c + "\n")

    with open(f"{DATA_DIR}/only_on_levels.txt", 'w') as f:
        for c in sorted(truly_only_levels):
            f.write(c + "\n")

    with open(f"{DATA_DIR}/on_both.txt", 'w') as f:
        for c in sorted(matched):
            f.write(c + "\n")

    print(f"\nResults saved.")

if __name__ == "__main__":
    main()

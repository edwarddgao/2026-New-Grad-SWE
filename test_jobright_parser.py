#!/usr/bin/env python3
"""
Test parsing jobright-ai GitHub README markdown table into structured data.
"""

import requests
import re
import json
from datetime import datetime

def parse_jobright_markdown():
    """
    Parse the jobright-ai README markdown table into structured JSON.
    """
    print("Fetching jobright-ai README...")
    url = "https://raw.githubusercontent.com/jobright-ai/2025-Software-Engineer-New-Grad/master/README.md"

    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        # Find the table in markdown
        # Look for TABLE_START marker
        table_start = content.find('TABLE_START')
        if table_start == -1:
            print("✗ Could not find TABLE_START marker")
            return None

        # Get content after TABLE_START
        table_content = content[table_start:]

        # Find the header and separator lines (note the extra space before "--------- |" in separator)
        header_match = re.search(r'\| Company \| Job Title \| Location \| Work Model \| Date Posted \|\n\| -+\s*\| -+\s*\|\s+-+\s*\| -+\s*\| -+\s*\|\n', table_content)

        if not header_match:
            print("✗ Could not find table header")
            return None

        # Get everything after the header
        rows_content = table_content[header_match.end():]

        # Split into rows (stop at end of file or next section)
        rows = rows_content.split('\n')

        jobs = []
        last_company = None
        last_company_url = None

        for row in rows:
            # Parse markdown table row: | **[Company](url)** | **[Title](url)** | Location | Model | Date |
            if not row.strip() or row.strip().startswith('|---') or not row.startswith('|'):
                continue

            cells = [cell.strip() for cell in row.split('|')[1:-1]]  # Remove empty first/last

            if len(cells) >= 5:
                # Check if this is a continuation row (starts with ↳)
                if cells[0].startswith('↳'):
                    company_name = last_company
                    company_url = last_company_url
                else:
                    # Extract company name and URL
                    company_match = re.search(r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*', cells[0])
                    company_name = company_match.group(1) if company_match else cells[0].strip('*')
                    company_url = company_match.group(2) if company_match else None
                    last_company = company_name
                    last_company_url = company_url

                # Extract job title and URL
                title_match = re.search(r'\*\*\[([^\]]+)\]\(([^)]+)\)\*\*', cells[1])
                job_title = title_match.group(1) if title_match else cells[1].strip('*')
                job_url = title_match.group(2) if title_match else None

                job = {
                    'company': company_name,
                    'company_url': company_url,
                    'title': job_title,
                    'job_url': job_url,
                    'location': cells[2],
                    'work_model': cells[3],
                    'date_posted': cells[4]
                }

                jobs.append(job)

        print(f"\n✓ Successfully parsed {len(jobs)} jobs from README")

        if jobs:
            print("\n" + "=" * 80)
            print("SAMPLE JOB ENTRY:")
            print("=" * 80)
            print(json.dumps(jobs[0], indent=2))

            print("\n" + "=" * 80)
            print("AVAILABLE FIELDS:")
            print("=" * 80)
            print(list(jobs[0].keys()))

            # Save to file
            output_file = '/home/user/Hidden-Gems/jobright_parsed_output.json'
            with open(output_file, 'w') as f:
                json.dump(jobs, f, indent=2)
            print(f"\n✓ Saved {len(jobs)} jobs to {output_file}")

        return jobs

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 80)
    print("JOBRIGHT-AI MARKDOWN PARSER TEST")
    print("=" * 80)
    print("\nNote: This repo only contains jobs from the last 7 days")
    print("      Jobs are updated daily\n")

    jobs = parse_jobright_markdown()

    if jobs:
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Total jobs parsed: {len(jobs)}")
        print(f"Data source: GitHub README markdown table")
        print(f"Update frequency: Daily")
        print(f"Job history: Last 7 days only")

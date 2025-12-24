#!/usr/bin/env python3
"""
Use Playwright to fetch Simplify.jobs company data
"""

import subprocess
import json
import re
import os

DATA_DIR = "/home/user/Hidden-Gems/data"

def fetch_with_playwright():
    """Use playwright to fetch the sitemap"""

    # First try fetching the sitemap directly
    js_code = '''
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    const page = await context.newPage();

    try {
        // Try the sitemap first
        console.log("Trying sitemap...");
        const response = await page.goto('https://simplify.jobs/sitemap/companies.xml', {
            waitUntil: 'networkidle',
            timeout: 60000
        });

        if (response.ok()) {
            const content = await page.content();
            console.log("SITEMAP_START");
            console.log(content);
            console.log("SITEMAP_END");
        } else {
            console.log("Sitemap failed with status:", response.status());

            // Try the companies list page
            console.log("Trying companies-list page...");
            await page.goto('https://simplify.jobs/companies-list', {
                waitUntil: 'networkidle',
                timeout: 60000
            });

            // Wait for content to load
            await page.waitForTimeout(3000);

            const content = await page.content();
            console.log("PAGE_START");
            console.log(content);
            console.log("PAGE_END");
        }
    } catch (e) {
        console.log("Error:", e.message);
    }

    await browser.close();
})();
'''

    # Write the JS file
    js_file = "/tmp/fetch_simplify.js"
    with open(js_file, 'w') as f:
        f.write(js_code)

    # Run with node
    result = subprocess.run(
        ['node', js_file],
        capture_output=True,
        text=True,
        timeout=120
    )

    print("STDOUT:", result.stdout[:5000] if result.stdout else "None")
    print("STDERR:", result.stderr[:2000] if result.stderr else "None")

    return result.stdout

if __name__ == "__main__":
    print("Fetching Simplify.jobs with Playwright...")
    output = fetch_with_playwright()

    # Extract company URLs from sitemap if found
    if "SITEMAP_START" in output:
        sitemap_content = output.split("SITEMAP_START")[1].split("SITEMAP_END")[0]

        # Extract company slugs
        pattern = re.compile(r'simplify\.jobs/c/([^"/<\s]+)')
        companies = set(m.lower() for m in pattern.findall(sitemap_content))

        print(f"\nFound {len(companies)} companies in sitemap")

        if companies:
            with open(f"{DATA_DIR}/simplify_sitemap_companies.txt", 'w') as f:
                for c in sorted(companies):
                    f.write(c + "\n")
            print(f"Saved to {DATA_DIR}/simplify_sitemap_companies.txt")

    elif "PAGE_START" in output:
        page_content = output.split("PAGE_START")[1].split("PAGE_END")[0]

        # Extract company links
        pattern = re.compile(r'href="[^"]*?/c/([^"/?]+)"')
        companies = set(m.lower() for m in pattern.findall(page_content))

        print(f"\nFound {len(companies)} companies in page")

        if companies:
            with open(f"{DATA_DIR}/simplify_page_companies.txt", 'w') as f:
                for c in sorted(companies):
                    f.write(c + "\n")
            print(f"Saved to {DATA_DIR}/simplify_page_companies.txt")

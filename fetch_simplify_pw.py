#!/usr/bin/env python3
"""
Use Playwright to fetch Simplify.jobs company data
"""

from playwright.sync_api import sync_playwright
import re
import os
import time

DATA_DIR = "/home/user/Hidden-Gems/data"

def fetch_simplify_data():
    companies = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        # Try the sitemap first
        print("Trying to fetch sitemap...")
        try:
            response = page.goto('https://simplify.jobs/sitemap/companies.xml', wait_until='networkidle', timeout=60000)
            if response and response.ok:
                content = page.content()
                print(f"Sitemap loaded, content length: {len(content)}")

                # Save raw content
                with open(f"{DATA_DIR}/simplify_sitemap_raw.xml", 'w') as f:
                    f.write(content)

                # Extract company slugs
                pattern = re.compile(r'simplify\.jobs/c/([^"/<\s&]+)')
                matches = pattern.findall(content)
                companies.update(m.lower() for m in matches if m and len(m) > 1)
                print(f"Found {len(companies)} companies in sitemap")
            else:
                print(f"Sitemap returned status: {response.status if response else 'No response'}")
        except Exception as e:
            print(f"Sitemap error: {e}")

        # If sitemap didn't work well, try the companies-list page
        if len(companies) < 100:
            print("\nTrying companies-list page...")
            try:
                page.goto('https://simplify.jobs/companies-list', wait_until='networkidle', timeout=60000)
                time.sleep(3)  # Wait for JS to render

                content = page.content()
                print(f"Page loaded, content length: {len(content)}")

                # Save raw content
                with open(f"{DATA_DIR}/simplify_companieslist_raw.html", 'w') as f:
                    f.write(content)

                # Extract company links
                pattern = re.compile(r'href="[^"]*?/c/([^"/?&]+)"')
                matches = pattern.findall(content)
                companies.update(m.lower() for m in matches if m and len(m) > 1)
                print(f"Total companies so far: {len(companies)}")

                # Try scrolling to load more
                print("Scrolling to load more content...")
                for i in range(5):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    content = page.content()
                    matches = pattern.findall(content)
                    new_count = len(set(m.lower() for m in matches))
                    print(f"  Scroll {i+1}: {new_count} companies found")
                    companies.update(m.lower() for m in matches if m and len(m) > 1)

            except Exception as e:
                print(f"Companies-list error: {e}")

        # Try the /companies page as well
        if len(companies) < 1000:
            print("\nTrying /companies page...")
            try:
                page.goto('https://simplify.jobs/companies', wait_until='networkidle', timeout=60000)
                time.sleep(3)

                content = page.content()
                print(f"Companies page loaded, content length: {len(content)}")

                with open(f"{DATA_DIR}/simplify_companies_raw.html", 'w') as f:
                    f.write(content)

                pattern = re.compile(r'href="[^"]*?/c/([^"/?&]+)"')
                matches = pattern.findall(content)
                companies.update(m.lower() for m in matches if m and len(m) > 1)
                print(f"Total companies: {len(companies)}")

                # Scroll and load more
                print("Scrolling to load more...")
                for i in range(10):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    content = page.content()
                    matches = pattern.findall(content)
                    companies.update(m.lower() for m in matches if m and len(m) > 1)
                    print(f"  Scroll {i+1}: total {len(companies)} companies")

            except Exception as e:
                print(f"Companies page error: {e}")

        browser.close()

    return companies

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)

    print("="*60)
    print("Fetching Simplify.jobs companies with Playwright")
    print("="*60)

    companies = fetch_simplify_data()

    if companies:
        # Save companies
        output_file = f"{DATA_DIR}/simplify_playwright_companies.txt"
        with open(output_file, 'w') as f:
            for c in sorted(companies):
                f.write(c + "\n")
        print(f"\nSaved {len(companies)} companies to {output_file}")
    else:
        print("\nNo companies found")

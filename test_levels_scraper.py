#!/usr/bin/env python3
"""Tests for the levels.fyi salary scraper"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from aggregator.levels_scraper import LevelsScraper


class TestCacheExpiry(unittest.TestCase):
    """Test cache expiration logic"""

    def setUp(self):
        """Create a temp cache file for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, ".levels_salary_cache.json")

    def tearDown(self):
        """Clean up temp files"""
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rmdir(self.temp_dir)

    def _create_scraper_with_cache(self, cache_data):
        """Helper to create a scraper with pre-populated cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f)
        with patch.object(LevelsScraper, 'CACHE_FILE', self.cache_file):
            return LevelsScraper()

    def test_404_expires_after_30_days(self):
        """404 entries should expire after 30 days"""
        old_date = (datetime.now() - timedelta(days=31)).strftime("%Y-%m-%d")
        cache = {
            "found": {},
            "not_found": {
                "old-company": {"date": old_date, "reason": "404"}
            }
        }
        scraper = self._create_scraper_with_cache(cache)
        self.assertNotIn("old-company", scraper._not_found_cache)

    def test_404_not_expired_within_30_days(self):
        """404 entries should not expire within 30 days"""
        recent_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        cache = {
            "found": {},
            "not_found": {
                "recent-company": {"date": recent_date, "reason": "404"}
            }
        }
        scraper = self._create_scraper_with_cache(cache)
        self.assertIn("recent-company", scraper._not_found_cache)

    def test_no_swe_data_expires_after_14_days(self):
        """no_swe_data entries should expire after 14 days"""
        old_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        cache = {
            "found": {},
            "not_found": {
                "no-swe-company": {"date": old_date, "reason": "no_swe_data"}
            }
        }
        scraper = self._create_scraper_with_cache(cache)
        self.assertNotIn("no-swe-company", scraper._not_found_cache)

    def test_no_entry_level_expires_after_7_days(self):
        """no_entry_level entries should expire after 7 days"""
        old_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        cache = {
            "found": {},
            "not_found": {
                "no-entry-company": {"date": old_date, "reason": "no_entry_level"}
            }
        }
        scraper = self._create_scraper_with_cache(cache)
        self.assertNotIn("no-entry-company", scraper._not_found_cache)

    def test_unknown_reason_defaults_to_7_days(self):
        """Unknown reasons should default to 7-day expiry"""
        old_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        cache = {
            "found": {},
            "not_found": {
                "unknown-company": {"date": old_date, "reason": "some_unknown_reason"}
            }
        }
        scraper = self._create_scraper_with_cache(cache)
        self.assertNotIn("unknown-company", scraper._not_found_cache)

    def test_salary_cache_persists(self):
        """Salary cache entries should persist (no expiry)"""
        cache = {
            "found": {
                "google": [150000, 200000]
            },
            "not_found": {}
        }
        scraper = self._create_scraper_with_cache(cache)
        self.assertEqual(scraper._salary_cache["google"], (150000, 200000))


class TestCompanyNormalization(unittest.TestCase):
    """Test company name normalization"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, ".levels_salary_cache.json")
        with open(self.cache_file, 'w') as f:
            json.dump({"found": {}, "not_found": {}}, f)
        with patch.object(LevelsScraper, 'CACHE_FILE', self.cache_file):
            self.scraper = LevelsScraper()

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rmdir(self.temp_dir)

    def test_lowercase(self):
        """Should lowercase company names"""
        self.assertEqual(self.scraper._normalize_company("Google"), "google")

    def test_spaces_to_dashes(self):
        """Should convert spaces to dashes"""
        self.assertEqual(self.scraper._normalize_company("Jane Street"), "jane-street")

    def test_removes_special_chars(self):
        """Should remove special characters"""
        result = self.scraper._normalize_company("Company (Inc.)")
        self.assertNotIn("(", result)
        self.assertNotIn(")", result)
        self.assertNotIn(".", result)


class TestNotFoundCache(unittest.TestCase):
    """Test not-found cache behavior"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, ".levels_salary_cache.json")
        with open(self.cache_file, 'w') as f:
            json.dump({"found": {}, "not_found": {}}, f)
        with patch.object(LevelsScraper, 'CACHE_FILE', self.cache_file):
            self.scraper = LevelsScraper()

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rmdir(self.temp_dir)

    def test_add_not_found_stores_date_and_reason(self):
        """_add_not_found should store date and reason"""
        self.scraper._add_not_found("test-company", "404")
        entry = self.scraper._not_found_cache["test-company"]
        self.assertEqual(entry["reason"], "404")
        self.assertEqual(entry["date"], datetime.now().strftime("%Y-%m-%d"))

    def test_cached_not_found_returns_none(self):
        """Companies in not-found cache should return (None, None)"""
        self.scraper._not_found_cache["cached-company"] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reason": "404"
        }
        result = self.scraper.get_salary("cached-company")
        self.assertEqual(result, (None, None))


class TestSalaryCache(unittest.TestCase):
    """Test salary cache behavior"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, ".levels_salary_cache.json")
        with open(self.cache_file, 'w') as f:
            json.dump({"found": {}, "not_found": {}}, f)
        with patch.object(LevelsScraper, 'CACHE_FILE', self.cache_file):
            self.scraper = LevelsScraper()

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rmdir(self.temp_dir)

    def test_cached_salary_returns_immediately(self):
        """Cached salaries should return without HTTP request"""
        self.scraper._salary_cache["cached-company"] = (100000, 150000)
        with patch.object(self.scraper, '_fetch_salary') as mock_fetch:
            result = self.scraper.get_salary("cached-company")
            mock_fetch.assert_not_called()
            self.assertEqual(result, (100000, 150000))

    def test_save_and_load_cache(self):
        """Cache should persist across scraper instances"""
        with patch.object(LevelsScraper, 'CACHE_FILE', self.cache_file):
            scraper = LevelsScraper()
            scraper._salary_cache["test-company"] = (120000, 180000)
            scraper._not_found_cache["missing-company"] = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "reason": "404"
            }
            scraper._save_cache()

            # Create new scraper instance
            new_scraper = LevelsScraper()

            self.assertEqual(new_scraper._salary_cache["test-company"], (120000, 180000))
            self.assertIn("missing-company", new_scraper._not_found_cache)


class TestExpiryDays(unittest.TestCase):
    """Test EXPIRY_DAYS configuration"""

    def test_expiry_days_values(self):
        """Verify expiry day values are correct"""
        self.assertEqual(LevelsScraper.EXPIRY_DAYS["404"], 30)
        self.assertEqual(LevelsScraper.EXPIRY_DAYS["no_swe_data"], 14)
        self.assertEqual(LevelsScraper.EXPIRY_DAYS["no_entry_level"], 7)


if __name__ == "__main__":
    unittest.main(verbosity=2)

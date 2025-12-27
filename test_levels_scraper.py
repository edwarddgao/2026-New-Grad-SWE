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


class TestEntryLevelDetection(unittest.TestCase):
    """Test entry-level detection logic - covers Fix #3 and Fix #4"""

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

    def test_is_entry_level_exact_match(self):
        """Exact match should work"""
        entry_slugs = {'sde', 'associate'}
        self.assertTrue(self.scraper._is_entry_level('sde', entry_slugs))
        self.assertTrue(self.scraper._is_entry_level('associate', entry_slugs))

    def test_is_entry_level_case_insensitive(self):
        """Matching should be case-insensitive"""
        entry_slugs = {'sde', 'associate'}
        self.assertTrue(self.scraper._is_entry_level('SDE', entry_slugs))
        self.assertTrue(self.scraper._is_entry_level('Associate', entry_slugs))

    def test_is_entry_level_suffix_i(self):
        """Level ending with -i should match base slug (sde-i matches sde)"""
        entry_slugs = {'sde', 'associate'}
        self.assertTrue(self.scraper._is_entry_level('sde-i', entry_slugs))

    def test_is_entry_level_suffix_1(self):
        """Level ending with -1 should match base slug"""
        entry_slugs = {'sde', 'software-engineer'}
        self.assertTrue(self.scraper._is_entry_level('sde-1', entry_slugs))
        self.assertTrue(self.scraper._is_entry_level('software-engineer-1', entry_slugs))

    def test_is_entry_level_suffix_numeral(self):
        """Level ending with 1 (no dash) should match"""
        entry_slugs = {'sde'}
        self.assertTrue(self.scraper._is_entry_level('sde1', entry_slugs))

    def test_is_entry_level_roman_numeral_i(self):
        """Standalone roman numeral I should be entry level"""
        entry_slugs = set()
        self.assertTrue(self.scraper._is_entry_level('i', entry_slugs))
        self.assertTrue(self.scraper._is_entry_level('software-engineer-i', entry_slugs))

    def test_is_entry_level_hardcoded_patterns(self):
        """Common entry-level patterns should match even without entry_slugs"""
        entry_slugs = set()  # Empty - rely on hardcoded patterns

        # These should all be recognized as entry-level
        patterns = [
            'new-grad', 'entry-level', 'junior', 'associate', 'graduate', 'grad',
            'software-engineer-i', 'software-engineer-1',
            'swe-i', 'swe-1', 'swe1',
            'sde-i', 'sde-1', 'sde1',
            'l1', 'l2', 'l3',  # Meta/Google style
            'e1', 'e2', 'e3',  # Meta/Uber style
            'ic1', 'ic2',      # Apple style
            'p1', 'p2',        # Some companies
        ]
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    self.scraper._is_entry_level(pattern, entry_slugs),
                    f"'{pattern}' should be recognized as entry-level"
                )

    def test_is_entry_level_not_senior(self):
        """Senior/staff levels should NOT match"""
        entry_slugs = {'sde'}

        non_entry_levels = [
            'senior', 'staff', 'principal', 'lead', 'manager',
            'sde-iii', 'sde-iv', 'sde-3', 'sde-4',
            'l5', 'l6', 'l7', 'l8',
            'e5', 'e6', 'e7',
            'ic4', 'ic5', 'ic6',
            'p4', 'p5', 'p6',
        ]
        for level in non_entry_levels:
            with self.subTest(level=level):
                self.assertFalse(
                    self.scraper._is_entry_level(level, entry_slugs),
                    f"'{level}' should NOT be recognized as entry-level"
                )

    def test_pagerduty_case(self):
        """Real case: pagerduty has entry_slugs=['sde', 'associate'] but data is in 'sde-i'"""
        entry_slugs = {'sde', 'associate-software-engineer'}
        self.assertTrue(self.scraper._is_entry_level('sde-i', entry_slugs))

    def test_canonical_case(self):
        """Real case: canonical has entry_slugs=['graduate'] but data is in 'software-engineer-i'"""
        entry_slugs = {'graduate'}
        # software-engineer-i should match as entry level via hardcoded patterns
        self.assertTrue(self.scraper._is_entry_level('software-engineer-i', entry_slugs))


class TestPercentilesFallback(unittest.TestCase):
    """Test fallback to percentiles/median for small sample sizes - covers Fix #1"""

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

    def _mock_response(self, averages, median, percentiles):
        """Create a mock response with given data structure"""
        next_data = {
            "props": {
                "pageProps": {
                    "averages": averages,
                    "median": median,
                    "percentiles": percentiles,
                    "levels": {"levels": []}
                }
            }
        }
        html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>'
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        return mock_resp

    def test_uses_median_when_averages_empty_small_sample(self):
        """When averages is empty but sample count is small, use median.commonRange"""
        mock_resp = self._mock_response(
            averages=[],  # Empty - no level breakdown
            median={
                "count": 2,
                "commonRangeStart": 57408,
                "commonRangeEnd": 66768,
            },
            percentiles={"tc": {"p25": 62400, "p75": 140000}}
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('synectics')

        # Should use median.commonRange for small sample sizes
        self.assertEqual(result, (57408, 66768))

    def test_no_fallback_when_sample_large(self):
        """When averages is empty and sample count is large, don't use fallback"""
        mock_resp = self._mock_response(
            averages=[],  # Empty - no level breakdown
            median={
                "count": 20,  # Large sample - mixed seniority
                "commonRangeStart": 0,
                "commonRangeEnd": 0,
            },
            percentiles={"tc": {"p25": 150000, "p75": 443000}}
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('domino-data-lab')

        # Should NOT fallback - too many samples means mixed seniority
        self.assertEqual(result, (None, None))

    def test_no_fallback_when_median_zero(self):
        """When median.commonRange is 0, don't use fallback even for small samples"""
        mock_resp = self._mock_response(
            averages=[],
            median={
                "count": 3,
                "commonRangeStart": 0,
                "commonRangeEnd": 0,
            },
            percentiles={"tc": {"p25": 100000, "p75": 200000}}
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('test-company')

        self.assertEqual(result, (None, None))

    def test_fallback_threshold(self):
        """Fallback should only apply when sample count <= 5"""
        # Test boundary: 5 samples should use fallback
        mock_resp_5 = self._mock_response(
            averages=[],
            median={"count": 5, "commonRangeStart": 80000, "commonRangeEnd": 100000},
            percentiles={"tc": {"p25": 80000, "p75": 150000}}
        )
        with patch.object(self.scraper.session, 'get', return_value=mock_resp_5):
            result = self.scraper._fetch_salary('company-5')
        self.assertEqual(result, (80000, 100000))

        # Test boundary: 6 samples should NOT use fallback
        mock_resp_6 = self._mock_response(
            averages=[],
            median={"count": 6, "commonRangeStart": 80000, "commonRangeEnd": 100000},
            percentiles={"tc": {"p25": 80000, "p75": 150000}}
        )
        with patch.object(self.scraper.session, 'get', return_value=mock_resp_6):
            result = self.scraper._fetch_salary('company-6')
        self.assertEqual(result, (None, None))


class TestEntryLevelWithMockedData(unittest.TestCase):
    """Test entry-level detection with mocked API responses"""

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

    def _mock_response(self, levels_list, averages):
        """Create a mock response with given levels and averages"""
        next_data = {
            "props": {
                "pageProps": {
                    "averages": averages,
                    "median": {"count": 10},
                    "percentiles": {},
                    "levels": {"levels": levels_list}
                }
            }
        }
        html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>'
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        return mock_resp

    def test_valon_p2_match(self):
        """Valon: order=0 has titleSlugs=['p2'], averages has 'p2' level"""
        mock_resp = self._mock_response(
            levels_list=[
                {"order": 0, "titleSlugs": ["p2"]},
                {"order": 1, "titleSlugs": ["p3"]},
            ],
            averages=[
                {"level": "p2", "samples": [
                    {"yearsOfExperience": 0, "totalCompensation": 200000},
                    {"yearsOfExperience": 2, "totalCompensation": 205000},
                ]},
                {"level": "p3", "samples": [
                    {"yearsOfExperience": 3, "totalCompensation": 250000},
                ]},
            ]
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('valon')

        self.assertEqual(result, (200000, 205000))

    def test_pagerduty_sde_i_match(self):
        """Pagerduty: order=0 has ['sde', 'associate-swe'], averages has 'sde-i'"""
        mock_resp = self._mock_response(
            levels_list=[
                {"order": 0, "titleSlugs": ["sde", "associate-software-engineer"]},
                {"order": 1, "titleSlugs": ["sde-ii"]},
            ],
            averages=[
                {"level": "sde-i", "samples": [
                    {"yearsOfExperience": 0, "totalCompensation": 120000},
                    {"yearsOfExperience": 1, "totalCompensation": 130000},
                ]},
                {"level": "sde-ii", "samples": [
                    {"yearsOfExperience": 3, "totalCompensation": 180000},
                ]},
            ]
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('pagerduty')

        # sde-i should match because it starts with 'sde'
        self.assertEqual(result, (120000, 130000))

    def test_canonical_software_engineer_i(self):
        """Canonical: order=0 has ['graduate'], averages has 'software-engineer-i'"""
        mock_resp = self._mock_response(
            levels_list=[
                {"order": 0, "titleSlugs": ["graduate"]},
            ],
            averages=[
                {"level": "software-engineer-i", "samples": [
                    {"yearsOfExperience": 1, "totalCompensation": 95000},
                ]},
            ]
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('canonical')

        # software-engineer-i should match via hardcoded patterns
        self.assertEqual(result, (95000, 95000))

    def test_filters_by_yoe(self):
        """Should only include samples with YOE <= MAX_NEW_GRAD_YOE"""
        mock_resp = self._mock_response(
            levels_list=[{"order": 0, "titleSlugs": ["l3"]}],
            averages=[
                {"level": "l3", "samples": [
                    {"yearsOfExperience": 0, "totalCompensation": 150000},
                    {"yearsOfExperience": 2, "totalCompensation": 170000},
                    {"yearsOfExperience": 5, "totalCompensation": 250000},  # Should be filtered
                    {"yearsOfExperience": 10, "totalCompensation": 350000}, # Should be filtered
                ]},
            ]
        )

        with patch.object(self.scraper.session, 'get', return_value=mock_resp):
            result = self.scraper._fetch_salary('test-company')

        # Only YOE 0 and 2 should be included (150k and 170k)
        self.assertEqual(result, (150000, 170000))


class TestEntryLevelsMapping(unittest.TestCase):
    """Test ENTRY_LEVELS manual mapping coverage"""

    def test_entry_levels_has_major_companies(self):
        """ENTRY_LEVELS should have mappings for major tech companies"""
        required_companies = [
            'google', 'meta', 'apple', 'amazon', 'microsoft', 'netflix',
            'stripe', 'coinbase', 'uber', 'lyft', 'airbnb',
            'openai', 'anthropic', 'databricks', 'snowflake',
        ]
        for company in required_companies:
            with self.subTest(company=company):
                self.assertIn(
                    company,
                    LevelsScraper.ENTRY_LEVELS,
                    f"ENTRY_LEVELS should include '{company}'"
                )

    def test_entry_levels_values_are_valid(self):
        """All ENTRY_LEVELS values should be non-empty strings"""
        for company, level in LevelsScraper.ENTRY_LEVELS.items():
            with self.subTest(company=company):
                self.assertIsInstance(level, str)
                self.assertTrue(len(level) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

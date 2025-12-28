#!/usr/bin/env python3
"""
Tests for SpeedyApplySource job parsing
"""

import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from aggregator.sources import SpeedyApplySource, Job


class TestSpeedyApplySource(unittest.TestCase):
    """Test the SpeedyApply source parsing"""

    def setUp(self):
        self.source = SpeedyApplySource()

    # ===== Salary Parsing Tests =====

    def test_parse_salary_annual_with_k(self):
        """Should parse '$172k/yr' to (172000, 172000)"""
        result = self.source._parse_salary("$172k/yr")
        self.assertEqual(result, (172000, 172000))

    def test_parse_salary_annual_without_suffix(self):
        """Should parse '$150k' to (150000, 150000)"""
        result = self.source._parse_salary("$150k")
        self.assertEqual(result, (150000, 150000))

    def test_parse_salary_hourly(self):
        """Should parse '$62/hr' to annual (62 * 2080 = 128960)"""
        result = self.source._parse_salary("$62/hr")
        self.assertEqual(result, (128960, 128960))

    def test_parse_salary_hourly_with_decimals(self):
        """Should parse '$55.5/hr' correctly"""
        result = self.source._parse_salary("$55.5/hr")
        expected = int(55.5 * 2080)
        self.assertEqual(result, (expected, expected))

    def test_parse_salary_empty(self):
        """Should return (None, None) for empty string"""
        result = self.source._parse_salary("")
        self.assertEqual(result, (None, None))

    def test_parse_salary_none(self):
        """Should return (None, None) for None"""
        result = self.source._parse_salary(None)
        self.assertEqual(result, (None, None))

    def test_parse_salary_invalid(self):
        """Should return (None, None) for invalid format"""
        result = self.source._parse_salary("competitive")
        self.assertEqual(result, (None, None))

    # ===== Age Parsing Tests =====

    def test_parse_age_zero_days(self):
        """Should return today's date for 0 days"""
        result = self.source._parse_age(0)
        expected = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(result, expected)

    def test_parse_age_one_day(self):
        """Should return yesterday's date for 1 day"""
        result = self.source._parse_age(1)
        expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(result, expected)

    def test_parse_age_week(self):
        """Should return correct date for 7 days ago"""
        result = self.source._parse_age(7)
        expected = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.assertEqual(result, expected)

    # ===== Markdown Parsing Tests =====

    def test_parse_row_with_salary(self):
        """Should parse a row with salary column"""
        markdown = '''| Company | Position | Location | Salary | Posting | Age |
|---|---|---|---|---|---|
| <a href="https://www.nvidia.com"><strong>NVIDIA</strong></a> | Firmware Engineer - New College Grad 2026 | Santa Clara, CA | $172k/yr | <a href="https://nvidia.wd5.myworkdayjobs.com/job/123"><img src="img.png" alt="Apply" width="70"/></a> | 4d |
'''
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = markdown
            mock_get.return_value = mock_response

            jobs = self.source.fetch()

            self.assertEqual(len(jobs), 1)
            job = jobs[0]
            self.assertEqual(job.company, "NVIDIA")
            self.assertEqual(job.title, "Firmware Engineer - New College Grad 2026")
            self.assertEqual(job.location, "Santa Clara, CA")
            self.assertEqual(job.salary_min, 172000)
            self.assertEqual(job.salary_max, 172000)
            self.assertEqual(job.url, "https://nvidia.wd5.myworkdayjobs.com/job/123")
            self.assertEqual(job.source, "speedyapply")
            self.assertEqual(job.experience_level, "new_grad")

    def test_parse_row_without_salary(self):
        """Should parse a row without salary column"""
        markdown = '''| Company | Position | Location | Posting | Age |
|---|---|---|---|---|
| <a href="https://www.blackrock.com/"><strong>BlackRock</strong></a> | Associate - Data Engineer | New York, NY | <a href="https://blackrock.wd1.myworkdayjobs.com/job/456"><img src="img.png" alt="Apply" width="70"/></a> | 4d |
'''
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = markdown
            mock_get.return_value = mock_response

            jobs = self.source.fetch()

            self.assertEqual(len(jobs), 1)
            job = jobs[0]
            self.assertEqual(job.company, "BlackRock")
            self.assertEqual(job.title, "Associate - Data Engineer")
            self.assertEqual(job.location, "New York, NY")
            self.assertIsNone(job.salary_min)
            self.assertIsNone(job.salary_max)
            self.assertEqual(job.url, "https://blackrock.wd1.myworkdayjobs.com/job/456")

    def test_parse_multiple_rows(self):
        """Should parse multiple job rows"""
        markdown = '''| Company | Position | Location | Salary | Posting | Age |
|---|---|---|---|---|---|
| <a href="https://www.nvidia.com"><strong>NVIDIA</strong></a> | Software Engineer | Santa Clara, CA | $180k/yr | <a href="https://nvidia.com/job/1"><img src="img.png" alt="Apply"/></a> | 2d |
| <a href="https://www.twitch.tv"><strong>Twitch</strong></a> | Software Engineer I | San Francisco, CA | $193k/yr | <a href="https://twitch.com/job/2"><img src="img.png" alt="Apply"/></a> | 10d |
'''
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = markdown
            mock_get.return_value = mock_response

            jobs = self.source.fetch()

            self.assertEqual(len(jobs), 2)
            self.assertEqual(jobs[0].company, "NVIDIA")
            self.assertEqual(jobs[1].company, "Twitch")

    def test_deduplicate_urls(self):
        """Should deduplicate jobs with same URL"""
        markdown = '''| Company | Position | Location | Salary | Posting | Age |
|---|---|---|---|---|---|
| <a href="https://www.nvidia.com"><strong>NVIDIA</strong></a> | Software Engineer | Santa Clara, CA | $180k/yr | <a href="https://nvidia.com/job/1"><img src="img.png" alt="Apply"/></a> | 2d |
| <a href="https://www.nvidia.com"><strong>NVIDIA</strong></a> | Software Engineer | Santa Clara, CA | $180k/yr | <a href="https://nvidia.com/job/1"><img src="img.png" alt="Apply"/></a> | 2d |
'''
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = markdown
            mock_get.return_value = mock_response

            jobs = self.source.fetch()

            self.assertEqual(len(jobs), 1)

    def test_handle_request_error(self):
        """Should return empty list on request error"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            jobs = self.source.fetch()

            self.assertEqual(jobs, [])

    def test_handle_non_200_response(self):
        """Should return empty list on non-200 response"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            jobs = self.source.fetch()

            self.assertEqual(jobs, [])

    def test_parse_hourly_salary_in_row(self):
        """Should correctly convert hourly rate to annual in job row"""
        markdown = '''| Company | Position | Location | Salary | Posting | Age |
|---|---|---|---|---|---|
| <a href="https://www.nvidia.com"><strong>NVIDIA</strong></a> | Intern | Santa Clara, CA | $62/hr | <a href="https://nvidia.com/job/intern"><img src="img.png" alt="Apply"/></a> | 1d |
'''
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = markdown
            mock_get.return_value = mock_response

            jobs = self.source.fetch()

            self.assertEqual(len(jobs), 1)
            # $62/hr * 2080 hours = $128,960
            self.assertEqual(jobs[0].salary_min, 128960)
            self.assertEqual(jobs[0].salary_max, 128960)


class TestSpeedyApplySourceIntegration(unittest.TestCase):
    """Integration tests that hit the real API (skip in CI)"""

    @unittest.skip("Integration test - run manually")
    def test_fetch_real_jobs(self):
        """Fetch real jobs from SpeedyApply repo"""
        source = SpeedyApplySource()
        jobs = source.fetch()

        # Should fetch some jobs
        self.assertGreater(len(jobs), 0)

        # All jobs should have required fields
        for job in jobs:
            self.assertIsInstance(job, Job)
            self.assertTrue(job.company)
            self.assertTrue(job.title)
            self.assertTrue(job.url)
            self.assertEqual(job.source, "speedyapply")


if __name__ == "__main__":
    unittest.main()

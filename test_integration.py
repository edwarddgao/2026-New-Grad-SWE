"""
Integration tests for the job aggregation pipeline.

Tests the complete data flow: fetching → caching → deduplication → filtering → enrichment
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, Mock

from aggregator.sources import JobAggregator, Job, SimplifySource, SpeedyApplySource
from aggregator.filters import is_new_grad_swe


class TestJobAggregatorIntegration(unittest.TestCase):
    """Integration tests for JobAggregator.fetch_all() pipeline"""

    def setUp(self):
        """Set up test fixtures with sample job data"""
        # Sample jobs from curated sources
        self.simplify_jobs = [
            Job(
                id="s1",
                title="Software Engineer - New Grad",
                company="Google",
                company_slug="google",
                location="Mountain View, CA",
                url="https://google.com/careers/job/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
            Job(
                id="s2",
                title="Backend Engineer",
                company="Meta",
                company_slug="meta",
                location="Menlo Park, CA",
                url="https://meta.com/careers/job/2",
                source="simplify_new_grad",
                date_posted="2026-01-02",
            ),
        ]

        self.speedyapply_jobs = [
            Job(
                id="sp1",
                title="Software Engineer",
                company="Stripe",
                company_slug="stripe",
                location="San Francisco, CA",
                url="https://stripe.com/jobs/1",
                source="speedyapply",
                date_posted="2026-01-01",
                salary_min=180000,
                salary_max=180000,
                experience_level="new_grad",
            ),
        ]

        # Jobs from non-curated sources (for filtering tests)
        self.linkedin_jobs_mixed = [
            Job(
                id="li1",
                title="Junior Software Engineer",
                company="Startup Inc",
                company_slug="startup-inc",
                location="New York, NY",
                url="https://linkedin.com/jobs/1",
                source="linkedin",
                date_posted="2026-01-03",
            ),
            Job(
                id="li2",
                title="Senior Software Engineer",
                company="BigCorp",
                company_slug="bigcorp",
                location="New York, NY",
                url="https://linkedin.com/jobs/2",
                source="linkedin",
                date_posted="2026-01-03",
            ),
            Job(
                id="li3",
                title="Staff Engineer",
                company="TechCo",
                company_slug="techco",
                location="San Francisco, CA",
                url="https://linkedin.com/jobs/3",
                source="linkedin",
                date_posted="2026-01-03",
            ),
            Job(
                id="li4",
                title="Software Developer Entry Level",
                company="DevShop",
                company_slug="devshop",
                location="Austin, TX",
                url="https://linkedin.com/jobs/4",
                source="linkedin",
                date_posted="2026-01-03",
            ),
        ]

        # PhD jobs (should be filtered from all sources)
        self.phd_jobs = [
            Job(
                id="phd1",
                title="PhD Software Engineer",
                company="Research Corp",
                company_slug="research-corp",
                location="Boston, MA",
                url="https://research.com/jobs/1",
                source="simplify_new_grad",  # Even curated source
                date_posted="2026-01-03",
            ),
            Job(
                id="phd2",
                title="Research Scientist PhD",
                company="AI Lab",
                company_slug="ai-lab",
                location="Seattle, WA",
                url="https://ailab.com/jobs/1",
                source="linkedin",
                date_posted="2026-01-03",
            ),
        ]

        # Jobs with duplicate URLs (for deduplication tests)
        self.duplicate_url_jobs = [
            Job(
                id="dup1",
                title="Software Engineer",
                company="Acme",
                company_slug="acme",
                location="NYC",
                url="https://boards.greenhouse.io/acme/jobs/123",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
            Job(
                id="dup2",
                title="Software Engineer",
                company="Acme",
                company_slug="acme",
                location="NYC",
                url="https://boards.greenhouse.io/acme/jobs/123?gh_jid=456",
                source="linkedin",
                date_posted="2026-01-02",
            ),
            Job(
                id="dup3",
                title="Software Engineer",
                company="Acme",
                company_slug="acme",
                location="NYC",
                url="https://job-boards.greenhouse.io/acme/jobs/123",
                source="indeed",
                date_posted="2026-01-01",
            ),
        ]

        # Create temp directory for cache tests
        self.temp_dir = tempfile.mkdtemp()
        self.temp_cache_file = os.path.join(self.temp_dir, ".scraped_jobs_cache.json")

    def tearDown(self):
        """Clean up temp files"""
        if os.path.exists(self.temp_cache_file):
            os.remove(self.temp_cache_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_full_pipeline_basic_flow(self, mock_simplify, mock_speedyapply):
        """Test complete fetch_all pipeline with mocked sources"""
        mock_simplify.return_value = self.simplify_jobs
        mock_speedyapply.return_value = self.speedyapply_jobs

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            jobs = agg.fetch_all(skip_enrichment=True)

        # Assert jobs from both sources are present
        self.assertEqual(len(jobs), 3)

        # Assert all required fields are populated
        for job in jobs:
            self.assertIsNotNone(job.id)
            self.assertIsNotNone(job.title)
            self.assertIsNotNone(job.company)
            self.assertIsNotNone(job.company_slug)
            self.assertIsNotNone(job.url)
            self.assertIsNotNone(job.source)

        # Assert correct sources
        sources = {job.source for job in jobs}
        self.assertIn('simplify_new_grad', sources)
        self.assertIn('speedyapply', sources)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_deduplication_removes_duplicate_urls(self, mock_simplify, mock_speedyapply):
        """Test URL-based deduplication with query parameter normalization"""
        mock_simplify.return_value = self.duplicate_url_jobs
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            jobs = agg.fetch_all(skip_enrichment=True)

        # All three jobs have same normalized URL, only one should remain
        self.assertEqual(len(jobs), 1)

        # The remaining job should be the first one encountered
        self.assertEqual(jobs[0].id, "dup1")

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_filtering_removes_senior_roles(self, mock_simplify, mock_speedyapply):
        """Test that filtering removes senior/staff roles from non-curated sources"""
        mock_simplify.return_value = self.linkedin_jobs_mixed
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            jobs = agg.fetch_all(skip_enrichment=True)

        # Should keep: Junior Software Engineer, Software Developer Entry Level
        # Should filter: Senior Software Engineer, Staff Engineer
        self.assertEqual(len(jobs), 2)

        titles = [job.title for job in jobs]
        self.assertIn("Junior Software Engineer", titles)
        self.assertIn("Software Developer Entry Level", titles)
        self.assertNotIn("Senior Software Engineer", titles)
        self.assertNotIn("Staff Engineer", titles)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_filtering_keeps_curated_source_jobs(self, mock_simplify, mock_speedyapply):
        """Test that jobs from curated sources are kept regardless of title"""
        # Even ambiguous titles from curated sources should be kept
        curated_jobs = [
            Job(
                id="c1",
                title="Engineer",  # Ambiguous title
                company="Google",
                company_slug="google",
                location="NYC",
                url="https://google.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
            Job(
                id="c2",
                title="Technical Role",  # No SWE keywords
                company="Meta",
                company_slug="meta",
                location="SF",
                url="https://meta.com/1",
                source="speedyapply",
                date_posted="2026-01-03",
            ),
        ]
        mock_simplify.return_value = curated_jobs
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            jobs = agg.fetch_all(skip_enrichment=True)

        # Both jobs should be kept because they're from curated sources
        self.assertEqual(len(jobs), 2)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_filtering_removes_phd_from_all_sources(self, mock_simplify, mock_speedyapply):
        """Test that PhD jobs are filtered out from ALL sources including curated"""
        mock_simplify.return_value = self.phd_jobs
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            jobs = agg.fetch_all(skip_enrichment=True)

        # All PhD jobs should be filtered out
        self.assertEqual(len(jobs), 0)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    @patch('aggregator.sources.get_scraper')
    def test_enrichment_adds_salary_data(self, mock_get_scraper, mock_simplify, mock_speedyapply):
        """Test that enrichment adds salary data to jobs"""
        jobs_without_salary = [
            Job(
                id="e1",
                title="Software Engineer",
                company="Google",
                company_slug="google",
                location="NYC",
                url="https://google.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
        ]
        mock_simplify.return_value = jobs_without_salary
        mock_speedyapply.return_value = []

        # Mock the scraper to add salary data
        mock_scraper = Mock()
        def enrich_side_effect(jobs):
            enriched_count = 0
            for job in jobs:
                if not job.salary_min:
                    job.salary_min = 150000
                    job.salary_max = 200000
                    enriched_count += 1
            return enriched_count
        mock_scraper.enrich_jobs.side_effect = enrich_side_effect
        mock_get_scraper.return_value = mock_scraper

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            jobs = agg.fetch_all(skip_enrichment=False)

        # Verify enrichment was called
        mock_scraper.enrich_jobs.assert_called_once()

        # Verify salary data was added
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].salary_min, 150000)
        self.assertEqual(jobs[0].salary_max, 200000)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_cache_integration(self, mock_simplify, mock_speedyapply):
        """Test that job cache preserves jobs across multiple fetch_all calls"""
        # First fetch: return some jobs
        first_batch = [
            Job(
                id="cache1",
                title="Software Engineer",
                company="CacheCo",
                company_slug="cacheco",
                location="NYC",
                url="https://cacheco.com/1",
                source="linkedin",  # Scraped source that gets cached
                date_posted="2026-01-03",
            ),
        ]
        mock_simplify.return_value = first_batch
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg1 = JobAggregator()
            jobs1 = agg1.fetch_all(skip_enrichment=True)

        # Should have 1 job
        self.assertEqual(len(jobs1), 1)

        # Second fetch: return different jobs
        second_batch = [
            Job(
                id="cache2",
                title="Backend Developer",
                company="NewCo",
                company_slug="newco",
                location="SF",
                url="https://newco.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-04",
            ),
        ]
        mock_simplify.return_value = second_batch
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg2 = JobAggregator()
            jobs2 = agg2.fetch_all(skip_enrichment=True)

        # Should have 2 jobs: new one + cached one
        self.assertEqual(len(jobs2), 2)

        urls = {job.url for job in jobs2}
        self.assertIn("https://cacheco.com/1", urls)
        self.assertIn("https://newco.com/1", urls)

    @patch.object(SpeedyApplySource, 'fetch')
    @patch.object(SimplifySource, 'fetch')
    def test_location_filtering(self, mock_simplify, mock_speedyapply):
        """Test that location filtering works correctly"""
        jobs_various_locations = [
            Job(
                id="loc1",
                title="Software Engineer",
                company="NYC Corp",
                company_slug="nyc-corp",
                location="New York, NY",
                url="https://nyc.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
            Job(
                id="loc2",
                title="Software Engineer",
                company="SF Corp",
                company_slug="sf-corp",
                location="San Francisco, CA",
                url="https://sf.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
            Job(
                id="loc3",
                title="Software Engineer",
                company="TX Corp",
                company_slug="tx-corp",
                location="Austin, TX",
                url="https://tx.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
            Job(
                id="loc4",
                title="Software Engineer",
                company="Canada Corp",
                company_slug="canada-corp",
                location="Toronto, Ontario, Canada",
                url="https://canada.com/1",
                source="simplify_new_grad",
                date_posted="2026-01-03",
            ),
        ]
        mock_simplify.return_value = jobs_various_locations
        mock_speedyapply.return_value = []

        with patch.object(JobAggregator, 'CACHE_FILE', self.temp_cache_file):
            agg = JobAggregator()
            agg.fetch_all(skip_enrichment=True)
            filtered = agg.filter_location(["nyc", "california"])

        # Should keep NYC and SF, filter out TX and Canada
        self.assertEqual(len(filtered), 2)

        locations = [job.location for job in filtered]
        self.assertTrue(any("New York" in loc for loc in locations))
        self.assertTrue(any("San Francisco" in loc for loc in locations))


class TestFilteringLogic(unittest.TestCase):
    """Unit tests for the is_new_grad_swe filtering function"""

    def test_curated_sources_always_pass(self):
        """Jobs from curated sources pass regardless of title (except PhD)"""
        self.assertTrue(is_new_grad_swe("Random Title", "simplify_new_grad"))
        self.assertTrue(is_new_grad_swe("Random Title", "speedyapply"))
        self.assertTrue(is_new_grad_swe("Engineer", "simplify_internship"))

    def test_phd_always_filtered(self):
        """PhD jobs are always filtered, even from curated sources"""
        self.assertFalse(is_new_grad_swe("PhD Software Engineer", "simplify_new_grad"))
        self.assertFalse(is_new_grad_swe("Research Scientist PhD", "linkedin"))
        self.assertFalse(is_new_grad_swe("Software Engineer (PhD)", "speedyapply"))

    def test_senior_keywords_filtered(self):
        """Senior/staff/lead roles are filtered from non-curated sources"""
        self.assertFalse(is_new_grad_swe("Senior Software Engineer", "linkedin"))
        self.assertFalse(is_new_grad_swe("Staff Engineer", "indeed"))
        self.assertFalse(is_new_grad_swe("Lead Developer", "glassdoor"))
        self.assertFalse(is_new_grad_swe("Engineering Manager", "linkedin"))
        self.assertFalse(is_new_grad_swe("Principal Engineer", "indeed"))

    def test_swe_keywords_pass(self):
        """Jobs with SWE keywords pass from non-curated sources"""
        self.assertTrue(is_new_grad_swe("Software Engineer", "linkedin"))
        self.assertTrue(is_new_grad_swe("Backend Developer", "indeed"))
        self.assertTrue(is_new_grad_swe("Frontend Engineer", "glassdoor"))
        self.assertTrue(is_new_grad_swe("Full Stack Developer", "linkedin"))
        self.assertTrue(is_new_grad_swe("SWE I", "indeed"))

    def test_new_grad_with_engineer_passes(self):
        """Generic engineer with new grad keyword passes"""
        self.assertTrue(is_new_grad_swe("New Grad Engineer", "linkedin"))
        self.assertTrue(is_new_grad_swe("Entry Level Engineer", "indeed"))
        self.assertTrue(is_new_grad_swe("Junior Engineer", "glassdoor"))


if __name__ == "__main__":
    unittest.main()

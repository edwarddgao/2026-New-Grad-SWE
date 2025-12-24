#!/usr/bin/env python3
"""
Test the job filtering logic and show what gets filtered out
"""

import unittest
from aggregator.sources import JobAggregator, Job
from aggregator.filters import (
    is_new_grad_swe,
    CURATED_SOURCES,
    SENIOR_KEYWORDS,
    SWE_KEYWORDS,
    NON_SWE_KEYWORDS,
    NEW_GRAD_KEYWORDS
)


class TestJobFiltering(unittest.TestCase):
    """Test the filtering logic for non-curated sources"""

    def _should_keep(self, title: str, source: str = "linkedin") -> bool:
        """Check if a job should be kept based on filtering logic"""
        return is_new_grad_swe(title, source)

    # ===== Tests for KEEPING jobs =====

    def test_keep_software_engineer(self):
        """Should keep: Software Engineer"""
        self.assertTrue(self._should_keep("Software Engineer"))

    def test_keep_software_engineer_new_grad(self):
        """Should keep: Software Engineer - New Grad"""
        self.assertTrue(self._should_keep("Software Engineer - New Grad"))

    def test_keep_swe_2025(self):
        """Should keep: SWE 2025"""
        self.assertTrue(self._should_keep("SWE 2025"))

    def test_keep_frontend_developer(self):
        """Should keep: Frontend Developer"""
        self.assertTrue(self._should_keep("Frontend Developer"))

    def test_keep_backend_engineer(self):
        """Should keep: Backend Engineer"""
        self.assertTrue(self._should_keep("Backend Engineer"))

    def test_keep_fullstack_developer(self):
        """Should keep: Fullstack Developer"""
        self.assertTrue(self._should_keep("Fullstack Developer"))

    def test_keep_ml_engineer(self):
        """Should keep: ML Engineer"""
        self.assertTrue(self._should_keep("ML Engineer"))

    def test_keep_data_engineer(self):
        """Should keep: Data Engineer"""
        self.assertTrue(self._should_keep("Data Engineer"))

    def test_keep_devops_engineer(self):
        """Should keep: DevOps Engineer"""
        self.assertTrue(self._should_keep("DevOps Engineer"))

    def test_keep_platform_engineer(self):
        """Should keep: Platform Engineer"""
        self.assertTrue(self._should_keep("Platform Engineer"))

    def test_keep_junior_developer(self):
        """Should keep: Junior Developer"""
        self.assertTrue(self._should_keep("Junior Developer"))

    def test_keep_associate_software_engineer(self):
        """Should keep: Associate Software Engineer"""
        self.assertTrue(self._should_keep("Associate Software Engineer"))

    def test_keep_entry_level_engineer_with_new_grad(self):
        """Should keep: Entry Level Engineer (has new grad keyword + engineer)"""
        self.assertTrue(self._should_keep("Entry Level Engineer"))

    def test_keep_university_graduate_engineer(self):
        """Should keep: University Graduate Engineer"""
        self.assertTrue(self._should_keep("University Graduate Engineer"))

    def test_keep_curated_source(self):
        """Should keep: Any title from curated source (Simplify/Jobright)"""
        self.assertTrue(self._should_keep("Random Title", source="simplify_new_grad"))
        self.assertTrue(self._should_keep("Random Title", source="jobright"))

    # ===== Tests for FILTERING OUT jobs =====

    def test_filter_senior_software_engineer(self):
        """Should filter: Senior Software Engineer"""
        self.assertFalse(self._should_keep("Senior Software Engineer"))

    def test_filter_staff_engineer(self):
        """Should filter: Staff Engineer"""
        self.assertFalse(self._should_keep("Staff Engineer"))

    def test_filter_principal_engineer(self):
        """Should filter: Principal Engineer"""
        self.assertFalse(self._should_keep("Principal Engineer"))

    def test_filter_lead_developer(self):
        """Should filter: Lead Developer"""
        self.assertFalse(self._should_keep("Lead Developer"))

    def test_filter_engineering_manager(self):
        """Should filter: Engineering Manager"""
        self.assertFalse(self._should_keep("Engineering Manager"))

    def test_filter_director_of_engineering(self):
        """Should filter: Director of Engineering"""
        self.assertFalse(self._should_keep("Director of Engineering"))

    def test_filter_founding_engineer(self):
        """Should filter: Founding Engineer"""
        self.assertFalse(self._should_keep("Founding Engineer"))

    def test_filter_sr_software_engineer(self):
        """Should filter: Sr Software Engineer"""
        self.assertFalse(self._should_keep("Sr Software Engineer"))

    def test_filter_software_engineer_iii(self):
        """Should filter: Software Engineer III"""
        self.assertFalse(self._should_keep("Software Engineer III"))

    def test_filter_structural_engineer(self):
        """Should filter: Structural Engineer"""
        self.assertFalse(self._should_keep("Structural Engineer"))

    def test_filter_civil_engineer(self):
        """Should filter: Civil Engineer"""
        self.assertFalse(self._should_keep("Civil Engineer"))

    def test_filter_mechanical_engineer(self):
        """Should filter: Mechanical Engineer"""
        self.assertFalse(self._should_keep("Mechanical Engineer"))

    def test_filter_electrical_engineer(self):
        """Should filter: Electrical Engineer"""
        self.assertFalse(self._should_keep("Electrical Engineer"))

    def test_filter_sales_engineer(self):
        """Should filter: Sales Engineer"""
        self.assertFalse(self._should_keep("Sales Engineer"))

    def test_filter_solutions_engineer(self):
        """Should filter: Solutions Engineer"""
        self.assertFalse(self._should_keep("Solutions Engineer"))

    def test_filter_generic_engineer_no_swe(self):
        """Should filter: Engineer (generic, no SWE keyword, no new grad)"""
        self.assertFalse(self._should_keep("Engineer"))

    def test_filter_product_manager(self):
        """Should filter: Product Manager (no SWE keyword)"""
        self.assertFalse(self._should_keep("Product Manager"))


def show_filtered_jobs():
    """Show what jobs would be filtered out from each source"""
    print("\n" + "=" * 60)
    print("CHECKING FILTERED JOBS FROM NON-CURATED SOURCES")
    print("=" * 60)

    agg = JobAggregator()

    # Fetch all jobs
    print("\nFetching jobs...")
    agg.fetch_all(
        include_linkedin=True, linkedin_limit=100,
        include_builtin=True, builtin_cities=["nyc"],
        include_indeed=True, indeed_limit=50,
        include_hn=True, hn_limit=100
    )

    print("\n" + "-" * 60)
    print("JOBS THAT WOULD BE FILTERED OUT (by reason):")
    print("-" * 60)

    filtered_senior = []
    filtered_non_swe = []
    filtered_no_swe_keyword = []
    kept = []

    for job in agg.jobs:
        if job.source in CURATED_SOURCES:
            kept.append(job)
            continue

        title_lower = job.title.lower()

        # Check senior
        if any(kw in title_lower for kw in SENIOR_KEYWORDS):
            filtered_senior.append(job)
            continue

        # Check non-SWE
        if any(kw in title_lower for kw in NON_SWE_KEYWORDS):
            filtered_non_swe.append(job)
            continue

        # Check SWE keywords
        has_swe = any(kw in title_lower for kw in SWE_KEYWORDS)
        has_new_grad = any(kw in title_lower for kw in NEW_GRAD_KEYWORDS)

        if has_swe or (has_new_grad and 'engineer' in title_lower):
            kept.append(job)
        else:
            filtered_no_swe_keyword.append(job)

    # Print filtered jobs by category
    print(f"\n🚫 FILTERED: Senior/Staff roles ({len(filtered_senior)}):")
    for job in filtered_senior[:20]:
        print(f"   [{job.source}] {job.company}: {job.title}")
    if len(filtered_senior) > 20:
        print(f"   ... and {len(filtered_senior) - 20} more")

    print(f"\n🚫 FILTERED: Non-SWE engineering ({len(filtered_non_swe)}):")
    for job in filtered_non_swe[:20]:
        print(f"   [{job.source}] {job.company}: {job.title}")
    if len(filtered_non_swe) > 20:
        print(f"   ... and {len(filtered_non_swe) - 20} more")

    print(f"\n🚫 FILTERED: No SWE keyword ({len(filtered_no_swe_keyword)}):")
    for job in filtered_no_swe_keyword[:20]:
        print(f"   [{job.source}] {job.company}: {job.title}")
    if len(filtered_no_swe_keyword) > 20:
        print(f"   ... and {len(filtered_no_swe_keyword) - 20} more")

    print(f"\n✅ KEPT: {len(kept)} jobs")

    # Show sample of kept non-curated jobs
    print(f"\n📋 Sample of KEPT jobs from non-curated sources:")
    non_curated_kept = [j for j in kept if j.source not in CURATED_SOURCES]
    for job in non_curated_kept[:15]:
        print(f"   [{job.source}] {job.company}: {job.title}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_filtered_jobs()
    else:
        # Run unit tests
        unittest.main(verbosity=2)

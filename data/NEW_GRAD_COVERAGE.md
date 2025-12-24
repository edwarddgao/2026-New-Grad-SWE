# New Grad SWE Job Coverage Analysis

## Key Finding

**Simplify and Jobright are complementary sources, not subsets of each other.**

| Source | Active New Grad Jobs | Unique Companies |
|--------|---------------------|------------------|
| **Simplify** | 2,544 jobs | 950 companies |
| **Jobright** | ~600 jobs | 249 companies |
| **Overlap** | - | ~83 companies |

### What Each Source Adds

| If you use... | Companies | You miss... |
|---------------|-----------|-------------|
| Simplify only | 950 | ~166 from Jobright |
| Jobright only | 249 | ~859 from Simplify |
| **Both** | ~1,100 | Minimal |

## Data Sources Explained

### Simplify (Primary Source)
- **What it is:** Job aggregator with browser extension
- **Data:** [GitHub listings.json](https://github.com/SimplifyJobs/New-Grad-Positions)
- **Coverage:** 950 companies with active new grad postings
- **Strength:** Largest curated new grad job database

### Jobright (Complementary Source)
- **What it is:** AI job search platform
- **Data:** [GitHub README](https://github.com/jobright-ai/2025-Software-Engineer-New-Grad)
- **Coverage:** 249 companies (rolling 7-day window)
- **Strength:** Scrapes Indeed, LinkedIn, company career pages directly
- **Adds:** ~166 companies not in Simplify

### levels.fyi (NOT a Job Source)
- **What it is:** Salary data database
- **Data:** 49,981 companies with salary information
- **Use case:** Find company career pages to check directly
- **NOT useful for:** Finding active job postings (it's salary data, not jobs)

## Companies Unique to Jobright

These 166 companies have active new grad postings on Jobright but NOT on Simplify:

### Notable Tech Companies
- **Plaid** - Fintech infrastructure
- **Unity** - Game engine
- **monday.com** - Work management platform
- **Verily** - Google health spinoff (Alphabet)
- **LaunchDarkly** - Feature flag platform
- **DiDi** - Ride-sharing

### Gaming Studios
- **Naughty Dog** - Sony (Uncharted, Last of Us)
- **NetherRealm Studios** - WB Games (Mortal Kombat)
- **2K** - Sports/action games

### Defense/Government
- **Noblis** - Government tech consulting
- **Jacobs** - Engineering services
- **Nightwing** - Defense/intelligence
- **HII** - Huntington Ingalls Industries
- **CalPERS** - California pension fund

### Healthcare
- **Mayo Clinic** - Healthcare system
- **Brown University Health** - Academic medical center

### Financial Services
- **Scotiabank** - Major Canadian bank
- **Milliman** - Actuarial consulting
- **Nassau Financial Group**

## Companies Unique to Simplify

Simplify has ~859 companies that Jobright doesn't have. These include major employers like:
- Large tech companies (Google, Meta, Amazon, Microsoft, Apple)
- Major banks (JPMorgan, Goldman Sachs, Capital One)
- Defense contractors (Lockheed Martin, Northrop Grumman)
- Startups and mid-size companies

## Methodology

### Previous (Flawed) Approach
```
❌ Used Jobright (249 companies) as "ground truth"
❌ Asked: "What % of Jobright is in Simplify?" → 59%
❌ Concluded: "Simplify only covers 59%"
```

This was wrong because Jobright is a SMALLER dataset than Simplify.

### Corrected Approach
```
✓ Compare active job counts from both sources
✓ Simplify: 950 companies with active new grad jobs
✓ Jobright: 249 companies with active new grad jobs
✓ Calculate unique contributions from each
```

### About levels.fyi
The previous analysis incorrectly used levels.fyi as a "gap filler" for job postings.

**Correction:** levels.fyi is a salary database, not a job board. Having a company on levels.fyi does NOT mean they're hiring. The correct use is:
1. Get company list from levels.fyi
2. Check their career pages directly for job postings
3. Or check levels.fyi/jobs (their actual job board)

## Recommendations

### For Maximum Coverage

1. **Use Simplify as primary source** (950 companies)
   - [SimplifyJobs GitHub](https://github.com/SimplifyJobs/New-Grad-Positions)
   - Largest curated database

2. **Add Jobright for additional companies** (+166 companies)
   - [jobright-ai GitHub](https://github.com/jobright-ai/2025-Software-Engineer-New-Grad)
   - Catches companies Simplify misses

3. **Combined coverage: ~1,100 companies**

### Using the Aggregator

The `aggregator/sources.py` module pulls from both:

```python
from aggregator.sources import JobAggregator

agg = JobAggregator()
jobs = agg.fetch_all()  # Combines Simplify + Jobright
print(agg.summary())
```

### For Specific Target Companies

If looking for a specific company not on either source:
1. Check levels.fyi for company info
2. Go to company career page directly
3. Check Indeed/LinkedIn

---
Generated: 2024-12-24
Data sources: SimplifyJobs GitHub (listings.json), jobright-ai GitHub (README.md)

## Appendix: Full List of Jobright-Only Companies

Companies on Jobright but NOT on Simplify (~166 companies):

1. 1Sphere AI
2. 360insights
3. Alchemy
4. Amatrol
5. Architect (Data Centers)
6. Bisnow
7. Broccoli AI
8. Brown University Health
9. CCL Label
10. CNH
11. CONTAX Inc.
12. CP Marine LLC
13. CalPERS
14. California Department of Social Services
15. Caltech
16. Carisk Partners
17. Crew
18. Dawn Foods Global
19. Delta Controls
20. DiDi
21. Dynamic Connections
22. Elsewhere Entertainment
23. FPS GOLD
24. FWI (FedWriters, Inc.)
25. Fieldwire by Hilti
26. Fluidstack
27. Gesa Credit Union
28. HII
29. Hygiena
30. Insurity
31. Isuzu Technical Center of America
32. J Street
33. Jacobs
34. K&L Gates
35. KEENFINITY Group
36. Ketryx
37. Kiewit
38. LaunchDarkly
39. Lighthouse Avionics
40. MP: Wired for HR
41. Mayo Clinic
42. MedWatchers
43. Mediacom Communications
44. Merkle
45. Milliman
46. Mission Technologies (HII)
47. Molex
48. Morton Buildings
49. Motivo
50. Multiply Mortgage
51. Nassau Community College
52. Nassau Financial Group
53. Naughty Dog
54. NetherRealm Studios (WB Games)
55. Nexxis Solutions
56. Nightwing
57. Noblis
58. Nongshim America
59. OPS Consulting
60. Ohio Department of Job and Family Services
61. P3S Corporation
62. PFM
63. Plaid
64. Planbase
65. Point C
66. PreSales Collective
67. QA Wolf
68. QSC
69. RISE Network
70. RKL LLP
71. SETWorks
72. Salient
73. Scalence L.L.C.
74. Scotiabank
75. Specialisterne USA
76. Tennis Channel
77. Teradyne
78. Tomorrow
79. Tower Mobility
80. Trissential
81. Trusted Concepts
82. UST
83. Unity
84. Vast.ai
85. Verily
86. Vertafore
87. Vinson & Elkins
88. Voxel
89. Washington Nationals
90. dentsu
91. enGen
92. iFIT
93. monday.com
(+ ~73 more smaller companies)

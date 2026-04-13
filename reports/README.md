# Reports Directory

This folder contains all generated financial reports for the Finance Planner project.

## Reports

| Report | Description | Type | Profile |
|--------|-------------|------|---------|
| **ALON_FINANCIAL_REPORT_2026_UPDATED.md** | Comprehensive 20+ page financial analysis with pension bridge implementation details | Financial Analysis | Alon |
| **ALON_FINANCIAL_REPORT_2026.md** | Initial comprehensive financial scenario analysis | Financial Analysis | Alon |
| **ALON_PORTFOLIO_GROWTH_REPORT.md** | Detailed portfolio growth and acceleration analysis with year-by-year metrics | Growth Analysis | Alon |
| **RECENT_CHANGES_SUMMARY.md** | Quick reference guide summarizing all recent changes and bug fixes | Summary | Project |
| **IMPLEMENTATION_SUMMARY.md** | Summary of implementation approach and architecture decisions | Summary | Project |

## Generating Reports

### Generate Growth Analysis Report
```bash
PYTHONPATH=/Users/alon/Documents/finance_planner python analysis/generate_report.py growth_analysis
```

This generates:
- Portfolio growth comparison across all scenarios
- Year-by-year growth rates and acceleration
- Milestone analysis (reaching specific portfolio amounts)
- Key insights on exit timing and compounding effects

### Output Location
All reports are automatically saved to this folder: `/Users/alon/Documents/finance_planner/reports/`

## Report Organization

**By Profile:**
- `ALON_*` reports are specific to the Alon profile
- Other reports apply to the entire project

**By Type:**
- **Financial Analysis**: Comprehensive scenario-by-scenario breakdowns
- **Growth Analysis**: Portfolio accumulation and acceleration metrics
- **Summary**: Quick reference guides for recent changes

## Workflow

1. Run simulations: `FINANCE_PROFILE=alon python analysis/run_simulations.py`
2. Generate reports: `python analysis/generate_report.py growth_analysis`
3. Reports automatically saved to this folder
4. All reports use consistent formatting and currency (₪ for Israeli Shekel)

## Report Standards

All reports include:
- Generation timestamp
- Scenario overview and parameters
- Detailed year-by-year analysis
- Cross-scenario comparisons
- Key metrics and milestones
- Strategic insights

---

**Last Updated:** 2026-04-13

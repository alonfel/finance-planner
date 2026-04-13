"""
Utility for generating financial reports to the reports/ folder.

Usage:
    python analysis/generate_report.py [report_type] [options]

Supported report types:
    - growth_analysis: Portfolio growth and acceleration analysis
    - financial_summary: Comprehensive financial scenario analysis
    - scenario_comparison: Side-by-side scenario comparison
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def get_reports_dir():
    """Get the reports directory, creating if needed."""
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def get_cache_path():
    """Get the simulation cache path for the active profile."""
    from infrastructure.data_layer import get_cache_path
    return get_cache_path()


def format_currency(amount):
    """Format amount as currency."""
    return f"₪{amount:,.0f}"


def generate_growth_analysis_report():
    """Generate portfolio growth and acceleration analysis report."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return None

    with open(cache_path) as f:
        cache = json.load(f)

    results = cache.get("results", {})

    # Try to load actual scenario data
    from infrastructure.loaders import load_scenarios, SETTINGS
    try:
        scenarios = load_scenarios()
        base_scenario = next(iter(scenarios.values())) if scenarios else None
        if base_scenario:
            base_income = base_scenario.monthly_income.total
            base_expenses = base_scenario.monthly_expenses.total
            monthly_savings = base_income - base_expenses
            initial_portfolio = base_scenario.initial_portfolio
            return_rate = base_scenario.return_rate
            withdrawal_rate = base_scenario.withdrawal_rate
        else:
            raise ValueError("No scenarios found")
    except Exception as e:
        # Fallback to defaults if loading fails
        base_income = 45_000
        base_expenses = 25_000
        monthly_savings = 20_000
        initial_portfolio = 1_400_000
        return_rate = 0.05
        withdrawal_rate = 0.04

    report_lines = []

    report_lines.append("=" * 100)
    report_lines.append("PORTFOLIO GROWTH & ACCELERATION ANALYSIS".center(100))
    report_lines.append("=" * 100)
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Base Income: {format_currency(base_income)}/month | Base Expenses: {format_currency(base_expenses)}/month | Monthly Savings: {format_currency(monthly_savings)}")
    report_lines.append(f"Initial Portfolio: {format_currency(initial_portfolio)} | Investment Return: {return_rate*100:.0f}% annually | Withdrawal Rate: {withdrawal_rate*100:.1f}%")
    report_lines.append("")

    # Scenario overview
    report_lines.append("SCENARIO OVERVIEW")
    report_lines.append("=" * 100)
    report_lines.append("")

    report_lines.append(f"{'Scenario':<30} {'Retirement':<15} {'Final Portfolio':<20}")
    report_lines.append("-" * 65)

    for scenario_name, scenario_data in sorted(results.items()):
        retirement_year = scenario_data.get('retirement_year', 'N/A')
        final_portfolio = scenario_data['year_data'][-1]['portfolio'] if scenario_data.get('year_data') else 0
        retirement_str = f"Year {retirement_year}" if isinstance(retirement_year, int) else str(retirement_year)
        report_lines.append(f"{scenario_name:<30} {retirement_str:<15} {format_currency(final_portfolio):<20}")

    report_lines.append("")
    report_lines.append("")

    # Detailed analysis for each scenario
    for scenario_name, scenario_data in sorted(results.items()):
        year_data = scenario_data.get('year_data', [])
        if not year_data:
            continue

        retirement_year = scenario_data.get('retirement_year')
        final_portfolio = year_data[-1]['portfolio']

        report_lines.append("=" * 100)
        report_lines.append(f"SCENARIO: {scenario_name}".upper())
        report_lines.append("=" * 100)
        report_lines.append("")
        report_lines.append(f"Retirement Year: {retirement_year if retirement_year else 'Never'}")
        report_lines.append(f"Final Portfolio: {format_currency(final_portfolio)}")
        report_lines.append("")

        # Year-by-year table
        report_lines.append(f"{'Year':<6} {'Portfolio':<18} {'Annual Growth':<18} {'Growth %':<12}")
        report_lines.append("-" * 60)

        for i, yd in enumerate(year_data[:15]):
            portfolio = yd['portfolio']

            if i == 0:
                growth = 0
                growth_pct = 0
            else:
                prior_portfolio = year_data[i-1]['portfolio']
                growth = portfolio - prior_portfolio
                growth_pct = (growth / prior_portfolio * 100) if prior_portfolio > 0 else 0

            report_lines.append(
                f"{yd['year']:<6} {format_currency(portfolio):<18} {format_currency(growth):<18} {growth_pct:>6.2f}%"
            )

        report_lines.append("")
        report_lines.append("")

    # Comparison table
    report_lines.append("=" * 100)
    report_lines.append("CROSS-SCENARIO COMPARISON")
    report_lines.append("=" * 100)
    report_lines.append("")

    # Get all scenarios
    scenarios_dict = {name: data.get('year_data', []) for name, data in results.items()}
    max_years = max(len(data) for data in scenarios_dict.values()) if scenarios_dict else 0

    if max_years > 0:
        header = f"{'Year':<6}"
        for scenario_name in sorted(scenarios_dict.keys()):
            header += f" {scenario_name[:20]:<20}"
        report_lines.append(header)

        report_lines.append("-" * (6 + 22 * len(scenarios_dict)))

        for i in range(min(15, max_years)):
            line_parts = []
            year = None

            for scenario_name in sorted(scenarios_dict.keys()):
                data = scenarios_dict[scenario_name]
                if i < len(data):
                    yd = data[i]
                    if year is None:
                        year = yd['year']
                    line_parts.append(f" {format_currency(yd['portfolio']):<20}")

            if year is not None:
                report_lines.append(f"{year:<6}" + "".join(line_parts))

    report_lines.append("")
    report_lines.append("=" * 100)

    return "\n".join(report_lines)


def save_report(content, filename):
    """Save report content to reports folder."""
    reports_dir = get_reports_dir()
    filepath = reports_dir / filename

    with open(filepath, 'w') as f:
        f.write(content)

    return filepath


def generate_yearly_comparison_report():
    """Generate elaborate yearly comparison report across all scenarios."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return None

    with open(cache_path) as f:
        cache = json.load(f)

    results = cache.get("results", {})

    # Load actual scenario data
    from infrastructure.loaders import load_scenarios
    try:
        scenarios = load_scenarios()
        base_scenario = next(iter(scenarios.values())) if scenarios else None
        if not base_scenario:
            raise ValueError("No scenarios found")

        start_age = base_scenario.age
    except Exception as e:
        print(f"Error loading scenario data: {e}")
        start_age = 41

    report_lines = []

    # Header
    report_lines.append("╔" + "═" * 118 + "╗")
    report_lines.append("║" + "YEARLY COMPARISON ANALYSIS".center(118) + "║")
    report_lines.append("╚" + "═" * 118 + "╝")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"All portfolio values in ₪ (Israeli Shekel)")
    report_lines.append("")

    # Get all scenarios and find max years
    scenarios_dict = {name: data.get('year_data', []) for name, data in sorted(results.items())}
    max_years = max(len(data) for data in scenarios_dict.values()) if scenarios_dict else 0

    if max_years == 0:
        return None

    # Create year-by-year comparison tables
    report_lines.append("YEAR-BY-YEAR PORTFOLIO COMPARISON")
    report_lines.append("=" * 120)
    report_lines.append("")

    # Portfolio values table
    report_lines.append("PORTFOLIO VALUES BY YEAR")
    report_lines.append("-" * 120)
    header = f"{'Year':<6} {'Age':<6}"
    for scenario_name in sorted(scenarios_dict.keys()):
        header += f" {scenario_name[:35]:<37}"
    report_lines.append(header)
    report_lines.append("-" * 120)

    for i in range(min(20, max_years)):
        line = f"{i+1:<6}"
        age_val = None

        for scenario_name in sorted(scenarios_dict.keys()):
            data = scenarios_dict[scenario_name]
            if i < len(data):
                yd = data[i]
                if age_val is None:
                    age_val = yd.get('age', start_age + i + 1)
                line += f" {format_currency(yd['portfolio']):<37}"

        if age_val:
            line = f"{i+1:<6} {age_val:<6}" + line[12:]
        report_lines.append(line)

    report_lines.append("")
    report_lines.append("")

    # Annual growth comparison
    report_lines.append("ANNUAL GROWTH (YEAR-OVER-YEAR CHANGE)")
    report_lines.append("-" * 120)
    header = f"{'Year':<6}"
    for scenario_name in sorted(scenarios_dict.keys()):
        header += f" {scenario_name[:35]:<37}"
    report_lines.append(header)
    report_lines.append("-" * 120)

    for i in range(1, min(20, max_years)):
        line = f"{i+1:<6}"

        for scenario_name in sorted(scenarios_dict.keys()):
            data = scenarios_dict[scenario_name]
            if i < len(data):
                yd_curr = data[i]
                yd_prev = data[i-1]
                growth = yd_curr['portfolio'] - yd_prev['portfolio']
                line += f" {format_currency(growth):<37}"

        report_lines.append(line)

    report_lines.append("")
    report_lines.append("")

    # Growth rate comparison
    report_lines.append("GROWTH RATE (% YEAR-OVER-YEAR)")
    report_lines.append("-" * 120)
    header = f"{'Year':<6}"
    for scenario_name in sorted(scenarios_dict.keys()):
        header += f" {scenario_name[:35]:<37}"
    report_lines.append(header)
    report_lines.append("-" * 120)

    for i in range(1, min(20, max_years)):
        line = f"{i+1:<6}"

        for scenario_name in sorted(scenarios_dict.keys()):
            data = scenarios_dict[scenario_name]
            if i < len(data):
                yd_curr = data[i]
                yd_prev = data[i-1]
                growth = yd_curr['portfolio'] - yd_prev['portfolio']
                growth_pct = (growth / yd_prev['portfolio'] * 100) if yd_prev['portfolio'] > 0 else 0
                line += f" {growth_pct:>6.2f}%{' ' * 31}"

        report_lines.append(line)

    report_lines.append("")
    report_lines.append("")

    # Milestone analysis
    report_lines.append("MILESTONE TARGETS: YEARS TO REACH EACH THRESHOLD")
    report_lines.append("-" * 120)

    milestones = [5_000_000, 10_000_000, 15_000_000, 20_000_000]

    for milestone in milestones:
        report_lines.append("")
        report_lines.append(f"TARGET: {format_currency(milestone)}")
        report_lines.append("-" * 120)

        for scenario_name in sorted(scenarios_dict.keys()):
            data = scenarios_dict[scenario_name]
            year_reached = None
            age_reached = None

            for i, yd in enumerate(data):
                if yd['portfolio'] >= milestone:
                    year_reached = yd['year']
                    age_reached = yd.get('age', start_age + year_reached)
                    break

            if year_reached:
                report_lines.append(f"  {scenario_name:<45} Year {year_reached:2d} (Age {age_reached})")
            else:
                report_lines.append(f"  {scenario_name:<45} Not reached within 20 years")

    report_lines.append("")

    return "\n".join(report_lines)


def generate_insights_report():
    """Generate comprehensive insights report with analysis and strategic recommendations."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return None

    with open(cache_path) as f:
        cache = json.load(f)

    results = cache.get("results", {})

    # Load actual scenario data
    from infrastructure.loaders import load_scenarios
    try:
        scenarios = load_scenarios()
        base_scenario = next(iter(scenarios.values())) if scenarios else None
        if not base_scenario:
            raise ValueError("No scenarios found")

        base_income = base_scenario.monthly_income.total
        base_expenses = base_scenario.monthly_expenses.total
        monthly_savings = base_income - base_expenses
        annual_savings = monthly_savings * 12
        start_age = base_scenario.age
        return_rate = base_scenario.return_rate
    except Exception as e:
        print(f"Error loading scenario data: {e}")
        return None

    report_lines = []

    # Header
    report_lines.append("╔" + "═" * 118 + "╗")
    report_lines.append("║" + "FINANCIAL INSIGHTS & STRATEGIC ANALYSIS".center(118) + "║")
    report_lines.append("╚" + "═" * 118 + "╝")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Key Metrics
    report_lines.append("KEY FINANCIAL METRICS")
    report_lines.append("=" * 120)
    report_lines.append("")
    report_lines.append(f"Monthly Savings Rate:        {format_currency(monthly_savings)} ({(monthly_savings/base_income*100):.1f}% of income)")
    report_lines.append(f"Annual Savings Capacity:     {format_currency(annual_savings)}")
    report_lines.append(f"Investment Return Rate:      {return_rate*100:.1f}%")
    report_lines.append("")
    report_lines.append("")

    # Scenario Comparison
    report_lines.append("SCENARIO ANALYSIS & OUTCOMES")
    report_lines.append("=" * 120)
    report_lines.append("")

    sorted_results = sorted(results.items())
    retirement_data = []

    for scenario_name, scenario_data in sorted_results:
        year_data = scenario_data.get('year_data', [])
        if not year_data:
            continue

        retirement_year = scenario_data.get('retirement_year')
        final_portfolio = year_data[-1]['portfolio']

        if retirement_year:
            retirement_age = start_age + retirement_year
            retirement_data.append({
                'name': scenario_name,
                'year': retirement_year,
                'age': retirement_age,
                'portfolio': final_portfolio
            })

    # Sort by retirement year
    retirement_data.sort(key=lambda x: x['year'] if x['year'] else float('inf'))

    report_lines.append("RETIREMENT TIMELINE COMPARISON")
    report_lines.append("-" * 120)

    for i, data in enumerate(retirement_data):
        status = "✓ ACHIEVES RETIREMENT" if data['year'] else "✗ NO RETIREMENT"
        report_lines.append(f"{i+1}. {data['name']:<45} {status}")
        report_lines.append(f"   Retirement Year: {data['year']} (Age {data['age']})")
        report_lines.append(f"   Final Portfolio: {format_currency(data['portfolio'])}")
        report_lines.append("")

    report_lines.append("")

    # Exit Event Impact Analysis
    report_lines.append("EXIT EVENT IMPACT ANALYSIS")
    report_lines.append("=" * 120)
    report_lines.append("")

    baseline_data = None
    exit_scenarios = []

    for scenario_name, scenario_data in sorted_results:
        if "Baseline" in scenario_name:
            baseline_data = scenario_data
        elif "Exit" in scenario_name or "IPO" in scenario_name:
            exit_scenarios.append((scenario_name, scenario_data))

    if baseline_data and exit_scenarios:
        baseline_retire = baseline_data.get('retirement_year')
        baseline_portfolio = baseline_data['year_data'][-1]['portfolio'] if baseline_data.get('year_data') else 0

        report_lines.append(f"Baseline Scenario: Retires Year {baseline_retire} with {format_currency(baseline_portfolio)}")
        report_lines.append("")

        for scenario_name, scenario_data in exit_scenarios:
            exit_retire = scenario_data.get('retirement_year')
            exit_portfolio = scenario_data['year_data'][-1]['portfolio'] if scenario_data.get('year_data') else 0

            if baseline_retire and exit_retire:
                years_saved = baseline_retire - exit_retire
                portfolio_diff = exit_portfolio - baseline_portfolio

                report_lines.append(f"{scenario_name}:")
                report_lines.append(f"  Retirement Impact: {years_saved:+d} years" + (" EARLIER ✓" if years_saved > 0 else " LATER"))
                diff_sign = "+" if portfolio_diff >= 0 else ""
                report_lines.append(f"  Portfolio Impact: {diff_sign}{format_currency(portfolio_diff)}" + (" HIGHER ✓" if portfolio_diff > 0 else " LOWER"))
                report_lines.append("")

        report_lines.append("")

    # Strategic Insights
    report_lines.append("STRATEGIC INSIGHTS")
    report_lines.append("=" * 120)
    report_lines.append("")

    report_lines.append("1. SAVINGS CAPACITY")
    report_lines.append("   " + "-" * 116)
    report_lines.append(f"   Your monthly savings of {format_currency(monthly_savings)} provides a strong foundation")
    report_lines.append(f"   for wealth accumulation. At {return_rate*100:.1f}% annual returns, this compounds significantly")
    report_lines.append(f"   over time, with growth rates accelerating as the portfolio grows.")
    report_lines.append("")

    report_lines.append("2. RETIREMENT TIMELINE")
    report_lines.append("   " + "-" * 116)
    if retirement_data:
        earliest = min(retirement_data, key=lambda x: x['year'])
        latest = max(retirement_data, key=lambda x: x['year'])
        report_lines.append(f"   Fastest path: {earliest['name']} → Year {earliest['year']} (Age {earliest['age']})")
        report_lines.append(f"   Conservative: {latest['name']} → Year {latest['year']} (Age {latest['age']})")
        report_lines.append(f"   Range: {latest['year'] - earliest['year']} year difference")
    report_lines.append("")

    report_lines.append("3. WEALTH ACCELERATION")
    report_lines.append("   " + "-" * 116)
    report_lines.append(f"   Portfolio growth accelerates mid-course due to compounding. Early years show")
    report_lines.append(f"   growth driven primarily by savings, while later years benefit from investment")
    report_lines.append(f"   returns on an increasingly large base.")
    report_lines.append("")

    report_lines.append("4. EXIT EVENT VALUE")
    report_lines.append("   " + "-" * 116)
    if exit_scenarios and baseline_retire:
        report_lines.append(f"   An exit event (IPO/acquisition) accelerates retirement by years, representing")
        report_lines.append(f"   a significant shift in financial timeline. The earlier you exit, the earlier")
        report_lines.append(f"   you achieve financial independence.")
    report_lines.append("")

    report_lines.append("RECOMMENDATIONS")
    report_lines.append("=" * 120)
    report_lines.append("")
    report_lines.append(f"✓ Maintain consistent savings discipline of {format_currency(monthly_savings)}/month")
    report_lines.append(f"✓ Keep investment returns at {return_rate*100:.1f}% through diversified portfolio")
    report_lines.append("✓ Monitor milestones annually to track progress toward retirement")
    report_lines.append("✓ If exit event occurs, plan carefully to maximize financial impact")
    report_lines.append("✓ Review and adjust assumptions annually (income growth, expenses, returns)")
    report_lines.append("")

    return "\n".join(report_lines)


def generate_comprehensive_financial_report():
    """Generate comprehensive financial analysis report with detailed scenario breakdowns."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return None

    with open(cache_path) as f:
        cache = json.load(f)

    results = cache.get("results", {})

    # Load actual scenario data
    from infrastructure.loaders import load_scenario_nodes, load_scenarios, SETTINGS
    try:
        scenarios = load_scenarios()
        base_scenario = next(iter(scenarios.values())) if scenarios else None
        if not base_scenario:
            raise ValueError("No scenarios found")

        base_income = base_scenario.monthly_income.total
        base_expenses = base_scenario.monthly_expenses.total
        monthly_savings = base_income - base_expenses
        annual_savings = monthly_savings * 12
        initial_portfolio = base_scenario.initial_portfolio
        return_rate = base_scenario.return_rate
        withdrawal_rate = base_scenario.withdrawal_rate
        retirement_threshold = base_expenses / withdrawal_rate
        start_age = base_scenario.age
    except Exception as e:
        print(f"Error loading scenario data: {e}")
        return None

    report_lines = []

    # Header
    report_lines.append("╔" + "═" * 118 + "╗")
    report_lines.append("║" + "ALON - COMPREHENSIVE FINANCIAL ANALYSIS".center(118) + "║")
    report_lines.append("╚" + "═" * 118 + "╝")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Executive Summary
    report_lines.append("EXECUTIVE SUMMARY")
    report_lines.append("=" * 120)
    report_lines.append("")
    report_lines.append(f"Monthly Income:              {format_currency(base_income)}")
    report_lines.append(f"Monthly Expenses:            {format_currency(base_expenses)}")
    report_lines.append(f"Monthly Savings:             {format_currency(monthly_savings)}")
    report_lines.append(f"Annual Savings:              {format_currency(annual_savings)}")
    report_lines.append(f"Initial Portfolio:           {format_currency(initial_portfolio)}")
    report_lines.append(f"Investment Return Rate:      {return_rate*100:.1f}%")
    report_lines.append(f"Withdrawal Rate:             {withdrawal_rate*100:.1f}%")
    report_lines.append(f"Retirement Threshold:        {format_currency(retirement_threshold)}")
    report_lines.append(f"Starting Age:                {start_age}")
    report_lines.append("")

    # Scenario Summary Table
    report_lines.append("SCENARIO OUTCOMES")
    report_lines.append("=" * 120)
    report_lines.append("")
    report_lines.append(f"{'Scenario':<40} {'Retirement':<20} {'Final Portfolio':<20}")
    report_lines.append("-" * 80)

    for scenario_name, scenario_data in sorted(results.items()):
        retirement_year = scenario_data.get('retirement_year')
        final_portfolio = scenario_data['year_data'][-1]['portfolio'] if scenario_data.get('year_data') else 0
        if retirement_year:
            retirement_age = start_age + retirement_year
            retirement_str = f"Year {retirement_year} (Age {retirement_age})"
        else:
            retirement_str = "Never (>30 years)"
        report_lines.append(f"{scenario_name:<40} {retirement_str:<20} {format_currency(final_portfolio):<20}")

    report_lines.append("")
    report_lines.append("")

    # Detailed scenario analysis
    for scenario_name, scenario_data in sorted(results.items()):
        year_data = scenario_data.get('year_data', [])
        if not year_data:
            continue

        retirement_year = scenario_data.get('retirement_year')
        final_portfolio = year_data[-1]['portfolio']

        report_lines.append("=" * 120)
        report_lines.append(f"SCENARIO: {scenario_name}")
        report_lines.append("=" * 120)
        report_lines.append("")

        if retirement_year:
            retirement_age = start_age + retirement_year
            report_lines.append(f"✓ RETIREMENT: Year {retirement_year} (Age {retirement_age})")
        else:
            report_lines.append(f"✗ RETIREMENT: Not achieved within 30 years")

        report_lines.append("")
        report_lines.append(f"Final Portfolio: {format_currency(final_portfolio)}")
        report_lines.append("")

        # Year-by-year table with ages
        report_lines.append(f"{'Year':<6} {'Age':<6} {'Portfolio':<18} {'Annual Growth':<18} {'Growth %':<12}")
        report_lines.append("-" * 70)

        for i, yd in enumerate(year_data[:15]):
            portfolio = yd['portfolio']
            age = yd.get('age', start_age + yd['year'])

            if i == 0:
                growth = 0
                growth_pct = 0
            else:
                prior_portfolio = year_data[i-1]['portfolio']
                growth = portfolio - prior_portfolio
                growth_pct = (growth / prior_portfolio * 100) if prior_portfolio > 0 else 0

            report_lines.append(
                f"{yd['year']:<6} {age:<6} {format_currency(portfolio):<18} {format_currency(growth):<18} {growth_pct:>6.2f}%"
            )

        report_lines.append("")
        report_lines.append("")

    return "\n".join(report_lines)


def generate_detailed_scenario_analysis():
    """Generate detailed 20-year analysis for all scenarios with savings vs returns breakdown."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return None

    with open(cache_path) as f:
        cache = json.load(f)

    results = cache.get("results", {})

    # Load actual scenario data for parameters
    from infrastructure.loaders import load_scenarios
    try:
        scenarios = load_scenarios()
        base_scenario = next(iter(scenarios.values())) if scenarios else None
        if not base_scenario:
            raise ValueError("No scenarios found")

        base_income = base_scenario.monthly_income.total
        base_expenses = base_scenario.monthly_expenses.total
        monthly_savings = base_income - base_expenses
        annual_savings = monthly_savings * 12
        initial_portfolio = base_scenario.initial_portfolio
        return_rate = base_scenario.return_rate
        start_age = base_scenario.age
    except Exception as e:
        print(f"Error loading scenario data: {e}")
        return None

    report_lines = []

    # Header
    report_lines.append("╔" + "═" * 130 + "╗")
    report_lines.append("║" + "ALL SCENARIOS - 20-YEAR DETAILED ANALYSIS".center(130) + "║")
    report_lines.append("║" + "SAVINGS vs INVESTMENT RETURNS BREAKDOWN".center(130) + "║")
    report_lines.append("╚" + "═" * 130 + "╝")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Parameters
    report_lines.append("SIMULATION PARAMETERS")
    report_lines.append("=" * 130)
    report_lines.append("")
    report_lines.append(f"  Initial Portfolio:           {format_currency(initial_portfolio)}")
    report_lines.append(f"  Monthly Savings:             {format_currency(monthly_savings)}")
    report_lines.append(f"  Annual Savings:              {format_currency(annual_savings)}")
    report_lines.append(f"  Investment Return Rate:      {return_rate*100:.1f}% annually")
    report_lines.append(f"  Starting Age:                {start_age}")
    report_lines.append("")
    report_lines.append("")

    # Process each scenario
    for scenario_name in sorted(results.keys()):
        scenario_data = results[scenario_name]
        year_data = scenario_data.get('year_data', [])

        if not year_data:
            continue

        # Scenario header
        report_lines.append("=" * 130)
        report_lines.append(f"SCENARIO: {scenario_name}")
        report_lines.append("=" * 130)
        report_lines.append("")

        # Detailed year-by-year table
        report_lines.append("YEAR-BY-YEAR BREAKDOWN (20 YEARS)")
        report_lines.append("-" * 130)
        report_lines.append(f"{'Year':<6} {'Age':<5} {'Portfolio':<18} {'YoY Delta':<18} {'Savings Contrib':<18} {'Returns Contrib':<18} {'% From Returns':<16}")
        report_lines.append("-" * 130)

        total_savings_contributed = 0
        total_returns_generated = 0

        for i, yd in enumerate(year_data[:20]):
            year = yd['year']
            age = yd.get('age', start_age + year)
            portfolio = yd['portfolio']

            if i == 0:
                yoy_delta = portfolio - initial_portfolio
                # For year 1: returns apply to initial portfolio + portion of savings
                returns_contributed = yoy_delta - annual_savings
                savings_contributed = annual_savings
            else:
                prev_portfolio = year_data[i-1]['portfolio']
                yoy_delta = portfolio - prev_portfolio
                # For subsequent years: returns apply to previous portfolio + savings
                returns_contributed = yoy_delta - annual_savings
                savings_contributed = annual_savings

            total_savings_contributed += savings_contributed
            total_returns_generated += returns_contributed

            pct_from_returns = (returns_contributed / yoy_delta * 100) if yoy_delta > 0 else 0

            report_lines.append(
                f"{year:<6} {age:<5} {format_currency(portfolio):<18} {format_currency(yoy_delta):<18} "
                f"{format_currency(savings_contributed):<18} {format_currency(returns_contributed):<18} {pct_from_returns:>6.1f}%{' ' * 8}"
            )

        report_lines.append("")
        report_lines.append("")

        # Summary statistics
        report_lines.append("20-YEAR CUMULATIVE SUMMARY")
        report_lines.append("-" * 130)
        report_lines.append(f"  Total Savings Contributed:        {format_currency(total_savings_contributed)}")
        report_lines.append(f"  Total Returns Generated:          {format_currency(total_returns_generated)}")
        report_lines.append(f"  Final Portfolio (Year 20):        {format_currency(year_data[19]['portfolio'])}")
        report_lines.append(f"  Returns-to-Savings Ratio:         {total_returns_generated / total_savings_contributed:.2f}x")
        report_lines.append("")

        # Phase analysis
        report_lines.append("WEALTH ACCELERATION PHASES")
        report_lines.append("-" * 130)

        phases = [
            ("PHASE 1", "Early Years", 1, 5, "Savings dominate growth"),
            ("PHASE 2", "Mid Years", 6, 10, "Transition point"),
            ("PHASE 3", "Late Years", 11, 15, "Returns exceed savings"),
            ("PHASE 4", "Mature Years", 16, 20, "Compound power dominates"),
        ]

        for phase_name, phase_label, start_yr, end_yr, description in phases:
            phase_data = [yd for yd in year_data if start_yr <= yd['year'] <= end_yr]
            if not phase_data:
                continue

            phase_savings = sum(annual_savings for _ in phase_data)

            # Calculate returns for this phase
            phase_returns = 0
            for yd in phase_data:
                year_idx = yd['year'] - 1  # Convert 1-indexed year to 0-indexed
                if year_idx == 0:
                    # Year 1: delta - savings = returns (includes growth on initial portfolio)
                    delta = yd['portfolio'] - initial_portfolio
                else:
                    # Subsequent years: delta is year_data[idx] - year_data[idx-1]
                    delta = yd['portfolio'] - year_data[year_idx - 1]['portfolio']

                returns_in_year = delta - annual_savings
                phase_returns += returns_in_year

            total_phase_growth = phase_savings + phase_returns
            pct_savings = (phase_savings / total_phase_growth * 100) if total_phase_growth > 0 else 0
            pct_returns = (phase_returns / total_phase_growth * 100) if total_phase_growth > 0 else 0

            report_lines.append(f"{phase_name}: {phase_label} (Years {start_yr}-{end_yr}) - {description}")
            report_lines.append(f"  Savings Contribution:     {format_currency(phase_savings)} ({pct_savings:.1f}% of growth)")
            report_lines.append(f"  Returns Contribution:     {format_currency(phase_returns)} ({pct_returns:.1f}% of growth)")
            if phase_savings > 0:
                report_lines.append(f"  Returns/Savings Ratio:    {phase_returns/phase_savings:.2f}x")

        report_lines.append("")

        retirement_year = scenario_data.get('retirement_year')
        if retirement_year:
            report_lines.append(f"✓ RETIREMENT ACHIEVED: Year {retirement_year} (Age {start_age + retirement_year})")
        else:
            report_lines.append(f"✗ RETIREMENT: Not achieved within 20 years")

        report_lines.append("")
        report_lines.append("")

    return "\n".join(report_lines)


def generate_detailed_baseline_analysis():
    """Generate detailed 20-year baseline analysis with savings vs returns breakdown (legacy function)."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return None

    with open(cache_path) as f:
        cache = json.load(f)

    results = cache.get("results", {})

    # Find baseline scenario
    baseline_data = None
    baseline_name = None
    for name, data in sorted(results.items()):
        if "Baseline" in name:
            baseline_data = data
            baseline_name = name
            break

    if not baseline_data:
        print("Error: No Baseline scenario found")
        return None

    # Load actual scenario data for parameters
    from infrastructure.loaders import load_scenarios
    try:
        scenarios = load_scenarios()
        base_scenario = next(iter(scenarios.values())) if scenarios else None
        if not base_scenario:
            raise ValueError("No scenarios found")

        base_income = base_scenario.monthly_income.total
        base_expenses = base_scenario.monthly_expenses.total
        monthly_savings = base_income - base_expenses
        annual_savings = monthly_savings * 12
        initial_portfolio = base_scenario.initial_portfolio
        return_rate = base_scenario.return_rate
        start_age = base_scenario.age
    except Exception as e:
        print(f"Error loading scenario data: {e}")
        return None

    year_data = baseline_data.get('year_data', [])
    if not year_data:
        return None

    report_lines = []

    # Header
    report_lines.append("╔" + "═" * 130 + "╗")
    report_lines.append("║" + "BASELINE SCENARIO - 20-YEAR DETAILED ANALYSIS".center(130) + "║")
    report_lines.append("║" + "SAVINGS vs INVESTMENT RETURNS BREAKDOWN".center(130) + "║")
    report_lines.append("╚" + "═" * 130 + "╝")
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # Parameters
    report_lines.append("SIMULATION PARAMETERS")
    report_lines.append("=" * 130)
    report_lines.append("")
    report_lines.append(f"  Initial Portfolio:           {format_currency(initial_portfolio)}")
    report_lines.append(f"  Monthly Savings:             {format_currency(monthly_savings)}")
    report_lines.append(f"  Annual Savings:              {format_currency(annual_savings)}")
    report_lines.append(f"  Investment Return Rate:      {return_rate*100:.1f}% annually")
    report_lines.append(f"  Starting Age:                {start_age}")
    report_lines.append("")
    report_lines.append("")

    # Detailed year-by-year table
    report_lines.append("YEAR-BY-YEAR BREAKDOWN (20 YEARS)")
    report_lines.append("=" * 130)
    report_lines.append("")
    report_lines.append(f"{'Year':<6} {'Age':<5} {'Portfolio':<18} {'YoY Delta':<18} {'Savings Contrib':<18} {'Returns Contrib':<18} {'% From Returns':<16}")
    report_lines.append("-" * 130)

    total_savings_contributed = 0
    total_returns_generated = 0

    for i, yd in enumerate(year_data[:20]):
        year = yd['year']
        age = yd.get('age', start_age + year)
        portfolio = yd['portfolio']

        if i == 0:
            yoy_delta = portfolio - initial_portfolio
            # For year 1: returns apply to initial portfolio + portion of savings
            returns_contributed = yoy_delta - annual_savings
            savings_contributed = annual_savings
        else:
            prev_portfolio = year_data[i-1]['portfolio']
            yoy_delta = portfolio - prev_portfolio
            # For subsequent years: returns apply to previous portfolio + savings
            returns_contributed = yoy_delta - annual_savings
            savings_contributed = annual_savings

        total_savings_contributed += savings_contributed
        total_returns_generated += returns_contributed

        pct_from_returns = (returns_contributed / yoy_delta * 100) if yoy_delta > 0 else 0

        report_lines.append(
            f"{year:<6} {age:<5} {format_currency(portfolio):<18} {format_currency(yoy_delta):<18} "
            f"{format_currency(savings_contributed):<18} {format_currency(returns_contributed):<18} {pct_from_returns:>6.1f}%{' ' * 8}"
        )

    report_lines.append("")
    report_lines.append("")

    # Summary statistics
    report_lines.append("20-YEAR CUMULATIVE SUMMARY")
    report_lines.append("=" * 130)
    report_lines.append("")
    report_lines.append(f"  Total Savings Contributed:        {format_currency(total_savings_contributed)}")
    report_lines.append(f"  Total Returns Generated:          {format_currency(total_returns_generated)}")
    report_lines.append(f"  Final Portfolio (Year 20):        {format_currency(year_data[19]['portfolio'])}")
    report_lines.append(f"  Returns-to-Savings Ratio:         {total_returns_generated / total_savings_contributed:.2f}x")
    report_lines.append("")
    report_lines.append("")

    # Phase analysis
    report_lines.append("WEALTH ACCELERATION PHASES")
    report_lines.append("=" * 130)
    report_lines.append("")

    phases = [
        ("PHASE 1", "Early Years", 1, 5, "Savings dominate growth"),
        ("PHASE 2", "Mid Years", 6, 10, "Transition point"),
        ("PHASE 3", "Late Years", 11, 15, "Returns exceed savings"),
        ("PHASE 4", "Mature Years", 16, 20, "Compound power dominates"),
    ]

    for phase_name, phase_label, start_yr, end_yr, description in phases:
        phase_data = [yd for yd in year_data if start_yr <= yd['year'] <= end_yr]
        if not phase_data:
            continue

        phase_savings = sum(annual_savings for _ in phase_data)

        # Calculate returns for this phase
        phase_returns = 0
        for yd in phase_data:
            year_idx = yd['year'] - 1  # Convert 1-indexed year to 0-indexed
            if year_idx == 0:
                # Year 1: delta - savings = returns (includes growth on initial portfolio)
                delta = yd['portfolio'] - initial_portfolio
            else:
                # Subsequent years: delta is year_data[idx] - year_data[idx-1]
                delta = yd['portfolio'] - year_data[year_idx - 1]['portfolio']

            returns_in_year = delta - annual_savings
            phase_returns += returns_in_year

        total_phase_growth = phase_savings + phase_returns
        pct_savings = (phase_savings / total_phase_growth * 100) if total_phase_growth > 0 else 0
        pct_returns = (phase_returns / total_phase_growth * 100) if total_phase_growth > 0 else 0

        report_lines.append(f"{phase_name}: {phase_label} (Years {start_yr}-{end_yr}) - {description}")
        report_lines.append(f"  Savings Contribution:     {format_currency(phase_savings)} ({pct_savings:.1f}% of growth)")
        report_lines.append(f"  Returns Contribution:     {format_currency(phase_returns)} ({pct_returns:.1f}% of growth)")
        if phase_savings > 0:
            report_lines.append(f"  Returns/Savings Ratio:    {phase_returns/phase_savings:.2f}x")
        report_lines.append("")

    retirement_year = baseline_data.get('retirement_year')
    if retirement_year:
        report_lines.append(f"✓ RETIREMENT ACHIEVED: Year {retirement_year} (Age {start_age + retirement_year})")
    else:
        report_lines.append(f"✗ RETIREMENT: Not achieved within 20 years")

    report_lines.append("")

    return "\n".join(report_lines)


if __name__ == "__main__":
    # Default: generate both yearly_comparison and insights reports
    if len(sys.argv) == 1:
        print("Generating both reports...")

        content1 = generate_yearly_comparison_report()
        if content1:
            filepath1 = save_report(content1, "ALON_YEARLY_COMPARISON_REPORT.md")
            print(f"✓ Report 1 saved to: {filepath1}")

        content2 = generate_insights_report()
        if content2:
            filepath2 = save_report(content2, "ALON_INSIGHTS_REPORT.md")
            print(f"✓ Report 2 saved to: {filepath2}")
    else:
        report_type = sys.argv[1]

        if report_type == "yearly_comparison":
            content = generate_yearly_comparison_report()
            if content:
                filepath = save_report(content, "ALON_YEARLY_COMPARISON_REPORT.md")
                print(f"✓ Report saved to: {filepath}")
            else:
                sys.exit(1)
        elif report_type == "insights":
            content = generate_insights_report()
            if content:
                filepath = save_report(content, "ALON_INSIGHTS_REPORT.md")
                print(f"✓ Report saved to: {filepath}")
            else:
                sys.exit(1)
        elif report_type == "growth_analysis":
            content = generate_growth_analysis_report()
            if content:
                filepath = save_report(content, "portfolio_growth_analysis.md")
                print(f"✓ Report saved to: {filepath}")
            else:
                sys.exit(1)
        elif report_type == "comprehensive":
            content = generate_comprehensive_financial_report()
            if content:
                filepath = save_report(content, "ALON_COMPREHENSIVE_FINANCIAL_REPORT.md")
                print(f"✓ Report saved to: {filepath}")
            else:
                sys.exit(1)
        elif report_type == "detailed_baseline":
            content = generate_detailed_baseline_analysis()
            if content:
                filepath = save_report(content, "BASELINE_20YEAR_DETAILED_ANALYSIS.md")
                print(f"✓ Report saved to: {filepath}")
            else:
                sys.exit(1)
        elif report_type == "detailed_all" or report_type == "detailed_scenarios":
            content = generate_detailed_scenario_analysis()
            if content:
                filepath = save_report(content, "ALL_SCENARIOS_20YEAR_DETAILED_ANALYSIS.md")
                print(f"✓ Report saved to: {filepath}")
            else:
                sys.exit(1)
        else:
            print(f"Unknown report type: {report_type}")
            print("Available types: yearly_comparison, insights, growth_analysis, comprehensive, detailed_baseline, detailed_all")
            sys.exit(1)

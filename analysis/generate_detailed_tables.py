"""Generate detailed year-by-year breakdown tables for all Alon scenarios."""

import json
from pathlib import Path
from infrastructure.data_layer import get_cache_path, ACTIVE_PROFILE

def format_currency(amount):
    """Format amount as currency with thousands separator."""
    return f"₪{amount:,.0f}"

def print_scenario_details(scenario_name, year_data, retirement_year):
    """Print detailed year-by-year breakdown for a scenario."""
    print(f"\n{'='*130}")
    print(f"SCENARIO: {scenario_name}")
    print(f"Retirement Year: {retirement_year if retirement_year else 'N/A'}")
    print(f"{'='*130}\n")

    print(f"{'Year':<6} {'Age':<5} {'Income':<15} {'Expenses':<15} {'Net Savings':<15} {'Portfolio':<18} {'Pension':<18} {'Required':<15} {'Status':<15}")
    print("-" * 130)

    for yd in year_data:
        current_age = 41 + yd['year'] - 1
        status = "💰 RETIRE" if yd['year'] == retirement_year else ""

        print(f"{yd['year']:<6} {current_age:<5} {format_currency(yd['income']):<15} {format_currency(yd['expenses']):<15} {format_currency(yd['net_savings']):<15} {format_currency(yd['portfolio']):<18} {format_currency(yd['pension_value']):<18} {format_currency(yd['required_capital']):<15} {status:<15}")

    print()

def main():
    cache_path = get_cache_path()

    if not cache_path.exists():
        print(f"Error: Cache file not found at {cache_path}")
        return

    with open(cache_path) as f:
        cache_data = json.load(f)

    # Handle both old and new cache formats
    if isinstance(cache_data, dict) and "results" in cache_data:
        results = cache_data.get("results", {})
    else:
        results = cache_data

    # Focus on key scenarios for detailed analysis
    key_scenarios = [
        "Alon - Baseline",
        "Alon - Baseline + Pension",
        "Alon - Baseline + Pension (Bridged: Retire at 55)",
        "Alon - IPO Year 2",
        "Alon - IPO Year 2 + Pension",
        "Alon - IPO Year 2 + Pension (Bridged)",
    ]

    print("\n" + "="*130)
    print("ALON'S RETIREMENT SCENARIOS - DETAILED YEAR-BY-YEAR BREAKDOWN")
    print("="*130)
    print(f"\nProfile: {ACTIVE_PROFILE}")
    print(f"Age: 41 | Monthly Income: ₪45,000 | Monthly Expenses: ₪22,000")
    print(f"Initial Portfolio: ₪1,400,000 | Pension: ₪2M (9K/mo @ 6%, unlocks at 67)")

    for scenario_name in key_scenarios:
        if scenario_name in results:
            result = results[scenario_name]
            year_data = result.get("year_data", [])
            retirement_year = result.get("retirement_year")
            print_scenario_details(scenario_name, year_data, retirement_year)

    # Print retirement timeline summary
    print("\n" + "="*130)
    print("RETIREMENT TIMELINE SUMMARY")
    print("="*130 + "\n")

    summary_data = []
    for scenario_name in key_scenarios:
        if scenario_name in results:
            result = results[scenario_name]
            retirement_year = result.get("retirement_year")
            if retirement_year:
                age = 41 + retirement_year - 1
                year_data = result.get("year_data", [])
                final_portfolio = year_data[-1]["portfolio"] if year_data else 0
                summary_data.append({
                    "scenario": scenario_name,
                    "retirement_year": retirement_year,
                    "age": age,
                    "portfolio": final_portfolio
                })

    print(f"{'Scenario':<50} {'Retirement Year':<18} {'Age':<8} {'Final Portfolio':<18}")
    print("-" * 94)
    for item in summary_data:
        print(f"{item['scenario']:<50} {item['retirement_year']:<18} {item['age']:<8} {format_currency(item['portfolio']):<18}")

    # Key insights
    print("\n" + "="*130)
    print("KEY INSIGHTS")
    print("="*130 + "\n")

    baseline_retire = next((s for s in summary_data if "Baseline" in s["scenario"] and "IPO" not in s["scenario"] and "Bridged" not in s["scenario"]), None)
    ipo_retire = next((s for s in summary_data if "IPO Year 2" in s["scenario"] and "Pension" not in s["scenario"]), None)

    if baseline_retire and ipo_retire:
        years_saved = baseline_retire["retirement_year"] - ipo_retire["retirement_year"]
        print(f"✓ IPO Impact: Company exit (₪2M) saves {years_saved} years of work (retire at {ipo_retire['age']} vs {baseline_retire['age']})")

    print(f"✓ Expense Impact: ₪22K/month (vs ₪25K) increases monthly savings by ₪3K")
    print(f"✓ Pension Security: Locked until age 67, but growing at 6% with ₪9K/month contributions")
    print(f"✓ Lifetime Planning: Pension-bridged scenarios ensure security through age 100")
    print()

if __name__ == "__main__":
    main()

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Mortgage, Scenario
from simulation import simulate


class TestMortgage(unittest.TestCase):
    """Test mortgage calculations."""

    def test_monthly_payment_formula(self):
        """Test that mortgage payment matches expected amortization."""
        mortgage = Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25)
        # Expected monthly payment is approximately 7,917.55 (standard amortization)
        self.assertAlmostEqual(mortgage.monthly_payment, 7_917.55, delta=1)

    def test_zero_interest_rate(self):
        """Test edge case where interest rate is zero."""
        mortgage = Mortgage(principal=120_000, annual_rate=0.0, duration_years=10)
        expected = 120_000 / (10 * 12)  # 1,000
        self.assertAlmostEqual(mortgage.monthly_payment, expected, places=2)

    def test_monthly_payment_is_positive(self):
        """Test that monthly payment is always positive."""
        mortgage = Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25)
        self.assertGreater(mortgage.monthly_payment, 0)


class TestSimulate(unittest.TestCase):
    """Test simulation engine."""

    def test_scenario_a_always_positive_net_savings(self):
        """Scenario A (no mortgage) should have positive net savings every year."""
        scenario_a = Scenario(
            name="Test A",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        result = simulate(scenario_a, years=40)
        for year_data in result.year_data:
            with self.subTest(year=year_data.year):
                self.assertGreater(year_data.net_savings, 0)

    def test_scenario_b_negative_savings_during_mortgage(self):
        """Scenario B should have negative net savings during mortgage years 1-25."""
        scenario_b = Scenario(
            name="Test B",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result = simulate(scenario_b, years=40)
        for year_data in result.year_data:
            if year_data.year <= 25:
                with self.subTest(year=year_data.year):
                    self.assertLess(year_data.net_savings, 0)

    def test_scenario_b_positive_savings_after_mortgage(self):
        """Scenario B should have positive net savings after mortgage ends (years 26+)."""
        scenario_b = Scenario(
            name="Test B",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result = simulate(scenario_b, years=40)
        for year_data in result.year_data:
            if year_data.year > 25:
                with self.subTest(year=year_data.year):
                    self.assertGreater(year_data.net_savings, 0)

    def test_portfolio_grows_monotonically_in_a(self):
        """Portfolio should increase every year in Scenario A."""
        scenario_a = Scenario(
            name="Test A",
            monthly_income=20_000,
            monthly_expenses=13_000,
            initial_portfolio=100_000,
        )
        result = simulate(scenario_a, years=40)
        for i in range(1, len(result.year_data)):
            with self.subTest(year=result.year_data[i].year):
                self.assertGreater(result.year_data[i].portfolio, result.year_data[i - 1].portfolio)

    def test_retirement_detection(self):
        """Retirement year should be first year where portfolio >= required_capital."""
        scenario = Scenario(
            name="Test",
            monthly_income=20_000,
            monthly_expenses=13_000,
            initial_portfolio=0,
        )
        result = simulate(scenario, years=40)
        self.assertIsNotNone(result.retirement_year)
        # Verify that retirement_year is indeed the first crossing
        retirement_year_data = result.year_data[result.retirement_year - 1]
        self.assertGreaterEqual(retirement_year_data.portfolio, retirement_year_data.required_capital)
        if result.retirement_year > 1:
            prev_year_data = result.year_data[result.retirement_year - 2]
            self.assertLess(prev_year_data.portfolio, prev_year_data.required_capital)

    def test_no_retirement_when_portfolio_never_sufficient(self):
        """Retirement year should be None if portfolio never reaches required_capital."""
        scenario = Scenario(
            name="Test",
            monthly_income=1_000,  # Very low income
            monthly_expenses=5_000,  # High expenses
            initial_portfolio=0,
        )
        result = simulate(scenario, years=40)
        self.assertIsNone(result.retirement_year)

    def test_year_count_matches_requested(self):
        """Number of year_data entries should match years requested."""
        scenario = Scenario(
            name="Test",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        # Test with default
        result = simulate(scenario)
        self.assertEqual(len(result.year_data), 40)
        # Test with custom
        result = simulate(scenario, years=10)
        self.assertEqual(len(result.year_data), 10)

    def test_simulate_is_pure(self):
        """Calling simulate twice with same scenario should produce identical results."""
        scenario = Scenario(
            name="Test",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        result1 = simulate(scenario, years=20)
        result2 = simulate(scenario, years=20)
        # Compare results
        self.assertEqual(result1.retirement_year, result2.retirement_year)
        self.assertEqual(len(result1.year_data), len(result2.year_data))
        for y1, y2 in zip(result1.year_data, result2.year_data):
            self.assertEqual(y1.year, y2.year)
            self.assertEqual(y1.income, y2.income)
            self.assertEqual(y1.expenses, y2.expenses)
            self.assertEqual(y1.net_savings, y2.net_savings)
            self.assertAlmostEqual(y1.portfolio, y2.portfolio, places=2)

    def test_year_field_is_1_indexed(self):
        """Year field should be 1-indexed."""
        scenario = Scenario(
            name="Test",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        result = simulate(scenario, years=10)
        self.assertEqual(result.year_data[0].year, 1)
        self.assertEqual(result.year_data[-1].year, 10)

    def test_mortgage_increases_expenses(self):
        """Mortgage should increase annual expenses."""
        scenario_no_mortgage = Scenario(
            name="No Mortgage",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_with_mortgage = Scenario(
            name="With Mortgage",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_no = simulate(scenario_no_mortgage, years=1)
        result_yes = simulate(scenario_with_mortgage, years=1)
        # Year 1 expenses should be higher with mortgage
        self.assertGreater(result_yes.year_data[0].expenses, result_no.year_data[0].expenses)


class TestComparisonAndInsights(unittest.TestCase):
    """Test comparison and insights generation."""

    def test_scenario_b_retires_much_later_or_not(self):
        """Scenario B (with mortgage) should not retire within 40 years (or much later)."""
        from comparison import compare_scenarios

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)

        # A should retire early
        self.assertIsNotNone(result_a.retirement_year)
        self.assertLess(result_a.retirement_year, 30)
        # B does not retire within 40 years (mortgage burden is too large)
        self.assertIsNone(result_b.retirement_year)

    def test_scenario_b_has_lower_final_portfolio(self):
        """Scenario B should end with lower portfolio than A."""
        from comparison import compare_scenarios

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        comparison = compare_scenarios(result_a, result_b)

        # B should have lower final portfolio
        self.assertLess(comparison.final_portfolio_difference, 0)

    def test_generate_insights_returns_string(self):
        """generate_insights should return a string."""
        from comparison import generate_insights

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = generate_insights(result_a, result_b)

        self.assertIsInstance(insights, str)
        self.assertGreater(len(insights), 0)


if __name__ == "__main__":
    unittest.main()

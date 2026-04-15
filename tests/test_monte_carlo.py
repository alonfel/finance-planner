"""Tests for Monte Carlo simulation engine and OAT sensitivity analysis."""

import unittest

from domain.models import Scenario
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
from domain.monte_carlo import run_monte_carlo, MonteCarloResult
from domain.sensitivity import run_oat_sensitivity, SensitivityResult


def _make_scenario(
    monthly_income=50_000,
    monthly_expenses=25_000,
    return_rate=0.07,
    initial_portfolio=1_000_000,
    age=40,
) -> Scenario:
    """Helper: create a simple scenario for testing."""
    return Scenario(
        name="Test",
        monthly_income=IncomeBreakdown({"income": monthly_income}),
        monthly_expenses=ExpenseBreakdown({"expenses": monthly_expenses}),
        return_rate=return_rate,
        initial_portfolio=initial_portfolio,
        age=age,
    )


class TestMonteCarloResult(unittest.TestCase):
    """Test MonteCarloResult structure and value correctness."""

    def setUp(self):
        scenario = _make_scenario()
        self.result = run_monte_carlo(scenario, n_trials=100, years=20)

    def test_returns_monte_carlo_result(self):
        """run_monte_carlo returns MonteCarloResult instance."""
        self.assertIsInstance(self.result, MonteCarloResult)

    def test_percentile_lengths_match_years(self):
        """p5, p50, p95 lists have one entry per simulated year."""
        self.assertEqual(len(self.result.percentile_p5), 20)
        self.assertEqual(len(self.result.percentile_p50), 20)
        self.assertEqual(len(self.result.percentile_p95), 20)

    def test_ages_length_matches_years(self):
        """ages list has one entry per simulated year."""
        self.assertEqual(len(self.result.ages), 20)

    def test_ages_start_at_age_plus_one(self):
        """First age is starting_age + 1 (end of year 1)."""
        self.assertEqual(self.result.ages[0], 41)

    def test_ages_increment_by_one(self):
        """Ages increment by 1 each year."""
        for i in range(1, len(self.result.ages)):
            self.assertEqual(self.result.ages[i], self.result.ages[i - 1] + 1)

    def test_percentile_ordering(self):
        """p5 <= p50 <= p95 for every year."""
        for p5, p50, p95 in zip(
            self.result.percentile_p5,
            self.result.percentile_p50,
            self.result.percentile_p95,
        ):
            self.assertLessEqual(p5, p50)
            self.assertLessEqual(p50, p95)

    def test_probabilities_in_range(self):
        """retirement_probability and survival_probability are in [0, 1]."""
        self.assertGreaterEqual(self.result.retirement_probability, 0.0)
        self.assertLessEqual(self.result.retirement_probability, 1.0)
        self.assertGreaterEqual(self.result.survival_probability, 0.0)
        self.assertLessEqual(self.result.survival_probability, 1.0)

    def test_years_field(self):
        """years field matches the requested simulation length."""
        self.assertEqual(self.result.years, 20)


class TestMonteCarloEdgeCases(unittest.TestCase):
    """Edge cases for Monte Carlo engine."""

    def test_strong_scenario_high_retirement_probability(self):
        """High savings rate scenario should achieve near 100% retirement probability."""
        scenario = _make_scenario(monthly_income=100_000, monthly_expenses=20_000)
        result = run_monte_carlo(scenario, n_trials=200, years=40)
        self.assertGreater(result.retirement_probability, 0.8)

    def test_weak_scenario_lower_probability(self):
        """Low savings rate scenario should have lower retirement probability than strong one."""
        strong = _make_scenario(monthly_income=80_000, monthly_expenses=20_000)
        weak = _make_scenario(monthly_income=80_000, monthly_expenses=70_000)
        strong_result = run_monte_carlo(strong, n_trials=200, years=40)
        weak_result = run_monte_carlo(weak, n_trials=200, years=40)
        self.assertGreater(
            strong_result.retirement_probability,
            weak_result.retirement_probability,
        )

    def test_higher_return_rate_increases_probability(self):
        """Higher return rate should produce equal or higher retirement probability."""
        low_return = _make_scenario(return_rate=0.03)
        high_return = _make_scenario(return_rate=0.10)
        low_result = run_monte_carlo(low_return, n_trials=200, years=30)
        high_result = run_monte_carlo(high_return, n_trials=200, years=30)
        self.assertGreaterEqual(
            high_result.retirement_probability,
            low_result.retirement_probability,
        )

    def test_minimum_trials(self):
        """Engine works with a single trial (n_trials=1)."""
        scenario = _make_scenario()
        result = run_monte_carlo(scenario, n_trials=1, years=10)
        self.assertEqual(len(result.percentile_p50), 10)

    def test_portfolio_grows_in_median_case(self):
        """Median portfolio should grow over time for a healthy scenario."""
        scenario = _make_scenario(monthly_income=80_000, monthly_expenses=20_000)
        result = run_monte_carlo(scenario, n_trials=200, years=20)
        self.assertGreater(result.percentile_p50[-1], result.percentile_p50[0])


class TestSensitivityAnalysis(unittest.TestCase):
    """Test OAT sensitivity analysis."""

    def setUp(self):
        scenario = _make_scenario()
        self.result = run_oat_sensitivity(scenario, n_trials=100, years=20)

    def test_returns_sensitivity_result(self):
        """run_oat_sensitivity returns SensitivityResult instance."""
        self.assertIsInstance(self.result, SensitivityResult)

    def test_exactly_six_drivers(self):
        """Sensitivity analysis always produces exactly 6 OAT drivers."""
        self.assertEqual(len(self.result.drivers), 6)

    def test_driver_names_are_expected(self):
        """Driver names match the 3 expected categories."""
        names = {d.name for d in self.result.drivers}
        self.assertIn("Return Rate", names)
        self.assertIn("Monthly Income", names)
        self.assertIn("Time Horizon", names)

    def test_directions_are_plus_or_minus(self):
        """Each driver direction is '+' or '-'."""
        for driver in self.result.drivers:
            self.assertIn(driver.direction, ("+", "-"))

    def test_each_category_has_both_directions(self):
        """Each of the 3 categories has one '+' and one '-' driver."""
        from collections import defaultdict
        by_name = defaultdict(set)
        for driver in self.result.drivers:
            by_name[driver.name].add(driver.direction)
        for name, directions in by_name.items():
            self.assertEqual(
                directions, {"+", "-"},
                msg=f"{name} missing a direction"
            )

    def test_drivers_sorted_by_abs_delta(self):
        """Drivers are sorted by absolute delta (largest impact first)."""
        deltas = [abs(d.delta) for d in self.result.drivers]
        self.assertEqual(deltas, sorted(deltas, reverse=True))

    def test_delta_is_float(self):
        """delta field is a float for all drivers."""
        for driver in self.result.drivers:
            self.assertIsInstance(driver.delta, float)

    def test_variant_probability_in_range(self):
        """variant_retirement_probability is in [0, 1] for all drivers."""
        for driver in self.result.drivers:
            self.assertGreaterEqual(driver.variant_retirement_probability, 0.0)
            self.assertLessEqual(driver.variant_retirement_probability, 1.0)


class TestRegressionRateSequenceOverride(unittest.TestCase):
    """Verify rate_sequence_override doesn't break existing simulation behaviour."""

    def test_simulate_without_override_unchanged(self):
        """Calling simulate without rate_sequence_override produces same result as before."""
        from domain.simulation import simulate

        scenario = _make_scenario()
        result1 = simulate(scenario, years=10)
        result2 = simulate(scenario, years=10)
        # Pure function: identical results every time
        self.assertEqual(result1.retirement_year, result2.retirement_year)
        for y1, y2 in zip(result1.year_data, result2.year_data):
            self.assertAlmostEqual(y1.portfolio, y2.portfolio, places=2)

    def test_rate_override_uses_provided_rates(self):
        """rate_sequence_override forces exact returns each year."""
        from domain.simulation import simulate

        scenario = _make_scenario(initial_portfolio=1_000_000, monthly_income=0, monthly_expenses=0)
        # Zero income/expenses → portfolio growth driven purely by return rate
        rates = [0.10] * 10  # Exactly 10% per year
        result = simulate(scenario, years=10, rate_sequence_override=rates)

        expected = 1_000_000 * (1.10 ** 10)
        self.assertAlmostEqual(result.year_data[-1].portfolio, expected, delta=1_000)


if __name__ == "__main__":
    unittest.main()

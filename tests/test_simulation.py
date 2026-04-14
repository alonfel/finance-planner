import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports

from domain.models import Mortgage, Scenario, Event, ScenarioNode
from domain.simulation import simulate
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown


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
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        result = simulate(scenario_a, years=40)
        for year_data in result.year_data:
            with self.subTest(year=year_data.year):
                self.assertGreater(year_data.net_savings, 0)

    def test_scenario_b_negative_savings_during_mortgage(self):
        """Scenario B should have negative net savings during mortgage years 1-25."""
        scenario_b = Scenario(
            name="Test B",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
            monthly_income=IncomeBreakdown({"income": 1_000}),  # Very low income
            monthly_expenses=ExpenseBreakdown({"expenses": 5_000}),  # High expenses
            initial_portfolio=0,
        )
        result = simulate(scenario, years=40)
        self.assertIsNone(result.retirement_year)

    def test_year_count_matches_requested(self):
        """Number of year_data entries should match years requested."""
        scenario = Scenario(
            name="Test",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        result = simulate(scenario, years=10)
        self.assertEqual(result.year_data[0].year, 1)
        self.assertEqual(result.year_data[-1].year, 10)

    def test_mortgage_increases_expenses(self):
        """Mortgage should increase annual expenses."""
        scenario_no_mortgage = Scenario(
            name="No Mortgage",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_with_mortgage = Scenario(
            name="With Mortgage",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_no = simulate(scenario_no_mortgage, years=1)
        result_yes = simulate(scenario_with_mortgage, years=1)
        # Year 1 expenses should be higher with mortgage
        self.assertGreater(result_yes.year_data[0].expenses, result_no.year_data[0].expenses)


class TestEvents(unittest.TestCase):
    """Test event handling in scenarios."""

    def test_event_portfolio_injection_positive(self):
        """Positive event (stock offering) should increase portfolio in that year."""
        scenario = Scenario(
            name="With Offering",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=2, portfolio_injection=1_000_000, description="Stock offering")],
        )
        result = simulate(scenario, years=5)
        # Year 1 portfolio before event
        year1_portfolio = result.year_data[0].portfolio
        # Year 2 portfolio should have the injection
        year2_portfolio = result.year_data[1].portfolio
        # Year 2 should be noticeably higher due to injection
        self.assertGreater(year2_portfolio, year1_portfolio * 1.5)

    def test_event_portfolio_injection_negative(self):
        """Negative event (expense) should decrease portfolio in that year."""
        scenario = Scenario(
            name="With Expense",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            initial_portfolio=500_000,
            events=[Event(year=2, portfolio_injection=-100_000, description="Emergency expense")],
        )
        result = simulate(scenario, years=5)
        # Without the event, portfolio would grow
        # But with the event, year 2 should show the impact
        year1_portfolio = result.year_data[0].portfolio
        year2_portfolio = result.year_data[1].portfolio
        year3_portfolio = result.year_data[2].portfolio
        # Year 2 should be lower due to expense
        self.assertLess(year2_portfolio, year1_portfolio * 1.07 * 1.07)

    def test_multiple_events_same_year(self):
        """Multiple events in the same year should all apply."""
        scenario = Scenario(
            name="Multiple Events",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[
                Event(year=2, portfolio_injection=1_000_000, description="Stock offering"),
                Event(year=2, portfolio_injection=-300_000, description="Expense"),
            ],
        )
        result = simulate(scenario, years=5)
        # Net injection should be 700,000
        year1_portfolio = result.year_data[0].portfolio
        year2_portfolio = result.year_data[1].portfolio
        # Year 2 should reflect net event of +700,000 before compounding
        self.assertGreater(year2_portfolio, year1_portfolio * 1.5)

    def test_event_compounds_same_year(self):
        """Events should compound in the same year they occur."""
        scenario = Scenario(
            name="Event Compounding",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            initial_portfolio=100,
            events=[Event(year=1, portfolio_injection=100, description="Injection")],
        )
        result = simulate(scenario, years=2)
        # Year 1: (100 + injection 100 + savings) * (1 + 0.07)
        # The injection should be included in the compounding
        year1_portfolio = result.year_data[0].portfolio
        # Should be more than if no injection
        self.assertGreater(year1_portfolio, 200)  # Base would be lower without injection

    def test_no_events_by_default(self):
        """Scenarios without events should work normally (events defaults to [])."""
        scenario = Scenario(
            name="No Events",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        result = simulate(scenario, years=5)
        # Should complete without error
        self.assertEqual(len(result.year_data), 5)
        # Portfolio should grow normally
        self.assertGreater(result.year_data[-1].portfolio, result.year_data[0].portfolio)

    def test_event_accelerates_retirement(self):
        """Large event injection should accelerate retirement."""
        scenario_no_event = Scenario(
            name="No Event",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_with_event = Scenario(
            name="With Event",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=2, portfolio_injection=2_000_000, description="Inheritance")],
        )
        result_no = simulate(scenario_no_event, years=40)
        result_yes = simulate(scenario_with_event, years=40)
        # Event scenario should retire earlier
        self.assertIsNotNone(result_no.retirement_year)
        self.assertIsNotNone(result_yes.retirement_year)
        self.assertLess(result_yes.retirement_year, result_no.retirement_year)


class TestComparisonAndInsights(unittest.TestCase):
    """Test comparison and insights generation."""

    def test_scenario_b_retires_much_later_or_not(self):
        """Scenario B (with mortgage) should not retire within 40 years (or much later)."""
        from domain.insights import compare_scenarios

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
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
        from domain.insights import compare_scenarios

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        comparison = compare_scenarios(result_a, result_b)

        # B should have lower final portfolio
        self.assertLess(comparison.final_portfolio_difference, 0)

    def test_generate_insights_returns_string(self):
        """generate_insights should return a string."""
        from domain.insights import generate_insights

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = generate_insights(result_a, result_b)

        self.assertIsInstance(insights, str)
        self.assertGreater(len(insights), 0)


class TestBuildInsights(unittest.TestCase):
    """Test structured insight generation (without formatting)."""

    def test_retirement_insight_count_always_two(self):
        """Should always have exactly 2 RetirementInsights (one per scenario)."""
        from domain.insights import build_insights, RetirementInsight

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        retirement_insights = [i for i in insights if isinstance(i, RetirementInsight)]
        self.assertEqual(len(retirement_insights), 2)

    def test_retirement_delta_only_when_both_retire(self):
        """RetirementDeltaInsight should only appear when both scenarios retire."""
        from domain.insights import build_insights, RetirementDeltaInsight

        # Both scenarios retire
        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Higher Income",
            monthly_income=IncomeBreakdown({"income": 30_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        delta_insights = [i for i in insights if isinstance(i, RetirementDeltaInsight)]
        # Both should retire, so there should be exactly 1 delta insight
        self.assertEqual(len(delta_insights), 1)

    def test_retirement_delta_absent_when_one_never_retires(self):
        """RetirementDeltaInsight should be absent when one scenario doesn't retire."""
        from domain.insights import build_insights, RetirementDeltaInsight

        # Scenario B with huge mortgage (will never retire in 20 years)
        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Big Mortgage",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 18_000}),
            mortgage=Mortgage(principal=5_000_000, annual_rate=0.05, duration_years=30),
        )
        result_a = simulate(scenario_a, years=20)
        result_b = simulate(scenario_b, years=20)
        insights = build_insights(result_a, result_b)

        delta_insights = [i for i in insights if isinstance(i, RetirementDeltaInsight)]
        # B doesn't retire, so no delta
        self.assertEqual(len(delta_insights), 0)

    def test_mortgage_insight_only_when_mortgage_present(self):
        """MortgageInsight should only appear when scenario B has a mortgage."""
        from domain.insights import build_insights, MortgageInsight

        # A without mortgage, B without mortgage
        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Also Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        mortgage_insights = [i for i in insights if isinstance(i, MortgageInsight)]
        # No mortgage in scenario B
        self.assertEqual(len(mortgage_insights), 0)

    def test_mortgage_insight_present_when_mortgage_in_b(self):
        """MortgageInsight should appear when scenario B has a mortgage."""
        from domain.insights import build_insights, MortgageInsight

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        mortgage_insights = [i for i in insights if isinstance(i, MortgageInsight)]
        # Mortgage in scenario B
        self.assertEqual(len(mortgage_insights), 1)
        self.assertEqual(mortgage_insights[0].scenario_name, "Buy Apartment")

    def test_portfolio_insight_difference_sign(self):
        """PortfolioInsight should correctly compute the difference (B - A)."""
        from domain.insights import build_insights, PortfolioInsight

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        portfolio_insights = [i for i in insights if isinstance(i, PortfolioInsight)]
        self.assertEqual(len(portfolio_insights), 1)
        # B has mortgage, so should have lower portfolio
        self.assertLess(portfolio_insights[0].difference, 0)

    def test_format_insights_output_unchanged(self):
        """Verify format_insights produces same output as original generate_insights."""
        from domain.insights import build_insights, format_insights, generate_insights

        scenario_a = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        scenario_b = Scenario(
            name="Buy Apartment",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_500_000, annual_rate=0.04, duration_years=25),
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)

        # Using generate_insights (backward-compatible wrapper)
        insights_string = generate_insights(result_a, result_b)
        # Using build_insights + format_insights
        structured_insights = build_insights(result_a, result_b)
        formatted_string = format_insights(structured_insights)

        # Both should produce identical output
        self.assertEqual(insights_string, formatted_string)


class TestScenarioNode(unittest.TestCase):
    """Test ScenarioNode tree-based scenario composition."""

    def test_root_node_resolves_like_person(self):
        """Root node (parent_name=None) resolves identically to old Person behavior."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            age=41,
        )
        node = ScenarioNode(name="Test Node", base_scenario=base)
        resolved = node.resolve()

        self.assertEqual(resolved.name, "Test Node")
        self.assertEqual(resolved.monthly_income.total, 20_000)
        self.assertEqual(resolved.monthly_expenses.total, 13_000)
        self.assertEqual(resolved.age, 41)

    def test_two_level_chain_inherits_scalars(self):
        """Child node inherits all scalar fields from resolved parent."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            age=41,
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root")

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(resolved.monthly_income.total, 20_000)
        self.assertEqual(resolved.monthly_expenses.total, 13_000)
        self.assertEqual(resolved.age, 41)

    def test_two_level_chain_overrides_scalar(self):
        """Child node overrides a scalar field from parent."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root", monthly_income=IncomeBreakdown({"income": 30_000}))

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(resolved.monthly_income.total, 30_000)
        self.assertEqual(resolved.monthly_expenses.total, 13_000)  # Not overridden

    def test_three_level_chain_resolves_correctly(self):
        """Grandchild inherits from parent, not from root."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 10_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 5_000}),
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root", monthly_income=IncomeBreakdown({"income": 20_000}))
        grandchild = ScenarioNode(name="Grandchild", parent_name="Child")  # No override

        all_nodes = {"Root": root, "Child": child, "Grandchild": grandchild}
        resolved = grandchild.resolve(all_nodes)

        # Should inherit child's overridden income, not root's
        self.assertEqual(resolved.monthly_income.total, 20_000)
        self.assertEqual(resolved.monthly_expenses.total, 5_000)

    def test_append_mode_accumulates_events(self):
        """event_mode='append' accumulates events from parent and child."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=1, portfolio_injection=100_000, description="Base event")],
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(
            name="Child",
            parent_name="Root",
            event_mode="append",
            events=[Event(year=2, portfolio_injection=200_000, description="Child event")],
        )

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(len(resolved.events), 2)
        self.assertEqual(resolved.events[0].year, 1)
        self.assertEqual(resolved.events[0].description, "Base event")
        self.assertEqual(resolved.events[1].year, 2)
        self.assertEqual(resolved.events[1].description, "Child event")

    def test_replace_mode_discards_parent_events(self):
        """event_mode='replace' discards parent events and uses only this node's."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=1, portfolio_injection=100_000, description="Base event")],
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(
            name="Child",
            parent_name="Root",
            event_mode="replace",
            events=[Event(year=5, portfolio_injection=500_000, description="New event")],
        )

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(len(resolved.events), 1)
        self.assertEqual(resolved.events[0].year, 5)
        self.assertEqual(resolved.events[0].description, "New event")

    def test_three_level_event_composition_replace_in_middle(self):
        """Replace in middle level discards root events, then grandchild appends."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=1, portfolio_injection=100_000, description="E1")],
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(
            name="Child",
            parent_name="Root",
            event_mode="replace",
            events=[Event(year=2, portfolio_injection=200_000, description="E2")],
        )
        grandchild = ScenarioNode(
            name="Grandchild",
            parent_name="Child",
            event_mode="append",
            events=[Event(year=3, portfolio_injection=300_000, description="E3")],
        )

        all_nodes = {"Root": root, "Child": child, "Grandchild": grandchild}
        resolved = grandchild.resolve(all_nodes)

        # Should have E2 (from replace) + E3 (appended), not E1
        self.assertEqual(len(resolved.events), 2)
        self.assertEqual(resolved.events[0].description, "E2")
        self.assertEqual(resolved.events[1].description, "E3")

    def test_three_level_event_composition_replace_at_leaf(self):
        """Replace at leaf level discards all ancestor events."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=1, portfolio_injection=100_000, description="E1")],
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(
            name="Child",
            parent_name="Root",
            event_mode="append",
            events=[Event(year=2, portfolio_injection=200_000, description="E2")],
        )
        grandchild = ScenarioNode(
            name="Grandchild",
            parent_name="Child",
            event_mode="replace",
            events=[Event(year=3, portfolio_injection=300_000, description="E3")],
        )

        all_nodes = {"Root": root, "Child": child, "Grandchild": grandchild}
        resolved = grandchild.resolve(all_nodes)

        # Should have only E3 (replace discards E1 and E2)
        self.assertEqual(len(resolved.events), 1)
        self.assertEqual(resolved.events[0].description, "E3")

    def test_resolve_does_not_mutate_base_scenario(self):
        """Resolving a multi-level chain does not mutate any base_scenario."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            events=[Event(year=1, portfolio_injection=100_000, description="Base")],
        )
        root = ScenarioNode(
            name="Root",
            base_scenario=base,
            events=[Event(year=2, portfolio_injection=200_000, description="Root")],
        )
        child = ScenarioNode(
            name="Child",
            parent_name="Root",
            event_mode="append",
            events=[Event(year=3, portfolio_injection=300_000, description="Child")],
        )

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        # Base should still have 1 event
        self.assertEqual(len(base.events), 1)
        # Resolved should have 3 (base + root + child)
        self.assertEqual(len(resolved.events), 3)

    def test_resolve_is_pure(self):
        """Calling resolve() twice on the same node returns identical results."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        root = ScenarioNode(name="Root", base_scenario=base, monthly_income=IncomeBreakdown({"income": 30_000}))
        child = ScenarioNode(name="Child", parent_name="Root", monthly_expenses=ExpenseBreakdown({"expenses": 10_000}))

        all_nodes = {"Root": root, "Child": child}
        resolved1 = child.resolve(all_nodes)
        resolved2 = child.resolve(all_nodes)

        self.assertEqual(resolved1.name, resolved2.name)
        self.assertEqual(resolved1.monthly_income, resolved2.monthly_income)
        self.assertEqual(resolved1.monthly_expenses, resolved2.monthly_expenses)
        self.assertEqual(len(resolved1.events), len(resolved2.events))

    def test_cycle_detection_raises_in_resolve(self):
        """Attempting to resolve a node with a cycle raises ValueError."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        # Create a cycle: A -> B -> A
        node_a = ScenarioNode(name="A", parent_name="B")  # Will point to B
        node_b = ScenarioNode(name="B", parent_name="A")  # Will point back to A

        all_nodes = {"A": node_a, "B": node_b}

        with self.assertRaises(ValueError) as context:
            node_a.resolve(all_nodes)

        self.assertIn("Cycle detected", str(context.exception))

    def test_missing_parent_raises_in_resolve(self):
        """Resolving a node with a non-existent parent raises KeyError."""
        node = ScenarioNode(name="Child", parent_name="NonExistent")
        all_nodes = {"Child": node}

        with self.assertRaises(KeyError):
            node.resolve(all_nodes)

    def test_mortgage_override_applied(self):
        """Child node's mortgage replaces parent's resolved mortgage."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            mortgage=Mortgage(principal=1_000_000, annual_rate=0.04, duration_years=20),
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        new_mortgage = Mortgage(principal=2_000_000, annual_rate=0.03, duration_years=25)
        child = ScenarioNode(name="Child", parent_name="Root", mortgage=new_mortgage)

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(resolved.mortgage.principal, 2_000_000)
        self.assertEqual(resolved.mortgage.annual_rate, 0.03)
        self.assertEqual(resolved.mortgage.duration_years, 25)

def test_resolved_node_is_valid_for_simulation(self):
        """A resolved ScenarioNode can be passed to simulate() without error."""
        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(
            name="Child",
            parent_name="Root",
            event_mode="append",
            events=[Event(year=2, portfolio_injection=1_000_000, description="Bonus")],
        )

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        # Should be able to simulate without error
        result = simulate(resolved, years=5)
        self.assertEqual(len(result.year_data), 5)
        self.assertEqual(result.scenario_name, "Child")


class TestHistoricalReturns(unittest.TestCase):
    """Test historical S&P 500 return rate simulation."""

    def test_historical_returns_dict_has_data(self):
        """SP500_ANNUAL_RETURNS should have entries for 1928-2024."""
        from domain.historical_returns import SP500_ANNUAL_RETURNS, HISTORICAL_START_YEAR, HISTORICAL_END_YEAR

        self.assertGreaterEqual(len(SP500_ANNUAL_RETURNS), 97)  # 1928-2024
        self.assertIn(1928, SP500_ANNUAL_RETURNS)
        self.assertIn(2024, SP500_ANNUAL_RETURNS)
        self.assertEqual(HISTORICAL_START_YEAR, 1928)
        self.assertEqual(HISTORICAL_END_YEAR, 2024)

    def test_get_historical_rate_sequence_known_year(self):
        """Sequence from known year (1990) should match historical data."""
        from domain.historical_returns import get_historical_rate_sequence, SP500_ANNUAL_RETURNS

        # 1990 was -3.17% (negative year)
        sequence = get_historical_rate_sequence(1990, 1)
        self.assertEqual(len(sequence), 1)
        self.assertEqual(sequence[0], SP500_ANNUAL_RETURNS[1990])

    def test_get_historical_rate_sequence_length(self):
        """Sequence length should match requested years."""
        from domain.historical_returns import get_historical_rate_sequence

        for num_years in [1, 5, 10, 30]:
            sequence = get_historical_rate_sequence(1990, num_years)
            self.assertEqual(len(sequence), num_years)

    def test_get_historical_rate_sequence_wraparound(self):
        """Sequence should wrap around past 2024 back to 1928."""
        from domain.historical_returns import get_historical_rate_sequence, SP500_ANNUAL_RETURNS

        # Start in 2023, request 3 years: should get 2023, 2024, 1928
        sequence = get_historical_rate_sequence(2023, 3)
        self.assertEqual(sequence[0], SP500_ANNUAL_RETURNS[2023])
        self.assertEqual(sequence[1], SP500_ANNUAL_RETURNS[2024])
        self.assertEqual(sequence[2], SP500_ANNUAL_RETURNS[1928])  # Wrapped around

    def test_get_historical_rate_sequence_invalid_year(self):
        """Invalid start year should raise ValueError."""
        from domain.historical_returns import get_historical_rate_sequence

        with self.assertRaises(ValueError):
            get_historical_rate_sequence(1800, 1)

        with self.assertRaises(ValueError):
            get_historical_rate_sequence(2099, 1)

    def test_simulate_with_historical_returns(self):
        """Simulation with historical_start_year should use historical rates."""
        scenario_historical = Scenario(
            name="Historical 1990",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            historical_start_year=1990,
        )
        scenario_fixed = Scenario(
            name="Fixed 7%",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            return_rate=0.07,
        )

        result_historical = simulate(scenario_historical, years=5)
        result_fixed = simulate(scenario_fixed, years=5)

        # Results should differ (historical 1990-1994 includes -3.17%, -9.1%, etc.)
        self.assertNotEqual(
            result_historical.year_data[-1].portfolio,
            result_fixed.year_data[-1].portfolio,
            "Historical and fixed rates should produce different portfolios"
        )

    def test_simulate_without_historical_returns_uses_fixed_rate(self):
        """Scenario without historical_start_year should use return_rate as before."""
        scenario = Scenario(
            name="Test",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            return_rate=0.07,
            historical_start_year=None,  # Explicit None
        )
        result = simulate(scenario, years=40)
        # Should complete without error and find retirement
        self.assertIsNotNone(result.retirement_year)
        self.assertEqual(len(result.year_data), 40)

    def test_simulate_historical_is_pure(self):
        """Historical simulation should be deterministic (pure function)."""
        scenario = Scenario(
            name="Pure Historical",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            historical_start_year=2000,
        )
        result1 = simulate(scenario, years=10)
        result2 = simulate(scenario, years=10)

        # Both runs should produce identical results
        self.assertEqual(len(result1.year_data), len(result2.year_data))
        for y1, y2 in zip(result1.year_data, result2.year_data):
            self.assertAlmostEqual(y1.portfolio, y2.portfolio, places=2)

    def test_historical_start_year_none_backward_compat(self):
        """Setting historical_start_year=None should be backward compatible."""
        scenario_old = Scenario(
            name="Old Style",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            return_rate=0.07,
        )
        scenario_new = Scenario(
            name="New Style",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            return_rate=0.07,
            historical_start_year=None,
        )

        result_old = simulate(scenario_old, years=20)
        result_new = simulate(scenario_new, years=20)

        # Should produce identical results (backward compatible)
        self.assertEqual(result_old.retirement_year, result_new.retirement_year)
        for y_old, y_new in zip(result_old.year_data, result_new.year_data):
            self.assertAlmostEqual(y_old.portfolio, y_new.portfolio, places=2)

    def test_historical_start_year_overrides_return_rate(self):
        """Historical start year should take precedence over return_rate."""
        scenario = Scenario(
            name="Override Test",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            return_rate=0.10,  # High fixed rate
            historical_start_year=2000,  # But use crash years instead
        )
        result = simulate(scenario, years=5)
        # 2000-2004 includes -9.1%, -11.9%, -22.1% — should be much worse than 10%
        final_portfolio = result.year_data[-1].portfolio
        # With 10% constant: portfolio should be higher than historical crash
        scenario_fixed_10 = Scenario(
            name="Fixed 10%",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            return_rate=0.10,
        )
        result_fixed = simulate(scenario_fixed_10, years=5)
        # Historical 2000 should be lower than constant 10%
        self.assertLess(final_portfolio, result_fixed.year_data[-1].portfolio)

    def test_scenario_node_inherits_historical_start_year(self):
        """ScenarioNode should properly inherit historical_start_year from parent."""
        from domain.models import ScenarioNode

        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            historical_start_year=1990,
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root")

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        # Child should inherit historical_start_year from root
        self.assertEqual(resolved.historical_start_year, 1990)

    def test_scenario_node_overrides_historical_start_year(self):
        """ScenarioNode child should be able to override historical_start_year."""
        from domain.models import ScenarioNode

        base = Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 13_000}),
            historical_start_year=1990,
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root", historical_start_year=2000)

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        # Child should override with 2000
        self.assertEqual(resolved.historical_start_year, 2000)

    def test_multi_index_backward_compat(self):
        """historical_index defaults to sp500 when not provided."""
        from domain.historical_returns import get_historical_rate_sequence

        # Call without index arg (backward compat)
        rates_default = get_historical_rate_sequence(1990, 5)
        rates_sp500 = get_historical_rate_sequence(1990, 5, index='sp500')

        # Should be identical
        self.assertEqual(rates_default, rates_sp500)

    def test_multi_index_nasdaq_different_from_sp500(self):
        """NASDAQ returns differ from S&P 500 for same period."""
        from domain.historical_returns import get_historical_rate_sequence

        rates_sp500 = get_historical_rate_sequence(1990, 10, index='sp500')
        rates_nasdaq = get_historical_rate_sequence(1990, 10, index='nasdaq')

        # Should be lists of same length
        self.assertEqual(len(rates_sp500), 10)
        self.assertEqual(len(rates_nasdaq), 10)

        # But should be different (not identical sequences)
        self.assertNotEqual(rates_sp500, rates_nasdaq)

    def test_multi_index_nasdaq_year_range_validation(self):
        """NASDAQ data only available from 1972 onward."""
        from domain.historical_returns import get_historical_rate_sequence

        # Valid year for NASDAQ
        rates = get_historical_rate_sequence(1990, 5, index='nasdaq')
        self.assertEqual(len(rates), 5)

        # Invalid year for NASDAQ (before 1972)
        with self.assertRaises(ValueError) as context:
            get_historical_rate_sequence(1970, 5, index='nasdaq')
        self.assertIn('out of range', str(context.exception))

    def test_multi_index_bonds_available_from_1928(self):
        """Bonds data available from 1928 same as S&P 500."""
        from domain.historical_returns import get_historical_rate_sequence

        rates_1928 = get_historical_rate_sequence(1928, 10, index='bonds')
        self.assertEqual(len(rates_1928), 10)

    def test_multi_index_russell2000_year_range(self):
        """Russell 2000 data only available from 1979 onward."""
        from domain.historical_returns import get_historical_rate_sequence

        # Valid year
        rates = get_historical_rate_sequence(1990, 5, index='russell2000')
        self.assertEqual(len(rates), 5)

        # Invalid year (before 1979)
        with self.assertRaises(ValueError):
            get_historical_rate_sequence(1970, 5, index='russell2000')

    def test_scenario_with_multi_index(self):
        """Scenario with historical_index='nasdaq' produces different results than sp500."""
        # Base scenario with NASDAQ
        scenario_nasdaq = Scenario(
            name="NASDAQ Backtest",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 10_000}),
            initial_portfolio=100_000,
            historical_start_year=1990,
            historical_index='nasdaq',
        )

        # Same scenario but with S&P 500
        scenario_sp500 = Scenario(
            name="S&P 500 Backtest",
            monthly_income=IncomeBreakdown({"income": 20_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 10_000}),
            initial_portfolio=100_000,
            historical_start_year=1990,
            historical_index='sp500',
        )

        result_nasdaq = simulate(scenario_nasdaq, years=10)
        result_sp500 = simulate(scenario_sp500, years=10)

        # Final portfolios should differ due to different annual returns
        self.assertNotEqual(
            result_nasdaq.year_data[-1].portfolio,
            result_sp500.year_data[-1].portfolio
        )


if __name__ == "__main__":
    unittest.main()

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports

from domain.models import Mortgage, Scenario, Event, ScenarioNode, EventOutcome, ProbabilisticEvent, StoryOutcome, StoryEventNode, FinancialStory
from domain.simulation import simulate, story_to_branches, story_to_scenario
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


class TestRetirementLifestyle(unittest.TestCase):
    """Test retirement lifestyle feature."""

    def test_full_retirement_at_50_income_drops_to_zero(self):
        """Full retirement at age 50 → income drops to 0."""
        scenario = Scenario(
            name="Full Retire at 50",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            initial_portfolio=2_000_000,
            age=40,  # Start at age 40
            retirement_lifestyle_mode="full",
            retirement_lifestyle_age=50,
        )
        result = simulate(scenario, years=30)

        # Before age 50 (years 1-10): income should be 100k
        for year_num in range(1, 11):
            year_data = result.year_data[year_num - 1]
            expected_age = 40 + year_num
            if expected_age < 50:
                # Income not yet affected
                self.assertEqual(year_data.active_income, 100_000 * 12)
                self.assertFalse(year_data.is_retired)

        # At age 50 (year 11): income drops to 0
        year_50 = result.year_data[10]  # Year 11
        self.assertEqual(year_50.active_income, 0)
        self.assertTrue(year_50.is_retired)

    def test_partial_retirement_income_reduction(self):
        """Partial retirement at age 45 with reduced income."""
        scenario = Scenario(
            name="Partial Retire at 45",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            initial_portfolio=2_000_000,
            age=40,
            retirement_lifestyle_mode="partial",
            retirement_lifestyle_age=45,
            partial_retirement_income=40_000,  # Consulting income
        )
        result = simulate(scenario, years=30)

        # Before age 45: income = 100k
        year_before = result.year_data[3]  # Year 4, age 44
        self.assertEqual(year_before.active_income, 100_000 * 12)
        self.assertFalse(year_before.is_retired)

        # At age 45: income = 40k
        year_at_45 = result.year_data[4]  # Year 5, age 45
        self.assertEqual(year_at_45.active_income, 40_000 * 12)
        self.assertTrue(year_at_45.is_retired)

    def test_no_retirement_lifestyle_backward_compatible(self):
        """Scenario without retirement lifestyle behaves same as before."""
        scenario_no_retire = Scenario(
            name="No Retirement Lifestyle",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            initial_portfolio=2_000_000,
            age=40,
            # No retirement_lifestyle settings
        )
        result = simulate(scenario_no_retire, years=30)

        # Income should stay constant
        for year_data in result.year_data:
            self.assertEqual(year_data.active_income, 100_000 * 12)
            self.assertFalse(year_data.is_retired)

    def test_retirement_age_properly_tracked(self):
        """Retirement age transition is properly tracked in year_data."""
        scenario = Scenario(
            name="Track Retirement Age",
            monthly_income=IncomeBreakdown({"salary": 80_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 60_000}),
            initial_portfolio=1_000_000,
            age=40,
            retirement_lifestyle_mode="full",
            retirement_lifestyle_age=55,
        )
        result = simulate(scenario, years=25)

        # Age 55 is reached at year_num = 55 - 40 = 15
        # So years 15-25 (inclusive) should have is_retired=True
        retired_years = [yd for yd in result.year_data if yd.is_retired]
        expected_retired_count = 25 - 15 + 1  # Years 15-25 inclusive = 11 years

        self.assertEqual(len(retired_years), expected_retired_count)

    def test_full_retirement_unsustainable(self):
        """Full retirement with low income/high expenses becomes unsustainable."""
        scenario = Scenario(
            name="Unsustainable Full Retire",
            monthly_income=IncomeBreakdown({"salary": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 80_000}),  # High expenses
            initial_portfolio=100_000,  # Small portfolio
            age=40,
            retirement_lifestyle_mode="full",
            retirement_lifestyle_age=50,
        )
        result = simulate(scenario, years=30)

        # Portfolio should deplete before the 30-year mark
        final_portfolio = result.year_data[-1].portfolio
        self.assertLess(final_portfolio, 0)

    def test_retirement_with_pension_unlocks_at_67(self):
        """Partial retirement before 67, pension unlocks at 67 to help sustain."""
        from domain.models import Pension

        pension = Pension(
            initial_value=1_000_000,
            monthly_contribution=10_000,
            annual_growth_rate=0.06,
            accessible_at_age=67,
        )

        scenario = Scenario(
            name="Retire at 50, Pension at 67",
            monthly_income=IncomeBreakdown({"salary": 100_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 70_000}),
            initial_portfolio=1_500_000,
            age=40,
            pension=pension,
            retirement_lifestyle_mode="partial",
            retirement_lifestyle_age=50,
            partial_retirement_income=40_000,
        )
        result = simulate(scenario, years=30)

        # At age 67 (year 28), pension should unlock
        year_67 = result.year_data[27]  # Year 28, age 67
        self.assertTrue(year_67.pension_accessible)


class TestSimulateBranches(unittest.TestCase):
    """Tests for simulate_branches() — deterministic multi-branch simulation."""

    def _make_scenario(self) -> Scenario:
        return Scenario(
            name="Baseline",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=1_000_000,
            age=40,
        )

    def _make_ipo_event(self) -> "ProbabilisticEvent":
        from domain.models import EventOutcome, ProbabilisticEvent
        return ProbabilisticEvent(
            name="IPO",
            outcomes=[
                EventOutcome(year=1, probability=0.20, portfolio_injection=0.0, description="No IPO"),
                EventOutcome(year=2, probability=0.60, portfolio_injection=1_500_000.0, description="IPO ₪1.5M"),
                EventOutcome(year=3, probability=0.20, portfolio_injection=3_000_000.0, description="IPO ₪3M"),
            ],
        )

    def test_no_probabilistic_events_returns_one_branch(self):
        """REGRESSION: simulate_branches with no probabilistic_events returns one result."""
        from domain.simulation import simulate_branches
        scenario = self._make_scenario()
        branches = simulate_branches(scenario, years=20)
        self.assertEqual(len(branches), 1)

    def test_no_probabilistic_events_matches_simulate(self):
        """REGRESSION: single branch result is identical to simulate()."""
        from domain.simulation import simulate, simulate_branches
        scenario = self._make_scenario()
        plain = simulate(scenario, years=20)
        label, prob, branch_result = simulate_branches(scenario, years=20)[0]
        self.assertEqual(prob, 1.0)
        self.assertEqual(branch_result.retirement_year, plain.retirement_year)
        for yd_plain, yd_branch in zip(plain.year_data, branch_result.year_data):
            self.assertAlmostEqual(yd_plain.portfolio, yd_branch.portfolio, places=2)

    def test_three_branch_ipo_returns_three_results(self):
        """HAPPY PATH: 3-outcome IPO event produces 3 branches."""
        from domain.simulation import simulate_branches
        scenario = self._make_scenario()
        scenario = scenario.__class__(
            **{**scenario.__dict__, "probabilistic_events": [self._make_ipo_event()]}
        )
        branches = simulate_branches(scenario, years=20)
        self.assertEqual(len(branches), 3)

    def test_branch_probabilities_match_outcomes(self):
        """Branch probabilities match the outcome probabilities."""
        from domain.simulation import simulate_branches
        from domain.models import EventOutcome, ProbabilisticEvent
        scenario = Scenario(
            name="Test",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=1_000_000,
            age=40,
            probabilistic_events=[self._make_ipo_event()],
        )
        branches = simulate_branches(scenario, years=20)
        probs = [p for _, p, _ in branches]
        self.assertAlmostEqual(probs[0], 0.20, places=5)
        self.assertAlmostEqual(probs[1], 0.60, places=5)
        self.assertAlmostEqual(probs[2], 0.20, places=5)

    def test_zero_probability_outcome_omitted(self):
        """Outcome with probability=0 is skipped."""
        from domain.simulation import simulate_branches
        from domain.models import EventOutcome, ProbabilisticEvent
        scenario = Scenario(
            name="Test",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=1_000_000,
            age=40,
            probabilistic_events=[ProbabilisticEvent(
                name="Partial IPO",
                outcomes=[
                    EventOutcome(year=1, probability=0.0, portfolio_injection=500_000.0, description="Cancelled"),
                    EventOutcome(year=2, probability=1.0, portfolio_injection=1_000_000.0, description="Happened"),
                ],
            )],
        )
        branches = simulate_branches(scenario, years=20)
        self.assertEqual(len(branches), 1)
        self.assertEqual(branches[0][0], "Happened")

    def test_windfall_branch_retires_earlier(self):
        """Branch with large windfall retires earlier than no-windfall branch."""
        from domain.simulation import simulate_branches
        from domain.models import EventOutcome, ProbabilisticEvent
        scenario = Scenario(
            name="Test",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 30_000}),
            initial_portfolio=500_000,
            age=40,
            probabilistic_events=[ProbabilisticEvent(
                name="Windfall",
                outcomes=[
                    EventOutcome(year=1, probability=0.5, portfolio_injection=0.0, description="No windfall"),
                    EventOutcome(year=1, probability=0.5, portfolio_injection=5_000_000.0, description="Big windfall"),
                ],
            )],
        )
        branches = simulate_branches(scenario, years=30)
        big_windfall = next(r for label, _, r in branches if "Big windfall" in label)
        no_windfall_r = next(r for label, _, r in branches if "No windfall" in label)
        self.assertLess(big_windfall.retirement_year, no_windfall_r.retirement_year)

    def test_two_events_produce_cross_product_branches(self):
        """Two independent probabilistic events with 2 outcomes each produce 4 branches (cross-product)."""
        from domain.simulation import simulate_branches
        from domain.models import EventOutcome, ProbabilisticEvent
        scenario = Scenario(
            name="Test",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=1_000_000,
            age=40,
            probabilistic_events=[
                ProbabilisticEvent(
                    name="Job",
                    outcomes=[
                        EventOutcome(year=1, probability=0.5, portfolio_injection=0.0, description="Same job"),
                        EventOutcome(year=1, probability=0.5, portfolio_injection=200_000.0, description="New job bonus"),
                    ],
                ),
                ProbabilisticEvent(
                    name="Investment",
                    outcomes=[
                        EventOutcome(year=2, probability=0.4, portfolio_injection=0.0, description="No return"),
                        EventOutcome(year=2, probability=0.6, portfolio_injection=500_000.0, description="Investment pays"),
                    ],
                ),
            ],
        )
        branches = simulate_branches(scenario, years=20)
        self.assertEqual(len(branches), 4)
        # Combined probabilities must sum to 1.0
        total_prob = sum(p for _, p, _ in branches)
        self.assertAlmostEqual(total_prob, 1.0, places=5)


class TestMonteCarloProbabilisticSampling(unittest.TestCase):
    """Tests for Monte Carlo outcome sampling with probabilistic events."""

    def _make_scenario_with_ipo(self) -> Scenario:
        from domain.models import EventOutcome, ProbabilisticEvent
        # Tight savings margin (5k/month net) so IPO windfall meaningfully improves retirement odds
        return Scenario(
            name="IPO Scenario",
            monthly_income=IncomeBreakdown({"income": 30_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=200_000,
            age=40,
            probabilistic_events=[ProbabilisticEvent(
                name="IPO",
                outcomes=[
                    EventOutcome(year=2, probability=0.20, portfolio_injection=0.0, description="No IPO"),
                    EventOutcome(year=2, probability=0.80, portfolio_injection=2_000_000.0, description="IPO"),
                ],
            )],
        )

    def test_mc_regression_no_probabilistic_events(self):
        """REGRESSION: MC with no probabilistic_events behaves same as before."""
        from domain.monte_carlo import run_monte_carlo
        scenario = Scenario(
            name="Plain",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=1_000_000,
            age=40,
        )
        result = run_monte_carlo(scenario, n_trials=100, years=20)
        self.assertEqual(len(result.percentile_p50), 20)
        self.assertGreaterEqual(result.retirement_probability, 0.0)
        self.assertLessEqual(result.retirement_probability, 1.0)

    def test_mc_with_ipo_higher_probability_than_no_ipo(self):
        """80% windfall scenario should have higher retirement probability than no-windfall baseline."""
        from domain.monte_carlo import run_monte_carlo
        with_ipo = self._make_scenario_with_ipo()
        # Same parameters as with_ipo but no probabilistic events — tests that 80% IPO chance lifts retirement odds
        without_ipo = Scenario(
            name="No IPO",
            monthly_income=IncomeBreakdown({"income": 30_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=200_000,
            age=40,
        )
        result_with = run_monte_carlo(with_ipo, n_trials=300, years=30)
        result_without = run_monte_carlo(without_ipo, n_trials=300, years=30)
        self.assertGreater(result_with.retirement_probability, result_without.retirement_probability)

    def test_mc_outcome_sampling_proportional(self):
        """Sampled outcomes across 500 trials should be ~proportional to probabilities (±10%)."""
        import random as rnd
        from domain.monte_carlo import _sample_probabilistic_events
        from domain.models import EventOutcome, ProbabilisticEvent

        rnd.seed(42)
        scenario = self._make_scenario_with_ipo()
        n_trials = 500
        windfall_count = 0

        for _ in range(n_trials):
            sampled = _sample_probabilistic_events(scenario)
            if any(e.portfolio_injection > 0 for e in sampled.events):
                windfall_count += 1

        observed_rate = windfall_count / n_trials
        self.assertAlmostEqual(observed_rate, 0.80, delta=0.10)


class TestProbabilisticEventModel(unittest.TestCase):
    """Tests for EventOutcome and ProbabilisticEvent domain models."""

    def _make_ipo_event(self) -> ProbabilisticEvent:
        """Return a 3-outcome IPO event: 20% no-IPO, 60% ₪1.5M year 2, 20% ₪3M year 3."""
        return ProbabilisticEvent(
            name="IPO",
            outcomes=[
                EventOutcome(year=1, probability=0.20, portfolio_injection=0.0, description="No IPO"),
                EventOutcome(year=2, probability=0.60, portfolio_injection=1_500_000.0, description="IPO ₪1.5M"),
                EventOutcome(year=3, probability=0.20, portfolio_injection=3_000_000.0, description="IPO ₪3M"),
            ],
        )

    # --- EventOutcome ---

    def test_event_outcome_fields(self):
        """EventOutcome stores year, probability, portfolio_injection, description."""
        outcome = EventOutcome(year=2, probability=0.6, portfolio_injection=1_500_000.0, description="IPO ₪1.5M")
        self.assertEqual(outcome.year, 2)
        self.assertAlmostEqual(outcome.probability, 0.6)
        self.assertAlmostEqual(outcome.portfolio_injection, 1_500_000.0)
        self.assertEqual(outcome.description, "IPO ₪1.5M")

    def test_event_outcome_default_description(self):
        """EventOutcome description defaults to empty string."""
        outcome = EventOutcome(year=1, probability=0.5, portfolio_injection=0.0)
        self.assertEqual(outcome.description, "")

    # --- ProbabilisticEvent validation ---

    def test_valid_three_outcome_event(self):
        """ProbabilisticEvent with 3 outcomes summing to 1.0 constructs without error."""
        event = self._make_ipo_event()
        self.assertEqual(event.name, "IPO")
        self.assertEqual(len(event.outcomes), 3)

    def test_bad_probabilities_raise_value_error(self):
        """ProbabilisticEvent raises ValueError when probabilities do not sum to 1.0."""
        with self.assertRaises(ValueError):
            ProbabilisticEvent(
                name="Bad",
                outcomes=[
                    EventOutcome(year=1, probability=0.50, portfolio_injection=0.0),
                    EventOutcome(year=2, probability=0.40, portfolio_injection=0.0),
                    # Total = 0.90, not 1.0
                ],
            )

    def test_single_outcome_probability_one(self):
        """ProbabilisticEvent with a single outcome at probability=1.0 is valid."""
        event = ProbabilisticEvent(
            name="Certain",
            outcomes=[EventOutcome(year=1, probability=1.0, portfolio_injection=500_000.0)],
        )
        self.assertEqual(len(event.outcomes), 1)

    def test_zero_outcomes_no_validation(self):
        """ProbabilisticEvent with no outcomes skips probability validation."""
        event = ProbabilisticEvent(name="Empty")
        self.assertEqual(len(event.outcomes), 0)

    def test_tolerance_within_0001(self):
        """Probabilities summing within 0.001 of 1.0 are accepted (float tolerance)."""
        event = ProbabilisticEvent(
            name="Within tolerance",
            outcomes=[
                EventOutcome(year=1, probability=0.3334, portfolio_injection=0.0),
                EventOutcome(year=2, probability=0.3333, portfolio_injection=0.0),
                EventOutcome(year=3, probability=0.3333, portfolio_injection=0.0),
                # Total = 1.0000 — within tolerance
            ],
        )
        self.assertEqual(len(event.outcomes), 3)

    # --- Scenario integration ---

    def test_scenario_has_probabilistic_events_field(self):
        """Scenario.probabilistic_events defaults to empty list."""
        scenario = Scenario(
            name="No prob events",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 30_000}),
        )
        self.assertEqual(scenario.probabilistic_events, [])

    def test_scenario_accepts_probabilistic_events(self):
        """Scenario stores probabilistic_events and they are accessible."""
        event = self._make_ipo_event()
        scenario = Scenario(
            name="With IPO",
            monthly_income=IncomeBreakdown({"income": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 30_000}),
            probabilistic_events=[event],
        )
        self.assertEqual(len(scenario.probabilistic_events), 1)
        self.assertEqual(scenario.probabilistic_events[0].name, "IPO")
        self.assertEqual(len(scenario.probabilistic_events[0].outcomes), 3)


class TestFinancialStory(unittest.TestCase):
    """Tests for FinancialStory domain model and story_to_branches / story_to_scenario."""

    def _base_scenario(self) -> Scenario:
        return Scenario(
            name="Base",
            monthly_income=IncomeBreakdown({"salary": 50_000}),
            monthly_expenses=ExpenseBreakdown({"expenses": 25_000}),
            initial_portfolio=1_000_000,
            age=40,
        )

    # --- Model construction ---

    def test_financial_story_fields(self):
        """FinancialStory stores name, base_scenario, events, story_id."""
        story = FinancialStory(name="My Story", base_scenario=self._base_scenario())
        self.assertEqual(story.name, "My Story")
        self.assertEqual(story.events, [])
        self.assertIsNone(story.story_id)

    def test_story_event_node_deterministic(self):
        """Deterministic StoryEventNode stores label, year, portfolio_injection."""
        node = StoryEventNode(node_id="n1", label="Bonus", year=3, event_type="deterministic", portfolio_injection=200_000)
        self.assertEqual(node.event_type, "deterministic")
        self.assertEqual(node.portfolio_injection, 200_000)
        self.assertEqual(node.outcomes, [])

    def test_story_event_node_probabilistic_valid(self):
        """Probabilistic StoryEventNode with outcomes summing to 1.0 constructs without error."""
        node = StoryEventNode(
            node_id="n2", label="IPO", year=3, event_type="probabilistic",
            outcomes=[
                StoryOutcome(label="Success", probability=0.7, portfolio_injection=2_000_000),
                StoryOutcome(label="No event", probability=0.3, portfolio_injection=0.0),
            ],
        )
        self.assertEqual(len(node.outcomes), 2)

    def test_story_event_node_probabilistic_bad_probs_raises(self):
        """Probabilistic StoryEventNode raises ValueError if outcomes don't sum to 1.0."""
        with self.assertRaises(ValueError):
            StoryEventNode(
                node_id="n3", label="Bad", year=2, event_type="probabilistic",
                outcomes=[
                    StoryOutcome(label="A", probability=0.4, portfolio_injection=0.0),
                    StoryOutcome(label="B", probability=0.4, portfolio_injection=0.0),
                    # Total = 0.80
                ],
            )

    # --- story_to_branches ---

    def test_deterministic_only_story_returns_one_branch(self):
        """Story with only deterministic events returns a single branch with probability=1.0."""
        story = FinancialStory(
            name="Bonus Story",
            base_scenario=self._base_scenario(),
            events=[
                StoryEventNode(node_id="n1", label="Bonus", year=2, event_type="deterministic", portfolio_injection=500_000),
            ],
        )
        branches = story_to_branches(story, years=20)
        self.assertEqual(len(branches), 1)
        label, prob, result = branches[0]
        self.assertAlmostEqual(prob, 1.0)
        self.assertIsNotNone(result)

    def test_single_probabilistic_node_returns_two_branches(self):
        """Story with one probabilistic node (2 outcomes) returns 2 branches."""
        story = FinancialStory(
            name="IPO Story",
            base_scenario=self._base_scenario(),
            events=[
                StoryEventNode(
                    node_id="n1", label="IPO", year=3, event_type="probabilistic",
                    outcomes=[
                        StoryOutcome(label="Success", probability=0.7, portfolio_injection=2_000_000),
                        StoryOutcome(label="No event", probability=0.3, portfolio_injection=0.0),
                    ],
                ),
            ],
        )
        branches = story_to_branches(story, years=20)
        self.assertEqual(len(branches), 2)
        total_prob = sum(prob for _, prob, _ in branches)
        self.assertAlmostEqual(total_prob, 1.0, places=5)

    def test_two_probabilistic_nodes_cross_product(self):
        """Two probabilistic nodes (2 outcomes each) produce 4 branches summing to 1.0."""
        story = FinancialStory(
            name="Double Split",
            base_scenario=self._base_scenario(),
            events=[
                StoryEventNode(
                    node_id="n1", label="IPO", year=3, event_type="probabilistic",
                    outcomes=[
                        StoryOutcome(label="IPO Success", probability=0.6, portfolio_injection=2_000_000),
                        StoryOutcome(label="IPO Miss", probability=0.4, portfolio_injection=0.0),
                    ],
                ),
                StoryEventNode(
                    node_id="n2", label="Bonus", year=5, event_type="probabilistic",
                    outcomes=[
                        StoryOutcome(label="Big Bonus", probability=0.5, portfolio_injection=300_000),
                        StoryOutcome(label="No Bonus", probability=0.5, portfolio_injection=0.0),
                    ],
                ),
            ],
        )
        branches = story_to_branches(story, years=20)
        self.assertEqual(len(branches), 4)
        total_prob = sum(prob for _, prob, _ in branches)
        self.assertAlmostEqual(total_prob, 1.0, places=5)

    def test_branches_with_deterministic_and_probabilistic(self):
        """Deterministic + probabilistic nodes: deterministic applies to all branches."""
        story = FinancialStory(
            name="Mixed",
            base_scenario=self._base_scenario(),
            events=[
                StoryEventNode(node_id="d1", label="Bonus", year=1, event_type="deterministic", portfolio_injection=100_000),
                StoryEventNode(
                    node_id="p1", label="IPO", year=3, event_type="probabilistic",
                    outcomes=[
                        StoryOutcome(label="Win", probability=0.8, portfolio_injection=1_000_000),
                        StoryOutcome(label="Lose", probability=0.2, portfolio_injection=0.0),
                    ],
                ),
            ],
        )
        branches = story_to_branches(story, years=20)
        self.assertEqual(len(branches), 2)

    # --- story_to_scenario ---

    def test_story_to_scenario_deterministic_only(self):
        """story_to_scenario returns Scenario with deterministic events only."""
        story = FinancialStory(
            name="Flat",
            base_scenario=self._base_scenario(),
            events=[
                StoryEventNode(node_id="d1", label="Windfall", year=2, event_type="deterministic", portfolio_injection=500_000),
                StoryEventNode(
                    node_id="p1", label="IPO", year=4, event_type="probabilistic",
                    outcomes=[
                        StoryOutcome(label="Yes", probability=0.5, portfolio_injection=1_000_000),
                        StoryOutcome(label="No", probability=0.5, portfolio_injection=0.0),
                    ],
                ),
            ],
        )
        scenario = story_to_scenario(story)
        self.assertEqual(len(scenario.events), 1)
        self.assertEqual(scenario.events[0].description, "Windfall")
        self.assertEqual(scenario.probabilistic_events, [])

    def test_story_to_scenario_uses_story_name(self):
        """story_to_scenario uses the story name, not the base scenario name."""
        story = FinancialStory(name="My Narrative", base_scenario=self._base_scenario())
        scenario = story_to_scenario(story)
        self.assertEqual(scenario.name, "My Narrative")

    def test_story_to_scenario_empty_events(self):
        """story_to_scenario with no events returns Scenario with empty events list."""
        story = FinancialStory(name="Empty", base_scenario=self._base_scenario())
        scenario = story_to_scenario(story)
        self.assertEqual(scenario.events, [])
        self.assertEqual(scenario.probabilistic_events, [])


if __name__ == "__main__":
    unittest.main()

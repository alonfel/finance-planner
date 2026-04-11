import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Mortgage, Scenario, Event, ScenarioNode
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


class TestEvents(unittest.TestCase):
    """Test event handling in scenarios."""

    def test_event_portfolio_injection_positive(self):
        """Positive event (stock offering) should increase portfolio in that year."""
        scenario = Scenario(
            name="With Offering",
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_with_event = Scenario(
            name="With Event",
            monthly_income=20_000,
            monthly_expenses=13_000,
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


class TestBuildInsights(unittest.TestCase):
    """Test structured insight generation (without formatting)."""

    def test_retirement_insight_count_always_two(self):
        """Should always have exactly 2 RetirementInsights (one per scenario)."""
        from comparison import build_insights, RetirementInsight

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
        insights = build_insights(result_a, result_b)

        retirement_insights = [i for i in insights if isinstance(i, RetirementInsight)]
        self.assertEqual(len(retirement_insights), 2)

    def test_retirement_delta_only_when_both_retire(self):
        """RetirementDeltaInsight should only appear when both scenarios retire."""
        from comparison import build_insights, RetirementDeltaInsight

        # Both scenarios retire
        scenario_a = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_b = Scenario(
            name="Higher Income",
            monthly_income=30_000,
            monthly_expenses=13_000,
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        delta_insights = [i for i in insights if isinstance(i, RetirementDeltaInsight)]
        # Both should retire, so there should be exactly 1 delta insight
        self.assertEqual(len(delta_insights), 1)

    def test_retirement_delta_absent_when_one_never_retires(self):
        """RetirementDeltaInsight should be absent when one scenario doesn't retire."""
        from comparison import build_insights, RetirementDeltaInsight

        # Scenario B with huge mortgage (will never retire in 20 years)
        scenario_a = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_b = Scenario(
            name="Big Mortgage",
            monthly_income=20_000,
            monthly_expenses=18_000,
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
        from comparison import build_insights, MortgageInsight

        # A without mortgage, B without mortgage
        scenario_a = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        scenario_b = Scenario(
            name="Also Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        result_a = simulate(scenario_a, years=40)
        result_b = simulate(scenario_b, years=40)
        insights = build_insights(result_a, result_b)

        mortgage_insights = [i for i in insights if isinstance(i, MortgageInsight)]
        # No mortgage in scenario B
        self.assertEqual(len(mortgage_insights), 0)

    def test_mortgage_insight_present_when_mortgage_in_b(self):
        """MortgageInsight should appear when scenario B has a mortgage."""
        from comparison import build_insights, MortgageInsight

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
        insights = build_insights(result_a, result_b)

        mortgage_insights = [i for i in insights if isinstance(i, MortgageInsight)]
        # Mortgage in scenario B
        self.assertEqual(len(mortgage_insights), 1)
        self.assertEqual(mortgage_insights[0].scenario_name, "Buy Apartment")

    def test_portfolio_insight_difference_sign(self):
        """PortfolioInsight should correctly compute the difference (B - A)."""
        from comparison import build_insights, PortfolioInsight

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
        insights = build_insights(result_a, result_b)

        portfolio_insights = [i for i in insights if isinstance(i, PortfolioInsight)]
        self.assertEqual(len(portfolio_insights), 1)
        # B has mortgage, so should have lower portfolio
        self.assertLess(portfolio_insights[0].difference, 0)

    def test_format_insights_output_unchanged(self):
        """Verify format_insights produces same output as original generate_insights."""
        from comparison import build_insights, format_insights, generate_insights

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
            monthly_income=20_000,
            monthly_expenses=13_000,
            age=41,
        )
        node = ScenarioNode(name="Test Node", base_scenario=base)
        resolved = node.resolve()

        self.assertEqual(resolved.name, "Test Node")
        self.assertEqual(resolved.monthly_income, 20_000)
        self.assertEqual(resolved.monthly_expenses, 13_000)
        self.assertEqual(resolved.age, 41)

    def test_two_level_chain_inherits_scalars(self):
        """Child node inherits all scalar fields from resolved parent."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            age=41,
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root")

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(resolved.monthly_income, 20_000)
        self.assertEqual(resolved.monthly_expenses, 13_000)
        self.assertEqual(resolved.age, 41)

    def test_two_level_chain_overrides_scalar(self):
        """Child node overrides a scalar field from parent."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root", monthly_income=30_000)

        all_nodes = {"Root": root, "Child": child}
        resolved = child.resolve(all_nodes)

        self.assertEqual(resolved.monthly_income, 30_000)
        self.assertEqual(resolved.monthly_expenses, 13_000)  # Not overridden

    def test_three_level_chain_resolves_correctly(self):
        """Grandchild inherits from parent, not from root."""
        base = Scenario(
            name="Baseline",
            monthly_income=10_000,
            monthly_expenses=5_000,
        )
        root = ScenarioNode(name="Root", base_scenario=base)
        child = ScenarioNode(name="Child", parent_name="Root", monthly_income=20_000)
        grandchild = ScenarioNode(name="Grandchild", parent_name="Child")  # No override

        all_nodes = {"Root": root, "Child": child, "Grandchild": grandchild}
        resolved = grandchild.resolve(all_nodes)

        # Should inherit child's overridden income, not root's
        self.assertEqual(resolved.monthly_income, 20_000)
        self.assertEqual(resolved.monthly_expenses, 5_000)

    def test_append_mode_accumulates_events(self):
        """event_mode='append' accumulates events from parent and child."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        root = ScenarioNode(name="Root", base_scenario=base, monthly_income=30_000)
        child = ScenarioNode(name="Child", parent_name="Root", monthly_expenses=10_000)

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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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
            monthly_income=20_000,
            monthly_expenses=13_000,
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


if __name__ == "__main__":
    unittest.main()

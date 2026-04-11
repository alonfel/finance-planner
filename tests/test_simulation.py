import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Mortgage, Scenario, Event, Person
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


class TestPerson(unittest.TestCase):
    """Test Person object (scenario composition)."""

    def test_resolve_no_overrides_inherits_all_base_fields(self):
        """All base fields should be inherited when no overrides are set."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            age=41,
            return_rate=0.07,
            withdrawal_rate=0.04,
        )
        person = Person(name="Test Person", base_scenario=base)
        resolved = person.resolve()

        # Should inherit all base fields (except name, which comes from person)
        self.assertEqual(resolved.name, "Test Person")
        self.assertEqual(resolved.monthly_income, 20_000)
        self.assertEqual(resolved.monthly_expenses, 13_000)
        self.assertEqual(resolved.age, 41)
        self.assertEqual(resolved.return_rate, 0.07)
        self.assertEqual(resolved.withdrawal_rate, 0.04)

    def test_resolve_name_becomes_scenario_name(self):
        """Person's name should become the resolved Scenario's name."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        person = Person(name="Alice - My Custom Scenario", base_scenario=base)
        resolved = person.resolve()

        self.assertEqual(resolved.name, "Alice - My Custom Scenario")
        # Base should not be mutated
        self.assertEqual(base.name, "Baseline")

    def test_resolve_scalar_override_applied(self):
        """Scalar overrides (income, expenses, age, etc.) should be applied."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            age=41,
        )
        person = Person(
            name="Test",
            base_scenario=base,
            monthly_income=60_000,  # Override
            age=50,  # Override
        )
        resolved = person.resolve()

        self.assertEqual(resolved.monthly_income, 60_000)
        self.assertEqual(resolved.monthly_expenses, 13_000)  # Not overridden
        self.assertEqual(resolved.age, 50)

    def test_resolve_extra_events_appended_to_base(self):
        """extra_events should be appended after base_scenario.events."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            events=[Event(year=1, portfolio_injection=100_000, description="Base event")],
        )
        person = Person(
            name="Test",
            base_scenario=base,
            extra_events=[
                Event(year=2, portfolio_injection=200_000, description="Extra event 1"),
                Event(year=3, portfolio_injection=300_000, description="Extra event 2"),
            ],
        )
        resolved = person.resolve()

        self.assertEqual(len(resolved.events), 3)
        self.assertEqual(resolved.events[0].year, 1)
        self.assertEqual(resolved.events[0].description, "Base event")
        self.assertEqual(resolved.events[1].year, 2)
        self.assertEqual(resolved.events[1].description, "Extra event 1")
        self.assertEqual(resolved.events[2].year, 3)
        self.assertEqual(resolved.events[2].description, "Extra event 2")

    def test_resolve_replace_events_replaces_base(self):
        """replace_events should completely replace base_scenario.events."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            events=[Event(year=1, portfolio_injection=100_000, description="Base event")],
        )
        person = Person(
            name="Test",
            base_scenario=base,
            replace_events=[
                Event(year=5, portfolio_injection=500_000, description="New event 1"),
                Event(year=6, portfolio_injection=600_000, description="New event 2"),
            ],
        )
        resolved = person.resolve()

        # Should have exactly the replace_events, not base + replace
        self.assertEqual(len(resolved.events), 2)
        self.assertEqual(resolved.events[0].year, 5)
        self.assertEqual(resolved.events[0].description, "New event 1")
        self.assertEqual(resolved.events[1].year, 6)
        self.assertEqual(resolved.events[1].description, "New event 2")

    def test_resolve_does_not_mutate_base_scenario(self):
        """Base scenario should not be mutated by resolve()."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            events=[Event(year=1, portfolio_injection=100_000, description="Base event")],
        )
        person = Person(
            name="Test",
            base_scenario=base,
            extra_events=[Event(year=2, portfolio_injection=200_000, description="Extra")],
        )
        resolved = person.resolve()

        # Base should still have only 1 event
        self.assertEqual(len(base.events), 1)
        # Resolved should have 2 events
        self.assertEqual(len(resolved.events), 2)

    def test_resolve_mortgage_override_applied(self):
        """Person's mortgage should replace base_scenario.mortgage if set."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
            mortgage=Mortgage(principal=1_000_000, annual_rate=0.04, duration_years=20),
        )
        new_mortgage = Mortgage(principal=2_000_000, annual_rate=0.03, duration_years=25)
        person = Person(
            name="Test",
            base_scenario=base,
            mortgage=new_mortgage,
        )
        resolved = person.resolve()

        self.assertEqual(resolved.mortgage.principal, 2_000_000)
        self.assertEqual(resolved.mortgage.annual_rate, 0.03)
        self.assertEqual(resolved.mortgage.duration_years, 25)

    def test_resolve_produces_valid_scenario_for_simulation(self):
        """Resolved person should produce a valid Scenario that can be simulated."""
        base = Scenario(
            name="Baseline",
            monthly_income=20_000,
            monthly_expenses=13_000,
        )
        person = Person(
            name="Test Person",
            base_scenario=base,
            extra_events=[Event(year=2, portfolio_injection=1_000_000, description="Bonus")],
        )
        resolved = person.resolve()

        # Should be able to simulate without error
        result = simulate(resolved, years=5)
        self.assertEqual(len(result.year_data), 5)
        self.assertEqual(result.scenario_name, "Test Person")


if __name__ == "__main__":
    unittest.main()

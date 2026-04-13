"""Parsers for converting JSON dictionaries to domain objects."""

from domain.models import Scenario, ScenarioNode, Mortgage, Event, Pension
from domain.breakdown import IncomeBreakdown, ExpenseBreakdown


def parse_mortgage(d: dict) -> Mortgage | None:
    """Parse a mortgage dict into a Mortgage object, or None if not present.

    Args:
        d: Dictionary with keys 'principal', 'annual_rate', 'duration_years', optional 'currency'

    Returns:
        Mortgage object or None
    """
    if not d:
        return None

    return Mortgage(
        principal=d["principal"],
        annual_rate=d["annual_rate"],
        duration_years=d["duration_years"],
        currency=d.get("currency", "ILS"),
    )


def parse_income_breakdown(value) -> IncomeBreakdown:
    """Parse income value — either a plain float or a dict of named components.

    Backward compatible: a plain float is treated as {"income": value}.
    A dict is used directly as components.

    Args:
        value: Either a number (int/float) or a dict of {label: amount}

    Returns:
        IncomeBreakdown with components dict

    Raises:
        ValueError: if value is not a number or dict
    """
    if isinstance(value, (int, float)):
        return IncomeBreakdown(components={"income": float(value)})
    if isinstance(value, dict):
        return IncomeBreakdown(components={k: float(v) for k, v in value.items()})
    raise ValueError(f"monthly_income must be a number or dict, got {type(value)}")


def parse_expense_breakdown(value) -> ExpenseBreakdown:
    """Parse expense value — either a plain float or a dict of named components.

    Backward compatible: a plain float is treated as {"expenses": value}.
    A dict is used directly as components.

    Args:
        value: Either a number (int/float) or a dict of {label: amount}

    Returns:
        ExpenseBreakdown with components dict

    Raises:
        ValueError: if value is not a number or dict
    """
    if isinstance(value, (int, float)):
        return ExpenseBreakdown(components={"expenses": float(value)})
    if isinstance(value, dict):
        return ExpenseBreakdown(components={k: float(v) for k, v in value.items()})
    raise ValueError(f"monthly_expenses must be a number or dict, got {type(value)}")


def parse_pension(d: dict) -> Pension | None:
    """Parse a pension dict into a Pension object, or None if not present.

    Args:
        d: Dictionary with keys 'initial_value', 'monthly_contribution', 'annual_growth_rate',
           optional 'accessible_at_age'

    Returns:
        Pension object or None
    """
    if not d:
        return None

    return Pension(
        initial_value=d["initial_value"],
        monthly_contribution=d["monthly_contribution"],
        annual_growth_rate=d["annual_growth_rate"],
        accessible_at_age=d.get("accessible_at_age", 67),
    )


def parse_events(event_list: list) -> list[Event]:
    """Parse a list of event dicts into Event objects.

    Args:
        event_list: List of event dicts with 'year', 'portfolio_injection', optional 'description'

    Returns:
        List of Event objects
    """
    return [
        Event(
            year=e["year"],
            portfolio_injection=e["portfolio_injection"],
            description=e.get("description", ""),
        )
        for e in event_list
    ]


def parse_scenario(d: dict, default_return_rate: float = 0.07, default_withdrawal_rate: float = 0.04) -> Scenario:
    """Parse a scenario dict into a Scenario object.

    Args:
        d: Dictionary with required keys 'name', 'monthly_income', 'monthly_expenses',
           optional keys for mortgage, pension, events, return_rate, withdrawal_rate, currency, age, initial_portfolio, retirement_mode
        default_return_rate: Default return rate if not in dict
        default_withdrawal_rate: Default withdrawal rate if not in dict

    Returns:
        Scenario object
    """
    mortgage = parse_mortgage(d.get("mortgage"))
    pension = parse_pension(d.get("pension"))
    events = parse_events(d.get("events", []))

    return Scenario(
        name=d["name"],
        monthly_income=parse_income_breakdown(d["monthly_income"]),
        monthly_expenses=parse_expense_breakdown(d["monthly_expenses"]),
        mortgage=mortgage,
        pension=pension,
        initial_portfolio=d.get("initial_portfolio", 0.0),
        return_rate=d.get("return_rate", default_return_rate),
        withdrawal_rate=d.get("withdrawal_rate", default_withdrawal_rate),
        currency=d.get("currency", "ILS"),
        age=d.get("age", 30),
        events=events,
        retirement_mode=d.get("retirement_mode", "liquid_only"),
    )


def parse_scenario_node(d: dict, all_scenarios: dict) -> ScenarioNode:
    """Parse a scenario node dict into a ScenarioNode object.

    A ScenarioNode can be a root node (with base_scenario) or a child node (with parent).
    This function does NOT validate the tree structure; that happens in load_scenario_nodes.

    Args:
        d: Dictionary with required key 'name', optional 'base_scenario' (root) or 'parent' (child),
           optional override fields and events
        all_scenarios: dict[str, Scenario] loaded from scenarios.json (for resolving base_scenario names)

    Returns:
        ScenarioNode object (not yet resolved via .resolve())

    Raises:
        ValueError: if base_scenario is specified but not found in all_scenarios, or event_mode is invalid
    """
    # Root node: base_scenario is resolved from scenarios.json
    base_scenario = None
    if "base_scenario" in d:
        scenario_name = d["base_scenario"]
        if scenario_name not in all_scenarios:
            raise ValueError(f"base_scenario '{scenario_name}' not found in scenarios.json")
        base_scenario = all_scenarios[scenario_name]

    # Child node: parent_name is a string key (validated later in load_scenario_nodes)
    parent_name = d.get("parent", None)

    # Parse events and event_mode
    events = parse_events(d.get("events", []))
    event_mode = d.get("event_mode", "append")
    if event_mode not in ("append", "replace"):
        raise ValueError(f"event_mode must be 'append' or 'replace', got '{event_mode}'")

    # Parse mortgage and pension
    mortgage = parse_mortgage(d.get("mortgage"))
    pension = parse_pension(d.get("pension"))

    return ScenarioNode(
        name=d["name"],
        base_scenario=base_scenario,
        parent_name=parent_name,
        monthly_income=parse_income_breakdown(d["monthly_income"]) if "monthly_income" in d else None,
        monthly_expenses=parse_expense_breakdown(d["monthly_expenses"]) if "monthly_expenses" in d else None,
        age=d.get("age"),
        initial_portfolio=d.get("initial_portfolio"),
        return_rate=d.get("return_rate"),
        withdrawal_rate=d.get("withdrawal_rate"),
        currency=d.get("currency"),
        retirement_mode=d.get("retirement_mode"),
        mortgage=mortgage,
        pension=pension,
        event_mode=event_mode,
        events=events,
    )

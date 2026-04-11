import dataclasses
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Event:
    """Represents a one-time portfolio event (e.g., stock offering, inheritance, emergency expense)."""
    year: int  # Which simulation year (1-indexed)
    portfolio_injection: float  # Positive = gain, negative = expense
    description: str = ""  # Optional label for the event


@dataclass
class Mortgage:
    """Represents a fixed-rate mortgage with standard amortization."""
    principal: float
    annual_rate: float
    duration_years: int
    currency: str = "ILS"  # Currency code (e.g., "ILS", "USD", "EUR")
    monthly_payment: float = field(init=False)

    def __post_init__(self):
        """Compute monthly payment using standard amortization formula."""
        r = self.annual_rate / 12
        n = self.duration_years * 12

        if r == 0:
            self.monthly_payment = self.principal / n
        else:
            numerator = r * (1 + r) ** n
            denominator = (1 + r) ** n - 1
            self.monthly_payment = self.principal * (numerator / denominator)


@dataclass
class Scenario:
    """Represents a financial scenario with income, expenses, optional mortgage, and one-time events."""
    name: str
    monthly_income: float
    monthly_expenses: float
    mortgage: Optional[Mortgage] = None
    initial_portfolio: float = 0.0
    return_rate: float = 0.07  # Annual portfolio return rate
    withdrawal_rate: float = 0.04  # Safe withdrawal rate (4% rule)
    currency: str = "ILS"  # Currency code (e.g., "ILS", "USD", "EUR")
    age: int = 30  # Current age (used to calculate retirement age)
    events: list[Event] = field(default_factory=list)  # One-time events


@dataclass
class Person:
    """A named individual built from a base Scenario with optional overrides.

    Allows reusing a base scenario across multiple people with different overrides
    (income, events, mortgage, age, etc.) without duplicating the base definition.
    """
    name: str
    base_scenario: Scenario

    # Scalar overrides — None means "inherit from base_scenario"
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    age: Optional[int] = None
    initial_portfolio: Optional[float] = None
    return_rate: Optional[float] = None
    withdrawal_rate: Optional[float] = None
    currency: Optional[str] = None

    # Mortgage override — replaces base_scenario.mortgage if set
    mortgage: Optional[Mortgage] = None

    # Event composition:
    # - extra_events are appended to base_scenario.events (default path)
    # - replace_events, if set, replaces base_scenario.events entirely
    extra_events: list[Event] = field(default_factory=list)
    replace_events: Optional[list[Event]] = None

    def resolve(self) -> Scenario:
        """Build final Scenario by merging base scenario with overrides.

        Does not mutate base_scenario. Returns a new Scenario with:
        - All base fields inherited
        - This person's name as the scenario name
        - Any scalar overrides applied
        - Events merged (either base + extra, or replace_events if set)
        - Mortgage replaced if set

        Returns:
            A new Scenario object ready for simulate()
        """
        # Determine final events
        if self.replace_events is not None:
            final_events = list(self.replace_events)
        else:
            final_events = list(self.base_scenario.events) + list(self.extra_events)

        # Build overrides dict: only include fields where person explicitly set a value
        overrides = {}
        for field_name in ['monthly_income', 'monthly_expenses', 'age',
                           'initial_portfolio', 'return_rate', 'withdrawal_rate', 'currency']:
            val = getattr(self, field_name)
            if val is not None:
                overrides[field_name] = val

        if self.mortgage is not None:
            overrides['mortgage'] = self.mortgage

        # Use dataclasses.replace() to create a shallow copy with overrides
        return dataclasses.replace(
            self.base_scenario,
            name=self.name,
            events=final_events,
            **overrides
        )

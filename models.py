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

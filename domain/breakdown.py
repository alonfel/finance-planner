"""Named income and expense components with aggregation.

Each breakdown holds a dict of labeled components that sum to a total.
This enables scenario analysis to vary individual components (e.g., "what if
salary changes?") while keeping others constant.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomeBreakdown:
    """Named income components that sum to total monthly income.

    Each key is a label (e.g. "salary", "freelance", "rental").
    Use .total to get the sum used in simulation.
    """
    components: dict[str, float]

    @property
    def total(self) -> float:
        """Return sum of all income components."""
        return sum(self.components.values())

    def merge(self, override: "IncomeBreakdown") -> "IncomeBreakdown":
        """Deep merge: return new breakdown with override keys replacing matching parent keys.

        Enables child scenarios to override just one component (e.g., freelance)
        while inheriting others (e.g., salary).
        """
        merged = dict(self.components)
        merged.update(override.components)
        return IncomeBreakdown(components=merged)


@dataclass(frozen=True)
class ExpenseBreakdown:
    """Named expense components that sum to total monthly expenses."""
    components: dict[str, float]

    @property
    def total(self) -> float:
        """Return sum of all expense components."""
        return sum(self.components.values())

    def merge(self, override: "ExpenseBreakdown") -> "ExpenseBreakdown":
        """Deep merge: return new breakdown with override keys replacing matching parent keys."""
        merged = dict(self.components)
        merged.update(override.components)
        return ExpenseBreakdown(components=merged)

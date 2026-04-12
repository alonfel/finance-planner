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
class ScenarioNode:
    """A node in a scenario inheritance tree.

    Supports tree-based scenario composition where each node can override fields
    from its parent and control event composition (append or replace).

    Root node: set base_scenario, leave parent_name=None
    Child node: set parent_name, leave base_scenario=None
    """
    name: str
    base_scenario: Optional[Scenario] = None
    parent_name: Optional[str] = None

    # Scalar overrides — None means "inherit from resolved parent"
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    age: Optional[int] = None
    initial_portfolio: Optional[float] = None
    return_rate: Optional[float] = None
    withdrawal_rate: Optional[float] = None
    currency: Optional[str] = None

    # Mortgage override — replaces resolved parent's mortgage if set
    mortgage: Optional[Mortgage] = None

    # Event composition: child controls mode relative to parent
    event_mode: str = "append"                         # "append" | "replace"
    events: list[Event] = field(default_factory=list)  # This node's own events

    def resolve(self, all_nodes: dict[str, "ScenarioNode"] = None) -> Scenario:
        """Resolve this node into a flat Scenario by walking the ancestor chain.

        For root nodes (parent_name=None), walks only this node.
        For child nodes, walks up to the root via parent_name links, then applies
        overrides root-to-leaf, merging events according to each node's event_mode.

        Does not mutate any node's base_scenario or any intermediate resolved Scenario.

        Args:
            all_nodes: dict[str, ScenarioNode] containing all nodes in the tree.
                      If None, treats as empty dict. For root nodes, can be omitted.

        Returns:
            A new Scenario object with name=self.name and merged events.
        """
        if all_nodes is None:
            all_nodes = {}

        # Build ancestor chain: root -> ... -> self
        ancestor_chain = self._build_ancestor_chain(all_nodes)

        # Start from root: apply overrides root-to-leaf, accumulating events
        current_scenario = ancestor_chain[0].base_scenario
        accumulated_events = list(ancestor_chain[0].base_scenario.events)

        # Apply overrides and events for each node in the chain (root to leaf)
        for i, node in enumerate(ancestor_chain):
            # Apply scalar overrides
            overrides = {}
            for field_name in ['monthly_income', 'monthly_expenses', 'age',
                               'initial_portfolio', 'return_rate', 'withdrawal_rate', 'currency']:
                val = getattr(node, field_name)
                if val is not None:
                    overrides[field_name] = val

            if node.mortgage is not None:
                overrides['mortgage'] = node.mortgage

            current_scenario = dataclasses.replace(current_scenario, **overrides)

            # Apply event merge
            if i == 0:
                # For the root node, start fresh: either use base_scenario.events + node.events (append)
                # or node.events only (replace)
                if node.event_mode == "replace":
                    accumulated_events = list(node.events)
                else:  # append
                    accumulated_events = accumulated_events + list(node.events)
            else:
                # For child nodes, merge with what we accumulated so far
                if node.event_mode == "replace":
                    accumulated_events = list(node.events)
                else:  # append
                    accumulated_events = accumulated_events + list(node.events)

        # Final scenario with this node's name and merged events
        return dataclasses.replace(
            current_scenario,
            name=self.name,
            events=accumulated_events
        )

    def _build_ancestor_chain(self, all_nodes: dict[str, "ScenarioNode"]) -> list["ScenarioNode"]:
        """Walk parent_name links from self to root, return [root, ..., self]."""
        chain = [self]
        current = self

        # Walk up to root
        while current.parent_name is not None:
            if current.parent_name not in all_nodes:
                raise KeyError(f"Parent '{current.parent_name}' not found in scenario nodes")
            parent = all_nodes[current.parent_name]

            # Cycle detection
            if parent.name in [n.name for n in chain]:
                raise ValueError(f"Cycle detected in scenario tree: {parent.name} is ancestor of itself")

            chain.insert(0, parent)
            current = parent

        return chain

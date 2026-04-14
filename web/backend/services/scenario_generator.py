"""
Scenario Generator Service

Converts questionnaire answers + template defaults into runnable Scenario objects,
runs simulations, and evaluates results against simple rules.

Design principles:
- Config-first (all rules in JSON, no hardcoding)
- Evolutionary (easy to add new questions, rules, profiles)
- Reuses existing domain models (Scenario, simulate(), insights)
"""

import json
import os
import re
import sys
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Add parent directory to path for domain imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import domain models (existing)
try:
    from domain.models import Scenario, Mortgage, Pension
    from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
    from domain.simulation import simulate
    from domain.insights import build_insights
except ImportError:
    # Fallback for absolute imports
    sys.path.insert(0, '.')
    from domain.models import Scenario, Mortgage, Pension
    from domain.breakdown import IncomeBreakdown, ExpenseBreakdown
    from domain.simulation import simulate
    from domain.insights import build_insights


class QuestionnaireConfig:
    """Loads and manages questionnaire configuration."""

    def __init__(self, config_path: str):
        """Load questionnaire from JSON file."""
        with open(config_path, 'r') as f:
            self.data = json.load(f)
        self.version = self.data.get('version', '1.0')
        self.questions = {q['id']: q for q in self.data['questions']}

    def get_required_questions(self) -> List[str]:
        """Return list of required question IDs (non-conditional)."""
        return [
            q['id'] for q in self.data['questions']
            if q.get('required', False) and not q.get('conditional', False)
        ]

    def get_all_questions(self) -> List[str]:
        """Return all question IDs."""
        return [q['id'] for q in self.data['questions']]

    def get_questions_by_section(self) -> Dict[str, List[Dict]]:
        """Return questions grouped by section in order."""
        sections = {}
        section_order = self.data.get('sections', {})

        for q in self.data['questions']:
            section = q.get('section', 'Other')
            if section not in sections:
                sections[section] = []
            sections[section].append(q)

        # Sort sections by order
        return dict(
            sorted(
                sections.items(),
                key=lambda x: section_order.get(x[0], {}).get('order', 999)
            )
        )

    def calculate_completeness_score(self, answers: Dict[str, Any]) -> float:
        """
        Calculate data completeness as % of required questions answered.

        Args:
            answers: Dict of question_id -> answer_value

        Returns:
            Score from 0.0 to 1.0
        """
        required = self.get_required_questions()
        if not required:
            return 1.0

        answered = sum(1 for q_id in required if q_id in answers and answers[q_id] is not None)
        return answered / len(required)

    def get_visible_questions(self, answers: Dict[str, Any]) -> List[Dict]:
        """
        Return list of questions that should be visible given current answers.

        Evaluates conditional visibility rules.
        """
        visible = []
        for q in self.data['questions']:
            condition = q.get('visible_when')
            if condition is None:
                # No condition, always visible
                visible.append(q)
            else:
                # Evaluate condition (simple eval, safe since we control config)
                try:
                    if eval(condition, {"__builtins__": {}}, answers):
                        visible.append(q)
                except:
                    pass
        return visible


class TemplateDefaults:
    """Loads and manages template default values."""

    def __init__(self, config_path: str):
        """Load defaults from JSON file."""
        with open(config_path, 'r') as f:
            self.data = json.load(f)
        self.profile = self.data.get('profile', 'default')
        self.defaults = self.data['defaults']

    def get_default(self, key: str, fallback: Any = None) -> Any:
        """Get a default value by key (supports nested keys like 'pension.initial_value')."""
        keys = key.split('.')
        value = self.defaults

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return fallback

        return value if value is not None else fallback


class EvaluationRules:
    """Loads and evaluates scenario results against rules."""

    def __init__(self, config_path: str):
        """Load rules from JSON file."""
        with open(config_path, 'r') as f:
            self.data = json.load(f)
        self.rules = self.data.get('rules', [])
        self.default = self.data.get('default_verdict', {})

    def evaluate(self, result) -> Dict[str, Any]:
        """
        Evaluate simulation result against rules.

        Returns dict with:
        - verdict: 'success', 'warning', 'fail'
        - emoji: emoji string
        - message: human-readable message
        - hint: actionable hint
        """
        # Build context for condition evaluation
        context = {
            'retirement_year': result.retirement_year,
            'final_portfolio': result.year_data[-1].portfolio if result.year_data else 0,
            '__builtins__': {}
        }

        # Check rules in priority order
        for rule in sorted(self.rules, key=lambda r: r.get('priority', 999)):
            condition = rule.get('condition', '')
            try:
                if eval(condition, {"__builtins__": {}}, context):
                    return {
                        'verdict': rule['verdict'],
                        'emoji': rule.get('emoji', ''),
                        'message': rule['message'],
                        'hint': rule['hint']
                    }
            except Exception as e:
                print(f"Error evaluating rule {rule['id']}: {e}")
                continue

        # No rule matched, return default
        return self.default


class ScenarioGeneratorService:
    """Main service for generating scenarios from questionnaire answers."""

    def __init__(self, config_dir: str = None):
        """
        Initialize service with config files.

        Args:
            config_dir: Path to config folder (defaults to web/backend/config)
        """
        if config_dir is None:
            config_dir = os.path.join(
                os.path.dirname(__file__),
                '../config'
            )

        self.config_dir = config_dir
        self.questionnaire = QuestionnaireConfig(
            os.path.join(config_dir, 'questionnaire_config.json')
        )
        self.defaults = TemplateDefaults(
            os.path.join(config_dir, 'template_defaults.json')
        )
        self.rules = EvaluationRules(
            os.path.join(config_dir, 'evaluation_rules.json')
        )

    def build_scenario_from_answers(
        self,
        answers: Dict[str, Any],
        profile: str = 'alon'
    ) -> Scenario:
        """
        Convert questionnaire answers + defaults → Scenario object.

        Missing answers are filled from template defaults.
        """
        # Extract basic fields
        age = answers.get('age', self.defaults.get_default('starting_age', 42))
        monthly_income_raw = answers.get(
            'monthly_income',
            self.defaults.get_default('monthly_income', {})
        )
        monthly_expenses_raw = answers.get(
            'monthly_expenses',
            self.defaults.get_default('monthly_expenses', {})
        )

        # Convert to IncomeBreakdown/ExpenseBreakdown
        # If answer is a number, wrap in default structure
        if isinstance(monthly_income_raw, (int, float)):
            income_breakdown = IncomeBreakdown({'salary': monthly_income_raw})
        else:
            income_breakdown = IncomeBreakdown(monthly_income_raw)

        if isinstance(monthly_expenses_raw, (int, float)):
            expense_breakdown = ExpenseBreakdown({'expenses': monthly_expenses_raw})
        else:
            expense_breakdown = ExpenseBreakdown(monthly_expenses_raw)

        # Extract optional fields with defaults
        initial_portfolio = answers.get(
            'initial_portfolio',
            self.defaults.get_default('initial_portfolio', 1500000)
        )
        # Handle case where default is a number but we expect it
        if not isinstance(initial_portfolio, (int, float)):
            initial_portfolio = 1500000
        return_rate = self.defaults.get_default('return_rate', 0.07)
        historical_index = self.defaults.get_default('historical_index', 'sp500')
        currency = self.defaults.get_default('currency', 'ILS')

        # Build mortgage if provided
        mortgage = None
        if answers.get('has_mortgage', False):
            mortgage = Mortgage(
                principal=answers.get('mortgage_amount', 0),
                annual_rate=answers.get('mortgage_annual_rate', 0.045) / 100,  # Convert % to decimal
                duration_years=answers.get('mortgage_years', 20)
            )

        # Build pension if provided
        pension = None
        if 'has_pension' in answers:
            # User explicitly answered the question
            if answers.get('has_pension', False):
                # User said yes to pension
                pension = Pension(
                    initial_value=answers.get('pension_initial', 2000000),
                    monthly_contribution=answers.get('pension_monthly_contribution', 9000),
                    annual_growth_rate=self.defaults.get_default('pension.annual_growth_rate', 0.06),
                    accessible_at_age=self.defaults.get_default('pension.accessible_at_age', 67)
                )
            # else: User said no to pension, keep pension = None
        else:
            # User never answered the question (didn't see it), use default if configured
            default_pension = self.defaults.get_default('pension')
            if default_pension:
                pension = Pension(**default_pension)

        # Build scenario name
        scenario_name = answers.get('scenario_name')
        if not scenario_name:
            scenario_name = self._generate_scenario_name()

        # Create Scenario object
        return Scenario(
            name=scenario_name,
            monthly_income=income_breakdown,
            monthly_expenses=expense_breakdown,
            initial_portfolio=initial_portfolio,
            return_rate=return_rate,
            historical_index=historical_index,
            mortgage=mortgage,
            pension=pension,
            age=int(age),
            currency=currency
        )

    def _generate_scenario_name(self) -> str:
        """Generate a default scenario name based on current timestamp."""
        now = datetime.now()
        return f"Quick Start - {now.strftime('%b %d, %Y %I:%M %p')}"

    def generate(self, answers: Dict[str, Any], profile: str = 'alon') -> Dict[str, Any]:
        """
        Generate scenario from answers.

        Returns dict with:
        - scenario (Scenario object)
        - result (SimulationResult)
        - completeness_score (float 0-1)
        - verdict (dict with verdict, message, hint)
        """
        # Calculate completeness
        completeness = self.questionnaire.calculate_completeness_score(answers)

        # Build scenario from answers
        scenario = self.build_scenario_from_answers(answers, profile)

        # Run simulation
        result = simulate(scenario, years=50)

        # Evaluate result
        verdict = self.rules.evaluate(result)

        return {
            'scenario': scenario,
            'result': result,
            'completeness_score': completeness,
            'verdict': verdict
        }


# Module-level helper for easy access
_service = None

def get_service(config_dir: str = None) -> ScenarioGeneratorService:
    """Get or create service instance (singleton)."""
    global _service
    if _service is None:
        _service = ScenarioGeneratorService(config_dir)
    return _service

# Presentation Layer: Output Formatting & Display

This layer handles all user-facing output: formatting numbers, displaying tables, rendering insights. Pure functions with no business logic.

## Architecture

**Single responsibility:** Convert domain objects → human-readable text.

**Design principle:** Presentation never imports from main.py or other presentation code. Only imports from domain/infrastructure.

## Constants (constants.py)

### CURRENCY_SYMBOLS
Mapping of currency codes to display symbols.

```python
CURRENCY_SYMBOLS = {
    "ILS": "₪",
    "USD": "$",
    "EUR": "€",
}
```

**Design note:** Consolidated from 3 locations:
- Previously hardcoded in main.py
- Previously hardcoded ₪ in 30+ lines of run_analysis.py
- Previously in insight objects as defaults

### get_currency_symbol(currency: str) → str
Get symbol for display. Returns currency code itself if not found.

```python
symbol = get_currency_symbol("ILS")  # "₪"
```

### format_retirement_year(retirement_year, fallback="Never") → str
Format retirement year for display. Consolidates 10+ inline ternaries across codebase.

```python
format_retirement_year(17)      # "Year 17"
format_retirement_year(None)    # "Never"
format_retirement_year(None, fallback="N/A")  # "N/A"
```

## Formatters (formatters.py)

### print_scenario_header(scenario: Scenario, settings: Settings) → None
Displays scenario input parameters as a formatted block.

**Configurable fields** (from settings.output.show_fields):
- `"income_expenses"` — Monthly income, expenses, net savings
- `"mortgage_details"` — Principal, rate, duration, computed payment
- `"events"` — List of one-time events with +/− amounts
- `"rates_settings"` — Return rate, withdrawal rate, simulation years, age

**Output:**
```
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Scenario Parameters: Buy Apartment
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Income:   ₪  45,000/month
  Expenses: ₪  25,000/month
  Net:      ₪  20,000/month
  Mortgage: ₪ 2,250,000 @ 4.0% for 25y  |  Monthly payment: ₪ 10,391
  Events: None
  Return rate: 7.0%  |  Withdrawal rate: 4.0%  |  Simulation: 20 years  |  Age: 41
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

**Design note:** Exact duplicate was in main.py and compare_all_scenarios.py. Consolidated here.

### print_year_summary(result: SimulationResult, scenario: Scenario, limit_years=40, start_age=30) → None
Displays year-by-year simulation results in a table.

**Output:**
```
Year   Income         Expenses       Net Savings    Portfolio        Req. Capital  
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
1      ₪     540,000 ₪     300,000 ₪     240,000 ₪     1,722,000 ₪   7,500,000
2      ₪     540,000 ₪     300,000 ₪     240,000 ₪     1,535,100 ₪   7,500,000
...

✓ Retires at year 16 (age 56)
```

**Parameters:**
- `limit_years` — Max rows to display (doesn't truncate simulation, just display)
- `start_age` — Age at year 1 (used to calculate retirement age)

## Usage Examples

### Display scenario with configurable fields
```python
from presentation.formatters import print_scenario_header
from infrastructure.loaders import SETTINGS

print_scenario_header(scenario, SETTINGS)
# Uses fields from settings.output.show_fields
```

### Hide mortgage details in output
Edit settings.json:
```json
{
  "output": {
    "show_fields": ["income_expenses", "rates_settings"]
  }
}
```

Then:
```python
print_scenario_header(scenario, SETTINGS)
# Mortgage section omitted!
```

### Display year-by-year results
```python
from presentation.formatters import print_year_summary
from domain.simulation import simulate

result = simulate(scenario, years=20)
print_year_summary(result, scenario, limit_years=20, start_age=41)
```

### Display retirement insights
```python
from domain.insights import build_insights, format_insights

insights = build_insights(result_a, result_b)
print(format_insights(insights))
# Output:
# Baseline retires at year 16.
# Buy Apartment does not reach retirement within 20 years.
# Buy Apartment delays retirement by 4+ years.
# ...
```

## Currency Support

All formatting functions respect scenario.currency:

```python
scenario_ils = Scenario(..., currency="ILS")
scenario_usd = Scenario(..., currency="USD")

print_scenario_header(scenario_ils, settings)
# Shows ₪ for all amounts

print_scenario_header(scenario_usd, settings)
# Shows $ for all amounts
```

## Output Configuration

### settings.json
```json
{
  "output": {
    "show_fields": [
      "income_expenses",
      "mortgage_details",
      "events",
      "rates_settings"
    ]
  }
}
```

**Field order** matches display order. Remove a field to hide it. Add/remove as needed.

### Valid Fields
| Field | Content |
|-------|---------|
| `income_expenses` | Monthly income, expenses, net savings |
| `mortgage_details` | Principal, rate, duration, monthly payment |
| `events` | List of one-time events with amounts |
| `rates_settings` | Return rate, withdrawal rate, years, age |

## Design Decisions

1. **No business logic:** Presentation never computes retirement years, portfolio growth, etc.
2. **Pure functions:** No side effects, no global state (except currency symbols)
3. **Currency-aware:** Respects scenario.currency for all displays
4. **Configurable:** Output fields controlled by settings.json, no code changes needed
5. **Format consistency:** All currency amounts use same symbol within a scenario
6. **Readable tables:** Fixed-width columns with right-alignment for numbers

## Key Principle

**Separation of concerns:** Domain objects contain data; presentation converts to text. Easy to add new output formats (JSON, CSV, HTML) without touching domain logic.

Example: Add JSON exporter:
```python
# new file: presentation/json_renderer.py
def render_scenario_to_json(scenario, result):
    return {
        "scenario": scenario.name,
        "retirement_year": result.retirement_year,
        "final_portfolio": result.year_data[-1].portfolio
    }
```

No changes needed to domain/ or infrastructure/.

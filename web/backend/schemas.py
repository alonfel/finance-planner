from pydantic import BaseModel, Field
from typing import List, Optional

# Base schemas - no dependencies
class YearDataSchema(BaseModel):
    year: int
    age: int
    income: float
    expenses: float
    net_savings: float
    portfolio: float
    required_capital: float
    mortgage_active: bool
    pension_value: float
    pension_accessible: bool

    class Config:
        from_attributes = True

class EventSchema(BaseModel):
    year: int
    portfolio_injection: float
    description: str = ""

class MortgageSchema(BaseModel):
    principal: float
    annual_rate: float
    duration_years: int
    currency: str = "ILS"

class PensionSchema(BaseModel):
    initial_value: float
    monthly_contribution: float
    annual_growth_rate: float
    accessible_at_age: int = 67

# Core request/response schemas
class WhatIfScenarioSchema(BaseModel):
    """Canonical shape for all What-If scenario state"""
    monthly_income: float
    monthly_expenses: float
    return_rate: float = 0.07
    historical_start_year: Optional[int] = None
    withdrawal_rate: float = 0.04
    starting_age: int
    initial_portfolio: float
    years: int = 20
    retirement_mode: str = "liquid_only"
    currency: str = "ILS"
    events: List[EventSchema] = []
    mortgage: Optional[MortgageSchema] = None
    pension: Optional[PensionSchema] = None

class SimulateRequest(WhatIfScenarioSchema):
    """Request for one-off simulation - inherits all fields from WhatIfScenarioSchema"""
    pass

class SaveScenarioRequest(WhatIfScenarioSchema):
    """Request to save a What-If scenario - inherits all scenario fields plus name"""
    scenario_name: str = Field(..., min_length=1, max_length=100)

class SimulateResponse(BaseModel):
    scenario_name: str
    retirement_year: Optional[int]
    final_portfolio: float
    total_savings: float
    year_data: List[YearDataSchema]

class SaveScenarioResponse(BaseModel):
    scenario_result_id: int
    run_id: int
    scenario_name: str
    retirement_year: Optional[int]
    final_portfolio: float

# Scenario detail response - uses forward reference for WhatIfScenarioSchema
class ScenarioResultSchema(BaseModel):
    id: int
    scenario_name: str
    retirement_year: Optional[int]
    year_data: List[YearDataSchema]
    events: List[EventSchema] = []
    mortgage: Optional[MortgageSchema] = None
    definition: Optional['WhatIfScenarioSchema'] = None

    class Config:
        from_attributes = True

class ScenarioSummarySchema(BaseModel):
    scenario_name: str
    retirement_year: Optional[int]
    final_portfolio: float
    years_simulated: int
    retirement_age: Optional[int]

class ScenarioCardSchema(BaseModel):
    id: int
    scenario_name: str
    retirement_year: Optional[int]
    final_portfolio: float

    class Config:
        from_attributes = True

class SimulationRunSchema(BaseModel):
    id: int
    generated_at: str
    num_scenarios: int
    label: Optional[str]

    class Config:
        from_attributes = True

class ProfileSchema(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Database schemas
class ScenarioDefinitionSchema(BaseModel):
    """Full scenario definition from database"""
    id: int
    profile_id: int
    name: str
    monthly_income: str  # JSON string
    monthly_expenses: str  # JSON string
    initial_portfolio: float
    age: int
    currency: str
    return_rate: float
    withdrawal_rate: float
    retirement_mode: str
    saved_from: Optional[str]
    saved_at: Optional[str]
    is_deleted: bool

    class Config:
        from_attributes = True

class ScenarioNodeSchema(BaseModel):
    """Scenario node for inheritance tree"""
    id: int
    profile_id: int
    name: str
    base_scenario_id: Optional[int]
    parent_id: Optional[int]
    event_mode: str
    age: Optional[int]
    initial_portfolio: Optional[float]
    return_rate: Optional[float]
    withdrawal_rate: Optional[float]
    currency: Optional[str]
    retirement_mode: Optional[str]
    monthly_income: Optional[str]  # JSON string
    monthly_expenses: Optional[str]  # JSON string

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import List, Optional

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

class ScenarioResultSchema(BaseModel):
    id: int
    scenario_name: str
    retirement_year: Optional[int]
    year_data: List[YearDataSchema]

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

class SimulateRequest(BaseModel):
    monthly_income: float
    monthly_expenses: float
    return_rate: float = 0.07
    starting_age: int
    initial_portfolio: float
    years: int = 20

class SimulateResponse(BaseModel):
    scenario_name: str
    retirement_year: Optional[int]
    final_portfolio: float
    total_savings: float
    year_data: List[YearDataSchema]

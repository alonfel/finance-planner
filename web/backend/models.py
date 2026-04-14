from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(String, nullable=True)

    runs = relationship("SimulationRun", back_populates="profile")
    scenario_definitions = relationship("ScenarioDefinition", back_populates="profile")
    scenario_nodes = relationship("ScenarioNode", back_populates="profile")
    settings = relationship("ProfileSettings", back_populates="profile", uselist=False)

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    generated_at = Column(String, nullable=False)
    num_scenarios = Column(Integer, nullable=False)
    label = Column(String, nullable=True)

    profile = relationship("Profile", back_populates="runs")
    scenario_results = relationship("ScenarioResult", back_populates="run")

class ScenarioDefinition(Base):
    __tablename__ = "scenario_definitions"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    monthly_income = Column(String, nullable=False)  # JSON TEXT
    monthly_expenses = Column(String, nullable=False)  # JSON TEXT
    initial_portfolio = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="ILS")
    return_rate = Column(Float, nullable=False)
    historical_start_year = Column(Integer, nullable=True)
    historical_index = Column(String, nullable=True)  # "sp500" | "nasdaq" | "bonds" | "russell2000"
    withdrawal_rate = Column(Float, nullable=False, default=0.04)
    retirement_mode = Column(String, nullable=False, default="liquid_only")
    saved_from = Column(String, nullable=True)
    saved_at = Column(String, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    profile = relationship("Profile", back_populates="scenario_definitions")
    events = relationship("ScenarioEvent", back_populates="scenario")
    mortgage = relationship("ScenarioMortgage", back_populates="scenario", uselist=False)
    pension = relationship("ScenarioPension", back_populates="scenario", uselist=False)
    scenario_results = relationship("ScenarioResult", back_populates="definition")


class ScenarioEvent(Base):
    __tablename__ = "scenario_events"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario_definitions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    portfolio_injection = Column(Float, nullable=False)
    description = Column(String, nullable=False, default="")

    scenario = relationship("ScenarioDefinition", back_populates="events")


class ScenarioMortgage(Base):
    __tablename__ = "scenario_mortgages"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario_definitions.id"), unique=True, nullable=False)
    principal = Column(Float, nullable=False)
    annual_rate = Column(Float, nullable=False)
    duration_years = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="ILS")

    scenario = relationship("ScenarioDefinition", back_populates="mortgage")


class ScenarioPension(Base):
    __tablename__ = "scenario_pensions"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("scenario_definitions.id"), unique=True, nullable=False)
    initial_value = Column(Float, nullable=False)
    monthly_contribution = Column(Float, nullable=False)
    annual_growth_rate = Column(Float, nullable=False)
    accessible_at_age = Column(Integer, nullable=False, default=67)

    scenario = relationship("ScenarioDefinition", back_populates="pension")


class ProfileSettings(Base):
    __tablename__ = "profile_settings"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), unique=True, nullable=False)
    years = Column(Integer, nullable=False, default=30)
    return_rate = Column(Float, nullable=False, default=0.05)
    withdrawal_rate = Column(Float, nullable=False, default=0.04)
    show_fields = Column(String, nullable=False, default="[]")  # JSON TEXT

    profile = relationship("Profile", back_populates="settings")


class ScenarioNode(Base):
    __tablename__ = "scenario_nodes"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    base_scenario_id = Column(Integer, ForeignKey("scenario_definitions.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("scenario_nodes.id"), nullable=True)
    event_mode = Column(String, nullable=False, default="append")
    age = Column(Integer, nullable=True)
    initial_portfolio = Column(Float, nullable=True)
    return_rate = Column(Float, nullable=True)
    withdrawal_rate = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    retirement_mode = Column(String, nullable=True)
    monthly_income = Column(String, nullable=True)  # JSON TEXT
    monthly_expenses = Column(String, nullable=True)  # JSON TEXT

    profile = relationship("Profile", back_populates="scenario_nodes")
    base_scenario = relationship("ScenarioDefinition")
    parent = relationship("ScenarioNode", remote_side=[id])
    events = relationship("ScenarioNodeEvent", back_populates="node")
    mortgage = relationship("ScenarioNodeMortgage", back_populates="node", uselist=False)
    pension = relationship("ScenarioNodePension", back_populates="node", uselist=False)


class ScenarioNodeEvent(Base):
    __tablename__ = "scenario_node_events"

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("scenario_nodes.id"), nullable=False)
    year = Column(Integer, nullable=False)
    portfolio_injection = Column(Float, nullable=False)
    description = Column(String, nullable=False, default="")

    node = relationship("ScenarioNode", back_populates="events")


class ScenarioNodeMortgage(Base):
    __tablename__ = "scenario_node_mortgages"

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("scenario_nodes.id"), unique=True, nullable=False)
    principal = Column(Float, nullable=False)
    annual_rate = Column(Float, nullable=False)
    duration_years = Column(Integer, nullable=False)
    currency = Column(String, nullable=False, default="ILS")

    node = relationship("ScenarioNode", back_populates="mortgage")


class ScenarioNodePension(Base):
    __tablename__ = "scenario_node_pensions"

    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("scenario_nodes.id"), unique=True, nullable=False)
    initial_value = Column(Float, nullable=False)
    monthly_contribution = Column(Float, nullable=False)
    annual_growth_rate = Column(Float, nullable=False)
    accessible_at_age = Column(Integer, nullable=False, default=67)

    node = relationship("ScenarioNode", back_populates="pension")


class ScenarioResult(Base):
    __tablename__ = "scenario_results"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenario_definitions.id"), nullable=True)
    scenario_name = Column(String, nullable=False)
    retirement_year = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    run = relationship("SimulationRun", back_populates="scenario_results")
    definition = relationship("ScenarioDefinition", back_populates="scenario_results")
    year_data = relationship("YearData", back_populates="result")

class YearData(Base):
    __tablename__ = "year_data"

    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey("scenario_results.id"), nullable=False)
    year = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    income = Column(Float, nullable=False)
    expenses = Column(Float, nullable=False)
    net_savings = Column(Float, nullable=False)
    portfolio = Column(Float, nullable=False)
    required_capital = Column(Float, nullable=False)
    mortgage_active = Column(Boolean, nullable=False, default=False)
    pension_value = Column(Float, nullable=False, default=0.0)
    pension_accessible = Column(Boolean, nullable=False, default=False)

    result = relationship("ScenarioResult", back_populates="year_data")

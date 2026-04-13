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

class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    generated_at = Column(String, nullable=False)
    num_scenarios = Column(Integer, nullable=False)
    label = Column(String, nullable=True)

    profile = relationship("Profile", back_populates="runs")
    scenario_results = relationship("ScenarioResult", back_populates="run")

class ScenarioResult(Base):
    __tablename__ = "scenario_results"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    scenario_name = Column(String, nullable=False)
    retirement_year = Column(Integer, nullable=True)

    run = relationship("SimulationRun", back_populates="scenario_results")
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

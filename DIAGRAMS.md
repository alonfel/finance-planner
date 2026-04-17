# Finance Planner — System Design Diagrams

A personal financial independence planner that simulates portfolio growth over time, models uncertain life events (IPO exits, bonuses, property purchases), and calculates the earliest year you can retire. Built with a pure-Python domain engine, a FastAPI backend, and a Vue 3 frontend. Supports deterministic simulation, probabilistic branching, and 500-trial Monte Carlo analysis across real historical index returns (S&P 500, NASDAQ, Bonds, Russell 2000).

Seven Mermaid diagrams covering architecture, data models, request flows, and simulation logic.

---

## Diagram 0: Client ↔ Two Servers

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#eef0ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#533afd",
    "lineColor": "#533afd",
    "edgeLabelBackground": "#ffffff",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "14px"
  }
}}%%
flowchart LR
    Browser(["🌐 Browser"])

    subgraph FE["🖥️  Vue Dev Server  · :5173"]
        Assets[/"① HTML · JS · CSS\n  served once"/]
        Vue{{"Vue 3 SPA\n runs in browser"}}
    end

    subgraph BE["⚡  FastAPI  · :8000"]
        Router(["🔀 Router"])
        Sim{{"⚙️ simulate()"}}
        MC{{"🎲 run_monte_carlo()"}}
        DB[("🗄️ SQLite")]
    end

    CORS{{"⚠️ CORS\nheaders required"}}

    Browser -->|"open app"| Assets
    Assets -->|"② bundle download\n  one time only"| Browser
    Browser -->|"③ user interacts\n  renders Vue"| Vue
    Vue -..->|"Vue runs IN the browser\nnot a proxy"| Browser

    Browser -->|"④ POST /simulate\n  POST /monte-carlo\n  GET /scenarios\n  direct from browser"| CORS
    CORS --> Router
    Router --> Sim & MC & DB
    Sim & MC & DB -->|"process"| Router
    Router -->|"⑤ JSON response"| Browser
    Browser -->|"⑥ render chart\n  + metric cards"| Vue

    style FE fill:#eef0ff,stroke:#533afd,color:#061b31
    style BE fill:#f0faf4,stroke:#15be53,color:#061b31
    style CORS fill:#fff9f0,stroke:#9b6829,color:#061b31
    style Vue fill:#eef0ff,stroke:#533afd,color:#061b31

    linkStyle 3 stroke:#b9b9f9,stroke-dasharray:5,stroke-width:1
    linkStyle 4 stroke:#ea2261,stroke-width:3
    linkStyle 8 stroke:#15be53,stroke-width:3
```

---

## Diagram 1: Layer Architecture & Dependencies

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#f0f4ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#b9b9f9",
    "lineColor": "#533afd",
    "secondaryColor": "#f6f9fc",
    "tertiaryColor": "#ffd7ef",
    "edgeLabelBackground": "#ffffff",
    "clusterBkg": "#f6f9fc",
    "clusterBorder": "#e5edf5",
    "titleColor": "#061b31",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "13px"
  }
}}%%
graph TD
    subgraph FE["🖥️  Frontend  ·  Vue 3  · :5173"]
        WhatIfView("What-If Explorer\nSliders · Events · Probabilistic")
        ScenarioDetailView("Scenario Detail")
        MonteCarloView("Monte Carlo View")
        ScenariosView("Saved Scenarios")
    end

    subgraph BE["⚡  Backend  ·  FastAPI  :8000"]
        simulate[/"POST /simulate"/]
        montecarlo[/"POST /monte-carlo"/]
        saves[/"POST /saved-scenarios"/]
        scenarios[/"GET /scenarios"/]
        generator[/"POST /generate-scenario"/]
    end

    subgraph Domain["🧠  Domain  ·  Pure Python"]
        simulation{{"simulation.py\nsimulate() · simulate_branches()"}}
        monte_carlo{{"monte_carlo.py\nrun_monte_carlo()"}}
        sensitivity{{"sensitivity.py\nrun_oat_sensitivity()"}}
        models["models.py\nScenario · Event · ProbabilisticEvent\nMortgage · Pension · FinancialStory"]
        historical["historical_returns.py\nS&P500 · NASDAQ · Bonds · Russell2000"]
    end

    subgraph Infra["🔧  Infrastructure"]
        loaders(["loaders.py — load_scenarios()"])
        parsers(["parsers.py — dict → model"])
        cache(["cache.py — SimulationCache"])
        data_layer(["data_layer.py — ProfileManager"])
    end

    subgraph DB["🗄️  SQLite"]
        profiles_t[(profiles)]
        scenario_defs[(scenario_definitions)]
        sim_runs[(simulation_runs + year_data)]
        prob_events[(probabilistic_events + outcomes)]
    end

    FE -->|"HTTP / JSON  :5173 → :8000"| BE
    BE --> Domain
    BE --> DB
    Domain --> Infra
    Infra --> DB

    style FE fill:#eef0ff,stroke:#533afd,color:#061b31
    style BE fill:#f0faf4,stroke:#15be53,color:#061b31
    style Domain fill:#fff9f0,stroke:#9b6829,color:#061b31
    style Infra fill:#fff0f7,stroke:#ea2261,color:#061b31
    style DB fill:#f6f9fc,stroke:#64748d,color:#061b31
```

---

## Diagram 2: Domain Model Relationships

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#eef0ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#533afd",
    "lineColor": "#533afd",
    "secondaryColor": "#f6f9fc",
    "tertiaryColor": "#eef0ff",
    "edgeLabelBackground": "#ffffff",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "13px",
    "classText": "#061b31"
  }
}}%%
classDiagram
    class Scenario {
        <<core model>>
        +str name
        +IncomeBreakdown monthly_income
        +ExpenseBreakdown monthly_expenses
        +float initial_portfolio
        +float return_rate
        +str historical_index
        +int age
        +str retirement_mode
        +Mortgage mortgage
        +Pension pension
    }

    class Event {
        <<one-time>>
        +int year
        +float portfolio_injection
        +str description
    }

    class ProbabilisticEvent {
        <<uncertain outcome>>
        +str name
        +list~EventOutcome~ outcomes
        +validate() probs sum to 1.0
    }

    class EventOutcome {
        +int year
        +float probability
        +float portfolio_injection
        +str description
    }

    class Mortgage {
        <<liability>>
        +float principal
        +float annual_rate
        +int duration_years
        +float monthly_payment
    }

    class Pension {
        <<deferred asset>>
        +float initial_value
        +float monthly_contribution
        +float annual_growth_rate
        +int accessible_at_age
    }

    class IncomeBreakdown {
        <<breakdown>>
        +dict components
        +float total
        +merge(override)
    }

    class ExpenseBreakdown {
        <<breakdown>>
        +dict components
        +float total
        +merge(override)
    }

    class ScenarioNode {
        <<inheritance>>
        +str name
        +str parent_name
        +resolve(nodes) Scenario
    }

    class FinancialStory {
        <<narrative>>
        +str name
        +Scenario base_scenario
        +list~StoryEventNode~ events
        +str story_id
    }

    class SimulationResult {
        <<output>>
        +str scenario_name
        +list~YearData~ year_data
        +int retirement_year
    }

    class YearData {
        <<yearly snapshot>>
        +int year · int age
        +float portfolio
        +float income · expenses
        +bool is_retired
        +float pension_value
    }

    Scenario "1" --> "0..*" Event : events
    Scenario "1" --> "0..*" ProbabilisticEvent : probabilistic_events
    Scenario "1" --> "0..1" Mortgage : mortgage
    Scenario "1" --> "0..1" Pension : pension
    Scenario "1" --> "1" IncomeBreakdown : monthly_income
    Scenario "1" --> "1" ExpenseBreakdown : monthly_expenses
    ProbabilisticEvent "1" --> "1..*" EventOutcome : outcomes
    ScenarioNode "1" --> "0..1" ScenarioNode : parent
    ScenarioNode ..> Scenario : resolve()
    FinancialStory "1" --> "1" Scenario : base_scenario
    FinancialStory "1" --> "0..*" Event : story events
    SimulationResult "1" --> "0..*" YearData : year_data
```

---

## Diagram 3: What-If Simulation — Request Flow

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#eef0ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#533afd",
    "lineColor": "#533afd",
    "secondaryColor": "#f6f9fc",
    "activationBorderColor": "#533afd",
    "activationBkgColor": "#eef0ff",
    "actorBkg": "#f6f9fc",
    "actorBorder": "#533afd",
    "actorTextColor": "#061b31",
    "actorLineColor": "#b9b9f9",
    "labelBoxBkgColor": "#eef0ff",
    "labelBoxBorderColor": "#533afd",
    "labelTextColor": "#061b31",
    "loopTextColor": "#273951",
    "noteBorderColor": "#b9b9f9",
    "noteBkgColor": "#ffd7ef",
    "noteTextColor": "#061b31",
    "signalColor": "#533afd",
    "signalTextColor": "#061b31",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "13px"
  }
}}%%
sequenceDiagram
    autonumber
    actor User
    participant Vue as WhatIfView.vue · :5173
    participant API as FastAPI · :8000
    participant Sim as simulate.py
    participant Domain as simulation.py
    participant DB as SQLite

    User->>Vue: Move slider / toggle event
    Vue->>Vue: toApiRequest() — serialize state
    Vue->>API: POST /api/v1/simulate

    API->>Sim: run_simulation(request)
    Sim->>Sim: Build Scenario domain object

    alt probabilistic_events present
        Sim->>Domain: simulate_branches(scenario)
        Domain->>Domain: _expand_branches() — cross-product
        loop Each outcome branch
            Domain->>Domain: simulate(scenario + branch events)
        end
        Domain-->>Sim: [(label, prob, SimulationResult) …]
    else deterministic
        Sim->>Domain: simulate(scenario)
        Domain-->>Sim: SimulationResult
    end

    Sim-->>API: {year_data[], branches[]}
    API-->>Vue: JSON response
    Vue->>Vue: Render chart lines + metric cards
    Vue-->>User: Updated visualization

    opt Save Scenario
        User->>Vue: Click "Save Scenario"
        Vue->>API: POST /saved-scenarios
        API->>DB: INSERT scenario_definitions\n+ events + probabilistic_events
        DB-->>API: Saved IDs
        API-->>Vue: SaveScenarioResponse
        Vue-->>User: "Saved ✓"
    end
```

---

## Diagram 4: Database Schema

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#eef0ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#533afd",
    "lineColor": "#533afd",
    "edgeLabelBackground": "#ffffff",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "13px",
    "attributeBackgroundColorEven": "#f6f9fc",
    "attributeBackgroundColorOdd": "#ffffff"
  }
}}%%
erDiagram
    profiles {
        int id PK
        string name
        string display_name
    }

    profile_settings {
        int id PK
        int profile_id FK
        int years
        float return_rate
        float withdrawal_rate
    }

    simulation_runs {
        int id PK
        int profile_id FK
        string generated_at
        int num_scenarios
    }

    scenario_definitions {
        int id PK
        int profile_id FK
        string name
        float initial_portfolio
        int age
        float return_rate
        string historical_index
        string retirement_mode
        bool is_deleted
    }

    scenario_events {
        int id PK
        int scenario_id FK
        int year
        float portfolio_injection
        string description
    }

    scenario_mortgages {
        int id PK
        int scenario_id FK
        float principal
        float annual_rate
        int duration_years
    }

    scenario_pensions {
        int id PK
        int scenario_id FK
        float initial_value
        float annual_growth_rate
        int accessible_at_age
    }

    scenario_probabilistic_events {
        int id PK
        int scenario_id FK
        string name
    }

    scenario_event_outcomes {
        int id PK
        int event_id FK
        int year
        float probability
        float portfolio_injection
    }

    scenario_results {
        int id PK
        int run_id FK
        int scenario_id FK
        int retirement_year
    }

    year_data {
        int id PK
        int result_id FK
        int year
        int age
        float portfolio
        float income
        float expenses
        bool is_retired
    }

    scenario_nodes {
        int id PK
        int profile_id FK
        int parent_id FK
        string name
        string event_mode
    }

    profiles ||--o{ simulation_runs : "runs"
    profiles ||--o{ scenario_definitions : "owns"
    profiles ||--o{ scenario_nodes : "owns"
    profiles ||--|| profile_settings : "settings"
    simulation_runs ||--o{ scenario_results : "contains"
    scenario_definitions ||--o{ scenario_results : "used in"
    scenario_definitions ||--o{ scenario_events : "events"
    scenario_definitions ||--o| scenario_mortgages : "mortgage"
    scenario_definitions ||--o| scenario_pensions : "pension"
    scenario_definitions ||--o{ scenario_probabilistic_events : "prob events"
    scenario_probabilistic_events ||--o{ scenario_event_outcomes : "outcomes"
    scenario_results ||--o{ year_data : "yearly data"
    scenario_nodes ||--o| scenario_nodes : "parent"
    scenario_nodes }o--|| scenario_definitions : "base"
```

---

## Diagram 5: Monte Carlo & Sensitivity Analysis

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#eef0ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#533afd",
    "lineColor": "#533afd",
    "secondaryColor": "#f6f9fc",
    "tertiaryColor": "#fff0f7",
    "edgeLabelBackground": "#ffffff",
    "clusterBkg": "#f6f9fc",
    "clusterBorder": "#b9b9f9",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "13px"
  }
}}%%
flowchart TD
    Start([Open Monte Carlo View]) --> Select("Select saved scenario")
    Select --> Request[/"POST /api/v1/monte-carlo\n{scenario_id, n_trials=500, years}"/]

    Request --> Load[("Load ScenarioDefinition\nfrom DB")]
    Load --> Build["Build Scenario\ndomain object"]

    Build --> Fork:::junction
    Fork --> MC{{"run_monte_carlo\n(scenario, n_trials=500)"}}
    Fork --> OAT{{"run_oat_sensitivity()"}}
    classDef junction fill:#533afd,stroke:#533afd,color:#fff,width:12px,height:12px

    MC --> Lognormal[/"Sample returns\nlognormal σ=15%  ·  N×Y matrix"/]
    Lognormal --> Trials

    subgraph Trials["500 Independent Trials"]
        direction LR
        T1("Trial 1")
        T2("Trial 2")
        TN("… Trial 500")
        T1 --- T2 --- TN
    end

    Trials --> Agg[/"p5 / p50 / p95 bands\nRetirement probability\nSurvival probability"/]

    subgraph OATVars["One-At-a-Time Variants"]
        direction LR
        V1["Return +2pp"] --- V2["Return −2pp"]
        V3["Income +20%"] --- V4["Income −20%"]
        V5["Horizon +5yr"] --- V6["Horizon −5yr"]
    end

    OAT --> OATVars
    OATVars --> Rank["Rank inputs by\nΔ retirement probability"]

    Agg --> Join:::junction
    Rank --> Join
    Join --> Response(["MonteCarloResponse"])
    classDef junction fill:#533afd,stroke:#533afd,color:#fff,width:12px,height:12px

    Response --> FanChart("FanChart.vue\np5 / p50 / p95 bands")
    Response --> Drivers("Driver ranking cards\n'Which inputs matter most'")

    style Trials fill:#eef0ff,stroke:#533afd,color:#061b31
    style OATVars fill:#fff9f0,stroke:#9b6829,color:#061b31

    linkStyle 1 stroke:#533afd,stroke-width:3
    linkStyle 12 stroke:#15be53,stroke-width:3
```

---

## Diagram 6: Probabilistic Events — Branch Simulation

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#ffffff",
    "primaryColor": "#eef0ff",
    "primaryTextColor": "#061b31",
    "primaryBorderColor": "#533afd",
    "lineColor": "#533afd",
    "secondaryColor": "#f6f9fc",
    "edgeLabelBackground": "#ffffff",
    "clusterBkg": "#fffbf0",
    "clusterBorder": "#b9b9f9",
    "fontFamily": "ui-monospace, monospace",
    "fontSize": "13px"
  }
}}%%
flowchart TD
    Input(["Scenario with probabilistic_events"])

    Input --> Check{Has probabilistic\nevents?}

    Check -->|No| Single{{"simulate(scenario)"}}
    Single --> SingleOut(["SimulationResult\n(deterministic)"])

    Check -->|Yes| Expand{{"_expand_branches()\nrecursive cross-product"}}

    subgraph CrossProduct["Example — 2 events × 2 outcomes = 4 branches"]
        direction TB
        IPO_Y[/"IPO: Success  70%"/]
        IPO_N[/"IPO: No event  30%"/]
        BON_H[\"Bonus: High  60%"\]
        BON_L[\"Bonus: Low  40%"\]

        B1("Branch 1\nSuccess + High  ·  p = 0.42")
        B2("Branch 2\nSuccess + Low   ·  p = 0.28")
        B3("Branch 3\nNo event + High ·  p = 0.18")
        B4("Branch 4\nNo event + Low  ·  p = 0.12")

        IPO_Y --> B1 & B2
        IPO_N --> B3 & B4
        BON_H --> B1 & B3
        BON_L --> B2 & B4
    end

    Expand --> CrossProduct

    B1 --> S1{{"simulate(branch 1)"}}
    B2 --> S2{{"simulate(branch 2)"}}
    B3 --> S3{{"simulate(branch 3)"}}
    B4 --> S4{{"simulate(branch 4)"}}

    S1 & S2 & S3 & S4 --> JoinBranches:::junction
    JoinBranches --> Results[/"branches[]\n(label, probability, SimulationResult)"/]
    classDef junction fill:#533afd,stroke:#533afd,color:#fff,width:12px,height:12px

    Results --> Assert>"assert sum(probabilities) == 1.0"]
    Assert --> UI("WhatIfView.vue\nOne colored line per branch\nProbability badge per metric card")

    style CrossProduct fill:#fffbf0,stroke:#9b6829,color:#061b31
    style B1 fill:#eef0ff,stroke:#533afd,color:#061b31
    style B2 fill:#f0faf4,stroke:#15be53,color:#061b31
    style B3 fill:#fff0f7,stroke:#ea2261,color:#061b31
    style B4 fill:#ffd7ef,stroke:#f96bee,color:#061b31
```

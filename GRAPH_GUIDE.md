# Portfolio Growth Graphs - Guide to Reading the Output

## The Three Components (Graph → Table → Insights)

Every analysis now shows:
1. **[YEARLY PORTFOLIO GROWTH]** — Visual line graph
2. **[METRIC TABLE]** or **[MILESTONE SNAPSHOTS]** — Numerical data
3. **[Insights]** or **[SUMMARY]** — Interpretation

---

## Example 1: Income Sensitivity (High Income vs Low Income)

### 1. THE GRAPH
```
[YEARLY PORTFOLIO GROWTH]
-----------------------------------
₪11.3M │                   █
₪10.5M │                  █ 
₪ 9.7M │                 █  
₪ 9.0M │                █   
₪ 8.2M │               █    
₪ 7.4M │             ██     
₪ 6.7M │            █       
₪ 5.9M │          ██        
₪ 5.1M │         █          
₪ 4.4M │       ██           
₪ 3.6M │     ██             
₪ 2.8M │   ██           ▓▓▓▓
₪ 2.1M │+██   ▓▓▓▓▓▓▓▓▓▓    ← Year 2: Surrogacy expense (-₪500K)
₪ 1.3M │ ▓▓▓▓▓              
₪ 0.5M │                    
      ├────────────────────
      │1 3 5 7 9 1 3 5 7 9 
```

**What you're seeing:**
- **X-axis (bottom):** Years 1-20 (every other number shown)
- **Y-axis (left):** Portfolio values from ₪0.5M to ₪11.3M
- **█ character (solid block):** High income (₪45K/month) scenario
- **▓ character (dark shade):** Low income (₪25K/month) scenario
- **+ symbol:** Overlapping values where both scenarios have same portfolio

**Key observation:** Year 2 shows a dip in both lines (the `+`) — this is the **-₪500K surrogacy expense** hitting both scenarios.

### 2. THE TABLE
```
Metric                                   high_income                         low_income                         
────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Retirement Year                          Year 16                             Never                              
Portfolio at Year 10                     ₪4,674,417                          ₪1,504,788
Portfolio at Year 20                     ₪10,783,762                         ₪2,451,142
Annual Savings (Year 1)                  ₪240,000                            ₪0
```

**What you're seeing:**
- High income saves ₪20K/month = ₪240K/year
- Low income saves ₪0/month (all income = expenses)
- High income retires in year 16 at age 57
- Low income never reaches retirement in 20 years

### 3. THE INSIGHTS
```
Insights:
  Alon Baseline (high_income) retires at year 16.
  Alon Baseline (low_income) does not reach retirement within 20 years.
  After 20 years, Alon Baseline (low_income)'s final portfolio is ₪8,332,620 
  lower than Alon Baseline (high_income)'s.
```

**What this means:**
- **Income matters:** ₪20K/month difference = ₪8.3M gap after 20 years
- **No monthly savings = no retirement:** At ₪25K income = ₪25K expenses, you have zero savings to grow
- **Compounding works against you:** Your ₪1.4M starting capital grows slower (only 5% annual return, no income added)

---

## Example 2: Exit Impact (No Exit vs ₪2M Exit vs ₪3M Exit)

### 1. THE GRAPH
```
[YEARLY PORTFOLIO GROWTH]
-----------------------------------
₪20.9M │                   ▓
₪19.5M │                  ▓ 
₪18.0M │                ▓▓ █
₪16.6M │               ▓ ██ 
₪15.1M │              ▓ █   
₪13.7M │            ▓▓██    
₪12.2M │          ▓▓██     ▒
₪10.8M │        ▓▓██      ▒ 
₪ 9.3M │      ▓▓██     ▒▒▒  
₪ 7.9M │   ▓▓▓██     ▒▒     
₪ 6.4M │ ▓▓███    ▒▒▒       
₪ 5.0M │+██    ▒▒▒          
₪ 3.5M │   ▒▒▒▒             
₪ 2.1M │▒▒▒                 
₪ 0.6M │                    
      ├────────────────────
      │1 3 5 7 9 1 3 5 7 9 
```

**Legend:**
- **█ = +₪2M Exit** → Final: ₪17,353,833
- **▓ = +₪3M Exit** → Final: ₪20,007,130
- **▒ = No Exit** → Final: ₪10,783,762

**What you're seeing:**
- All three scenarios start near the same point (₪1.4M)
- Year 1: Exit scenarios jump up (visible gap between █/▓ and ▒) ← Exit injection
- Year 2: All dip together (surrogacy expense)
- Years 3+: Exit scenarios pull further ahead due to compounding
- ▓ (₪3M exit) reaches highest level by year 20

### 2. THE TABLE
```
Year     | No Exit       | +₪2M Exit       | +₪3M Exit
─────────┼───────────────┼─────────────────┼──────────────
1        | ₪1,722,000    | ₪3,822,000      | ₪4,872,000
5        | ₪2,571,500    | ₪5,731,816      | ₪7,008,098
10       | ₪4,674,417    | ₪8,707,871      | ₪10,336,765
15       | ₪7,358,332    | ₪12,506,154     | ₪14,585,082
20       | ₪10,783,762   | ₪17,353,833     | ₪20,007,130
```

**Key patterns:**
- Year 1: Exit scenarios jump by ₪2M and ₪3M respectively
- Year 2: All scenarios show the surrogacy dip
- Years 5-20: Gap widens due to compounding (5% return on the bigger base)
- Year 20: ₪3M exit = ₪9.2M more than no exit

### 3. THE SUMMARY
```
No Exit
  Retirement: Year 16
  Final Portfolio: ₪10,783,762

+₪2M Exit
  Retirement: Year 9        ← 7 years earlier!
  Final Portfolio: ₪17,353,833

+₪3M Exit
  Retirement: Year 6        ← 10 years earlier!
  Final Portfolio: ₪20,007,130
```

**What this means:**
- **₪2M exit accelerates retirement by 7 years**
- **₪3M exit accelerates retirement by 10 years**
- Exit event has **compounding benefits**: ₪2M injected year 1 grows to ₪6.6M extra by year 20 (5% × 19 years)
- Surrogacy doesn't change retirement timing for exit scenarios (still feasible)

---

## Reading the Graphs: Key Visual Patterns

### Pattern 1: Steep Lines = Compounding Kicking In
```
Year 5-20: Lines get steeper
Why: Portfolio is bigger, so 5% return = more ₪ each year
Example: 5% of ₪1M = ₪50K. 5% of ₪10M = ₪500K.
```

### Pattern 2: Horizontal or Flat = Not Enough Savings
```
Alon Baseline (low_income) - flat line
Why: ₪0 monthly savings + 5% return on ₪1.4M ≈ ₪70K/year growth (barely visible)
The -₪500K surrogacy expense negates one year's growth entirely
```

### Pattern 3: Diverging Lines = Compound Effect
```
Year 1: Exit scenarios jump up
Year 2: All dip together (surrogacy)
Year 3+: Exit scenarios pull away faster
Why: ₪2M/₪3M grows at 5% per year, creating wider gap each year
```

### Pattern 4: Steep Upward Slope = Retirement Threshold Crossed
```
Right before retirement year, line accelerates sharply upward
Why: Portfolio finally reaches ₪625K (= ₪25K annual expenses ÷ 0.04)
Once you hit this, you're financially independent (live on 4% withdrawal)
```

---

## How to Use These Graphs

### For Decision Making
- **Compare retirement timing:** Which exit scenario saves the most years?
- **Visualize trade-offs:** Buying apartment (mortgage) shows as flatter growth
- **See income sensitivity:** How much does income matter? (high_income vs low_income gap)

### For Understanding Assumptions
- **Year 2 dip:** That's the -₪500K surrogacy (life event)
- **Year 1 jump:** That's exit proceeds (₪2M or ₪3M injection)
- **Steady curves:** That's 5% annual returns compounding

### For Scenario Testing
Run different analyses and compare graphs:
- **Same scenario, different income levels** → How sensitive is retirement to salary?
- **Same income, different exit amounts** → How much exit value needed?
- **Buy apartment vs no apartment** → How much does mortgage cost in retirement years?

---

## Symbol Legend

All possible graph symbols:

| Symbol | Meaning |
|--------|---------|
| `█` | First scenario (darkest) |
| `▓` | Second scenario (dark gray) |
| `▒` | Third scenario (medium gray) |
| `░` | Fourth scenario (light gray) |
| `●` | Fifth scenario (dot) |
| `○` | Sixth scenario (hollow dot) |
| `◆` | Seventh scenario (diamond) |
| `◇` | Eighth scenario (hollow diamond) |
| `■` | Ninth scenario (small square) |
| `□` | Tenth scenario (hollow square) |
| `+` | Overlapping values (both scenarios at same point) |

---

## Tips for Reading the Numbers

### Retirement Threshold Calculation
```
Retirement when: Portfolio ≥ (Annual Expenses ÷ Withdrawal Rate)

Your baseline:
  Annual Expenses = ₪25K/month × 12 = ₪300K/year
  Safe Withdrawal Rate = 4% (0.04)
  Retirement Threshold = ₪300K ÷ 0.04 = ₪7.5M
  
Look on the graph for when the portfolio line first exceeds ₪7.5M
That's approximately when you hit retirement.
```

### Compounding Math
```
5% annual return on ₪1.4M initial:
  Year 1: ₪1.4M × 1.05 = ₪1.47M
  Year 5: ₪1.4M × (1.05^5) = ₪1.78M
  Year 10: ₪1.4M × (1.05^10) = ₪2.28M
  Year 20: ₪1.4M × (1.05^20) = ₪3.73M
  
With ₪240K annual savings added each year (high income):
  Actual year 20 portfolio = ₪10.78M
  Why so much higher? The ₪240K gets invested for 19, 18, 17... years too!
```

---

## What the Graphs Don't Show

- **Taxes** → Real-world portfolios are after-tax
- **Inflation** → Returns shown in nominal ₪, not purchasing power
- **Risk/volatility** → Shown as smooth 5%, but real returns fluctuate
- **Market cycles** → You might hit a bear market in year 16
- **Life changes** → What if you lose your job? Get married? Move?

The graphs show **expected outcomes** assuming stable assumptions, not ranges of possible outcomes.

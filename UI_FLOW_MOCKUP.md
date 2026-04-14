# Guided Scenario Generator — UI Flow & Mockup

**Last Updated:** April 14, 2026  
**Version:** 1.0 (MVP)

---

## Overview

Three-screen flow: **Questionnaire → Loading → Results**

All screens render within a modal overlay, allowing users to generate scenarios without leaving the What-If Explorer.

---

## Screen 1: Questionnaire Form

### Layout

```
╔════════════════════════════════════════════════════════════════╗
║                                                              ✕ ║
║  Generate Your Scenario                                        ║
║                                                                ║
╟────────────────────────────────────────────────────────────────╢
║                                                                ║
║  Data Completeness: ▓▓░░░░░░░░ 40%                            ║
║  Answer a few more questions for better insights              ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  📋 Demographics                                               ║
║  Basic information about you                                   ║
║                                                                ║
║  What age are you today? *                                     ║
║  [    42    ] years                                            ║
║  💡 Used to calculate years until retirement                   ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  💰 Income & Expenses                                          ║
║  Your monthly cash flow                                        ║
║                                                                ║
║  What's your monthly income? *                                 ║
║  [  45,000  ] ₪                                                ║
║  💡 Gross monthly income (salary, freelance, etc.)             ║
║                                                                ║
║  What are your monthly expenses? *                             ║
║  [  25,000  ] ₪                                                ║
║  💡 Total monthly spending (rent, food, utilities, etc.)       ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  🏦 Savings & Investments                                      ║
║  What you've already saved                                     ║
║                                                                ║
║  How much do you have saved today?                             ║
║  [  1,500,000 ] ₪                                              ║
║  💡 Total liquid savings + investments                         ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  🎯 Goals                                                       ║
║                                                                ║
║  At what age do you want to retire?                            ║
║  [    55     ] years                                           ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  🏠 Debt & Obligations                                          ║
║                                                                ║
║  Do you have a mortgage?                                       ║
║  [ Yes ]  [ No ✓ ]                                             ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  📚 Retirement Security                                         ║
║                                                                ║
║  Do you have a pension plan?                                   ║
║  [ Yes ]  [ No ✓ ]                                             ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  📝 Summary                                                     ║
║                                                                ║
║  Give your scenario a name (optional)                          ║
║  [ Early Retirement Plan            ]                          ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║                                                                ║
║                        [ Cancel ]  [ Generate Scenario ]       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Key Features

- **Grouped by sections** (Demographics, Income & Expenses, etc.)
- **Progress bar** shows data completeness as % (updates real-time)
- **Conditional visibility**: Mortgage/pension sub-questions only show if user answers "Yes"
- **Help text** under each question (💡 emoji)
- **Optional fields** marked with "(optional)" label
- **Skip-enabled**: User can generate with incomplete answers
- **Scrollable**: Questions flow vertically, user scrolls through sections
- **Generate button** enabled after first question answered

### User Interactions

| Action | Behavior |
|--------|----------|
| Answer Q1 (age) | Score updates to 20%, Generate button enabled |
| Answer Q2 (income) | Score updates to 40% |
| Answer 3 out of 5 required | Score = 60%, can generate |
| Click "Yes" on mortgage | Mortgage sub-questions appear (animation slide-in) |
| Click "No" on mortgage | Mortgage sub-questions disappear, score unchanged |
| Click "Generate Scenario" | Modal → Loading screen |
| Click "Cancel" | Modal closes, form reset |

---

## Screen 2: Loading

### Layout

```
╔════════════════════════════════════════════════════════════════╗
║                                                              ✕ ║
║  Generate Your Scenario                                        ║
║                                                                ║
╟────────────────────────────────────────────────────────────────╢
║                                                                ║
║                                                                ║
║                          ⟳ ⟳ ⟳                                 ║
║                                                                ║
║                    Generating your scenario...                 ║
║                                                                ║
║                                                                ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Behavior

- **Spinning animation** indicates processing
- **Duration**: ~1-2 seconds (depends on simulation)
- **Auto-transition** to Results screen
- **Error handling**: If generation fails, return to Questionnaire with error message

---

## Screen 3: Results

### Layout

```
╔════════════════════════════════════════════════════════════════╗
║                                                              ✕ ║
║  Generate Your Scenario                                        ║
║                                                                ║
╟────────────────────────────────────────────────────────────────╢
║                                                                ║
║  ✅ You're on track for retirement in your 50s.               ║
║  Small changes to income or expenses could bring this earlier. ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║  Scenario Name       │ Retirement Year  │ Final Portfolio       ║
║  ─────────────────────────────────────────────────────────────║
║  Early Retirement    │ Year 11          │ ₪ 8,200,000          ║
║  ─────────────────────────────────────────────────────────────║
║  Monthly Income      │ Monthly Expenses │ Monthly Net           ║
║  ─────────────────────────────────────────────────────────────║
║  ₪ 45,000           │ ₪ 25,000         │ ₪ 20,000             ║
║  ─────────────────────────────────────────────────────────────║
║  Initial Portfolio   │ Data Completeness                        ║
║  ─────────────────────────────────────────────────────────────║
║  ₪ 1,500,000        │ 100%                                      ║
║                                                                ║
║  ─────────────────────────────────────────────────────────────║
║                                                                ║
║                      [ ← Back ]  [ Save Scenario ]             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

### Verdict Color Coding

| Verdict | Color | Emoji | Example |
|---------|-------|-------|---------|
| Success | Green | ✅ | "You're on track..." |
| Warning | Amber | ⚠️ | "Retirement likely at or after 67" |
| Fail | Red | ❌ | "Portfolio depletes before age 100" |

### Key Features

- **Verdict card** at top (large emoji, message, hint)
- **Metrics grid** shows key numbers (6 metrics in 2 rows)
- **Numbers formatted** with thousands separator (₪ 1,500,000)
- **Back button** returns to questionnaire (answers preserved)
- **Save button** opens sub-modal

---

## Screen 3b: Save Modal (Sub-Modal)

### Layout

```
                    ┌─────────────────────────────────┐
                    │ Save Scenario                   │
                    │                                 │
                    │ Enter scenario name:            │
                    │                                 │
                    │ [ Early Retirement Plan        ]│
                    │                                 │
                    │  [ Cancel ]  [ Save ]           │
                    └─────────────────────────────────┘
```

### Behavior

- **Pre-filled** with generated scenario name
- **User can edit** before saving
- **Save button** calls `/api/whatif-saves` to persist
- **Success**: Modal closes, main generator modal closes, new scenario appears in list
- **Error**: Shows error message, stays open

---

## Interaction Flow Diagram

```
┌──────────────┐
│   What-If    │
│  Explorer    │
└──────┬───────┘
       │
       │ Click "Generate Scenario" button
       │
       ▼
┌──────────────────────────────────────┐
│  ScenarioGeneratorModal (isOpen)     │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ QuestionnaireForm              │  │
│  │ (load config on mount)         │  │
│  │                                │  │
│  │ - Display questions by section │  │
│  │ - Handle answer updates        │  │
│  │ - Update score bar             │  │
│  │ - Validate conditional visible │  │
│  │ - On Generate: call API        │  │
│  │                                │  │
│  │ [Cancel]  [Generate Scenario]  │  │
│  └────────────────────────────────┘  │
│            (visible)                 │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ Loading Spinner                │  │
│  │ (hidden, shown during POST)    │  │
│  │                                │  │
│  │ ⟳  Generating your scenario... │  │
│  │                                │  │
│  └────────────────────────────────┘  │
│            (hidden)                  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ ResultsScreen                  │  │
│  │ (hidden, shown after POST)     │  │
│  │                                │  │
│  │ ✅ Verdict card                │  │
│  │ Metrics grid                   │  │
│  │ [Back]  [Save Scenario]        │  │
│  │         ↓                      │  │
│  │    SaveModal (nested)          │  │
│  │    [ Save ] / [ Cancel ]       │  │
│  │    On Save: call /whatif-saves │  │
│  │                                │  │
│  └────────────────────────────────┘  │
│            (hidden)                  │
│                                      │
└──────────────────────────────────────┘
       │
       │ Back button → Show questionnaire (answers preserved)
       │ Save button → Call API → Close modal
       │ Cancel button → Close modal
       │
       ▼
┌──────────────────┐
│  Scenario List   │
│ (updated with   │
│  new scenario)  │
└──────────────────┘
```

---

## CSS/Styling Notes

- **Modal backdrop**: Semi-transparent black (rgba 0,0,0,0.5), full screen overlay
- **Modal width**: 600px max, 90% on mobile
- **Max height**: 80vh, scrollable body
- **Border radius**: 8px throughout
- **Colors**:
  - Primary (blue): #3b82f6
  - Success (green): #16a34a
  - Warning (amber): #f59e0b
  - Fail (red): #dc2626
  - Neutral grays: #1f2937, #6b7280, #e5e7eb, #f9fafb

- **Typography**:
  - Modal title: 20px, weight 600
  - Section title: 16px, weight 600
  - Question label: 14px, weight 500
  - Help text: 12px, color gray-600
  - Metric value: 16px, weight 600

- **Animations**:
  - Section questions slide in (0.3s ease-out)
  - Progress bar width animates (0.3s ease)
  - Modal fade in (0.2s ease)

---

## Responsive Design

- **Desktop (600px+)**: Full modal width, 2-column metrics grid
- **Tablet (400px)**: Modal 90% width, 1-column metrics grid
- **Mobile (320px)**: Same as tablet, tighter padding

---

## Accessibility

- All inputs have associated `<label>` elements
- Focus states visible on buttons/inputs
- Keyboard navigation supported (Tab, Enter, Escape)
- Color not sole indicator (emoji + text for verdicts)
- Proper semantic HTML (sections, headings)
- ARIA labels where needed

---

## Next Steps (Phase 2+)

- Add conditional mortgage/pension detail questions
- Support multiple profiles in future
- Add scenario comparison (side-by-side with generated)
- Add "What-If" variations (sensitivity analysis)


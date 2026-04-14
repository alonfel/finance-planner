# Quick Start: Claude Code Skills

## Available Skills

Two skills are available in this project:

### 1. `/feature-creation`

**When to use:** Implementing a new feature

```
/feature-creation
↓
PHASE 1: Planning Mode (design architecture, get user approval)
PHASE 2: Implementation (backend code + tests)
PHASE 3: Core Scenarios (happy path tests)
PHASE 4: Mark TODOs (document what's left)
PHASE 5: Summary Output (for next skill)
```

**Output:** Working feature with TODO list ready for polish

---

### 2. `/feature-finish-cycle`

**When to use:** Polishing a feature before merge

```
/feature-finish-cycle
↓
STEP 1: Architecture Validation ✓
STEP 2: Code Quality Improvement ✓
STEP 3: Test Coverage Completion ✓
STEP 4: Documentation ✓
STEP 5: Self-Review Checklist ✓
STEP 6: User Verification ⏸️ (STOP)
STEP 7: Git Commit 🚀
```

**Output:** Production-ready feature + clean commit

---

## Typical Workflow

```
1. User: "Add X feature"
2. Claude: /feature-creation
   - Design validated
   - Backend implemented
   - Tests passing
   - TODOs marked

3. User: "Polish it"
4. Claude: /feature-finish-cycle
   - 7-step pipeline
   - Step 6 waits for user approval
   - Feature committed when ready
```

---

## Rules

✅ **Don't Skip Steps**
  - Feature Creation: All 5 phases required
  - Feature Finish Cycle: All 7 steps required

✅ **User Approval Gates**
  - Feature Creation PHASE 1: Design review
  - Feature Finish Cycle STEP 6: Quality review

✅ **Test Coverage Required**
  - Happy path + edge cases
  - Integration test + regression test
  - All tests must pass

✅ **Follow Existing Patterns**
  - Models: Immutable dataclasses
  - Parsers: Defensive, backward-compatible
  - Tests: Pure unittest + subTest

---

## File Locations

| File | Location |
|------|----------|
| Feature Creation Skill | `.claude/skills/feature-creation/SKILL.md` |
| Feature Finish Cycle Skill | `.claude/skills/feature-finish-cycle/SKILL.md` |
| Architecture Source | `~/.claude/projects/.../memory/SKILL_DESIGN_2026.md` |
| This Guide | `.claude/SKILLS_QUICK_START.md` |

---

## Example: Adding Tax Bracket Support

```
User: "Add tax bracket modeling to scenarios"

Claude: /feature-creation
├─ PHASE 1: Design
│  ├─ Model: Add TaxBracket dataclass
│  ├─ Parser: Add parse_tax_brackets()
│  ├─ Simulation: Calculate taxes in year loop
│  └─ Show to user → APPROVED
├─ PHASE 2: Implement
│  ├─ domain/models.py: TaxBracket + tax_brackets field
│  ├─ infrastructure/parsers.py: parse_tax_brackets()
│  ├─ domain/simulation.py: calculate_annual_taxes()
│  └─ domain/models.py: Add annual_taxes to YearData
├─ PHASE 3: Tests
│  ├─ Happy path: Single bracket, multi-bracket
│  ├─ Edge cases: Zero income, below threshold
│  ├─ Integration: Full scenario with taxes
│  └─ Regression: Scenario without taxes (no change)
├─ PHASE 4: TODOs
│  ├─ TODO: Add schema to web/backend/schemas.py
│  ├─ TODO: Add API endpoint
│  └─ TODO: Add UI sliders
└─ PHASE 5: Summary
   └─ Output for Feature Finish Cycle

User: "Polish it"

Claude: /feature-finish-cycle
├─ STEP 1: Validate architecture → ✓ Follows Mortgage pattern
├─ STEP 2: Improve code quality → ✓ Clear names, type hints
├─ STEP 3: Complete tests → ✓ 6 tests all passing
├─ STEP 4: Document → ✓ Updated CLAUDE.md
├─ STEP 5: Self-review → ✓ All 8 items checked
├─ STEP 6: User verification
│  └─ Show changes to user → APPROVED
└─ STEP 7: Git commit
   └─ Feature committed to main 🚀
```

---

## Key Files Modified

When using Feature Creation + Feature Finish Cycle for most features:

```
domain/models.py              (New dataclass + field)
infrastructure/parsers.py     (New parse_X() function)
domain/simulation.py          (Update year loop)
tests/test_simulation.py      (New test class, 4-6 tests)
CLAUDE.md                     (Documentation, if user-facing)
```

Optional (if API/UI needed, separate Feature Creation task):

```
web/backend/schemas.py        (Pydantic models)
web/backend/routers/*.py      (Endpoints)
web/frontend/src/views/*.vue  (UI components)
```

---

## Questions?

Check these resources:

- **"How do I run feature-creation?"** → This guide (top section)
- **"What steps must I follow?"** → See SKILL.md files directly
- **"What if a test fails?"** → See "What If Something Fails?" in SKILL.md
- **"Can I skip a step?"** → No. All steps are mandatory.
- **"Where are the skills?"** → `.claude/skills/feature-creation/SKILL.md` and `.claude/skills/feature-finish-cycle/SKILL.md`

---

**Ready to build a feature?** Invoke `/feature-creation` and follow the phases!

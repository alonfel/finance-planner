# Development Skills: Feature Creation & Finish Cycle

> **Updated April 14, 2026** — Added feature branch as first step to protect `main` from breaking changes.

This document describes two reusable development skills for building features safely and maintaining code quality.

## Quick Summary

1. **Feature Creation Skill** — Plan and implement a new feature on a feature branch
2. **Feature Finish Cycle** — Polish, test, and prepare for merge to main

### The Workflow

```
┌─────────────────────┐
│  User Request       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  FEATURE CREATION SKILL                 │
│  Step 0: git checkout -b feature/...    │ ← CREATE BRANCH FIRST
│  Step 1: Understand Request             │
│  Step 2: Map to Architecture            │
│  Step 3: Design Minimal Diff            │
│  Step 4: Implement Happy Path           │
│  Step 5: Document with TODOs            │
└──────────┬──────────────────────────────┘
           │
           ▼ (happy path working)
┌─────────────────────────────────────────┐
│  FEATURE FINISH CYCLE                   │
│  Step 1: Architecture Validation        │
│  Step 2: Code Quality Refactoring       │
│  Step 3: Full Test Coverage             │
│  Step 4: Documentation Updates          │
│  Step 5: Self-Review Checklist          │
│  Step 6: User Verification (⏸ ASK)     │
│  Step 7: Commit on branch               │
└──────────┬──────────────────────────────┘
           │
           ▼ (user approval)
┌─────────────────────────────────────────┐
│  MERGE TO MAIN                          │
│  git checkout main                      │
│  git merge feature/your-feature         │
│  git push origin main                   │
└─────────────────────────────────────────┘
```

## Why Feature Branches?

**Lesson learned:** Previous feature attempt (unified scenario view) broke the app when working directly on `main`.

**Branch protection benefits:**
- ✅ `main` always stays working — if a feature breaks, users are unaffected
- ✅ Easy rollback — just `git checkout main` or delete the branch
- ✅ Clean history — one PR per feature, easy review
- ✅ Safe collaboration — multiple people can work on different features simultaneously
- ✅ Safe revert — if feature needs major rework, leave it on branch, start fresh, or delete it

---

## SKILL 1: Feature Creation (On Feature Branch)

### Step 0: CREATE FEATURE BRANCH (Always First)

```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name
git push -u origin feature/your-feature-name

# Verify
git status  # Should show: "On branch feature/your-feature-name"
```

**Branch naming:**
- `feature/add-tax-calculation`
- `feature/fix-mortgage-rate-bug`
- `feature/unify-scenario-views`
- Format: `feature/{descriptive-short-name}` or `bugfix/{issue}`

### Step 1: Understand the Feature Request

- Read carefully
- Ask clarifications if needed:
  - Is this a model field or calculation?
  - When does it matter (during simulation, at retirement, etc.)?
  - Is it optional or always present?
  - Does it have settings (like pension has `accessible_at_age`)?

### Step 2: Map to Existing Architecture

Identify which layers are affected:
- Domain model? (add field to Scenario or new dataclass)
- Infrastructure? (need parser function?)
- API? (need new request/response schema?)
- Simulation? (need year-by-year logic?)
- Frontend? (need new UI controls?)

Look for similar features and reuse abstractions.

### Step 3: Design the Minimal Diff

- Domain model first — add field(s) to dataclass
- Ensure composition — if complex, create sub-dataclass (like Mortgage, Pension)
- Add parser if needed
- Update simulate() only where needed
- Add schema only if API-exposed

### Step 4: Implement Happy Path

Implement the core feature, getting it working end-to-end (at least tests passing).

### Step 5: Document with TODOs

Mark unfinished work with inline comments:
```python
# TODO: add tax_brackets to SimulateRequest schema (web/backend/schemas.py)
# TODO: add tax bracket UI (web/frontend/src/views/WhatIfView.vue)
```

---

## SKILL 2: Feature Finish Cycle (On Feature Branch)

### Step 1: Architecture Validation

Review the actual code:
- Does it follow existing patterns? (e.g., does TaxBracket follow Mortgage pattern?)
- Is it in the correct module? (domain vs infrastructure vs web?)
- Any duplication vs existing logic?
- Any unnecessary abstraction?
- Are defaults correct? (None vs field(default_factory=list))

Fix any issues **before proceeding**.

### Step 2: Code Quality Refactoring

- Variable names clear?
- Function names describe behavior?
- Type hints complete?
- Docstrings for public functions? (Args, Returns, Raises)
- Comments only for non-obvious logic

### Step 3: Full Test Coverage

**Review existing tests:**
- Does happy path test work? ✅
- Edge cases covered? (zero values, boundaries, multiple items)
- Error cases tested? (malformed input, invalid states)

**Add missing tests** — aim for 70%+ coverage of new code.

**Run tests:**
```bash
python -m unittest tests.test_simulation -v
```

All tests must pass.

### Step 4: Documentation

Update CLAUDE.md only if the feature is user-facing. Be concise.

### Step 5: Self-Review Checklist

- [ ] Code integrates cleanly (no shared mutable state)
- [ ] No naming conflicts
- [ ] No hidden coupling
- [ ] Unnecessary imports?
- [ ] Default values safe? (no mutable defaults in dataclasses)
- [ ] Error handling matches existing patterns?
- [ ] Potential regressions? (did I break existing features?)
- [ ] Performance acceptable?

### Step 6: User Verification (MANDATORY STOP)

Show the user:
1. What changed (minimal diff summary)
2. What the feature does (behavior examples)
3. What tests cover it (test names)
4. Ask explicitly:
   - "Does this match your expectation?"
   - "Any changes before I commit?"
   - "Ready to merge to main?"

**⏸ WAIT for explicit approval before proceeding.**

### Step 7: Commit on Feature Branch

Ensure you're on the feature branch:
```bash
git status  # Should NOT show "main"
```

Prepare clean commit:
```bash
# Stage specific files
git add domain/models.py
git add infrastructure/parsers.py
git add tests/test_simulation.py

# Create commit
git commit -m "$(cat <<'EOF'
Feature: Clear title (under 70 chars)

- What changed
- Why it changed
- Key behavior

Tests: What's tested

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
EOF
)"

# Push to remote
git push origin feature/your-feature
```

### Step 8: Merge to Main (After User Approval)

```bash
# Switch to main and update
git checkout main
git pull origin main

# Merge feature branch
git merge feature/your-feature

# Push to main
git push origin main

# Clean up (optional)
git branch -d feature/your-feature
git push origin --delete feature/your-feature
```

---

## Key Rules (No Exceptions)

1. **Always create a feature branch first** — never work directly on `main`
2. **Never skip Feature Finish steps** — all steps must pass before user verification
3. **User approval is mandatory** — don't commit/merge without explicit go-ahead
4. **Tests must all pass** — never merge failing tests
5. **No refactoring unrelated code** — stay focused on the feature
6. **Preserve consistency** — match existing naming, style, patterns
7. **Document only essentials** — don't over-document

---

## When to Use Each Skill

| Situation | Use |
|-----------|-----|
| "Add a new feature" | Feature Creation |
| "Fix a bug" | Feature Creation (same process) |
| "Refactor this component" | Feature Creation (careful, minimal diff) |
| "Happy path implemented, needs polish" | Feature Finish Cycle |
| "Ready to merge" | Merge to main (after user approval) |
| "Feature broke the app" | Stay on branch, fix it, or delete and start over |

---

## Example: Real Feature (Tax Brackets)

**User:** "Add progressive tax brackets to scenarios"

### Feature Creation Response

**Step 0:** Create branch
```bash
git checkout -b feature/tax-brackets
```

**Steps 1-5:** Design + implement

Final output: Tax calculation in simulate(), tests passing, TODOs marked for API/UI.

### Feature Finish Response

**Steps 1-7:** Validate architecture, refactor for clarity, add full test coverage, get user approval, commit.

### Merge

After user says "looks good":
```bash
git checkout main
git merge feature/tax-brackets
git push origin main
```

---

## Summary

✅ **Start with a branch** — safe from breaking `main`  
✅ **Go through Feature Creation** — plan, implement, test  
✅ **Go through Feature Finish** — polish, verify, get approval  
✅ **Merge to main** — clean, reviewed code gets deployed  
✅ **Delete branch** — keep repo clean  

**Remember:** The reason we have these two skills is to prevent what happened with the unified scenario view — a feature breaking the entire app because we worked directly on main without proper testing and review.

Feature branches protect everyone. Always use them.

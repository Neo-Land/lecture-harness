## What & why
<!-- One or two sentences. Link the plan task: Phase N — task name -->

## Changes
-

## Tests
- [ ] New/updated tests cover this change
- [ ] `ruff check . && ruff format --check .` passes
- [ ] `pytest --cov=app --cov-fail-under=85` passes
- [ ] (if `web/` changed) lint, typecheck, test, build pass

## Docs
- [ ] `CHANGELOG.md` updated
- [ ] `README.md` / `docs/ARCHITECTURE.md` updated if setup, modules, or endpoints changed
- [ ] ADR added for any non-obvious decision or new dependency
- [ ] `docs/PROJECT_PLAN.md` task ticked (or will be after merge)

## Safety
- [ ] No secrets, `.env`, or `data/` contents committed
- [ ] No real network/API calls in tests
- [ ] New dependencies justified below

## Notes for reviewer

# Dev-Workflow Bootstrap — Design (first tests + CI)

**Status: approved for build, 2026-08-09 session.** Owner directive: make
the first test runs, hone in on the workflow, synthetic/mocked data allowed,
early feedback via CI/CD, fast-forward commit principles. This spec covers
the workflow skeleton only; `2026-08-09-audit-cli-design.md` remains
authoritative for product scope and stays deferred except for the one slice
named below.

## Goal

Prove the full development loop once, end to end, with the smallest honest
slice: failing test → implementation → green run → atomic commit → push →
CI verdict on GitHub. Every future module repeats this loop unchanged.

## Decisions

### Test harness: pytest (dev-only dependency)

stdlib `unittest` was considered (zero deps, V1 precedent) and rejected: the
audit-CLI spec's testing section assumes pytest idioms (`tmp_path`, golden
files, parametrized fixtures). Runtime stays stdlib-only; pytest is tooling,
not a dependency of the code. Config lives in `pyproject.toml`
(`[tool.pytest.ini_options]` with `pythonpath = ["."]`, `testpaths =
["tests"]`) — no packaging section, since packaging is a stated non-goal.

### First slice: `fuck/kpis.py` — TDD, zero mocks

Rank-1 testable seam: pure arithmetic, formulas and target bands already
fixed in `docs/finance-os.md` §1. Five functions over explicit aggregates —
not `list[Transaction]`; the Transaction contract gets frozen when the first
dialect parser is built, and KPI math must not prematurely bind to it:

- `savings_rate(net_income, expenses)` → `Decimal | None`
- `fixed_cost_ratio(fixed_costs, net_income)` → `Decimal | None`
- `recurring_margin(recurring_income, fixed_costs)` → `Decimal`
- `income_streams(income_by_source)` → `dict[str, Decimal]` (shares of
  total, ordered largest first)
- `emergency_fund_months(liquid_funds, avg_monthly_expenses)` → `Decimal | None`

`None` means "not computable" (division guards: net income ≤ 0, average
monthly expenses ≤ 0); the future report surfaces that in its honesty
section instead of guessing. All money and ratios are `Decimal`.

Band classifiers with exact boundary semantics (from `finance-os.md`):

- Savings rate: `< 0.10` below_floor · `[0.10, 0.15)` floor ·
  `[0.15, 0.20)` solid · `≥ 0.20` wealth_building
- Fixed-cost ratio: `< 0.30` comfortable · `[0.30, 0.50]` acceptable ·
  `(0.50, 0.65]` over_ceiling · `> 0.65` critical
- Emergency-fund months: `< 3` under_band · `[3, 6]` in_band · `> 6`
  above_band (cash above the band is drag, not safety)
- Recurring margin and income streams carry no bands: they are judged as
  trend / concentration by the human, run over run.

### Smoke-and-mirrors preview: `fuck/report.py` + `fuck/demo.py`

Owner directive (mid-session): "simulate before the build takes effect …
scratch designs quickly … smoke and mirrors for the start." The one-pager
report is the product's user-facing surface, so it gets rendered *now* from
synthetic aggregates — the design can be judged and honed before any parser
exists.

- `fuck/report.py` — real module code (TDD, golden-file test, exactly as the
  audit-cli spec prescribes): renders the one-pager from KPI values + bands.
  Sections that depend on unbuilt modules (fixed-cost ranking, snapshot
  diff) render as explicit `[not built yet — needs detect.py/diff.py]`
  stubs, never as fake findings.
- `fuck/demo.py` — labeled throwaway (TDD-exempt prototype, owner-sanctioned):
  feeds `report.render()` canned synthetic numbers and prints to stdout via
  `python -m fuck.demo`. Deleted the day the real pipeline feeds the report.
- Honesty discipline from day one: the rendered page opens with a
  `SIMULATED DATA` banner naming the demo as synthetic; the future real
  report replaces that banner with the coverage section.
- CI runs `python -m fuck.demo` as a smoke step: proves import + render on
  every supported Python.

### Test data policy

Synthetic only, ever (privacy invariant: real financial data never enters
git; `.gitignore` already guards `exports/`, `snapshot.json`, `journal.md`).
For `kpis.py` no fixtures or mocks are needed at all — inputs are numbers.

### CI: one workflow, deliberately small

`.github/workflows/ci.yml`: on push to `main` and `claude/**` and on PRs to
`main`, run pytest on Python 3.10 (spec floor) and 3.13 (current), Ubuntu
only, then run `python -m fuck.demo` as a smoke step. **Windows is excluded
on purpose:** the repository name `F.U.C.K.` ends in a dot, an illegal
trailing character for Windows directory names — checkout fails before any
step runs. Concurrency-cancel per ref. No lint,
coverage, release, or dependabot jobs — each gets added only when it earns
its keep (README Principle 4).

### Workflow conventions → CLAUDE.md (first repo instruction file)

Codifies, tersely: stdlib-only runtime; TDD mandatory (vendored skill);
synthetic-data-only invariant; Conventional Commits plus the two Claude
trailers; **fast-forward commit principles** — small atomic commits, linear
history, rebase local work onto latest `main` before integrating, integrate
fast-forward or squash (no merge commits), `git pull --rebase`, no
force-push to shared branches without explicit request; review before
merge; spec/plan path conventions.

## Out of scope (deferred, per audit-cli spec sequencing)

Dialect parsers, normalize/netting, detect, diff, the `fuck audit` CLI
entry point (the report's fixed-cost and diff sections stay stubs until
detect.py/diff.py exist);
property-test tooling (arrives with `normalize.py`); coverage gates;
linters/pre-commit; Windows/macOS CI; release automation; GitHub
branch-protection changes (a settings recommendation to the owner, not
something an agent flips silently).

## Verification

This bootstrap is proven when (1) pytest is green locally with the
failing-first evidence recorded during TDD, and (2) the pushed branch's CI
run completes green on GitHub — the early-feedback loop observed working
once, not assumed.

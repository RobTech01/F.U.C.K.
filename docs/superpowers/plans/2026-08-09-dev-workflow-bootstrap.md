# Dev-Workflow Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the full development loop once — failing test → code → green → atomic commit → push → CI verdict — via the smallest honest slice: KPI math plus a simulated one-pager report, with the repo's first CI workflow and CLAUDE.md.

**Architecture:** `fuck/kpis.py` holds the five pure KPI functions and band classifiers (aggregates in, numbers out — deliberately not bound to the future Transaction contract). `fuck/report.py` renders the one-pager from aggregates by calling `kpis`; unbuilt sections render as explicit stubs. `fuck/demo.py` is a labeled throwaway feeding `render()` canned synthetic numbers (`python -m fuck.demo`). CI runs pytest plus the demo as a smoke step.

**Tech Stack:** Python ≥ 3.10 stdlib only; pytest (dev-only); GitHub Actions.

## Global Constraints

- Runtime is **stdlib-only**; pytest is the only dev tool (audit-cli spec: "Architecture (Python ≥3.10, stdlib-only)").
- All money and ratios are `decimal.Decimal`; `None` means "not computable" — never guess.
- Test data is **synthetic only** — real financial data never enters git.
- Report output is ASCII-only (`>=`, `--`, `EUR`), for terminal and golden-file safety.
- Every commit: Conventional Commits subject, body explains why, plus BOTH trailers, verbatim:
  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4
  ```
- Commit directly on branch `claude/using-superpowers-wb260x`, sequentially — history stays linear, no merges. Do NOT push; the orchestrator pushes.
- Working directory for all commands: `/home/user/F.U.C.K.`
- Band boundary semantics come from `docs/finance-os.md` §1 and are exact:
  savings rate `< 0.10` below_floor · `[0.10, 0.15)` floor · `[0.15, 0.20)` solid · `≥ 0.20` wealth_building;
  fixed-cost ratio `< 0.30` comfortable · `[0.30, 0.50]` acceptable · `(0.50, 0.65]` over_ceiling · `> 0.65` critical;
  emergency fund `< 3` under_band · `[3, 6]` in_band · `> 6` above_band.

---

### Task 1: pytest scaffolding + `fuck/kpis.py` (TDD)

**Files:**
- Create: `pyproject.toml`
- Modify: `.gitignore` (append)
- Create: `fuck/__init__.py`
- Create: `fuck/kpis.py`
- Test: `tests/test_kpis.py`

**Interfaces:**
- Consumes: nothing (first code in the repo).
- Produces (Task 2 relies on these exact names/signatures, all `Decimal` in/out):
  `savings_rate(net_income, expenses) -> Decimal | None`,
  `savings_rate_band(rate: Decimal) -> str`,
  `fixed_cost_ratio(fixed_costs, net_income) -> Decimal | None`,
  `fixed_cost_band(ratio: Decimal) -> str`,
  `recurring_margin(recurring_income, fixed_costs) -> Decimal`,
  `income_streams(income_by_source: Mapping[str, Decimal]) -> dict[str, Decimal]`,
  `emergency_fund_months(liquid_funds, avg_monthly_expenses) -> Decimal | None`,
  `emergency_fund_band(months: Decimal) -> str`.

- [ ] **Step 1: Add tooling config (TDD-exempt configuration)**

`pyproject.toml` (entire file):

```toml
# Tooling config only — packaging is a stated non-goal (audit-cli spec:
# "No packaging, no marketing, no PyPI").
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-q"
```

Append to `.gitignore`:

```
# Tooling caches / agent worktrees
.pytest_cache/
.worktrees/
```

Run: `pytest --version` — needs pytest ≥ 7 for `pythonpath` support (sandbox has pytest installed; report the version you see).

- [ ] **Step 2: Commit the config**

```bash
git add pyproject.toml .gitignore
git commit -m "chore: Configure pytest and extend gitignore

pyproject.toml carries pytest config only — no packaging section,
packaging is a stated non-goal. pythonpath=['.'] lets tests import the
fuck package without an install step (runtime is stdlib-only).
.gitignore gains tool caches and the agent worktree directory.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4"
```

- [ ] **Step 3: Write the failing tests**

`tests/test_kpis.py` (entire file):

```python
"""Tests for the five quarterly numbers (docs/finance-os.md section 1).

Band boundaries are pinned exactly as the finance-os doc states them;
if a boundary test surprises you, the doc wins, not the test.
"""

from decimal import Decimal

import pytest

from fuck import kpis

D = Decimal


class TestSavingsRate:
    def test_formula(self):
        assert kpis.savings_rate(D("3000"), D("2400")) == D("0.2")

    def test_overspending_goes_negative(self):
        assert kpis.savings_rate(D("2000"), D("2500")) == D("-0.25")

    @pytest.mark.parametrize("net_income", [D("0"), D("-1")])
    def test_not_computable_without_positive_income(self, net_income):
        assert kpis.savings_rate(net_income, D("100")) is None

    @pytest.mark.parametrize(
        ("rate", "band"),
        [
            (D("-0.05"), "below_floor"),
            (D("0.0999"), "below_floor"),
            (D("0.10"), "floor"),  # ">=10% floor" is inclusive
            (D("0.1499"), "floor"),
            (D("0.15"), "solid"),
            (D("0.1999"), "solid"),
            (D("0.20"), "wealth_building"),
            (D("0.50"), "wealth_building"),
        ],
    )
    def test_bands(self, rate, band):
        assert kpis.savings_rate_band(rate) == band


class TestFixedCostRatio:
    def test_formula(self):
        assert kpis.fixed_cost_ratio(D("900"), D("3000")) == D("0.3")

    @pytest.mark.parametrize("net_income", [D("0"), D("-500")])
    def test_not_computable_without_positive_income(self, net_income):
        assert kpis.fixed_cost_ratio(D("900"), net_income) is None

    @pytest.mark.parametrize(
        ("ratio", "band"),
        [
            (D("0.2999"), "comfortable"),
            (D("0.30"), "acceptable"),
            (D("0.50"), "acceptable"),  # "50% ceiling" — the ceiling itself is acceptable
            (D("0.5001"), "over_ceiling"),
            (D("0.65"), "over_ceiling"),
            (D("0.6501"), "critical"),  # ">65% critical" is exclusive
        ],
    )
    def test_bands(self, ratio, band):
        assert kpis.fixed_cost_band(ratio) == band


class TestRecurringMargin:
    def test_formula(self):
        assert kpis.recurring_margin(D("2600"), D("950")) == D("1650")

    def test_can_go_negative(self):
        assert kpis.recurring_margin(D("800"), D("950")) == D("-150")


class TestIncomeStreams:
    def test_shares_sum_to_one_and_order_largest_first(self):
        # Amounts chosen so shares are exact Decimals (no precision noise).
        shares = kpis.income_streams(
            {"freelance": D("2500"), "salary": D("7500")}
        )
        assert list(shares) == ["salary", "freelance"]
        assert shares["salary"] == D("0.75")
        assert shares["freelance"] == D("0.25")
        assert sum(shares.values()) == D("1")

    def test_equal_shares_tie_break_alphabetically(self):
        shares = kpis.income_streams({"b": D("50"), "a": D("50")})
        assert list(shares) == ["a", "b"]

    def test_non_positive_sources_are_dropped(self):
        shares = kpis.income_streams(
            {"salary": D("100"), "refund_noise": D("0"), "correction": D("-20")}
        )
        assert list(shares) == ["salary"]
        assert shares["salary"] == D("1")

    @pytest.mark.parametrize(
        "sources", [{}, {"a": D("0")}, {"a": D("-5"), "b": D("-1")}]
    )
    def test_no_positive_income_yields_empty(self, sources):
        assert kpis.income_streams(sources) == {}


class TestEmergencyFund:
    def test_formula(self):
        assert kpis.emergency_fund_months(D("12000"), D("2400")) == D("5")

    @pytest.mark.parametrize("avg", [D("0"), D("-100")])
    def test_not_computable_without_positive_expenses(self, avg):
        assert kpis.emergency_fund_months(D("12000"), avg) is None

    @pytest.mark.parametrize(
        ("months", "band"),
        [
            (D("2.99"), "under_band"),
            (D("3"), "in_band"),
            (D("6"), "in_band"),  # "3-6 months as a band" — both ends inclusive
            (D("6.01"), "above_band"),  # cash above the band is drag
        ],
    )
    def test_bands(self, months, band):
        assert kpis.emergency_fund_band(months) == band
```

- [ ] **Step 4: Run tests to verify they fail for the right reason**

Run: `python -m pytest tests/test_kpis.py -v 2>&1 | head -20`
Expected: collection error — `ModuleNotFoundError: No module named 'fuck'`. Record this output; it is the RED evidence.

- [ ] **Step 5: Write the minimal implementation**

`fuck/__init__.py` (entire file):

```python
"""F.U.C.K. — Finances Under Control Kit (audit core, V2)."""
```

`fuck/kpis.py` (entire file):

```python
"""The five quarterly numbers (docs/finance-os.md section 1).

Pure arithmetic over explicit aggregates. Deliberately not bound to the
Transaction contract yet — that gets frozen with the first dialect
parser. All money and ratios are Decimal. None means "not computable";
the report surfaces that instead of guessing.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping


def savings_rate(net_income: Decimal, expenses: Decimal) -> Decimal | None:
    """(net income - expenses) / net income; None when net income <= 0."""
    if net_income <= 0:
        return None
    return (net_income - expenses) / net_income


def savings_rate_band(rate: Decimal) -> str:
    if rate < Decimal("0.10"):
        return "below_floor"
    if rate < Decimal("0.15"):
        return "floor"
    if rate < Decimal("0.20"):
        return "solid"
    return "wealth_building"


def fixed_cost_ratio(fixed_costs: Decimal, net_income: Decimal) -> Decimal | None:
    """fixed costs / net income; None when net income <= 0."""
    if net_income <= 0:
        return None
    return fixed_costs / net_income


def fixed_cost_band(ratio: Decimal) -> str:
    if ratio < Decimal("0.30"):
        return "comfortable"
    if ratio <= Decimal("0.50"):
        return "acceptable"
    if ratio <= Decimal("0.65"):
        return "over_ceiling"
    return "critical"


def recurring_margin(recurring_income: Decimal, fixed_costs: Decimal) -> Decimal:
    """recurring income - fixed costs; subscription creep erodes this."""
    return recurring_income - fixed_costs


def income_streams(income_by_source: Mapping[str, Decimal]) -> dict[str, Decimal]:
    """Share of total income per source, largest first (ties: by name).

    Non-positive sources are dropped; {} when nothing positive remains —
    no concentration statement is better than a wrong one.
    """
    positive = {k: v for k, v in income_by_source.items() if v > 0}
    total = sum(positive.values(), Decimal("0"))
    if total == 0:
        return {}
    shares = {k: v / total for k, v in positive.items()}
    return dict(sorted(shares.items(), key=lambda kv: (-kv[1], kv[0])))


def emergency_fund_months(
    liquid_funds: Decimal, avg_monthly_expenses: Decimal
) -> Decimal | None:
    """liquid funds / average monthly expenses; None when expenses <= 0."""
    if avg_monthly_expenses <= 0:
        return None
    return liquid_funds / avg_monthly_expenses


def emergency_fund_band(months: Decimal) -> str:
    if months < 3:
        return "under_band"
    if months <= 6:
        return "in_band"
    return "above_band"
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_kpis.py -v`
Expected: all PASS, zero failures. Record the summary line.

- [ ] **Step 7: Commit**

```bash
git add fuck/__init__.py fuck/kpis.py tests/test_kpis.py
git commit -m "feat: Add the five KPI computations with target bands

First production code of V2, built test-first (TDD): pure functions
over explicit aggregates, per docs/finance-os.md section 1. Not bound
to the Transaction contract on purpose — that gets frozen with the
first dialect parser. None = not computable; the report will surface
it instead of guessing.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4"
```

---

### Task 2: Simulated one-pager — `fuck/report.py` + `fuck/demo.py` (TDD + golden file)

**Files:**
- Create: `fuck/report.py`
- Create: `fuck/demo.py`
- Create: `tests/golden/demo_report.txt` (generated, then eyeballed)
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes from Task 1: every function listed in Task 1's "Produces" block, exactly as specified there (`from fuck import kpis`).
- Produces: `report.render(*, banner, net_income, expenses, fixed_costs, recurring_income, income_by_source, liquid_funds, avg_monthly_expenses) -> str` (keyword-only, all `Decimal` except `banner: str` and `income_by_source: Mapping[str, Decimal]`); `demo.demo_page() -> str`; `python -m fuck.demo` prints the page.

- [ ] **Step 1: Write the failing tests**

`tests/test_report.py` (entire file):

```python
"""Golden-file + behavior tests for the simulated one-pager."""

from decimal import Decimal
from pathlib import Path

from fuck import demo, report

GOLDEN = Path(__file__).parent / "golden" / "demo_report.txt"

D = Decimal


def render_minimal(**overrides):
    args = dict(
        banner="!! TEST !!",
        net_income=D("1000"),
        expenses=D("800"),
        fixed_costs=D("300"),
        recurring_income=D("1000"),
        income_by_source={"salary": D("1000")},
        liquid_funds=D("4000"),
        avg_monthly_expenses=D("800"),
    )
    args.update(overrides)
    return report.render(**args)


def test_demo_page_matches_golden_file():
    assert demo.demo_page() == GOLDEN.read_text(encoding="utf-8")


def test_demo_page_declares_itself_simulated():
    page = demo.demo_page()
    assert "SIMULATED DATA" in page
    # The banner must come before any number is shown.
    assert page.index("SIMULATED DATA") < page.index("savings rate")


def test_unbuilt_sections_are_stubs_not_fake_data():
    page = demo.demo_page()
    assert "[not built yet -- fixed-cost ranking needs detect.py]" in page
    assert "[not built yet -- decision verification needs diff.py]" in page


def _kpi_line(page: str, label: str) -> str:
    return next(
        line for line in page.splitlines() if line.strip().startswith(label)
    )


def test_not_computable_kpis_render_as_na_without_bands():
    page = render_minimal(net_income=D("0"), avg_monthly_expenses=D("0"))
    # Value slot AND band slot must both read n/a — a KPI that cannot be
    # computed must not carry a band verdict. (The static target text on
    # each line contains band words, so substring checks on the whole
    # page would lie; check the two slots instead.)
    for label in ("savings rate", "fixed-cost ratio", "emergency fund"):
        line = _kpi_line(page, label)
        assert line.count("n/a") == 2, line


def test_page_is_ascii_only():
    demo.demo_page().encode("ascii")  # raises UnicodeEncodeError if violated
```

- [ ] **Step 2: Run tests to verify they fail for the right reason**

Run: `python -m pytest tests/test_report.py -v 2>&1 | head -20`
Expected: collection error — `ImportError` (`fuck.demo` / `fuck.report` do not exist). Record as RED evidence.

- [ ] **Step 3: Write the implementation**

`fuck/report.py` (entire file):

```python
"""Terminal one-pager along the review agenda (docs/finance-os.md section 5).

Aggregates in, page out. Sections whose upstream modules do not exist
yet render as explicit stubs — never as fake findings.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from fuck import kpis

WIDTH = 72
NOT_BUILT_FIXED = "[not built yet -- fixed-cost ranking needs detect.py]"
NOT_BUILT_DIFF = "[not built yet -- decision verification needs diff.py]"


def _pct(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{(value * 100).quantize(Decimal('0.1'))}%"


def _eur(value: Decimal) -> str:
    return f"EUR {value.quantize(Decimal('0.01'))}"


def _months(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{value.quantize(Decimal('0.1'))} months"


def render(
    *,
    banner: str,
    net_income: Decimal,
    expenses: Decimal,
    fixed_costs: Decimal,
    recurring_income: Decimal,
    income_by_source: Mapping[str, Decimal],
    liquid_funds: Decimal,
    avg_monthly_expenses: Decimal,
) -> str:
    rate = kpis.savings_rate(net_income, expenses)
    fixed_ratio = kpis.fixed_cost_ratio(fixed_costs, net_income)
    margin = kpis.recurring_margin(recurring_income, fixed_costs)
    streams = kpis.income_streams(income_by_source)
    months = kpis.emergency_fund_months(liquid_funds, avg_monthly_expenses)

    rate_band = kpis.savings_rate_band(rate) if rate is not None else "n/a"
    fixed_band = (
        kpis.fixed_cost_band(fixed_ratio) if fixed_ratio is not None else "n/a"
    )
    months_band = (
        kpis.emergency_fund_band(months) if months is not None else "n/a"
    )
    streams_text = (
        ", ".join(f"{name} {_pct(share)}" for name, share in streams.items())
        if streams
        else "n/a"
    )

    lines = [
        "=" * WIDTH,
        "F.U.C.K. -- quarterly audit one-pager",
        "=" * WIDTH,
        "",
        "1. Coverage",
        f"   {banner}",
        "",
        "2. The five numbers",
        f"   savings rate       {_pct(rate):>8}  {rate_band:<15}"
        f"  target: >=10% floor / 15-20% solid / 20%+ wealth-building",
        f"   fixed-cost ratio   {_pct(fixed_ratio):>8}  {fixed_band:<15}"
        f"  target: <30% comfortable / <=50% ceiling / >65% critical",
        f"   recurring margin   {_eur(margin):>12}  judged as a trend, run over run",
        f"   income streams     {streams_text}",
        f"   emergency fund     {_months(months):>10}  {months_band:<15}"
        f"  target: 3-6 months, a band not a maximum",
        "",
        "3. Fixed costs by annual cost",
        f"   {NOT_BUILT_FIXED}",
        "",
        "4. Diff vs. last run",
        f"   {NOT_BUILT_DIFF}",
        "",
    ]
    return "\n".join(lines)
```

`fuck/demo.py` (entire file):

```python
"""Smoke-and-mirrors preview -- THROWAWAY.

Renders the one-pager from canned SYNTHETIC aggregates so the report
design can be judged before any parser exists. Every number below is
invented. Delete this module the day the real pipeline feeds
report.render(). Run: python -m fuck.demo
"""

from decimal import Decimal

from fuck import report

BANNER = (
    "!! SIMULATED DATA -- synthetic demo numbers; no real exports were read !!"
)


def demo_page() -> str:
    return report.render(
        banner=BANNER,
        net_income=Decimal("8400.00"),
        expenses=Decimal("7000.00"),
        fixed_costs=Decimal("3080.00"),
        recurring_income=Decimal("7800.00"),
        income_by_source={
            "salary": Decimal("7800.00"),
            "freelance": Decimal("600.00"),
        },
        liquid_funds=Decimal("12600.00"),
        avg_monthly_expenses=Decimal("2333.33"),
    )


def main() -> None:
    print(demo_page())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Generate the golden file, then eyeball it**

```bash
mkdir -p tests/golden
python -c "from pathlib import Path; from fuck.demo import demo_page; Path('tests/golden/demo_report.txt').write_text(demo_page(), encoding='utf-8')"
cat tests/golden/demo_report.txt
```

Eyeball checklist before proceeding: banner on top, savings rate `16.7%` + `solid`, fixed-cost ratio `36.7%` + `acceptable`, recurring margin `EUR 4720.00`, streams `salary 92.9%, freelance 7.1%`, emergency fund `5.4 months` + `in_band`, both `[not built yet ...]` stubs present. If any of these differ, the implementation diverged from Task 1's contracts — stop and fix before committing.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest -v`
Expected: all tests (Task 1 + Task 2) PASS. Record the summary line.

- [ ] **Step 6: Smoke-run the demo exactly as CI will**

Run: `python -m fuck.demo`
Expected: the one-pager prints, exit code 0.

- [ ] **Step 7: Commit**

```bash
git add fuck/report.py fuck/demo.py tests/test_report.py tests/golden/demo_report.txt
git commit -m "feat: Add simulated one-pager report (smoke-and-mirrors preview)

Owner asked to simulate before the build takes effect. report.render()
is real module code (golden-file tested, as the audit-cli spec
prescribes); demo.py is a labeled throwaway feeding it canned synthetic
numbers so the report design can be judged now. The page opens with a
SIMULATED DATA banner and renders unbuilt sections as explicit stubs,
never as fake findings.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4"
```

---

### Task 3: First CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `python -m pytest` (Task 1 config) and `python -m fuck.demo` (Task 2 smoke entry).
- Produces: a `CI` workflow that runs on every push to `main`/`claude/**` and on PRs to `main` — the early-feedback loop.

- [ ] **Step 1: Write the workflow (TDD-exempt configuration; its test is the push)**

`.github/workflows/ci.yml` (entire file):

```yaml
# First CI for F.U.C.K. -- deliberately small (README Principle 4).
# Linux-only on purpose: the repository name ends in a dot, which is an
# illegal trailing character for Windows directory names, so a Windows
# runner fails at checkout before any step runs.
name: CI

on:
  push:
    branches: [main, "claude/**"]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        # 3.10 = the audit-cli spec's floor; 3.13 = current.
        python-version: ["3.10", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install test runner (runtime is stdlib-only)
        run: python -m pip install pytest
      - name: Run tests
        run: python -m pytest
      - name: Smoke-run the simulated report
        run: python -m fuck.demo
```

- [ ] **Step 2: Sanity-check locally what CI will do**

```bash
python -m pytest && python -m fuck.demo >/dev/null && echo "CI steps OK locally"
```

Expected: `CI steps OK locally` (the YAML itself is proven by the push in the orchestrator's verification phase).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: Add first CI workflow (pytest + demo smoke)

First automated check in this repo's history: pytest plus a smoke run
of the simulated report, on Python 3.10 (spec floor) and 3.13, Ubuntu
only -- the repo name's trailing dot is an illegal Windows path, so
Windows runners cannot even check out. Runs on pushes to main and
claude/** so feedback arrives before any PR exists.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4"
```

---

### Task 4: CLAUDE.md — codify the workflow

**Files:**
- Create: `CLAUDE.md`

**Interfaces:**
- Consumes: conventions proven in Tasks 1-3.
- Produces: the repo's first instruction file; outranks vendored skills where they conflict.

- [ ] **Step 1: Write the file**

`CLAUDE.md` (entire file):

```markdown
# F.U.C.K. — Finances Under Control Kit

Working agreements for this repo. Where these conflict with the vendored
skills in `.claude/skills/`, this file wins.

## Hard constraints

- **Runtime is stdlib-only, Python >= 3.10.** pytest is the only dev
  tool. Any new dependency (runtime or dev) needs the owner's explicit
  OK first.
- **Never commit real financial data.** Test data is synthetic, always.
  `exports/`, `snapshot.json`, `journal.md` are gitignored on purpose.
- **Lean is the house style** (README Principle 4): every added line is
  a liability. No speculative features, no unrequested tooling.

## Workflow

- **TDD for all production code**
  (`.claude/skills/test-driven-development`): failing test first,
  minimal implementation, green, commit. Configuration files are exempt.
- Run tests: `python -m pytest` (config in `pyproject.toml`).
- Specs go to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`,
  plans to `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`.
- Code review before merging to `main`.
- Never claim tests pass without a fresh run in the same message.

## Git: fast-forward commit principles

- Small, atomic commits; each commit leaves the tree green.
- **History stays linear.** Rebase local work onto latest `main` before
  integrating; integrate fast-forward (`git merge --ff-only`) or squash.
  No merge commits.
- `git pull --rebase`, never a plain pull on a diverged branch.
- Never force-push a shared branch without the owner's explicit request.
- Conventional Commits (`feat:` `fix:` `docs:` `ci:` `chore:`, `!` for
  breaking changes), imperative subject, body explains why. Every
  Claude-authored commit carries its Co-Authored-By and Claude-Session
  trailers.

## CI

`.github/workflows/ci.yml` runs pytest plus the demo smoke on Python
3.10 and 3.13, Ubuntu only — the repo name's trailing dot is an illegal
Windows path, so Windows runners cannot check this repo out. Keep CI
green; a red run on your branch is yours to fix.
```

- [ ] **Step 2: Verify the referenced commands and paths exist**

```bash
python -m pytest && ls .github/workflows/ci.yml pyproject.toml docs/superpowers/specs docs/superpowers/plans
```

Expected: tests green, all paths listed.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: Add CLAUDE.md codifying the dev workflow

The repo's first instruction file: stdlib-only + synthetic-data-only
hard constraints, TDD workflow, and fast-forward commit principles
(linear history, rebase before integrating, ff-only or squash). Per
using-superpowers, repo-level instructions outrank the vendored skills
where they conflict.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4"
```

---

## Post-plan verification (orchestrator, not a task)

Push `claude/using-superpowers-wb260x` with `git push -u origin` (retry with backoff on network errors), then watch the `CI` workflow run for that push via the GitHub API until it completes. Green on both Python versions = the early-feedback loop is proven. Red = fix forward on this branch before reporting. Integration into `main` is the owner's decision (3-option menu), not the orchestrator's.

# Report verdict 2B + dialect inspect command

**Owner verdicts (2026-08-25, chat):** issue #11 decision 2 = option B
(compact legend at end of section 2) with the legend label changed from
`bands:` to `target:`. Decision 1 (width) is settled by 2B for free —
every section-2 line lands under 72 columns. Decision 3 stays open.
Second ask, verbatim: "let's run the test, I can provide a csv … what is
the terminal command?" — there is no command; the parser is
library-only. Build one.

Branch: `claude/using-superpowers-wb260x`. TDD per CLAUDE.md; two atomic
commits, each leaving the tree green.

## Task 1 — report: move target hints to a section legend (verdict 2B)

`fuck/report.py`, section 2 block only. Replace the current five KPI
lines (report.py:74-81) with:

```python
        "2. The five numbers",
        f"   savings rate       {_pct(rate):>8}  {rate_band}",
        f"   fixed-cost ratio   {_pct(fixed_ratio):>8}  {fixed_band}",
        f"   recurring margin   {_eur(margin):>12}  (trend, judged run over run)",
        f"   income streams     {streams_text}",
        f"   emergency fund     {_months(months):>10}  {months_band}",
        "",
        "   target: savings >=10% floor / 15-20% solid / 20%+ wealth-building",
        "           fixed   <30% comfortable / <=50% ceiling / >65% critical",
        "           fund    3-6 months, a band not a maximum",
```

Constraints:

- Band slots lose their `:<15` padding — with nothing after them it
  becomes trailing whitespace. **No line in the rendered page may carry
  trailing whitespace** (test it).
- Legend wording is the former inline hints verbatim; continuation
  indent is 11 spaces (aligns under `savings`); `fixed`/`fund` padded to
  8 chars. Longest legend line is 68 chars.
- Recurring-margin annotation changes to `(trend, judged run over run)`
  (owner-approved mockup wording).
- No blanket `<= 72` width test: the demo banner line is 76 chars and
  belongs to the caller, not the renderer. Assert width only for the
  section-2 lines this task owns.

Tests (`tests/test_report.py`) — write first, red, then implement:

1. Golden test: regenerate `tests/golden/demo_report.txt` from the demo
   aggregates after the render change; existing equality test keeps
   guarding it. Regeneration is the *last* step of this task, after the
   targeted tests pass.
2. Legend present: output contains the three legend lines exactly; KPI
   lines contain no `target:` fragment.
3. No trailing whitespace on any rendered line; section-2 lines <= 72.
4. **Deferred from #11:** empty `income_by_source={}` renders
   `income streams     n/a`.
5. **Deferred from #11:** net 1000 / expenses 1200 renders
   `-20.0%  below_floor` (negative rate is shown, banded honestly).

Commit: `feat: move KPI target hints to a section legend (verdict 2B)`

## Task 2 — CSV inspect command: `python -m fuck.dialects <file>`

New `fuck/dialects/__main__.py` (stdlib only, ~60 lines). Purpose:
issue #6's verification harness — feed a real export, see how the
parser performs, without any CLI framework. Real data stays on the
user's terminal; nothing is written anywhere.

Interface: `main(argv: list[str] | None = None) -> int`, module-level
`if __name__ == "__main__": raise SystemExit(main())`.

- Not exactly one argument → usage line to stderr
  (`usage: python -m fuck.dialects <csv-file>`), return 2.
- Missing/unreadable file → `no such file: <path>` to stderr, return 1.
- `UnknownDialectError` → `str(e)` to stderr (it already names the file
  and previews <= 3 raw lines), return 1.
- Success → report to stdout, return 0:

```
file: revolut_eur.csv
dialect: revolut
transactions: 8
date range: 2026-01-03 .. 2026-03-14
sum(amount_eur): EUR 1234.56 over 8 rows
rows without EUR amount: 0
quality flags: none
skipped: 2 (state=PENDING: 1, state=REVERTED: 1)
tx_id collisions (within this file): 0
```

(Numbers above are format illustration — derive the real expectations
from the fixtures.) Details:

- `dialect:` from `sniff()` on the first `SNIFF_BYTES`; parse via
  `REGISTRY[name].parse(path)` — same seams `parse_file` uses.
- `date range:` min/max of `booked_date`, `n/a` when no transactions.
- `sum(amount_eur):` via `_eur`-style quantize to 0.01, over rows whose
  `amount_eur is not None`; count those rows.
- `quality flags:` counts per flag sorted by (-count, name), rendered
  `flag: n, flag: n`; `none` when empty. Same shape for skip reasons
  inside the `skipped:` parentheses; plain `skipped: 0` when none.
- `tx_id collisions (within this file):` `len(txs) - len({t.tx_id for t
  in txs})` — detects collisions inside this one export only. It is
  NOT the #6 Balance-stability experiment (same window exported twice,
  before and after a pending row posts, then diff the completed rows'
  Balance) — that still needs the two exports; this command reads one
  file at a time and has nothing to diff against.
- ASCII only, no trailing whitespace.

Tests (`tests/test_dialects_main.py`) — write first, red, then
implement. Reuse the existing fixtures; derive exact expected counts
from the fixture files themselves:

1. `revolut_eur.csv` → rc 0; assert the full stdout block line by line
   (dialect, transaction count, date range, sum, collisions 0, skip
   histogram matching the fixture's non-COMPLETED rows).
2. `revolut_usd.csv` → rc 0; `rows without EUR amount:` equals its row
   count; `quality flags:` shows `non_eur_unconverted`.
3. Unknown CSV (tmp_path, junk header) → rc 1; stderr names the file
   and includes its first raw line; stdout empty.
4. No args → rc 2, usage on stderr.
5. Nonexistent path → rc 1, `no such file:` on stderr.

Invoke `main([...])` directly with `capsys`; do not spawn subprocesses.

Commit: `feat: add CSV inspect command (python -m fuck.dialects)`

## Out of scope

Decision-3 additions (run date, liquid-funds line, reminder line,
income trend), README changes, CI changes, new dialects, multi-file
inspect. `fuck/demo.py` stays until the real pipeline lands.

## Verification

Full suite green (`python -m pytest`) after each commit; golden file
regenerated exactly once; CI green on the pushed branch before merge.

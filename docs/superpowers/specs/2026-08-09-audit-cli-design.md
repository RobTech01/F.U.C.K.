# Audit CLI — Design (build deferred)

**Status: approved design, deliberately not built yet.** Decision 2026-08-09:
"MVP first — the core loop must work"; the LLM-assist module is explicitly
cut from initial scope. This document exists so the build can start cold in
a future session without redoing discovery.

## Context: why this tool, and only this tool

Six discovery passes (competitive landscape, demand-side, tool quick-check,
browser-tool verification, source-export mechanics, TaxHacker evaluation)
converged on:

- The categorizer niche (V1) is served: GnuCash Bayesian matching, Actual
  Budget auto-rules, beancount smart_importer, into-ledger et al. Standalone
  CLI categorizers plateau ≈110 GitHub stars/decade. Audience for a new one: ~0.
- Subscription/fixed-cost auditing from bank data, local and trustworthy,
  is a real gap: Finanzguru does it best but is a cloud aggregator; the
  2025/26 browser-tool wave is closed-source with unverifiable "local"
  claims; waskostetmich (open source, verifiable) parses 0 of our 4 source
  dialects; Actual's "Find schedules" lacks price-change/cancel framing.
- TaxHacker: architecture reference only (pluggable LLM provider slot,
  self-host stance). Receipt-shaped, no statement parsing, no audit logic.
- **This is an n=1 tool.** Demand research found no audience for the CLI
  shape (closest prior art: 1 GitHub star). It is built for the author's
  quarterly review, full stop. No packaging, no marketing, no PyPI.

## Goal

One command, run on demand — sporadically, irregularly, by need:

```
fuck audit exports/2026-Q3/*.csv
```

reads whatever CSV exports it is given (BBBank, Revolut, Trade Republic,
PayPal), prints a one-page report along the review agenda
(`docs/finance-os.md` §5), and updates a snapshot for the next run's diff.
No run may assume when the previous one happened — any gap length is
normal operation, not an edge case.

## Non-goals (scope guard)

**Permanent non-goals:** no always-on server, no budgeting suite, no
transaction categorization beyond fixed/variable/transfer/income, no Depot
analytics (Portfolio Performance owns that), no FinTS/PSD2, no tax logic,
no encryption ceremony (nothing leaves the machine; the source CSVs
already sit in Downloads in plaintext).

**Sequencing exclusions — not for the start, built only where need
presents itself in real use:** interaction layers beyond the CLI (a UI is
a possible later delivery shell, never the core), library/PyPI packaging,
the LLM-assist module (below). Every component exists for the function it
fulfills; the core stays delivery-agnostic so any later shell wraps the
same modules unchanged.

## MVP scope: the deterministic core loop

```
parse → normalize → merge/dedupe (incl. transfer netting) → detect recurring
→ compute KPIs → diff vs. snapshot → report
```

**Cut from MVP** (modules that "fall out initially"):

- **LLM-assist classification.** Would only ever be programmatic single-shot
  classify calls (merchant string → label) via an OpenAI-compatible endpoint
  (Ollama local by default, API opt-in) — TaxHacker's provider pattern.
  Designed for, not built.
- Nudge automation (a calendar/Claude reminder does this without code).
- Anything interactive. The tool is a pure filter: files in, report out.

## Architecture (Python ≥3.10, stdlib-only)

Function-first: each module below exists for exactly one function.
`__main__.py` (the CLI) is only the first and thinnest delivery shell
around a delivery-agnostic core — a later UI, Claude skill, or library
import wraps the same modules without changing them.

```
fuck/
  dialects/     one parser per source → list[Transaction]; registry + sniffing
  normalize.py  payee cleanup, transfer detection, cross-source dedup
  detect.py     recurring/fixed-cost detection (signals below)
  kpis.py       the five quarterly numbers (savings rate, fixed-cost ratio,
                recurring margin, income streams, emergency-fund months) —
                net worth stays in Portfolio Performance, not here
  diff.py       snapshot load/compare/save (single JSON file)
  report.py     terminal one-pager along the review agenda
  __main__.py   CLI: audit / report-only / --map fallback for unknown CSVs
tests/
  fixtures/     synthetic per-dialect CSVs (accepted: synthetic first,
                validate against real headers when available)
```

### Data contract: canonical Transaction

`source, account, booked_date, amount_eur (signed Decimal), currency,
raw_amount, payee_raw, payee_norm, memo, booking_type, mandate_ref?,
creditor_id?, mcc?, tx_id (derived), quality flags`

### Dialect notes (from verified research; re-verify *(unverified)* items
against real exports before building)

- **BBBank** (Atruvia/VR family): Windows-1252, semicolon, junk pre/postamble
  around the real header (`Buchungstag;Valuta;…`), amounts with `S`/`H`
  suffix, embedded linebreaks corrupt rows → needs a cleanup pre-pass.
  Booking type in Buchungstext/Geschäftsart (`DAUERAUFTRAG`,
  `FOLGELASTSCHRIFT` = single-row recurring signals). Mandatsreferenz /
  Gläubiger-ID probably embedded in Verwendungszweck as MREF+/CRED+ tags
  *(unverified)*. Footer carries Anfangs-/Endsaldo → balance for the
  emergency-fund KPI.
- **Revolut**: comma-delimited, English headers (`Type, Product, Started
  Date, Completed Date, Description, Amount, Fee, Currency, State,
  Balance`), decimal point; drop `State != COMPLETED`; one file per
  currency pocket.
- **Trade Republic**: native Transaktionsexport since ~2026-04, one table
  for brokerage/cash/crypto/interest/Saveback/**card payments with merchant
  + MCC**. Delimiter/encoding suspected UTF-16LE + semicolon *(unverified —
  no mature parser exists anywhere; build against a real sample)*.
- **PayPal**: `Datum, Zeit, Name, Typ, Brutto, Entgelt, Netto, Guthaben,
  Transaktionscode, …` — real merchant in `Name`. Export "Guthaben-relevant"
  in 12-month chunks. `Typ` as recurring flag *(unverified)* → heuristic.

### Transfer netting (the architecturally critical piece)

Inter-account movements must cancel out or every KPI lies:
BBBank→Revolut top-ups, BBBank→TR transfers, PayPal's bank-side debits vs.
PayPal-side purchases. Approach: match candidate pairs across sources by
amount (±0.01), date window (±4 business days), and counterparty/IBAN or
known-self markers; classify matched pairs `transfer`, excluded from
income/expenses. PayPal: bank-side debit is the funding leg; PayPal-side
rows are the real expenses (merchant-level). Unmatched candidates surface
in the report's data-quality section rather than being silently guessed.

### Recurring/fixed-cost detection (deterministic, explainable)

Confidence from independent signals — single-row signals reduce the history
needed (works with irregular cadence):

1. Booking type: `DAUERAUFTRAG`/`FOLGELASTSCHRIFT` (BBBank) → certain.
2. Stable mandate reference / creditor ID where available → certain.
3. Recurrence: normalized payee, ≥2–3 hits at monthly (28–35d), quarterly
   (~91±10d), or yearly (~365±20d) intervals, amount stable or drifted
   ≤25% (drift ⇒ PRICE flag).
4. Memo/MCC hints (keywords, subscription-typical MCCs) → supporting only.

Yearly subscriptions need ≥2 years of data — reported as a stated
limitation, not guessed.

### Report (one page, mirrors the review agenda)

1. Coverage: sources seen, date ranges, gaps, unmatched transfers (honesty
   section — the report must say what it did NOT see).
2. The five KPIs with target bands.
3. Fixed costs ranked by annual cost; flags NEW / PRICE↑↓ / STOPPED
   (STOPPED suppressed when the covered window has gaps — a gap is not a
   cancellation).
4. Diff vs. last run: verification list for last quarter's logged decisions.

### Snapshot

One JSON file (`snapshot.json`, schema-versioned): last run's recurring set
+ KPI values + coverage windows. Plaintext by design (see non-goals).

### Error handling

Unknown/changed dialect → name the file, show the first raw lines, offer
`--map col=…` manual mapping; never silently skip rows — skipped/quality
issues are counted and shown in the coverage section.

### Testing

TDD. Synthetic fixtures per dialect encoding the documented quirks
(Win-1252 + S/H + preamble; UTF-16LE; State filtering; 12-month chunk
overlap → dedup). Golden-file test for the report. Property test for
transfer netting (no invented or vanished money: sum preserved).

## Open questions for the build session

1. Real header + 2–3 anonymized rows per source (owner offered synthetic
   first; collect when convenient) — resolves all *(unverified)* items.
2. TR export: confirm delimiter/encoding/columns from a real file.
3. PayPal `Typ` values for subscriptions — confirm or drop the signal.
4. BBBank: are Mandatsreferenz/Gläubiger-ID separate columns or embedded?

## Estimate

~800–1,000 LOC production + tests in the same order of magnitude.
4 dialect parsers ≈ 30–80 lines each; netting, detection, KPIs, diff,
report ≈ 550–700; CLI + state ≈ 100.

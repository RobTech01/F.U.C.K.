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
fuck audit exports/2026-Q3/*
```

reads whatever exports it is given (BBBank camt.052 XML; Revolut, Trade
Republic, PayPal CSV), prints a one-page report along the review agenda
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
  fixtures/     synthetic per-dialect exports, CSV/XML (accepted: synthetic
                first, validate against real files when available)
```

### Data contract: canonical Transaction

`source, account, booked_date, amount_eur (signed Decimal), currency,
raw_amount, payee_raw, payee_norm, memo, booking_type, mandate_ref?,
creditor_id?, mcc?, tx_id (derived), quality flags`

### Dialect notes (from verified research; re-verify *(unverified)* items
against real exports before building)

- **BBBank** (Atruvia/VR family): **camt.052.001.08 XML — verified against
  a real one-year export, 2026-08-26 (issue #6); the earlier CSV plan is
  dropped.** ISO-8859-1 declared in the prolog; the bank hands a ZIP of
  sequential single-line XML chunks that are pages of ONE report — every
  chunk stamps `PgNb=1`, only `LastPgInd` marks the last, so ordering
  comes from the `_00000N` filename suffix; no entry duplication across
  chunks. Per `Ntry`: unsigned `Amt` + `CdtDbtInd` carry the sign;
  `Sts=BOOK`; `AcctSvcrRef` present on every entry and globally unique
  across the year → the tx_id source (rank-1 immutable reference; no
  balance fallback needed). Exactly one `TxDtls` per `Ntry` throughout.
  Counterparty name + IBAN on every entry → transfer netting viable.
  `MndtId`/creditor ID as dedicated fields on every entry that carries a
  SEPA mandate at all (~1/3; parser-verified 2026-08-26: entries without
  the fields carry no `MREF`/`CRED` text either — the `Ustrd`-token
  fallback exists for other camt producers, not for BBBank). Booking type in
  `AddtlNtryInf` (`Lastschrift`, `Dauerauftrag`, `Lohn/Gehalt/Rente`,
  `Abschluss`, …) plus DK GVC codes in `BkTxCd/Prtry`. `OPBD`/`CLBD`
  balances per page → emergency-fund KPI input.
- **Revolut**: comma-delimited, English headers (`Type, Product, Started
  Date, Completed Date, Description, Amount, Fee, Currency, State,
  Balance`), decimal point; drop `State != COMPLETED`; one file per
  currency pocket.
- **Trade Republic**: native Transaktionsexport, **verified against a real
  sample 2026-08-27 (issue #6)** — plain ASCII/UTF-8, comma-delimited,
  all fields quoted (the UTF-16LE+semicolon suspicion was wrong for this
  export). 23 columns: `date` (ISO) + full `datetime`; `amount` already
  signed with separate signed `fee` and `tax` (cash impact =
  amount+fee+tax; KESt withheld at source). `fee`'s negative sign is
  verified (the real sample's IBM buy row); `tax` sign *(inferred from
  `fee`'s verified convention; the 2026-08-27 sample carries no taxed
  row — verify against the first real taxed dividend/sell and remove
  this hedge)*. `transaction_id` UUID → rank-1 tx_id;
  `counterparty_name`/`counterparty_iban` on cash movements (netting);
  `original_amount`/`original_currency`/`fx_rate` with `amount` already
  EUR-converted by TR; `mcc_code` for card payments; `category`
  (CASH/TRADING) + `type` (CUSTOMER_INPAYMENT, TRANSFER_*_INBOUND, BUY,
  DIVIDEND observed; more exist — parse type-agnostically, carry `type`
  verbatim).
- **PayPal**: consumer activity CSV, **verified against a real one-year
  export 2026-08-27 (issue #6)** — English-locale headers (`Date, Time,
  TimeZone, Name, Type, Status, Currency, Gross, Fee, Net, …,
  Transaction ID, …, Reference Txn ID, …, Balance Impact`; the spec's
  earlier German names are the other locale of the same export) with
  **German decimal-comma numbers**; UTF-8 with BOM; ~12-month windows.
  `Net` is already signed and consistent with `Balance Impact`;
  `Transaction ID` unique on every row → tx_id. **The file is PayPal's
  full internal ledger**: real merchant/P2P rows plus plumbing (funding
  legs `Bank Deposit to PP Account`/`General Card Deposit`, currency
  conversions from held foreign balances, authorization holds); in the
  verified sample `Status != Completed` is exactly the funding-leg +
  hold set, so the state filter skips the noisiest plumbing, and the
  rest parses verbatim for normalize to classify. `Reference Txn ID`
  starting `B-` is a billing-agreement ID → `mandate_ref` (PayPal's
  mandate analog; supersedes the old `Typ` heuristic). Multi-currency
  within one file → account per currency.

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
   *(BBBank: resolved 2026-08-26 via a real camt.052 export, issue #6.
   TR and PayPal still pending.)*
2. TR export: confirm delimiter/encoding/columns from a real file.
   *(Resolved 2026-08-27 via a real sample — see the TR dialect note.)*
3. PayPal `Typ` values for subscriptions — confirm or drop the signal.
   *(Resolved 2026-08-27 via a real activity export: `Reference Txn ID`
   values starting `B-` are billing-agreement IDs — a stronger,
   mandate-like recurring signal that supersedes the `Typ` heuristic.
   An earlier sample was a merchant Balance-Reconciliation report with
   0 records; see issue #6.)*
4. BBBank: are Mandatsreferenz/Gläubiger-ID separate columns or embedded?
   *(Resolved 2026-08-26: dedicated `MndtId`/creditor-ID XML fields where
   the bank fills them, else `MREF:`/`CRED:` tokens inside `Ustrd`.)*
5. Revolut re-export: do already-completed rows keep a stable Balance once earlier pending rows post? Decides whether the balance-based tx_id discriminator survives real data.

## Estimate

~800–1,000 LOC production + tests in the same order of magnitude.
4 dialect parsers ≈ 30–80 lines each; netting, detection, KPIs, diff,
report ≈ 550–700; CLI + state ≈ 100.

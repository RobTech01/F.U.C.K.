# Audit Core Slice 2: Transaction Model + Revolut Dialect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the canonical `Transaction` data contract and land the first dialect parser (Revolut, the one fully-verified format) with registry + sniffing, so every later module (netting, detection, KPI wiring) has real parsed input to consume.

**Architecture:** `fuck/model.py` holds the frozen `Transaction` dataclass (the audit-cli spec's data contract), plus `ParseResult`/`SkippedRow` (parsers never silently drop rows — skips are counted with reasons, feeding the report's future coverage section) and `derive_tx_id` (stable content hash for cross-export dedup). `fuck/dialects/` is a registry with byte-level sniffing: `parse_file()` sniffs and dispatches; unknown files raise `UnknownDialectError` carrying the filename and first raw lines (spec's error-handling rule). `fuck/dialects/revolut.py` is the first registered dialect.

**Tech Stack:** Python ≥ 3.10 stdlib only (`csv`, `dataclasses`, `datetime`, `decimal`, `hashlib`, `pathlib`); pytest.

## Global Constraints

- Runtime **stdlib-only**; pytest is the only dev tool.
- All money is `decimal.Decimal`; `None` means "not computable" — never guess (a non-EUR amount is NOT converted; it is `None` + a quality flag).
- **Never silently skip rows** (audit-cli spec): every dropped/unparseable row becomes a `SkippedRow` with a reason.
- Test data is **synthetic only**; fixture names must be plainly fake (no real merchants' unique strings, no real IBANs).
- TDD for all production code: failing test first, RED evidence, then implement, GREEN evidence.
- Every commit: Conventional Commits subject, body explains why, plus BOTH trailers verbatim:
  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01Qnfj9X98tyMN7xYtT9Rws4
  ```
- Commit sequentially on branch `claude/using-superpowers-wb260x`; do NOT push (orchestrator pushes).
- Working directory: `/home/user/F.U.C.K.`
- Spec authority order: this plan → `docs/superpowers/specs/2026-08-09-audit-cli-design.md` (data contract §"Data contract", Revolut notes §"Dialect notes", error handling §"Error handling") → `docs/finance-os.md` §4.

---

### Task 1: `fuck/model.py` — the canonical Transaction contract (TDD)

**Files:**
- Create: `fuck/model.py`
- Test: `tests/test_model.py`

**Interfaces:**
- Consumes: nothing new (stdlib + existing package).
- Produces (Task 2 relies on these exactly):

```python
@dataclass(frozen=True, slots=True)
class Transaction:
    source: str                      # dialect name, e.g. "revolut"
    account: str                     # pocket/account identity, e.g. "Revolut Current EUR"
    booked_date: datetime.date
    amount_eur: Decimal | None       # signed; None = not computable in EUR (quality flag says why)
    currency: str                    # ISO code of the row's native currency
    raw_amount: str                  # verbatim original amount cell
    payee_raw: str
    tx_id: str                       # derive_tx_id(...) result
    payee_norm: str = ""             # filled later by normalize.py, "" until then
    memo: str = ""
    booking_type: str = ""           # source's own label (DAUERAUFTRAG, CARD_PAYMENT, ...)
    mandate_ref: str | None = None
    creditor_id: str | None = None
    mcc: str | None = None
    quality: tuple[str, ...] = ()    # e.g. ("non_eur_unconverted", "fee_deducted")

@dataclass(frozen=True, slots=True)
class SkippedRow:
    reason: str                      # "state=PENDING", "state=REVERTED", "malformed"
    raw: str                         # the raw CSV line or a repr of the row dict

@dataclass(frozen=True, slots=True)
class ParseResult:
    transactions: list[Transaction]
    skipped: tuple[SkippedRow, ...] = ()

def derive_tx_id(*parts: str) -> str:
    """sha256 of "|".join(parts), first 16 hex chars. Order-sensitive.

    Dialects choose parts that are stable across re-exports of the same
    row (so overlapping exports dedup) and distinct between genuinely
    different rows (include a per-row discriminator like Balance or a
    source transaction code where available).
    """
```

- [ ] **Step 1: Write the failing tests** — `tests/test_model.py` with exactly these test cases:
  - `test_transaction_is_frozen`: constructing a minimal `Transaction` then `pytest.raises(dataclasses.FrozenInstanceError)` on attribute assignment.
  - `test_transaction_optional_fields_default`: minimal construction (only the 8 non-default fields) yields `payee_norm == ""`, `memo == ""`, `booking_type == ""`, `mandate_ref is None`, `creditor_id is None`, `mcc is None`, `quality == ()`.
  - `test_derive_tx_id_is_stable`: `derive_tx_id("a", "b", "c")` called twice returns the same 16-char lowercase hex string.
  - `test_derive_tx_id_is_order_sensitive`: `derive_tx_id("a", "b") != derive_tx_id("b", "a")`.
  - `test_derive_tx_id_distinguishes_parts_from_concatenation`: `derive_tx_id("ab", "c") != derive_tx_id("a", "bc")` (the separator matters).
  - `test_parse_result_defaults`: `ParseResult(transactions=[])` has `skipped == ()`.
- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_model.py -v 2>&1 | head -15`. Expected: `ModuleNotFoundError: No module named 'fuck.model'`. Record as RED.
- [ ] **Step 3: Implement `fuck/model.py`** — module docstring cites the audit-cli spec's data-contract section; implement exactly the interfaces above (`from __future__ import annotations`; `hashlib.sha256`; no other logic — this module is data + one hash helper, nothing else).
- [ ] **Step 4: Run full suite** — `python -m pytest`. Expected: 41 existing + 6 new = 47 passed. Record as GREEN.
- [ ] **Step 5: Commit** — subject `feat: Freeze canonical Transaction contract (model module)`; body explains: contract from the audit-cli spec's data-contract section, ParseResult/SkippedRow exist so parsers can honor "never silently skip rows", tx_id derivation is the dedup foundation; both trailers.

---

### Task 2: `fuck/dialects/` registry + Revolut parser (TDD, synthetic fixtures)

**Files:**
- Create: `fuck/dialects/__init__.py`
- Create: `fuck/dialects/revolut.py`
- Create: `tests/fixtures/revolut_eur.csv` (verbatim below)
- Create: `tests/fixtures/revolut_usd.csv` (verbatim below)
- Test: `tests/test_dialects_revolut.py`

**Interfaces:**
- Consumes from Task 1: `Transaction`, `ParseResult`, `SkippedRow`, `derive_tx_id` from `fuck.model` — exactly as specified there.
- Produces:

```python
# fuck/dialects/__init__.py
class UnknownDialectError(Exception):
    """Message contains the file name and its first raw lines (≤3)."""

REGISTRY: dict[str, object]         # {"revolut": revolut module}; explicit, no magic
def sniff(sample: bytes) -> str | None    # first matching dialect name, else None
def parse_file(path: Path) -> ParseResult # sniff (first 4096 bytes) + dispatch; raises UnknownDialectError

# fuck/dialects/revolut.py
HEADER = "Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance"
def sniffs(sample: bytes) -> bool   # utf-8 decode (errors="replace"), first line strip() == HEADER
def parse(path: Path) -> ParseResult
```

**Revolut parsing rules (from the audit-cli spec §Dialect notes + finance-os.md §4, decisions fixed here):**
- `csv.DictReader`, comma-delimited, UTF-8, decimal point.
- **State filter:** rows with `State != "COMPLETED"` become `SkippedRow(reason=f"state={State}", raw=<the row's raw line or repr>)` — never parsed, never silently dropped.
- **Malformed rows** (missing required column value or `InvalidOperation` on Decimal) become `SkippedRow(reason="malformed", raw=...)`; the parser NEVER raises per-row.
- `booked_date`: first 10 chars of `Completed Date` → `date.fromisoformat` (handles both "YYYY-MM-DD" and "YYYY-MM-DD HH:MM:SS" forms).
- **Amount:** balance-impacting value = `Decimal(Amount) - Decimal(Fee)` (Revolut reports Fee separately; a 1.00 fee on a -100.00 exchange means -101.00 left the pocket). When `Fee != 0`, add quality flag `"fee_deducted"`. `raw_amount` stays the verbatim `Amount` cell.
- **Currency honesty:** `currency` = the `Currency` cell. `amount_eur` = the computed amount only when `Currency == "EUR"`; otherwise `amount_eur = None` and quality flag `"non_eur_unconverted"` (no FX guessing — spec's None-honesty rule).
- `account` = `f"Revolut {Product} {Currency}"`; `source` = `"revolut"`; `payee_raw` = `Description`; `booking_type` = `Type`; `memo` = `""`; `mandate_ref`/`creditor_id`/`mcc` = `None`.
- `tx_id` = `derive_tx_id("revolut", account, <Completed Date verbatim>, <Amount verbatim>, <Fee verbatim>, <Currency>, <Description>, <Balance verbatim>)` — Balance is the per-row discriminator making same-day-same-amount rows distinct while staying stable across re-exports.

**Fixture `tests/fixtures/revolut_eur.csv` (verbatim, synthetic):**

```csv
Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
TOPUP,Current,2026-07-01 09:00:12,2026-07-01 09:00:14,Top-Up by *0000,900.00,0.00,EUR,COMPLETED,900.00
CARD_PAYMENT,Current,2026-07-03 08:15:02,2026-07-04 06:10:11,COFFEE CORNER SYNTH,-4.50,0.00,EUR,COMPLETED,895.50
CARD_PAYMENT,Current,2026-07-05 12:44:31,2026-07-06 03:22:47,SYNTH SUPERMARKT 42,-63.20,0.00,EUR,COMPLETED,832.30
TRANSFER,Current,2026-07-10 10:00:00,2026-07-10 10:00:02,To EUR Savings,-200.00,0.00,EUR,COMPLETED,632.30
CARD_PAYMENT,Current,2026-07-12 19:03:55,2026-07-13 02:11:09,STREAMFLIX ABO,-12.99,0.00,EUR,COMPLETED,619.31
EXCHANGE,Current,2026-07-15 14:30:00,2026-07-15 14:30:01,Exchanged to USD,-100.00,1.00,EUR,COMPLETED,518.31
CARD_REFUND,Current,2026-07-18 09:12:00,2026-07-18 09:12:03,SYNTH SUPERMARKT 42,15.00,0.00,EUR,COMPLETED,533.31
CARD_PAYMENT,Current,2026-07-20 21:40:12,,GADGET STORE ONLINE,-89.99,0.00,EUR,PENDING,533.31
CARD_PAYMENT,Current,2026-07-22 11:11:11,2026-07-22 11:11:12,DOUBLE CHARGE SHOP,-25.00,0.00,EUR,REVERTED,533.31
TOPUP,Current,2026-07-28 09:00:10,2026-07-28 09:00:12,Top-Up by *0000,400.00,0.00,EUR,COMPLETED,933.31
```

**Fixture `tests/fixtures/revolut_usd.csv` (verbatim, synthetic):**

```csv
Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
EXCHANGE,Current,2026-07-15 14:30:02,2026-07-15 14:30:03,Exchanged from EUR,108.20,0.00,USD,COMPLETED,108.20
CARD_PAYMENT,Current,2026-07-19 16:20:00,2026-07-20 01:05:44,US WEB SERVICE INC,-20.00,0.00,USD,COMPLETED,88.20
```

- [ ] **Step 1: Write the failing tests** — `tests/test_dialects_revolut.py` with exactly these cases (fixtures loaded via `Path(__file__).parent / "fixtures" / ...`):
  - `test_sniffs_accepts_revolut_header`: `revolut.sniffs(eur_fixture_bytes)` is True.
  - `test_sniffs_rejects_other_content`: False for `b"Buchungstag;Valuta;Umsatz\n1;2;3"` and for `b""`.
  - `test_parse_counts`: EUR fixture → 8 transactions, 2 skipped.
  - `test_skip_reasons_name_the_state`: skipped reasons == `{"state=PENDING", "state=REVERTED"}` (as a set).
  - `test_completed_date_becomes_booked_date`: first transaction `booked_date == date(2026, 7, 1)`.
  - `test_amounts_are_signed_decimals`: coffee row `amount_eur == Decimal("-4.50")`; salary-like top-up `Decimal("900.00")`.
  - `test_fee_is_deducted_and_flagged`: EXCHANGE row `amount_eur == Decimal("-101.00")`, `"fee_deducted" in quality`, `raw_amount == "-100.00"`.
  - `test_eur_rows_carry_no_currency_flag`: no EUR transaction has `"non_eur_unconverted"` in quality.
  - `test_non_eur_amount_is_none_and_flagged`: USD fixture → both transactions `amount_eur is None`, `currency == "USD"`, flag present.
  - `test_account_and_source_and_booking_type`: first EUR row → `source == "revolut"`, `account == "Revolut Current EUR"`, `booking_type == "TOPUP"`.
  - `test_tx_ids_unique_across_fixture`: 8 distinct `tx_id` values, each 16 lowercase hex chars.
  - `test_malformed_row_is_skipped_not_raised`: write a tmp_path CSV with the Revolut header + one row whose Amount is `"abc"` → `parse` returns 0 transactions, 1 skipped with reason `"malformed"`.
  - `test_registry_dispatch`: `dialects.parse_file(eur_fixture_path)` returns the same counts as calling `revolut.parse` directly.
  - `test_unknown_dialect_error_names_file_and_previews`: `parse_file` on a tmp_path file containing `"Datum;Betrag\n1;2\n"` raises `UnknownDialectError` whose message contains the file's name and the string `"Datum;Betrag"`.
- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_dialects_revolut.py -v 2>&1 | head -15`. Expected: `ModuleNotFoundError`/`ImportError` for `fuck.dialects`. Record as RED.
- [ ] **Step 3: Create the two fixture files verbatim**, then implement `fuck/dialects/__init__.py` and `fuck/dialects/revolut.py` per the interfaces and parsing rules above. Keep `__init__.py` to registry/sniff/dispatch only; all Revolut knowledge lives in `revolut.py`.
- [ ] **Step 4: Run full suite** — `python -m pytest`. Expected: 47 + 14 = 61 passed. Record as GREEN. Also run `python -m fuck.demo >/dev/null && echo OK` (must still exit 0 — nothing in this task touches the report path).
- [ ] **Step 5: Commit** — subject `feat: Add dialect registry and Revolut parser`; body explains: first of four dialects, the only spec-verified format; sniff-then-dispatch with UnknownDialectError previews per the spec's error-handling rule; skips counted with reasons, no silent drops; fee folded into balance impact; non-EUR amounts stay None (no FX guessing); both trailers.

---

## Post-plan verification (orchestrator, not a task)

Final whole-branch review (opus per owner directive), push `claude/using-superpowers-wb260x`, verify the CI run for the pushed head completes green via the GitHub API. Integration into `main` is the owner's decision.

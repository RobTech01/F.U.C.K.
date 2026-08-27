# Trade Republic dialect (Transaktionsexport)

**Owner provided a real TR sample 2026-08-27 (issue #6); format verified**
— see the spec's TR dialect note (amended in this commit). Third dialect
in the registry. Branch `claude/using-superpowers-wb260x`, TDD per
CLAUDE.md, ONE atomic commit:
`feat: add Trade Republic dialect (Transaktionsexport)`

Verified invariants this plan encodes: plain ASCII/UTF-8 comma CSV, all
fields quoted; `amount` already signed; separate signed `fee` and `tax`
columns (cash impact = amount + fee + tax; TR withholds KESt at source).
`fee`'s negative sign is verified (the real sample's IBM buy row); `tax`
sign *(inferred from `fee`'s verified convention; the 2026-08-27 sample
carries no taxed row — verify against the first real taxed
dividend/sell and remove this hedge)*. `transaction_id` UUID on every
row; `counterparty_name`/`counterparty_iban` on cash movements, empty on
trades; `original_amount`/`original_currency`/`fx_rate` present when TR
converted FX — `amount` is already EUR; `mcc_code` only on card
payments; no state column (everything exported is booked).

## `fuck/dialects/tr.py` (+ registry, vocab, fixture, tests)

### Interface (mirrors revolut.py / camt052.py)

- `sniffs(sample: bytes) -> bool`: decode first bytes as `utf-8-sig`
  (errors="replace"); True iff the first line starts with
  `"datetime","date","account_type"`.
- `parse(path) -> ParseResult`: `open(path, encoding="utf-8-sig",
  newline="")`, `csv.DictReader`.

### Per-row rules, in order

1. Required non-empty: `date`, `amount`, `currency`, `transaction_id`.
   (`type` was required in the first cut; the final review demoted it —
   a row with a blank source label is still real money, counted with
   `booking_type=""` rather than skipped.) Any missing/empty, or
   `date.fromisoformat` /
   `Decimal(...)` failure, or a non-finite Decimal (`is_finite()`)
   anywhere in amount/fee/tax → skip `"malformed"` (raw = the row dict
   repr, matching revolut's convention).
2. `fee` / `tax`: empty string → `Decimal("0")`; otherwise `Decimal`,
   signed as given (TR exports them negative). Same finite guard.
3. `currency == "EUR"` → `amount_eur = amount + fee + tax`. Non-EUR →
   `amount_eur = None`, quality `"non_eur_unconverted"`. (`original_*`
   columns describe FX TR already converted — no flag; the description
   carries it.)
4. Quality flags, appended in this order after the currency flag:
   `"fee_deducted"` when fee != 0; `"tax_deducted"` when tax != 0.
   **`tax_deducted` is a NEW controlled-vocabulary flag — add it to
   `fuck/model.py`'s module-docstring quality list in this commit**
   (justification: withheld KESt makes cash impact differ from the
   gross `amount`; silently folding it would hide taxes).
5. `raw_amount` = the `amount` field verbatim (gross, already signed —
   fee/tax folding is visible by comparing raw_amount to amount_eur).
6. `payee_raw` = `counterparty_name` or `name` or `""` (for trades,
   `name` is the instrument — the honest "other party").
7. `memo` = `description` verbatim; `booking_type` = `type` verbatim
   (unseen future types parse rather than break); `mcc` = `mcc_code`
   or None; `mandate_ref = creditor_id = None`; `payee_norm = ""`.
8. `booked_date` from the `date` column (not `datetime`).
9. `source = "tr"`; `account = "TR <account_type>"` with no trailing
   space when the label is empty (sample: `TR DEFAULT`);
   `tx_id = derive_tx_id("tr", transaction_id)` — the final review
   dropped the account label from the hash parts: the UUID is the
   rank-1 discriminator, and a display label in the hash would break
   re-export dedup the day TR renames it.

Registry: `REGISTRY = {"revolut": ..., "camt052": ..., "tr": tr}`.

### Fixture `tests/fixtures/tr_transaktionsexport.csv` — synthetic, always

UTF-8, header row copied verbatim from the real export's 23 columns,
every field quoted like the real file. Rows (dates ascending; all values
below are asserted):

| # | type / content | expected |
|---|----------------|----------|
| R1 | `CUSTOMER_INPAYMENT` +500.00 EUR 2026-06-01, counterparty `Testbank Owner` + IBAN `DE89370400440532013000` | +500.00, payee `Testbank Owner`, booking_type `CUSTOMER_INPAYMENT` |
| R2 | `BUY` FUND -125.00 EUR 2026-06-02, name `Test ETF EUR (Dist)`, symbol `LU0000000001`, description containing a comma (`"Savings plan execution, quantity: 1.0"`) | -125.00, payee `Test ETF EUR (Dist)` (name fallback), no flags |
| R3 | `BUY` STOCK -1000.00 EUR 2026-06-03 with fee `-1.00`, name `MÜSTER AG` | amount_eur **-1001.00**, raw_amount `-1000.00`, quality `("fee_deducted",)`, payee `MÜSTER AG` (utf-8 pin) |
| R4 | `DIVIDEND` +10.00 EUR 2026-06-04 with tax `-2.64`, original 11.40/USD/fx_rate | amount_eur **7.36**, quality `("tax_deducted",)` |
| R5 | `CARD_PAYMENT` -15.50 EUR 2026-06-05, counterparty `TESTMARKT`, mcc_code `5411` | -15.50, mcc `"5411"`, payee `TESTMARKT` (type unseen in the real sample — pins type-agnosticism) |
| R6 | `TRANSFER_INSTANT_INBOUND` +20.00 EUR 2026-06-06 | +20.00 |
| R7 | `INTEREST` 50.00 **CHF** 2026-06-07 | amount_eur None, currency `CHF`, quality `("non_eur_unconverted",)`, raw_amount `50.00` |
| S1 | row with empty `amount` | skip `malformed` |
| S2 | row with `date` = `not-a-date` | skip `malformed` |
| S3 | row with amount `NaN` | skip `malformed` |

Totals: 7 transactions, 3 skips (`malformed: 3`); EUR sum = 500 − 125
− 1001 + 7.36 − 15.50 + 20 = **-614.14 over 6 rows**; date range
2026-06-01 .. 2026-06-07. (Recompute — do not trust this arithmetic.)

### Tests `tests/test_dialects_tr.py` (~15; RED first, then implement)

1. `sniffs` True on the fixture bytes (and with a UTF-8 BOM prepended);
   False on revolut/camt052 fixture bytes and junk. Both other dialects
   still sniff themselves (three-way registry coexistence).
2. `parse`: 7 transactions / 3 skips, reasons exactly `{"malformed"}`×3.
3. Per-roster assertions R1–R7 incl. `tx_id ==
   derive_tx_id("tr", <transaction_id>)` for R1, dates as
   `datetime.date`, fee/tax folding, flag tuples exact, mcc capture,
   comma-in-description survives (R2 memo verbatim).
4. tx_ids unique.
5. `parse_file` dispatches to tr (compare tx_id lists).
6. Inspect command end-to-end on the fixture: full stdout block pinned
   (`dialect: tr`, counts, `sum(amount_eur): EUR -614.14 over 6 rows`,
   `rows without EUR amount: 1`, quality histogram in the command's
   (-count, name) sort — all counts 1, so alphabetical:
   `fee_deducted: 1, non_eur_unconverted: 1, tax_deducted: 1` —
   `skipped: 3 (malformed: 3)`, collisions 0).
7. `fuck/model.py` docstring lists `tax_deducted`.

## Out of scope

PayPal (blocked on the right export — issue #6), any classification of
TRADING vs CASH rows (normalize/detect's job), Saveback/crypto special
cases (type-agnostic parsing covers them), README changes.

## Verification

Full suite green after the commit (baseline 104 → higher). After merge,
controller runs the real TR sample (session-local, never committed):
expected 20/20 parsed, 0 skipped, 0 collisions, and the IBM buy row's
amount_eur = -10147.86 (fee folded).

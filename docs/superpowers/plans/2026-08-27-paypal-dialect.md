# PayPal dialect (activity export)

**Owner provided a real one-year activity CSV 2026-08-27 (issue #6);
format verified** — see the spec's PayPal note (amended in this commit).
Fourth and final planned dialect. Branch `claude/using-superpowers-wb260x`,
TDD per CLAUDE.md, ONE atomic commit:
`feat: add PayPal dialect (activity export)`

Verified invariants this plan encodes: English-locale headers with
**German decimal-comma numbers** (thousands dot possible: `-1.234,56`);
UTF-8 **with BOM**; all fields quoted; `Net` already signed and 100%
consistent with `Balance Impact`; `Transaction ID` unique on every row;
dates `DD/MM/YYYY`; the file is PayPal's full internal ledger — real
merchant/P2P rows plus plumbing — and in the real sample
`Status != Completed` is exactly the funding-leg + authorization-hold
set; `Reference Txn ID` starting `B-` is a billing-agreement ID;
multi-currency rows in one file (EUR + held USD balance).

## `fuck/dialects/paypal.py` (+ registry, fixture, tests)

No new vocabulary: `state=<Status>`, `malformed`, `fee_deducted`,
`non_eur_unconverted` all exist.

### Interface (mirrors the three siblings)

- `sniffs(sample: bytes) -> bool`: decode `utf-8-sig` (errors="replace");
  True iff the first line starts with `"Date","Time","TimeZone","Name"`.
  (The German-locale header variant of the same export is added only
  when a real file demands it — note this in the module docstring.)
- `parse(path) -> ParseResult`: `open(path, encoding="utf-8-sig",
  newline="")`, `csv.DictReader`.

### Number and date parsing

- `_decimal(text)`: strip thousands dots, then comma → dot:
  `Decimal(text.replace(".", "").replace(",", "."))`. `InvalidOperation`
  or non-finite → the row is `malformed`. This dialect is
  comma-decimal by verified observation; an English-locale-numbers file
  would fail loudly as malformed rows, never parse wrong by 100×.
- Dates: `datetime.strptime(row["Date"], "%d/%m/%Y").date()`;
  `ValueError` → `malformed`.

### Per-row rules, in order

1. Required non-empty: `Date`, `Net`, `Currency`, `Transaction ID`,
   `Status`. Missing/empty or unparseable → skip `"malformed"`
   (raw = row-dict repr). `Type` is NOT required (TR precedent: a blank
   source label is still real money; `booking_type=""`).
2. `Status != "Completed"` → skip `f"state={status}"` (counted). In the
   real sample that removes exactly the `Bank Deposit to PP Account`
   funding legs and the authorization holds; Completed plumbing
   (`General Card Deposit`, `General Currency Conversion`, hold
   reversals, withdrawals) parses verbatim — classifying it is
   normalize.py's job, and it is identifiable by `Type` alone.
3. `currency = Currency`; EUR → `amount_eur = _decimal(Net)` (Net IS
   the cash impact); non-EUR → `amount_eur = None`, quality
   `("non_eur_unconverted",)`.
4. `Fee`: `_decimal` when non-empty, else 0; fee != 0 → append
   `"fee_deducted"` (order: currency flag first, then fee — the
   canonical order). Note: fee is NOT folded — `Net` already includes
   it; the flag marks that `raw_amount` (gross) differs from the cash
   impact, same net semantics as the other dialects.
5. `raw_amount` = the `Gross` field verbatim (e.g. `-1.234,56`).
6. `payee_raw` = `Name` or `""` (plumbing rows keep `""` honestly).
7. `memo` = `" / ".join(dict.fromkeys(t for t in (row["Item Title"],
   row["Subject"], row["Note"]) if t))` — deduped, stable order; PayPal
   often repeats the same text across these columns.
8. `booking_type` = `Type` or `""` verbatim.
9. `mandate_ref` = `Reference Txn ID` if it starts with `"B-"` else
   None (billing agreement = PayPal's mandate analog; resolves spec
   open question 3). Non-`B-` reference IDs are deliberately NOT
   captured — the contract has no field for them; within-PayPal
   funding legs are identifiable by `Type` alone, and if normalize.py
   ever needs the exact linkage, that is a contract discussion, not a
   parser hack.
10. `creditor_id = None`, `mcc = None`, `payee_norm = ""`.
11. `booked_date` from `Date`; `source = "paypal"`;
    `account = f"PayPal {currency}"` (per-currency balances are real
    sub-accounts); `tx_id = derive_tx_id("paypal",
    row["Transaction ID"])` — 2 args, TR precedent: the ID is the
    spec-mandated rank-1 discriminator, labels stay out of the hash.

Registry: add `"paypal": paypal` (fourth entry).

### Fixture `tests/fixtures/paypal_activity.csv` — synthetic, always

Written as UTF-8 **with a real BOM** (`b"\xef\xbb\xbf"` prefix — write
bytes, and mind that the Edit tool corrupts non-trivial encodings; use
a Python write). Header row EXACTLY this line (the real export's 41
columns, verbatim — an earlier draft of this plan miscounted 40; the
literal line below is authoritative):

```
"Date","Time","TimeZone","Name","Type","Status","Currency","Gross","Fee","Net","From Email Address","To Email Address","Transaction ID","Shipping Address","Address Status","Item Title","Item ID","Shipping and Handling Amount","Insurance Amount","Sales Tax","Option 1 Name","Option 1 Value","Option 2 Name","Option 2 Value","Reference Txn ID","Invoice Number","Custom Number","Quantity","Receipt ID","Balance","Address Line 1","Address Line 2/District/Neighborhood","Town/City","State/Province/Region/County/Territory/Prefecture/Republic","Zip/Postal Code","Country","Contact Phone Number","Subject","Note","Country Code","Balance Impact"
```

All fields quoted. Synthetic emails only (`owner@example.test`,
`shop@example.test`). Rows, dates ascending (all values asserted):

| # | content | expected |
|---|---------|----------|
| R1 | `Express Checkout Payment` Completed EUR, Gross `-32,00`, Fee `0,00`, Net `-32,00`, Name `TESTSHOP GMBH`, Item Title `Bestellung 42`, 01/06/2026 | -32.00, payee `TESTSHOP GMBH`, memo `Bestellung 42`, booking_type verbatim, date 2026-06-01 |
| R2 | `Mobile Payment` Completed EUR Net `-15,00`, Note `Testnote Ü`, 02/06/2026 | -15.00, memo `Testnote Ü` (BOM+umlaut pin) |
| R3 | `PreApproved Payment Bill User Payment` Completed EUR Net `-9,99`, Reference Txn ID `B-TESTAGREEMENT01`, Item Title `Abo`, Subject `Abo`, 03/06/2026 | mandate_ref `B-TESTAGREEMENT01`, memo `Abo` (dedupe pin: identical Item Title+Subject collapse) |
| R4 | `Payment Refund` Completed EUR Gross `39,99` Net `39,99`, 04/06/2026 | +39.99 (unsigned positive) |
| R5 | `Express Checkout Payment` Completed **USD** Gross `-64,00` Net `-64,00`, 05/06/2026 | amount_eur None, currency `USD`, quality `("non_eur_unconverted",)`, raw_amount `-64,00`, account `PayPal USD` |
| R6 | `General Payment` Completed EUR Gross `10,00`, Fee `-0,35`, Net `9,65`, 06/06/2026 | amount_eur **9.65**, raw_amount `10,00`, quality `("fee_deducted",)` |
| R7 | `Mobile Payment` Completed EUR Gross `-1.234,56` Net `-1.234,56`, 07/06/2026 | **-1234.56** (thousands-dot pin) |
| S1 | `Bank Deposit to PP Account ` (note the real export's trailing space in Type) Pending EUR | skip `state=Pending` |
| S2 | row with empty `Net` | skip `malformed` |
| S3 | row with Net `NaN` (comma-format irrelevant) | skip `malformed` |
| S4 | `Account Hold for Open Authorization` Pending EUR | skip `state=Pending` |

Totals: 7 transactions, 4 skips; EUR sum = −32 − 15 − 9.99 + 39.99
+ 9.65 − 1234.56 = **-1241.91 over 6 rows**; `rows without EUR
amount: 1`; flags `fee_deducted: 1, non_eur_unconverted: 1`; skip
histogram (counts equal → alphabetical): `malformed: 2,
state=Pending: 2`; date range 2026-06-01 .. 2026-06-07. (Recompute —
do not trust this arithmetic.)

### Tests `tests/test_dialects_paypal.py` (~15; RED first)

1. `sniffs` True on the fixture bytes INCLUDING its BOM; False on the
   other three dialects' fixture bytes and junk; four-way registry
   coexistence (each fixture sniffs only its own dialect).
2. `parse`: 7 transactions / 4 skips; skip-reason multiset exactly
   `{malformed: 2, state=Pending: 2}`.
3. Per-roster assertions R1–R7 incl.
   `tx_id == derive_tx_id("paypal", <Transaction ID>)`, dates as
   `datetime.date`, the memo dedupe (R3), thousands-dot (R7).
4. tx_ids unique.
5. `parse_file` dispatch (compare tx_id lists).
6. Inspect end-to-end: full stdout block pinned per the totals above.

## Out of scope

German-locale header alias, capturing non-`B-` reference IDs, any
plumbing classification (normalize.py), README changes, no model.py
change (vocabulary already covers everything).

## Verification

Full suite green after the commit (baseline 122 → higher). After merge,
controller runs the real 120-row export (session-local, never
committed): expected 92 parsed / 28 skipped (all `state=Pending`),
0 collisions.

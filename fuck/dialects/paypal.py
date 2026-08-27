"""PayPal dialect -- consumer activity export CSV.

Parsing rules pinned in docs/superpowers/plans/2026-08-27-paypal-dialect.md,
verified against a real one-year activity export (issue #6). Fourth and
final planned dialect. English-locale headers (`Date, Time, TimeZone,
Name, Type, Status, Currency, Gross, Fee, Net, ..., Transaction ID, ...,
Reference Txn ID, ..., Balance Impact`) but German-locale decimal-comma
numbers (`_decimal` strips a thousands dot, then converts the decimal
comma) -- this dialect is comma-decimal by verified observation, so a
hypothetical English-locale-numbers file would fail loudly as malformed
rows, never parse wrong by 100x. The German-locale HEADER variant of the
same export (translated column names, same data) is added only when a
real file demands it -- out of scope here; `sniffs` matches the English
header only.

The file is PayPal's full internal ledger: real merchant/P2P rows plus
plumbing (funding legs like `Bank Deposit to PP Account`, currency
conversions, authorization holds). In the verified sample
`Status != "Completed"` is exactly that plumbing + hold set, so the state
filter removes the noisiest rows and the rest -- including Completed
plumbing such as `General Card Deposit` -- parses verbatim; classifying
it is normalize.py's job, and it is identifiable by `Type` alone. `Net`
is already PayPal's signed cash impact; `Fee` is NOT folded into it a
second time here (unlike TR's separate fee/tax columns) -- `fee_deducted`
only flags that `raw_amount` (`Gross`) differs from the cash impact, same
net semantics as the other dialects. `Reference Txn ID` starting `B-` is
a billing-agreement ID, PayPal's mandate analog.

`tx_id` hashes `Transaction ID` alone -- model.py's rank-1 discriminator,
and the one it names PayPal for explicitly: a source-native transaction
code present and unique on every row (spec-verified). `account` (built
from `Currency`, a cosmetic per-balance label) deliberately stays OUT of
the hash: if PayPal ever relabels a currency display string, mixing it in
would re-hash every row and break re-export dedup, the exact failure
model.py's docstring warns about for Revolut's balance-based fallback.
The Transaction ID alone is already stable across re-exports and globally
unique, so nothing else is needed -- same rationale as tr.py's
`transaction_id`-only hash.
"""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fuck.model import ParseResult, SkippedRow, Transaction, derive_tx_id

_SNIFF_PREFIX = '"Date","Time","TimeZone","Name"'

# Rank-1 discriminators per the plan's "Per-row rules" step 1. "Type" is
# deliberately NOT required (TR precedent, revolut.py's guard rationale
# for "Balance"): a blank source label is still real money, and must be
# counted (booking_type="") rather than skipped as malformed over a
# cosmetic field.
_REQUIRED_FIELDS = ("Date", "Net", "Currency", "Transaction ID", "Status")


def sniffs(sample: bytes) -> bool:
    # utf-8-sig strips a leading UTF-8 BOM if present and reads BOM-less
    # files identically; PayPal's own export is BOM-prefixed, so this
    # matters here more than for the other dialects.
    text = sample.decode("utf-8-sig", errors="replace")
    first_line = text.splitlines()[0] if text else ""
    return first_line.startswith(_SNIFF_PREFIX)


def _decimal(text: str) -> Decimal:
    # German-locale number: strip the thousands dot (if any), then turn
    # the decimal comma into a decimal point. "-1.234,56" -> "-1234.56".
    return Decimal(text.replace(".", "").replace(",", "."))


def parse(path: Path) -> ParseResult:
    transactions: list[Transaction] = []
    skipped: list[SkippedRow] = []

    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if any(not row.get(field) for field in _REQUIRED_FIELDS):
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            status = row["Status"]
            if status != "Completed":
                skipped.append(SkippedRow(reason=f"state={status}", raw=repr(row)))
                continue

            try:
                booked_date = datetime.strptime(row["Date"], "%d/%m/%Y").date()
                net = _decimal(row["Net"])
                fee = _decimal(row["Fee"]) if row.get("Fee") else Decimal("0")
            except (InvalidOperation, ValueError):
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            if not (net.is_finite() and fee.is_finite()):
                # Decimal("NaN") / Decimal("Infinity") parse without
                # raising InvalidOperation, but would poison
                # sum(amount_eur) and every KPI built on it.
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            currency = row["Currency"]
            quality: list[str] = []
            if currency == "EUR":
                amount_eur = net
            else:
                amount_eur = None
                quality.append("non_eur_unconverted")

            if fee != 0:
                quality.append("fee_deducted")

            memo = " / ".join(
                dict.fromkeys(
                    t
                    for t in (row["Item Title"], row["Subject"], row["Note"])
                    if t
                )
            )

            reference_txn_id = row["Reference Txn ID"]
            mandate_ref = (
                reference_txn_id if reference_txn_id.startswith("B-") else None
            )

            payee_raw = row["Name"] or ""
            account = f"PayPal {currency}"
            tx_id = derive_tx_id("paypal", row["Transaction ID"])

            transactions.append(
                Transaction(
                    source="paypal",
                    account=account,
                    booked_date=booked_date,
                    amount_eur=amount_eur,
                    currency=currency,
                    raw_amount=row["Gross"],
                    payee_raw=payee_raw,
                    tx_id=tx_id,
                    memo=memo,
                    booking_type=row["Type"] or "",
                    mandate_ref=mandate_ref,
                    creditor_id=None,
                    mcc=None,
                    quality=tuple(quality),
                )
            )

    return ParseResult(transactions=transactions, skipped=tuple(skipped))

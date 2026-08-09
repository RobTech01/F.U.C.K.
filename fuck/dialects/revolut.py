"""Revolut CSV dialect -- the first dialect, the only one spec-verified.

Parsing rules pinned in docs/superpowers/specs/2026-08-09-audit-cli-design.md
("Dialect notes") and docs/finance-os.md (section 4, source cheat sheet);
decisions are already made there and in the Task 2 brief, not re-derived
here. Comma-delimited, English headers, decimal point, one export file
per currency pocket. Non-COMPLETED rows and malformed rows are counted
skips, never silent drops, and this parser never raises per-row.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fuck.model import ParseResult, SkippedRow, Transaction, derive_tx_id

HEADER = "Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance"

# Columns a row must have a non-empty value for to be parseable. "State" is
# checked separately (its own skip reason); "Started Date" is never used.
# "Balance" is deliberately NOT required: it is only a per-row hash
# discriminator (see derive_tx_id's docstring), not transactional data --
# a COMPLETED row missing it is still real money and must be counted, not
# skipped as malformed over a cosmetic column.
_REQUIRED_FIELDS = (
    "Type",
    "Product",
    "Completed Date",
    "Description",
    "Amount",
    "Fee",
    "Currency",
)


def sniffs(sample: bytes) -> bool:
    # utf-8-sig strips a leading UTF-8 BOM if present and reads BOM-less
    # files identically, so exports saved with a BOM still sniff correctly.
    text = sample.decode("utf-8-sig", errors="replace")
    first_line = text.splitlines()[0] if text else ""
    return first_line.strip() == HEADER


def parse(path: Path) -> ParseResult:
    transactions: list[Transaction] = []
    skipped: list[SkippedRow] = []

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            state = row.get("State")
            if state is None:
                # Column missing entirely (a truncated row) -- structurally
                # broken, not a recognized state; "state=None" would be
                # misleading about what actually went wrong.
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue
            if state != "COMPLETED":
                skipped.append(SkippedRow(reason=f"state={state}", raw=repr(row)))
                continue

            if any(not row.get(field) for field in _REQUIRED_FIELDS):
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            try:
                completed_date = row["Completed Date"]
                amount_raw = row["Amount"]
                fee_raw = row["Fee"]
                booked_date = date.fromisoformat(completed_date[:10])
                fee = Decimal(fee_raw)
                amount = Decimal(amount_raw) - fee
            except (InvalidOperation, ValueError):
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            currency = row["Currency"]
            description = row["Description"]
            product = row["Product"]
            balance_raw = row.get("Balance") or ""
            booking_type = row["Type"]

            quality: list[str] = []
            if fee != 0:
                quality.append("fee_deducted")

            if currency == "EUR":
                amount_eur = amount
            else:
                amount_eur = None
                quality.append("non_eur_unconverted")

            account = f"Revolut {product} {currency}"
            tx_id = derive_tx_id(
                "revolut",
                account,
                completed_date,
                amount_raw,
                fee_raw,
                currency,
                description,
                balance_raw,
            )

            transactions.append(
                Transaction(
                    source="revolut",
                    account=account,
                    booked_date=booked_date,
                    amount_eur=amount_eur,
                    currency=currency,
                    raw_amount=amount_raw,
                    payee_raw=description,
                    tx_id=tx_id,
                    booking_type=booking_type,
                    quality=tuple(quality),
                )
            )

    return ParseResult(transactions=transactions, skipped=tuple(skipped))

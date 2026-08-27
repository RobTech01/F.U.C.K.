"""Trade Republic dialect -- native Transaktionsexport CSV.

Parsing rules pinned in docs/superpowers/plans/2026-08-27-tr-dialect.md,
verified against a real sample (issue #6). Plain UTF-8 comma CSV, every
field quoted; `amount` is already signed, and for FX rows already
converted to EUR by TR -- `original_amount`/`original_currency`/`fx_rate`
describe that conversion, not one this parser must perform. Separate
signed `fee` and `tax` columns fold into `amount_eur` (TR withholds KESt
at source, so a taxed row's cash impact differs from the gross `amount`;
`tax_deducted` flags that, same shape as `fee_deducted`). `fee`'s
negative sign is verified, via the real sample's IBM buy row; `tax`'s
is only INFERRED from `fee`'s convention -- the 2026-08-27 sample
carries no taxed row, so verify the sign against the first real taxed
dividend/sell and drop this caveat then. There is no state column:
everything TR exports is already booked, so this dialect has exactly
one skip reason, "malformed", and never raises per-row.

`tx_id` hashes `transaction_id` alone -- model.py's rank-1 discriminator,
a source-native immutable UUID present on every row -- deliberately
WITHOUT the `account` label. `account` is a display string built from
`account_type`, a cosmetic field with no bearing on which transaction
this is; if TR ever renames it, mixing it into the hash would re-hash
every row and break re-export dedup, the exact failure model.py's
docstring warns about for Revolut's balance-based fallback. The UUID
alone is already stable across re-exports and globally unique, so
nothing else is needed.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fuck.model import ParseResult, SkippedRow, Transaction, derive_tx_id

_SNIFF_PREFIX = '"datetime","date","account_type"'

# Rank-1 discriminators per the plan's "Per-row rules" step 1, minus
# "type": same guard rationale revolut.py documents for "Balance" -- a
# row missing a non-transactional column is still real money, and must
# be counted (booking_type="") rather than skipped as malformed over a
# cosmetic field. account_type is likewise deliberately NOT required
# here -- it only feeds the account label (step 9), it is not
# transactional data.
_REQUIRED_FIELDS = ("date", "amount", "currency", "transaction_id")


def sniffs(sample: bytes) -> bool:
    # utf-8-sig strips a leading UTF-8 BOM if present and reads BOM-less
    # files identically, so exports saved with a BOM still sniff correctly.
    text = sample.decode("utf-8-sig", errors="replace")
    first_line = text.splitlines()[0] if text else ""
    return first_line.startswith(_SNIFF_PREFIX)


def parse(path: Path) -> ParseResult:
    transactions: list[Transaction] = []
    skipped: list[SkippedRow] = []

    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if any(not row.get(field) for field in _REQUIRED_FIELDS):
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            try:
                booked_date = date.fromisoformat(row["date"])
                amount = Decimal(row["amount"])
                fee = Decimal(row["fee"]) if row.get("fee") else Decimal("0")
                tax = Decimal(row["tax"]) if row.get("tax") else Decimal("0")
            except (InvalidOperation, ValueError):
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            if not (amount.is_finite() and fee.is_finite() and tax.is_finite()):
                # Decimal("NaN") / Decimal("Infinity") parse without
                # raising InvalidOperation, but would poison
                # sum(amount_eur) and every KPI built on it.
                skipped.append(SkippedRow(reason="malformed", raw=repr(row)))
                continue

            currency = row["currency"]
            quality: list[str] = []
            if currency == "EUR":
                amount_eur = amount + fee + tax
            else:
                amount_eur = None
                quality.append("non_eur_unconverted")

            if fee != 0:
                quality.append("fee_deducted")
            if tax != 0:
                quality.append("tax_deducted")

            payee_raw = row.get("counterparty_name") or row.get("name") or ""
            # DictReader's restval is None, not "", so `or ""` is required
            # to avoid a literal "None" leaking into the label; join
            # instead of an f-string so an empty/missing account_type
            # produces "TR" -- never the trailing-space "TR ".
            account = " ".join(t for t in ("TR", row.get("account_type") or "") if t)
            tx_id = derive_tx_id("tr", row["transaction_id"])

            transactions.append(
                Transaction(
                    source="tr",
                    account=account,
                    booked_date=booked_date,
                    amount_eur=amount_eur,
                    currency=currency,
                    raw_amount=row["amount"],
                    payee_raw=payee_raw,
                    tx_id=tx_id,
                    memo=row.get("description") or "",
                    booking_type=row.get("type") or "",
                    mcc=row.get("mcc_code") or None,
                    quality=tuple(quality),
                )
            )

    return ParseResult(transactions=transactions, skipped=tuple(skipped))

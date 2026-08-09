"""The canonical Transaction contract.

Frozen at docs/superpowers/specs/2026-08-09-audit-cli-design.md, section
"Data contract: canonical Transaction". Dialect parsers (fuck/dialects/)
produce these; normalize.py fills payee_norm later. Data only, plus the
one hash helper dialects use to derive stable, order-sensitive IDs --
nothing else belongs here.
"""

from __future__ import annotations

import datetime
import hashlib
from dataclasses import dataclass
from decimal import Decimal


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
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]

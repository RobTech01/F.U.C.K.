"""The canonical Transaction contract.

Frozen at docs/superpowers/specs/2026-08-09-audit-cli-design.md, section
"Data contract: canonical Transaction". Dialect parsers (fuck/dialects/)
produce these; normalize.py fills payee_norm later. Data only, plus the
one hash helper dialects use to derive stable, order-sensitive IDs --
nothing else belongs here.

Controlled vocabulary (part of the frozen contract; a new value is only
introduced by extending this list first, here, before it appears in any
dialect):

- ``Transaction.quality`` flags: ``"non_eur_unconverted"``,
  ``"fee_deducted"``.
- ``SkippedRow.reason`` shapes: ``"state=<STATE>"`` (``STATE`` is the raw
  status value the source used, e.g. ``"state=PENDING"``), ``"malformed"``.
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
    different rows. Per-row discriminator, ranked -- prefer (1), fall
    back to (2) only when the source leaves no choice:

    1. A source-native immutable transaction code (e.g. PayPal's
       Transaktionscode), whenever the source provides one. PayPal MUST
       use it.
    2. A running balance, only as a last resort for sources with no row
       ID of their own (Revolut today). This is unstable: a balance is
       DERIVED state, not an identity. If an earlier PENDING row later
       posts, every later row's balance shifts, so re-exporting the same
       real transaction after that point re-hashes to a different
       tx_id -- overlapping exports would then fail to dedup.
    """
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]

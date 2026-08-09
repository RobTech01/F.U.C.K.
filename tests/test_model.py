"""Tests for the canonical Transaction contract (audit-cli spec, data
contract section). Field order in fuck/model.py matters: dialect
parsers (Task 2 onward) rely on the 8 required fields preceding the
defaulted ones exactly as declared there.
"""

import dataclasses
from datetime import date
from decimal import Decimal

import pytest

from fuck.model import ParseResult, Transaction, derive_tx_id


def _minimal_transaction(**overrides) -> Transaction:
    fields = dict(
        source="revolut",
        account="Revolut Current EUR",
        booked_date=date(2026, 7, 1),
        amount_eur=Decimal("-4.50"),
        currency="EUR",
        raw_amount="-4.50",
        payee_raw="COFFEE CORNER SYNTH",
        tx_id="0" * 16,
    )
    fields.update(overrides)
    return Transaction(**fields)


def test_transaction_is_frozen():
    tx = _minimal_transaction()
    with pytest.raises(dataclasses.FrozenInstanceError):
        tx.amount_eur = Decimal("0")


def test_transaction_optional_fields_default():
    tx = _minimal_transaction()
    assert tx.payee_norm == ""
    assert tx.memo == ""
    assert tx.booking_type == ""
    assert tx.mandate_ref is None
    assert tx.creditor_id is None
    assert tx.mcc is None
    assert tx.quality == ()


def test_derive_tx_id_is_stable():
    first = derive_tx_id("a", "b", "c")
    second = derive_tx_id("a", "b", "c")
    assert first == second
    assert len(first) == 16
    assert first == first.lower()
    int(first, 16)  # raises ValueError if not hex


def test_derive_tx_id_is_order_sensitive():
    assert derive_tx_id("a", "b") != derive_tx_id("b", "a")


def test_derive_tx_id_distinguishes_parts_from_concatenation():
    # If parts were joined without a separator, "ab"+"c" would collide
    # with "a"+"bc" -- the "|" join is what tells them apart.
    assert derive_tx_id("ab", "c") != derive_tx_id("a", "bc")


def test_parse_result_defaults():
    result = ParseResult(transactions=[])
    assert result.skipped == ()

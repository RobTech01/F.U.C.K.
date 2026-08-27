"""Tests for the PayPal (activity export) dialect parser and its registry
entry.

Fourth and final dialect, verified against a real sample (issue #6;
docs/superpowers/plans/2026-08-27-paypal-dialect.md). Fixture is
synthetic, loaded from tests/fixtures/ -- UTF-8 WITH a real BOM (PayPal's
own export convention), every field quoted, German decimal-comma numbers,
with a literal Ü (0xC3 0x9C) in row 2's Note, pinning the BOM + umlaut
decode path together.
"""

from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from fuck import dialects
from fuck.dialects import __main__ as inspect_cmd
from fuck.dialects import paypal
from fuck.model import derive_tx_id

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE = FIXTURES_DIR / "paypal_activity.csv"
REVOLUT_FIXTURE = FIXTURES_DIR / "revolut_eur.csv"
CAMT052_FIXTURE = FIXTURES_DIR / "camt052_bbbank.xml"
TR_FIXTURE = FIXTURES_DIR / "tr_transaktionsexport.csv"


@pytest.fixture(scope="module")
def result():
    return paypal.parse(FIXTURE)


def _tx_by_date(result, booked_date):
    return next(
        (t for t in result.transactions if t.booked_date == booked_date), None
    )


def test_sniffs_accepts_fixture_bytes_including_bom():
    sample = FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]
    assert paypal.sniffs(sample) is True


def test_sniffs_rejects_other_dialect_fixtures_and_junk():
    assert paypal.sniffs(REVOLUT_FIXTURE.read_bytes()) is False
    assert paypal.sniffs(CAMT052_FIXTURE.read_bytes()) is False
    assert paypal.sniffs(TR_FIXTURE.read_bytes()) is False
    assert paypal.sniffs(b"not a csv at all, just junk data") is False
    assert paypal.sniffs(b"") is False


def test_registry_four_way_sniff_coexistence():
    assert (
        dialects.sniff(REVOLUT_FIXTURE.read_bytes()[: dialects.SNIFF_BYTES])
        == "revolut"
    )
    assert (
        dialects.sniff(CAMT052_FIXTURE.read_bytes()[: dialects.SNIFF_BYTES])
        == "camt052"
    )
    assert dialects.sniff(TR_FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]) == "tr"
    assert dialects.sniff(FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]) == "paypal"


def test_parse_counts(result):
    assert len(result.transactions) == 7
    assert len(result.skipped) == 4


def test_skip_reasons_exact_multiset(result):
    assert Counter(row.reason for row in result.skipped) == Counter(
        {"malformed": 2, "state=Pending": 2}
    )


def test_r1_express_checkout_item_title_memo_and_tx_id(result):
    r1 = _tx_by_date(result, date(2026, 6, 1))
    assert r1 is not None
    assert r1.amount_eur == Decimal("-32.00")
    assert r1.currency == "EUR"
    assert r1.raw_amount == "-32,00"
    assert r1.payee_raw == "TESTSHOP GMBH"
    assert r1.memo == "Bestellung 42"
    assert r1.booking_type == "Express Checkout Payment"
    assert r1.quality == ()
    assert r1.mandate_ref is None
    assert r1.account == "PayPal EUR"
    assert r1.tx_id == derive_tx_id("paypal", "TESTTXN00000001")


def test_r2_mobile_payment_note_memo_bom_and_umlaut(result):
    r2 = _tx_by_date(result, date(2026, 6, 2))
    assert r2 is not None
    assert r2.amount_eur == Decimal("-15.00")
    assert r2.memo == "Testnote Ü"
    assert r2.quality == ()


def test_r3_billing_agreement_mandate_ref_and_memo_dedupe(result):
    r3 = _tx_by_date(result, date(2026, 6, 3))
    assert r3 is not None
    assert r3.amount_eur == Decimal("-9.99")
    assert r3.mandate_ref == "B-TESTAGREEMENT01"
    # Item Title and Subject are both "Abo" -- dedupe must collapse them,
    # never "Abo / Abo".
    assert r3.memo == "Abo"


def test_r4_refund_positive_unsigned(result):
    r4 = _tx_by_date(result, date(2026, 6, 4))
    assert r4 is not None
    assert r4.amount_eur == Decimal("39.99")
    assert r4.quality == ()


def test_r5_usd_row_unconverted(result):
    r5 = _tx_by_date(result, date(2026, 6, 5))
    assert r5 is not None
    assert r5.amount_eur is None
    assert r5.currency == "USD"
    assert r5.raw_amount == "-64,00"
    assert r5.quality == ("non_eur_unconverted",)
    assert r5.account == "PayPal USD"


def test_r6_fee_deducted_net_not_folded_again(result):
    r6 = _tx_by_date(result, date(2026, 6, 6))
    assert r6 is not None
    # Net (9.65) is already the cash impact -- NOT Gross+Fee folded a
    # second time by this parser.
    assert r6.amount_eur == Decimal("9.65")
    assert r6.raw_amount == "10,00"
    assert r6.quality == ("fee_deducted",)


def test_r7_thousands_dot_pin(result):
    r7 = _tx_by_date(result, date(2026, 6, 7))
    assert r7 is not None
    assert r7.amount_eur == Decimal("-1234.56")
    assert r7.raw_amount == "-1.234,56"
    assert r7.quality == ()


def test_tx_ids_unique_across_fixture(result):
    ids = [t.tx_id for t in result.transactions]
    assert len(set(ids)) == 7


def test_registry_dispatch_routes_to_paypal():
    direct = paypal.parse(FIXTURE)
    via_registry = dialects.parse_file(FIXTURE)
    assert [t.tx_id for t in via_registry.transactions] == [
        t.tx_id for t in direct.transactions
    ]
    assert len(via_registry.skipped) == len(direct.skipped)


def test_inspect_command_end_to_end(capsys):
    rc = inspect_cmd.main([str(FIXTURE)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert captured.out == (
        f"file: {FIXTURE.name}\n"
        "dialect: paypal\n"
        "transactions: 7\n"
        "date range: 2026-06-01 .. 2026-06-07\n"
        "sum(amount_eur): EUR -1241.91 over 6 rows\n"
        "rows without EUR amount: 1\n"
        "quality flags: fee_deducted: 1, non_eur_unconverted: 1\n"
        "skipped: 4 (malformed: 2, state=Pending: 2)\n"
        "tx_id collisions (within this file): 0\n"
    )

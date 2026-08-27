"""Tests for the Trade Republic (Transaktionsexport) dialect parser and
its registry entry.

Third dialect, verified against a real sample (issue #6;
docs/superpowers/plans/2026-08-27-tr-dialect.md). Fixture is synthetic,
loaded from tests/fixtures/ -- plain UTF-8, every field quoted, with a
literal Ü (0xC3 0x9C) in the R3 payee, pinning the utf-8-sig decode path.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from fuck import dialects
from fuck.dialects import __main__ as inspect_cmd
from fuck.dialects import tr
from fuck.model import derive_tx_id

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE = FIXTURES_DIR / "tr_transaktionsexport.csv"
REVOLUT_FIXTURE = FIXTURES_DIR / "revolut_eur.csv"
CAMT052_FIXTURE = FIXTURES_DIR / "camt052_bbbank.xml"


@pytest.fixture(scope="module")
def result():
    return tr.parse(FIXTURE)


def _tx_by_raw_amount(result, raw_amount, currency="EUR"):
    return next(
        t
        for t in result.transactions
        if t.raw_amount == raw_amount and t.currency == currency
    )


def test_sniffs_accepts_fixture_and_bom_prefixed():
    sample = FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]
    assert tr.sniffs(sample) is True
    assert tr.sniffs(b"\xef\xbb\xbf" + sample) is True


def test_sniffs_rejects_other_dialect_fixtures_and_junk():
    assert tr.sniffs(REVOLUT_FIXTURE.read_bytes()) is False
    assert tr.sniffs(CAMT052_FIXTURE.read_bytes()) is False
    assert tr.sniffs(b"not a csv at all, just junk data") is False
    assert tr.sniffs(b"") is False


def test_registry_three_way_sniff_coexistence():
    assert (
        dialects.sniff(REVOLUT_FIXTURE.read_bytes()[: dialects.SNIFF_BYTES])
        == "revolut"
    )
    assert (
        dialects.sniff(CAMT052_FIXTURE.read_bytes()[: dialects.SNIFF_BYTES])
        == "camt052"
    )
    assert dialects.sniff(FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]) == "tr"


def test_parse_counts(result):
    assert len(result.transactions) == 7
    assert len(result.skipped) == 3


def test_skip_reasons_exact_set(result):
    reasons = {row.reason for row in result.skipped}
    assert reasons == {"malformed"}


def test_r1_customer_inpayment_uses_counterparty_and_tx_id(result):
    r1 = _tx_by_raw_amount(result, "500.00")
    assert r1.amount_eur == Decimal("500.00")
    assert r1.booked_date == date(2026, 6, 1)
    assert r1.payee_raw == "Testbank Owner"
    assert r1.booking_type == "CUSTOMER_INPAYMENT"
    assert r1.quality == ()
    assert r1.account == "TR DEFAULT"
    assert r1.tx_id == derive_tx_id(
        "tr", "TR DEFAULT", "11111111-1111-4111-8111-111111111101"
    )


def test_r2_buy_fund_name_fallback_no_flags_and_comma_memo(result):
    r2 = _tx_by_raw_amount(result, "-125.00")
    assert r2.amount_eur == Decimal("-125.00")
    assert r2.booked_date == date(2026, 6, 2)
    assert r2.payee_raw == "Test ETF EUR (Dist)"
    assert r2.quality == ()
    assert r2.memo == "Savings plan execution, quantity: 1.0"


def test_r3_buy_stock_fee_folded_and_umlaut_payee(result):
    r3 = _tx_by_raw_amount(result, "-1000.00")
    assert r3.amount_eur == Decimal("-1001.00")
    assert r3.booked_date == date(2026, 6, 3)
    assert r3.payee_raw == "MÜSTER AG"
    assert r3.quality == ("fee_deducted",)


def test_r4_dividend_tax_folded(result):
    r4 = _tx_by_raw_amount(result, "10.00")
    assert r4.amount_eur == Decimal("7.36")
    assert r4.booked_date == date(2026, 6, 4)
    assert r4.quality == ("tax_deducted",)


def test_r5_card_payment_mcc_and_counterparty_payee(result):
    r5 = _tx_by_raw_amount(result, "-15.50")
    assert r5.amount_eur == Decimal("-15.50")
    assert r5.booked_date == date(2026, 6, 5)
    assert r5.payee_raw == "TESTMARKT"
    assert r5.mcc == "5411"
    assert r5.booking_type == "CARD_PAYMENT"
    assert r5.quality == ()


def test_r6_transfer_instant_inbound(result):
    r6 = _tx_by_raw_amount(result, "20.00")
    assert r6.amount_eur == Decimal("20.00")
    assert r6.booked_date == date(2026, 6, 6)
    assert r6.quality == ()


def test_r7_chf_amount_unconverted(result):
    r7 = _tx_by_raw_amount(result, "50.00", currency="CHF")
    assert r7.amount_eur is None
    assert r7.currency == "CHF"
    assert r7.booked_date == date(2026, 6, 7)
    assert r7.quality == ("non_eur_unconverted",)


def test_non_finite_amount_is_skipped_malformed(result):
    # Decimal("NaN") parses without raising InvalidOperation, so it needs
    # its own explicit finiteness guard or it becomes a Transaction that
    # poisons sum(amount_eur) and every KPI built on it.
    assert not any(t.raw_amount == "NaN" for t in result.transactions)
    malformed_raw = [row.raw for row in result.skipped if row.reason == "malformed"]
    assert any("111111111110" in raw for raw in malformed_raw)


def test_tx_ids_unique_across_fixture(result):
    ids = [t.tx_id for t in result.transactions]
    assert len(set(ids)) == 7


def test_registry_dispatch_routes_to_tr():
    direct = tr.parse(FIXTURE)
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
        "dialect: tr\n"
        "transactions: 7\n"
        "date range: 2026-06-01 .. 2026-06-07\n"
        "sum(amount_eur): EUR -614.14 over 6 rows\n"
        "rows without EUR amount: 1\n"
        "quality flags: fee_deducted: 1, non_eur_unconverted: 1, tax_deducted: 1\n"
        "skipped: 3 (malformed: 3)\n"
        "tx_id collisions (within this file): 0\n"
    )


def test_model_docstring_lists_tax_deducted():
    import fuck.model as model

    assert "tax_deducted" in model.__doc__

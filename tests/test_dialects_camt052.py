"""Tests for the camt.052 (BBBank) dialect parser and its registry entry.

Second dialect, verified against a real one-year camt.052 export (issue
#6; docs/superpowers/specs/2026-08-09-audit-cli-design.md, "Dialect
notes"). Fixture is synthetic, loaded from tests/fixtures/ -- built as
real ISO-8859-1 bytes with a literal Ü (0xDC) in the E2 payee, pinning
the declared-encoding parse path.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from fuck import dialects
from fuck.dialects import __main__ as inspect_cmd
from fuck.dialects import camt052
from fuck.model import derive_tx_id

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE = FIXTURES_DIR / "camt052_bbbank.xml"
REVOLUT_FIXTURE = FIXTURES_DIR / "revolut_eur.csv"

CAMT053_SAMPLE = (
    b'<?xml version="1.0" encoding="ISO-8859-1"?>'
    b'<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">'
    b"<BkToCstmrStmt/></Document>"
)


@pytest.fixture(scope="module")
def result():
    return camt052.parse(FIXTURE)


def _tx_by_raw_amount(result, raw_amount, currency="EUR"):
    return next(
        tx
        for tx in result.transactions
        if tx.raw_amount == raw_amount and tx.currency == currency
    )


def test_sniffs_accepts_camt052_fixture():
    sample = FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]
    assert camt052.sniffs(sample) is True


def test_sniffs_rejects_other_content():
    assert camt052.sniffs(CAMT053_SAMPLE) is False
    assert camt052.sniffs(REVOLUT_FIXTURE.read_bytes()) is False
    assert camt052.sniffs(b"not xml at all, just junk data") is False
    assert camt052.sniffs(b"") is False


def test_registry_still_sniffs_revolut():
    sample = REVOLUT_FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]
    assert dialects.sniff(sample) == "revolut"


def test_registry_sniffs_camt052():
    sample = FIXTURE.read_bytes()[: dialects.SNIFF_BYTES]
    assert dialects.sniff(sample) == "camt052"


def test_parse_counts(result):
    assert len(result.transactions) == 7
    assert len(result.skipped) == 5


def test_skip_reasons_exact_set(result):
    reasons = {row.reason for row in result.skipped}
    assert reasons == {"state=PDNG", "malformed", "unsupported=multi-txdtls"}


def test_source_and_account_for_every_transaction(result):
    for tx in result.transactions:
        assert tx.source == "testbank"
        assert tx.account == "Testbank 3000"


def test_e1_lastschrift_dedicated_mandate_and_creditor(result):
    e1 = _tx_by_raw_amount(result, "-12.34")
    assert e1.amount_eur == Decimal("-12.34")
    assert e1.currency == "EUR"
    assert e1.booked_date == date(2026, 1, 5)
    assert e1.payee_raw == "MUSTERSHOP GMBH"
    assert e1.mandate_ref == "MANDATE-XYZ-1"
    assert e1.creditor_id == "DE98ZZZ09999999999"
    assert e1.booking_type == "Lastschrift"
    assert e1.tx_id == derive_tx_id(
        "testbank", "DE89370400440532013000", "2026010500000001000"
    )


def test_e2_umlaut_payee_and_split_ustrd_memo_fallback(result):
    e2 = _tx_by_raw_amount(result, "-9.99")
    assert e2.amount_eur == Decimal("-9.99")
    assert e2.payee_raw == "MÜLLER VERSICHERUNG AG"
    assert e2.booked_date == date(2026, 1, 12)
    assert e2.memo == (
        "Rechnung 998/2026 MREF: MREF-FALLBACK-77 CRED: DE11ZZZ00000000011"
    )
    assert e2.mandate_ref == "MREF-FALLBACK-77"
    assert e2.creditor_id == "DE11ZZZ00000000011"


def test_e3_dauerauftrag_no_mandate(result):
    e3 = _tx_by_raw_amount(result, "-350.00")
    assert e3.amount_eur == Decimal("-350.00")
    assert e3.booking_type == "Dauerauftrag"
    assert e3.mandate_ref is None


def test_e4_credit_uses_debtor_as_other_party(result):
    e4 = _tx_by_raw_amount(result, "2500.00")
    assert e4.amount_eur == Decimal("2500.00")
    assert e4.payee_raw == "ARBEITGEBER AG"


def test_e5_no_txdtls_falls_back_to_addtlntryinf(result):
    e5 = _tx_by_raw_amount(result, "-4.50")
    assert e5.amount_eur == Decimal("-4.50")
    assert e5.payee_raw == "Abschluss"
    assert e5.memo == ""
    assert e5.mandate_ref is None


def test_e6_non_eur_amount_is_none_and_flagged(result):
    e6 = _tx_by_raw_amount(result, "100.00", currency="USD")
    assert e6.amount_eur is None
    assert e6.currency == "USD"
    assert e6.quality == ("non_eur_unconverted",)
    assert e6.raw_amount == "100.00"


def test_e7_non_eur_debit_and_empty_ustrd_none_text_guard(result):
    # DBIT (not CRDT, unlike E6) so raw_amount's sign is also pinned here;
    # the empty <Ustrd/> sibling's .text is None, exercising the memo
    # join's `u.text or ""` guard rather than assuming every Ustrd has text.
    e7 = _tx_by_raw_amount(result, "-55.00", currency="USD")
    assert e7.amount_eur is None
    assert e7.currency == "USD"
    assert e7.quality == ("non_eur_unconverted",)
    assert e7.raw_amount == "-55.00"
    assert e7.memo == "Invoice USD-2026-0077"


def test_non_finite_amount_is_skipped_malformed(result):
    # Decimal("NaN") parses without raising InvalidOperation, so it needs
    # its own explicit finiteness guard or it becomes a Transaction that
    # poisons sum(amount_eur) and every KPI built on it.
    assert not any(tx.raw_amount == "-NaN" for tx in result.transactions)
    malformed_raw = [row.raw for row in result.skipped if row.reason == "malformed"]
    assert any('Ccy="EUR">NaN<' in raw for raw in malformed_raw)


def test_missing_sts_element_is_skipped_malformed(result):
    malformed_raw = [row.raw for row in result.skipped if row.reason == "malformed"]
    assert any("2026021500000012000" in raw for raw in malformed_raw)


def test_tx_ids_unique_across_fixture(result):
    ids = [tx.tx_id for tx in result.transactions]
    assert len(set(ids)) == 7


def test_registry_dispatch_routes_to_camt052():
    direct = camt052.parse(FIXTURE)
    via_registry = dialects.parse_file(FIXTURE)
    assert [tx.tx_id for tx in via_registry.transactions] == [
        tx.tx_id for tx in direct.transactions
    ]
    assert len(via_registry.skipped) == len(direct.skipped)


def test_inspect_command_end_to_end(capsys):
    rc = inspect_cmd.main([str(FIXTURE)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert captured.out == (
        f"file: {FIXTURE.name}\n"
        "dialect: camt052\n"
        "transactions: 7\n"
        "date range: 2026-01-05 .. 2026-02-12\n"
        "sum(amount_eur): EUR 2123.17 over 5 rows\n"
        "rows without EUR amount: 2\n"
        "quality flags: non_eur_unconverted: 2\n"
        "skipped: 5 (malformed: 3, state=PDNG: 1, unsupported=multi-txdtls: 1)\n"
        "tx_id collisions (within this file): 0\n"
    )


def test_model_docstring_lists_multi_txdtls_skip_reason():
    import fuck.model as model

    assert "unsupported=multi-txdtls" in model.__doc__

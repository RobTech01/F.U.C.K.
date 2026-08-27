"""Tests for the PayPal (activity export) dialect parser and its registry
entry.

Fourth and final dialect, verified against a real sample (issue #6;
docs/superpowers/plans/2026-08-27-paypal-dialect.md). Fixture is
synthetic, loaded from tests/fixtures/ -- UTF-8 WITH a real BOM (PayPal's
own export convention), every field quoted, German decimal-comma numbers,
with a literal Ü (0xC3 0x9C) in row 2's Note, pinning the BOM + umlaut
decode path together.
"""

import csv
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


def _tx_by_payee(result, payee_raw):
    return next((t for t in result.transactions if t.payee_raw == payee_raw), None)


def _skip_reason(result, marker):
    # Skipped rows only carry reason + repr(row); find one by a unique
    # Transaction ID substring in that repr.
    row = next((r for r in result.skipped if marker in r.raw), None)
    return row.reason if row is not None else None


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
    assert len(result.skipped) == 6


def test_skip_reasons_exact_multiset(result):
    assert Counter(row.reason for row in result.skipped) == Counter(
        {"malformed": 3, "state=Pending": 3}
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


def test_dot_decimal_amount_fails_loudly_as_malformed(result):
    # English-locale "32.00" on an otherwise-identical English-header row
    # must never parse as 100x/1000x the real amount -- the number-shape
    # guard rejects it before any conversion happens.
    assert _skip_reason(result, "TESTTXN00000012") == "malformed"
    skipped_tx_id = derive_tx_id("paypal", "TESTTXN00000012")
    assert not any(t.tx_id == skipped_tx_id for t in result.transactions)


def test_pending_row_skipped_by_state_before_date_ever_parsed(result):
    # Skip order is required-fields -> state -> parse guards: this row's
    # Date ("99/99/2026") would fail strptime, but state is judged first,
    # so it must report state=Pending, never malformed.
    assert _skip_reason(result, "TESTTXN00000013") == "state=Pending"


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
        "skipped: 6 (malformed: 3, state=Pending: 3)\n"
        "tx_id collisions (within this file): 0\n"
    )


# -- Coverage rows: robustness edge cases the main (verified) fixture
# doesn't exercise. Minimal header covering only the columns paypal.parse()
# actually reads -- not the real export's 41 columns (test_inspect_command
# _end_to_end and the R1-R7 tests above already pin fidelity to the real
# header; this one is scoped to edge cases, tr-style: see
# tests/test_dialects_tr.py's _COVERAGE_HEADER/_COVERAGE_ROWS).
_COVERAGE_HEADER = [
    "Date",
    "Status",
    "Currency",
    "Transaction ID",
    "Net",
    "Gross",
    "Fee",
    "Name",
    "Type",
    "Item Title",
    "Subject",
    "Note",
    "Reference Txn ID",
]

_COVERAGE_ROWS = [
    # (a) invalid calendar date (month=13) -- pins the ValueError arm /
    # strptime strictness, distinct from the shape-guard's InvalidOperation.
    {
        "Date": "31/13/2025",
        "Status": "Completed",
        "Currency": "EUR",
        "Transaction ID": "COVBADDATE0001",
        "Net": "5,00",
        "Gross": "5,00",
        "Fee": "0,00",
        "Name": "Bad Date Shop",
        "Type": "General Payment",
        "Item Title": "",
        "Subject": "",
        "Note": "",
        "Reference Txn ID": "",
    },
    # (b) empty Gross, valid Net -- raw_amount must fall back to the Net
    # cell verbatim, never "".
    {
        "Date": "01/07/2026",
        "Status": "Completed",
        "Currency": "EUR",
        "Transaction ID": "COVEMPTYGROSS1",
        "Net": "12,34",
        "Gross": "",
        "Fee": "0,00",
        "Name": "Fallback Shop",
        "Type": "General Payment",
        "Item Title": "",
        "Subject": "",
        "Note": "",
        "Reference Txn ID": "",
    },
    # (c) distinct Item Title + Note, non-"B-" Reference Txn ID -- both
    # memo parts join, and a real (non-billing-agreement) reference must
    # not be mistaken for a mandate.
    {
        "Date": "02/07/2026",
        "Status": "Completed",
        "Currency": "EUR",
        "Transaction ID": "COVTITLENOTE01",
        "Net": "-3,50",
        "Gross": "-3,50",
        "Fee": "0,00",
        "Name": "Title Note Shop",
        "Type": "General Payment",
        "Item Title": "Gadget",
        "Subject": "",
        "Note": "Spare part",
        "Reference Txn ID": "TESTREFPLAIN01",
    },
    # (d) USD (unconverted) + a deducted Fee -- both quality flags apply,
    # in non_eur-then-fee order.
    {
        "Date": "03/07/2026",
        "Status": "Completed",
        "Currency": "USD",
        "Transaction ID": "COVUSDFEEFLAG1",
        "Net": "9,65",
        "Gross": "10,00",
        "Fee": "-0,35",
        "Name": "Fee Usd Shop",
        "Type": "General Payment",
        "Item Title": "",
        "Subject": "",
        "Note": "",
        "Reference Txn ID": "",
    },
]


@pytest.fixture
def coverage_result(tmp_path):
    path = tmp_path / "paypal_coverage.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_COVERAGE_HEADER, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(_COVERAGE_ROWS)
    return paypal.parse(path)


def test_invalid_calendar_date_is_malformed_not_raised(coverage_result):
    assert len(coverage_result.skipped) == 1
    assert coverage_result.skipped[0].reason == "malformed"
    assert "Bad Date Shop" in coverage_result.skipped[0].raw


def test_empty_gross_falls_back_to_net_for_raw_amount(coverage_result):
    tx = _tx_by_payee(coverage_result, "Fallback Shop")
    assert tx is not None
    assert tx.raw_amount == "12,34"
    assert tx.amount_eur == Decimal("12.34")


def test_distinct_title_and_note_join_with_non_billing_reference(coverage_result):
    tx = _tx_by_payee(coverage_result, "Title Note Shop")
    assert tx is not None
    assert tx.memo == "Gadget / Spare part"
    assert tx.mandate_ref is None


def test_usd_row_with_fee_flags_non_eur_then_fee_deducted(coverage_result):
    tx = _tx_by_payee(coverage_result, "Fee Usd Shop")
    assert tx is not None
    assert tx.quality == ("non_eur_unconverted", "fee_deducted")


def test_short_row_never_raises_and_parses_when_required_cells_present(tmp_path):
    # DictReader's restval for a row shorter than the header is None, not
    # "" -- a short row must never raise (e.g. AttributeError from calling
    # .startswith on a None Reference Txn ID).
    path = tmp_path / "short_row.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
        writer.writerow(_COVERAGE_HEADER)
        # Row ends right after the required cells (Date, Status, Currency,
        # Transaction ID, Net) -- every later column, including Reference
        # Txn ID, is missing entirely from this row (restval None).
        writer.writerow(["04/07/2026", "Completed", "EUR", "COVSHORTROW001", "7,00"])

    result = paypal.parse(path)

    assert result.skipped == ()
    assert len(result.transactions) == 1
    tx = result.transactions[0]
    assert tx.memo == ""
    assert tx.mandate_ref is None
    assert tx.payee_raw == ""
    assert tx.booking_type == ""
    assert tx.raw_amount == "7,00"


def test_missing_item_title_column_entirely_parses_normally(tmp_path):
    # A file whose header starts like the real export but omits the "Item
    # Title" column altogether -- a narrower column set, not a short row.
    # row["Item Title"] must not raise KeyError.
    header = [
        "Date",
        "Time",
        "TimeZone",
        "Name",
        "Type",
        "Status",
        "Currency",
        "Gross",
        "Fee",
        "Net",
        "Transaction ID",
        "Reference Txn ID",
        "Subject",
        "Note",
    ]
    path = tmp_path / "no_item_title.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerow(
            {
                "Date": "05/07/2026",
                "Time": "09:00:00",
                "TimeZone": "CEST",
                "Name": "No Title Shop",
                "Type": "General Payment",
                "Status": "Completed",
                "Currency": "EUR",
                "Gross": "8,00",
                "Fee": "0,00",
                "Net": "8,00",
                "Transaction ID": "COVNOITEMTITLE1",
                "Reference Txn ID": "",
                "Subject": "Order note",
                "Note": "Extra note",
            }
        )

    result = paypal.parse(path)

    assert result.skipped == ()
    assert len(result.transactions) == 1
    assert result.transactions[0].memo == "Order note / Extra note"

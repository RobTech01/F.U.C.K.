"""Tests for the Revolut dialect parser and the dialects registry.

Revolut is the first of four planned dialects and the only one verified
against the audit-cli spec's dialect notes (docs/superpowers/specs/
2026-08-09-audit-cli-design.md, "Dialect notes"; docs/finance-os.md
section 4). Fixtures are synthetic, loaded from tests/fixtures/.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from fuck import dialects
from fuck.dialects import revolut

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EUR_FIXTURE = FIXTURES_DIR / "revolut_eur.csv"
USD_FIXTURE = FIXTURES_DIR / "revolut_usd.csv"
WINDOW_FIXTURE = FIXTURES_DIR / "revolut_eur_window.csv"


@pytest.fixture(scope="module")
def eur_result():
    return revolut.parse(EUR_FIXTURE)


@pytest.fixture(scope="module")
def usd_result():
    return revolut.parse(USD_FIXTURE)


@pytest.fixture(scope="module")
def window_result():
    return revolut.parse(WINDOW_FIXTURE)


def test_sniffs_accepts_revolut_header():
    assert revolut.sniffs(EUR_FIXTURE.read_bytes()) is True


def test_sniffs_rejects_other_content():
    assert revolut.sniffs(b"Buchungstag;Valuta;Umsatz\n1;2;3") is False
    assert revolut.sniffs(b"") is False


def test_parse_counts(eur_result):
    assert len(eur_result.transactions) == 8
    assert len(eur_result.skipped) == 2


def test_skip_reasons_name_the_state(eur_result):
    reasons = {row.reason for row in eur_result.skipped}
    assert reasons == {"state=PENDING", "state=REVERTED"}


def test_completed_date_becomes_booked_date(eur_result):
    assert eur_result.transactions[0].booked_date == date(2026, 7, 1)


def test_amounts_are_signed_decimals(eur_result):
    coffee = next(
        tx for tx in eur_result.transactions if tx.payee_raw == "COFFEE CORNER SYNTH"
    )
    topup = next(tx for tx in eur_result.transactions if tx.raw_amount == "900.00")
    assert coffee.amount_eur == Decimal("-4.50")
    assert topup.amount_eur == Decimal("900.00")


def test_fee_is_deducted_and_flagged(eur_result):
    exchange = next(
        tx for tx in eur_result.transactions if tx.payee_raw == "Exchanged to USD"
    )
    assert exchange.amount_eur == Decimal("-101.00")
    assert "fee_deducted" in exchange.quality
    assert exchange.raw_amount == "-100.00"


def test_eur_rows_carry_no_currency_flag(eur_result):
    assert all(
        "non_eur_unconverted" not in tx.quality for tx in eur_result.transactions
    )


def test_non_eur_amount_is_none_and_flagged(usd_result):
    assert len(usd_result.transactions) == 2
    for tx in usd_result.transactions:
        assert tx.amount_eur is None
        assert tx.currency == "USD"
        assert "non_eur_unconverted" in tx.quality


def test_account_and_source_and_booking_type(eur_result):
    first = eur_result.transactions[0]
    assert first.source == "revolut"
    assert first.account == "Revolut Current EUR"
    assert first.booking_type == "TOPUP"


def test_tx_ids_unique_across_fixture(eur_result):
    ids = [tx.tx_id for tx in eur_result.transactions]
    assert len(set(ids)) == 8
    for tx_id in ids:
        assert len(tx_id) == 16
        assert tx_id == tx_id.lower()
        int(tx_id, 16)  # raises ValueError if not hex


def test_reexport_window_tx_ids_are_subset(eur_result, window_result):
    # revolut_eur_window.csv is a byte-identical 3-row slice of
    # revolut_eur.csv (coffee, supermarkt, transfer) standing in for an
    # overlapping re-export chunk. Regression pin for the balance-based
    # tx_id discriminator: as long as Balance hasn't shifted (see
    # derive_tx_id's docstring), the same rows re-hash identically, so
    # overlapping exports dedup instead of minting duplicate transactions.
    window_ids = {tx.tx_id for tx in window_result.transactions}
    full_ids = {tx.tx_id for tx in eur_result.transactions}
    assert len(window_ids) == 3
    assert window_ids <= full_ids


def test_malformed_row_is_skipped_not_raised(tmp_path):
    bad_csv = tmp_path / "revolut_bad.csv"
    bad_csv.write_text(
        revolut.HEADER + "\n"
        "CARD_PAYMENT,Current,2026-07-01 00:00:00,2026-07-01 00:00:01,"
        "BAD ROW,abc,0.00,EUR,COMPLETED,100.00\n",
        encoding="utf-8",
    )
    result = revolut.parse(bad_csv)
    assert len(result.transactions) == 0
    assert len(result.skipped) == 1
    assert result.skipped[0].reason == "malformed"


def test_empty_balance_row_still_parses(tmp_path):
    # Balance is a hash discriminator, not transactional data -- a
    # COMPLETED row missing it is still real money and must be counted.
    csv_path = tmp_path / "revolut_empty_balance.csv"
    csv_path.write_text(
        revolut.HEADER + "\n"
        "CARD_PAYMENT,Current,2026-07-01 00:00:00,2026-07-01 00:00:01,"
        "SYNTH ROW,-10.00,0.00,EUR,COMPLETED,\n",
        encoding="utf-8",
    )
    result = revolut.parse(csv_path)
    assert len(result.transactions) == 1
    assert len(result.skipped) == 0
    assert len(result.transactions[0].tx_id) == 16
    int(result.transactions[0].tx_id, 16)  # raises ValueError if not hex


def test_truncated_row_is_malformed(tmp_path):
    # A row missing the State column entirely (not just an unexpected
    # value in it) is structurally broken, not a recognized state -- it
    # must be "malformed", not the misleading "state=None".
    bad_csv = tmp_path / "revolut_truncated.csv"
    bad_csv.write_text(
        revolut.HEADER + "\n" "CARD_PAYMENT,Current,2026-07-01 00:00:00\n",
        encoding="utf-8",
    )
    result = revolut.parse(bad_csv)
    assert len(result.transactions) == 0
    assert len(result.skipped) == 1
    assert result.skipped[0].reason == "malformed"


def test_registry_dispatch():
    direct = revolut.parse(EUR_FIXTURE)
    via_registry = dialects.parse_file(EUR_FIXTURE)
    assert len(via_registry.transactions) == len(direct.transactions)
    assert len(via_registry.skipped) == len(direct.skipped)


def test_unknown_dialect_error_names_file_and_previews(tmp_path):
    mystery = tmp_path / "mystery.csv"
    mystery.write_text("Datum;Betrag\n1;2\n", encoding="utf-8")
    with pytest.raises(dialects.UnknownDialectError) as exc_info:
        dialects.parse_file(mystery)
    message = str(exc_info.value)
    assert mystery.name in message
    assert "Datum;Betrag" in message


def test_bom_prefixed_export_is_recognized(tmp_path):
    bom_csv = tmp_path / "revolut_bom.csv"
    bom_csv.write_bytes(b"\xef\xbb\xbf" + EUR_FIXTURE.read_bytes())
    sample = bom_csv.read_bytes()[: dialects.SNIFF_BYTES]
    assert dialects.sniff(sample) == "revolut"
    result = dialects.parse_file(bom_csv)
    assert len(result.transactions) == 8
    assert len(result.skipped) == 2

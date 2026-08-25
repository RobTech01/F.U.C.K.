"""Tests for the CSV inspect command: `python -m fuck.dialects <file>`.

Issue #6's verification harness: feed a real export, see how the
parser performs, without any CLI framework. Fixtures are the source
of truth for expected counts -- derived from tests/fixtures/ and
cross-checked against tests/test_dialects_revolut.py, never guessed.
"""

from pathlib import Path

from fuck.dialects import __main__ as inspect_cmd

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EUR_FIXTURE = FIXTURES_DIR / "revolut_eur.csv"
USD_FIXTURE = FIXTURES_DIR / "revolut_usd.csv"


def test_revolut_eur_fixture_full_report(capsys):
    rc = inspect_cmd.main([str(EUR_FIXTURE)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert captured.out == (
        "file: revolut_eur.csv\n"
        "dialect: revolut\n"
        "transactions: 8\n"
        "date range: 2026-07-01 .. 2026-07-28\n"
        "sum(amount_eur): EUR 933.31 over 8 rows\n"
        "rows without EUR amount: 0\n"
        "quality flags: fee_deducted: 1\n"
        "skipped: 2 (state=PENDING: 1, state=REVERTED: 1)\n"
        "tx_id collisions (within this file): 0\n"
    )


def test_revolut_usd_fixture_reports_unconverted_rows(capsys):
    # Both rows in this fixture are USD; neither carries a EUR amount, so
    # the sum line must say n/a rather than render a fabricated EUR 0.00.
    rc = inspect_cmd.main([str(USD_FIXTURE)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.err == ""
    assert captured.out == (
        "file: revolut_usd.csv\n"
        "dialect: revolut\n"
        "transactions: 2\n"
        "date range: 2026-07-15 .. 2026-07-20\n"
        "sum(amount_eur): n/a (no row carries an EUR amount)\n"
        "rows without EUR amount: 2\n"
        "quality flags: non_eur_unconverted: 2\n"
        "skipped: 0\n"
        "tx_id collisions (within this file): 0\n"
    )


def test_non_utf8_body_reports_cannot_read_as_utf8(tmp_path, capsys):
    # Header is plain ASCII and sniffs fine; the body is CP1252, not
    # UTF-8, so the unknown-dialect path never fires and the failure
    # must be caught where the real parse happens, not left as a bare
    # traceback.
    header = EUR_FIXTURE.read_bytes().splitlines()[0]
    bad_row = (
        b"CARD_PAYMENT,Current,2026-07-03 08:15:02,2026-07-04 06:10:11,"
        b"CAF\xc9 M\xdcLLER,-4.50,0.00,EUR,COMPLETED,895.50"
    )
    bad_file = tmp_path / "cp1252.csv"
    bad_file.write_bytes(header + b"\n" + bad_row + b"\n")

    rc = inspect_cmd.main([str(bad_file)])
    captured = capsys.readouterr()

    assert rc == 1
    assert captured.out == ""
    assert bad_file.name in captured.err
    assert "UTF-8" in captured.err


def test_unknown_dialect_reports_to_stderr_and_empty_stdout(tmp_path, capsys):
    mystery = tmp_path / "mystery.csv"
    mystery.write_text("Datum;Betrag\n1;2\n", encoding="utf-8")
    rc = inspect_cmd.main([str(mystery)])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert mystery.name in captured.err
    assert "Datum;Betrag" in captured.err


def test_no_args_prints_usage_and_returns_2(capsys):
    rc = inspect_cmd.main([])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert captured.err == "usage: python -m fuck.dialects <csv-file>\n"


def test_nonexistent_path_reports_to_stderr(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.csv"
    rc = inspect_cmd.main([str(missing)])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert captured.err.startswith("cannot read")


def test_directory_path_reports_cannot_read(tmp_path, capsys):
    # A directory is not "no such file" -- it exists. The OSError message
    # must say so honestly instead of guessing a reason.
    rc = inspect_cmd.main([str(tmp_path)])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert captured.err.startswith("cannot read")


def test_header_only_file_reports_zero_transactions(tmp_path, capsys):
    header = EUR_FIXTURE.read_bytes().splitlines()[0]
    empty = tmp_path / "header_only.csv"
    empty.write_bytes(header + b"\n")

    rc = inspect_cmd.main([str(empty)])
    captured = capsys.readouterr()

    assert rc == 0
    lines = captured.out.splitlines()
    assert "transactions: 0" in lines
    assert "date range: n/a" in lines
    assert "quality flags: none" in lines
    assert "skipped: 0" in lines


def test_skipped_reasons_sorted_by_count_descending(tmp_path, capsys):
    # Two rows made malformed (blanking a different required field on
    # each, mutated from real fixture rows) plus one PENDING row, copied
    # verbatim from the fixture -- 3 skips, "malformed" (2) must sort
    # ahead of "state=PENDING" (1).
    header = "Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance"
    malformed_blank_amount = (
        "TOPUP,Current,2026-07-01 09:00:12,2026-07-01 09:00:14,"
        "Top-Up by *0000,,0.00,EUR,COMPLETED,900.00"
    )
    malformed_blank_fee = (
        "CARD_PAYMENT,Current,2026-07-03 08:15:02,2026-07-04 06:10:11,"
        "COFFEE CORNER SYNTH,-4.50,,EUR,COMPLETED,895.50"
    )
    pending_row = next(
        line
        for line in EUR_FIXTURE.read_text(encoding="utf-8").splitlines()
        if ",PENDING," in line
    )
    rows = tmp_path / "skips.csv"
    rows.write_text(
        "\n".join(
            [header, malformed_blank_amount, malformed_blank_fee, pending_row, ""]
        ),
        encoding="utf-8",
    )

    rc = inspect_cmd.main([str(rows)])
    captured = capsys.readouterr()

    assert rc == 0
    assert "skipped: 3 (malformed: 2, state=PENDING: 1)" in captured.out.splitlines()

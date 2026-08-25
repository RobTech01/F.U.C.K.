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
        "tx_id collisions: 0\n"
    )


def test_revolut_usd_fixture_reports_unconverted_rows(capsys):
    rc = inspect_cmd.main([str(USD_FIXTURE)])
    captured = capsys.readouterr()
    assert rc == 0
    lines = captured.out.splitlines()
    assert "rows without EUR amount: 2" in lines
    quality_line = next(line for line in lines if line.startswith("quality flags:"))
    assert "non_eur_unconverted" in quality_line


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
    assert "no such file:" in captured.err

"""Golden-file + behavior tests for the simulated one-pager."""

from decimal import Decimal
from pathlib import Path

from fuck import demo, report

GOLDEN = Path(__file__).parent / "golden" / "demo_report.txt"

D = Decimal


def render_minimal(**overrides):
    args = dict(
        banner="!! TEST !!",
        net_income=D("1000"),
        expenses=D("800"),
        fixed_costs=D("300"),
        recurring_income=D("1000"),
        income_by_source={"salary": D("1000")},
        liquid_funds=D("4000"),
        avg_monthly_expenses=D("800"),
    )
    args.update(overrides)
    return report.render(**args)


def test_demo_page_matches_golden_file():
    assert demo.demo_page() == GOLDEN.read_text(encoding="utf-8")


def test_demo_page_declares_itself_simulated():
    page = demo.demo_page()
    assert "SIMULATED DATA" in page
    # The banner must come before any number is shown.
    assert page.index("SIMULATED DATA") < page.index("savings rate")


def test_unbuilt_sections_are_stubs_not_fake_data():
    page = demo.demo_page()
    assert "[not built yet -- fixed-cost ranking needs detect.py]" in page
    assert "[not built yet -- decision verification needs diff.py]" in page


def _kpi_line(page: str, label: str) -> str:
    return next(
        line for line in page.splitlines() if line.strip().startswith(label)
    )


def test_not_computable_kpis_render_as_na_without_bands():
    page = render_minimal(net_income=D("0"), avg_monthly_expenses=D("0"))
    # Value slot AND band slot must both read n/a — a KPI that cannot be
    # computed must not carry a band verdict. (The static target text on
    # each line contains band words, so substring checks on the whole
    # page would lie; check the two slots instead.)
    for label in ("savings rate", "fixed-cost ratio", "emergency fund"):
        line = _kpi_line(page, label)
        assert line.count("n/a") == 2, line


def test_page_is_ascii_only():
    demo.demo_page().encode("ascii")  # raises UnicodeEncodeError if violated

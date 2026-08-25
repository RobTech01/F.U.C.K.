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
    # computed must not carry a band verdict.
    for label in ("savings rate", "fixed-cost ratio", "emergency fund"):
        line = _kpi_line(page, label)
        assert line.count("n/a") == 2, line


def test_page_is_ascii_only():
    demo.demo_page().encode("ascii")  # raises UnicodeEncodeError if violated


def test_section_two_legend_lines_present_and_kpi_lines_omit_inline_target():
    # Verdict 2B: target hints move out of the KPI lines into a compact
    # legend at the end of section 2.
    page = render_minimal()
    assert (
        "   target: savings >=10% floor / 15-20% solid / 20%+ wealth-building"
        in page
    )
    assert (
        "           fixed   <30% comfortable / <=50% ceiling / >65% critical"
        in page
    )
    assert "           fund    3-6 months, a band not a maximum" in page
    for label in (
        "savings rate",
        "fixed-cost ratio",
        "recurring margin",
        "income streams",
        "emergency fund",
    ):
        line = _kpi_line(page, label)
        assert "target:" not in line, line


def test_no_rendered_line_has_trailing_whitespace():
    for page in (demo.demo_page(), render_minimal()):
        for line in page.splitlines():
            assert line == line.rstrip(), repr(line)


def test_section_two_lines_fit_in_72_columns():
    page = demo.demo_page()
    lines = page.splitlines()
    start = lines.index("2. The five numbers")
    end = lines.index("3. Fixed costs by annual cost")
    for line in lines[start:end]:
        assert len(line) <= 72, (len(line), line)


def test_income_streams_renders_na_for_empty_sources():
    # Deferred from #11.
    page = render_minimal(income_by_source={})
    line = _kpi_line(page, "income streams")
    assert line == "   income streams     n/a"


def test_negative_savings_rate_is_shown_and_banded_honestly():
    # Deferred from #11: a negative rate is real signal, not hidden.
    page = render_minimal(net_income=D("1000"), expenses=D("1200"))
    line = _kpi_line(page, "savings rate")
    assert line == "   savings rate           -20.0%  below_floor"

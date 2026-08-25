"""Terminal one-pager along the review agenda (docs/finance-os.md section 5).

Aggregates in, page out. Sections whose upstream modules do not exist
yet render as explicit stubs — never as fake findings.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

from fuck import kpis

WIDTH = 72
NOT_BUILT_FIXED = "[not built yet -- fixed-cost ranking needs detect.py]"
NOT_BUILT_DIFF = "[not built yet -- decision verification needs diff.py]"


def _pct(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{(value * 100).quantize(Decimal('0.1'))}%"


def _eur(value: Decimal) -> str:
    return f"EUR {value.quantize(Decimal('0.01'))}"


def _months(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return f"{value.quantize(Decimal('0.1'))} months"


def render(
    *,
    banner: str,
    net_income: Decimal,
    expenses: Decimal,
    fixed_costs: Decimal,
    recurring_income: Decimal,
    income_by_source: Mapping[str, Decimal],
    liquid_funds: Decimal,
    avg_monthly_expenses: Decimal,
) -> str:
    rate = kpis.savings_rate(net_income, expenses)
    fixed_ratio = kpis.fixed_cost_ratio(fixed_costs, net_income)
    margin = kpis.recurring_margin(recurring_income, fixed_costs)
    streams = kpis.income_streams(income_by_source)
    months = kpis.emergency_fund_months(liquid_funds, avg_monthly_expenses)

    rate_band = kpis.savings_rate_band(rate) if rate is not None else "n/a"
    fixed_band = (
        kpis.fixed_cost_band(fixed_ratio) if fixed_ratio is not None else "n/a"
    )
    months_band = (
        kpis.emergency_fund_band(months) if months is not None else "n/a"
    )
    streams_text = (
        ", ".join(f"{name} {_pct(share)}" for name, share in streams.items())
        if streams
        else "n/a"
    )

    lines = [
        "=" * WIDTH,
        "F.U.C.K. -- quarterly audit one-pager",
        "=" * WIDTH,
        "",
        "1. Coverage",
        f"   {banner}",
        "",
        "2. The five numbers",
        f"   savings rate       {_pct(rate):>8}  {rate_band}",
        f"   fixed-cost ratio   {_pct(fixed_ratio):>8}  {fixed_band}",
        f"   recurring margin   {_eur(margin):>12}  (trend, judged run over run)",
        f"   income streams     {streams_text}",
        f"   emergency fund     {_months(months):>10}  {months_band}",
        "",
        "   target: savings >=10% floor / 15-20% solid / 20%+ wealth-building",
        "           fixed   <30% comfortable / <=50% ceiling / >65% critical",
        "           fund    3-6 months, a band not a maximum",
        "",
        "3. Fixed costs by annual cost",
        f"   {NOT_BUILT_FIXED}",
        "",
        "4. Diff vs. last run",
        f"   {NOT_BUILT_DIFF}",
        "",
    ]
    return "\n".join(lines)

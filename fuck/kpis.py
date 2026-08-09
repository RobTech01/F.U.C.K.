"""The five quarterly numbers (docs/finance-os.md section 1).

Pure arithmetic over explicit aggregates. Deliberately not bound to the
Transaction contract yet — that gets frozen with the first dialect
parser. All money and ratios are Decimal. None means "not computable";
the report surfaces that instead of guessing.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping


def savings_rate(net_income: Decimal, expenses: Decimal) -> Decimal | None:
    """(net income - expenses) / net income; None when net income <= 0."""
    if net_income <= 0:
        return None
    return (net_income - expenses) / net_income


def savings_rate_band(rate: Decimal) -> str:
    if rate < Decimal("0.10"):
        return "below_floor"
    if rate < Decimal("0.15"):
        return "floor"
    if rate < Decimal("0.20"):
        return "solid"
    return "wealth_building"


def fixed_cost_ratio(fixed_costs: Decimal, net_income: Decimal) -> Decimal | None:
    """fixed costs / net income; None when net income <= 0."""
    if net_income <= 0:
        return None
    return fixed_costs / net_income


def fixed_cost_band(ratio: Decimal) -> str:
    if ratio < Decimal("0.30"):
        return "comfortable"
    if ratio <= Decimal("0.50"):
        return "acceptable"
    if ratio <= Decimal("0.65"):
        return "over_ceiling"
    return "critical"


def recurring_margin(recurring_income: Decimal, fixed_costs: Decimal) -> Decimal:
    """recurring income - fixed costs; subscription creep erodes this."""
    return recurring_income - fixed_costs


def income_streams(income_by_source: Mapping[str, Decimal]) -> dict[str, Decimal]:
    """Share of total income per source, largest first (ties: by name).

    Non-positive sources are dropped; {} when nothing positive remains —
    no concentration statement is better than a wrong one.
    """
    positive = {k: v for k, v in income_by_source.items() if v > 0}
    total = sum(positive.values(), Decimal("0"))
    if total == 0:
        return {}
    shares = {k: v / total for k, v in positive.items()}
    return dict(sorted(shares.items(), key=lambda kv: (-kv[1], kv[0])))


def emergency_fund_months(
    liquid_funds: Decimal, avg_monthly_expenses: Decimal
) -> Decimal | None:
    """liquid funds / average monthly expenses; None when expenses <= 0."""
    if avg_monthly_expenses <= 0:
        return None
    return liquid_funds / avg_monthly_expenses


def emergency_fund_band(months: Decimal) -> str:
    if months < 3:
        return "under_band"
    if months <= 6:
        return "in_band"
    return "above_band"

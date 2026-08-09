"""Tests for the five quarterly numbers (docs/finance-os.md section 1).

Band boundaries are pinned exactly as the finance-os doc states them;
if a boundary test surprises you, the doc wins, not the test.
"""

from decimal import Decimal

import pytest

from fuck import kpis

D = Decimal


class TestSavingsRate:
    def test_formula(self):
        assert kpis.savings_rate(D("3000"), D("2400")) == D("0.2")

    def test_overspending_goes_negative(self):
        assert kpis.savings_rate(D("2000"), D("2500")) == D("-0.25")

    @pytest.mark.parametrize("net_income", [D("0"), D("-1")])
    def test_not_computable_without_positive_income(self, net_income):
        assert kpis.savings_rate(net_income, D("100")) is None

    @pytest.mark.parametrize(
        ("rate", "band"),
        [
            (D("-0.05"), "below_floor"),
            (D("0.0999"), "below_floor"),
            (D("0.10"), "floor"),  # ">=10% floor" is inclusive
            (D("0.1499"), "floor"),
            (D("0.15"), "solid"),
            (D("0.1999"), "solid"),
            (D("0.20"), "wealth_building"),
            (D("0.50"), "wealth_building"),
        ],
    )
    def test_bands(self, rate, band):
        assert kpis.savings_rate_band(rate) == band


class TestFixedCostRatio:
    def test_formula(self):
        assert kpis.fixed_cost_ratio(D("900"), D("3000")) == D("0.3")

    @pytest.mark.parametrize("net_income", [D("0"), D("-500")])
    def test_not_computable_without_positive_income(self, net_income):
        assert kpis.fixed_cost_ratio(D("900"), net_income) is None

    @pytest.mark.parametrize(
        ("ratio", "band"),
        [
            (D("0.2999"), "comfortable"),
            (D("0.30"), "acceptable"),
            (D("0.50"), "acceptable"),  # "50% ceiling" — the ceiling itself is acceptable
            (D("0.5001"), "over_ceiling"),
            (D("0.65"), "over_ceiling"),
            (D("0.6501"), "critical"),  # ">65% critical" is exclusive
        ],
    )
    def test_bands(self, ratio, band):
        assert kpis.fixed_cost_band(ratio) == band


class TestRecurringMargin:
    def test_formula(self):
        assert kpis.recurring_margin(D("2600"), D("950")) == D("1650")

    def test_can_go_negative(self):
        assert kpis.recurring_margin(D("800"), D("950")) == D("-150")


class TestIncomeStreams:
    def test_shares_sum_to_one_and_order_largest_first(self):
        # Amounts chosen so shares are exact Decimals (no precision noise).
        shares = kpis.income_streams(
            {"freelance": D("2500"), "salary": D("7500")}
        )
        assert list(shares) == ["salary", "freelance"]
        assert shares["salary"] == D("0.75")
        assert shares["freelance"] == D("0.25")
        assert sum(shares.values()) == D("1")

    def test_equal_shares_tie_break_alphabetically(self):
        shares = kpis.income_streams({"b": D("50"), "a": D("50")})
        assert list(shares) == ["a", "b"]

    def test_non_positive_sources_are_dropped(self):
        shares = kpis.income_streams(
            {"salary": D("100"), "refund_noise": D("0"), "correction": D("-20")}
        )
        assert list(shares) == ["salary"]
        assert shares["salary"] == D("1")

    @pytest.mark.parametrize(
        "sources", [{}, {"a": D("0")}, {"a": D("-5"), "b": D("-1")}]
    )
    def test_no_positive_income_yields_empty(self, sources):
        assert kpis.income_streams(sources) == {}


class TestEmergencyFund:
    def test_formula(self):
        assert kpis.emergency_fund_months(D("12000"), D("2400")) == D("5")

    @pytest.mark.parametrize("avg", [D("0"), D("-100")])
    def test_not_computable_without_positive_expenses(self, avg):
        assert kpis.emergency_fund_months(D("12000"), avg) is None

    @pytest.mark.parametrize(
        ("months", "band"),
        [
            (D("2.99"), "under_band"),
            (D("3"), "in_band"),
            (D("6"), "in_band"),  # "3-6 months as a band" — both ends inclusive
            (D("6.01"), "above_band"),  # cash above the band is drag
        ],
    )
    def test_bands(self, months, band):
        assert kpis.emergency_fund_band(months) == band

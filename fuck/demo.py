"""Smoke-and-mirrors preview -- THROWAWAY.

Renders the one-pager from canned SYNTHETIC aggregates so the report
design can be judged before any parser exists. Every number below is
invented. Delete this module the day the real pipeline feeds
report.render(). Run: python -m fuck.demo
"""

from decimal import Decimal

from fuck import report

BANNER = (
    "!! SIMULATED DATA -- synthetic demo numbers; no real exports were read !!"
)


def demo_page() -> str:
    return report.render(
        banner=BANNER,
        net_income=Decimal("8400.00"),
        expenses=Decimal("7000.00"),
        fixed_costs=Decimal("3080.00"),
        recurring_income=Decimal("7800.00"),
        income_by_source={
            "salary": Decimal("7800.00"),
            "freelance": Decimal("600.00"),
        },
        liquid_funds=Decimal("12600.00"),
        avg_monthly_expenses=Decimal("2333.33"),
    )


def main() -> None:
    print(demo_page())


if __name__ == "__main__":
    main()

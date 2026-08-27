"""CSV inspect command: `python -m fuck.dialects <export-file>`.

Issue #6's verification harness -- feed a real export, see how the
parser performs, without any CLI framework. Read-only: nothing is
written anywhere, so real financial data never leaves the terminal.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from fuck import dialects

USAGE = "usage: python -m fuck.dialects <export-file>"


def _eur(value: Decimal) -> str:
    return f"EUR {value.quantize(Decimal('0.01'))}"


def _counts(items: Iterable[str]) -> str:
    tally = Counter(items)
    if not tally:
        return "none"
    ordered = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))
    return ", ".join(f"{name}: {n}" for name, n in ordered)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 2

    path = Path(argv[0])
    try:
        with open(path, "rb") as fh:
            sample = fh.read(dialects.SNIFF_BYTES)
    except OSError as e:
        print(f"cannot read {path}: {e}", file=sys.stderr)
        return 1

    name = dialects.sniff(sample)
    if name is None:
        try:
            dialects.parse_file(path)
        except dialects.UnknownDialectError as e:
            print(str(e), file=sys.stderr)
            return 1

    try:
        result = dialects.REGISTRY[name].parse(path)
    except UnicodeDecodeError as e:
        print(f"cannot read {path.name} as UTF-8: {e}", file=sys.stderr)
        return 1
    except ET.ParseError as e:
        print(f"cannot parse {path.name}: {e}", file=sys.stderr)
        return 1

    txs = result.transactions
    eur_amounts = [tx.amount_eur for tx in txs if tx.amount_eur is not None]
    dates = [tx.booked_date for tx in txs]
    date_range = f"{min(dates)} .. {max(dates)}" if dates else "n/a"
    tx_ids = {tx.tx_id for tx in txs}
    skipped = result.skipped

    if eur_amounts:
        sum_line = (
            f"sum(amount_eur): {_eur(sum(eur_amounts, Decimal('0')))}"
            f" over {len(eur_amounts)} rows"
        )
    else:
        sum_line = "sum(amount_eur): n/a (no row carries an EUR amount)"

    lines = [
        f"file: {path.name}",
        f"dialect: {name}",
        f"transactions: {len(txs)}",
        f"date range: {date_range}",
        sum_line,
        f"rows without EUR amount: {len(txs) - len(eur_amounts)}",
        f"quality flags: {_counts(flag for tx in txs for flag in tx.quality)}",
        "skipped: {}{}".format(
            len(skipped),
            f" ({_counts(row.reason for row in skipped)})" if skipped else "",
        ),
        f"tx_id collisions (within this file): {len(txs) - len(tx_ids)}",
    ]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

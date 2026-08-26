"""Dialect registry: sniff a CSV sample, then dispatch to its parser.

Registry-only knowledge lives here -- explicit, no magic (no
auto-discovery or plugin scanning). Per-source parsing rules live in
each dialect module (fuck/dialects/revolut.py, ...). Error handling
follows docs/superpowers/specs/2026-08-09-audit-cli-design.md, "Error
handling": an unknown or changed dialect must name the file and show
its first raw lines rather than fail silently or guess a mapping.
"""

from __future__ import annotations

import types
from pathlib import Path

from fuck.dialects import camt052, revolut
from fuck.model import ParseResult

SNIFF_BYTES = 4096
PREVIEW_LINES = 3
PREVIEW_BYTES = 300

REGISTRY: dict[str, types.ModuleType] = {
    "revolut": revolut,
    "camt052": camt052,
}


class UnknownDialectError(Exception):
    """Message contains the file name and its first raw lines (≤3)."""


def sniff(sample: bytes) -> str | None:
    for name, dialect in REGISTRY.items():
        if dialect.sniffs(sample):
            return name
    return None


def parse_file(path: Path) -> ParseResult:
    with open(path, "rb") as fh:
        sample = fh.read(SNIFF_BYTES)

    name = sniff(sample)
    if name is None:
        preview = "\n".join(
            sample.decode("utf-8", errors="replace").splitlines()[:PREVIEW_LINES]
        )
        if len(preview) > PREVIEW_BYTES:
            preview = preview[:PREVIEW_BYTES] + " [truncated]"
        if preview:
            message = f"Unrecognized dialect for {path.name}; first lines:\n{preview}"
        else:
            message = f"Unrecognized dialect for {path.name}"
        raise UnknownDialectError(message)

    return REGISTRY[name].parse(path)

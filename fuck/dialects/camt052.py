"""camt.052 XML dialect -- BBBank (Atruvia/VR family) exports.

Parsing rules pinned in docs/superpowers/specs/2026-08-09-audit-cli-design.md
("Dialect notes", BBBank entry), verified against a real one-year camt.052
export (issue #6). ISO-8859-1 declared in the prolog; unsigned Amt +
CdtDbtInd carry the sign; Sts=BOOK marks a real posting; AcctSvcrRef is
present on every entry and globally unique across a year, so it is the
tx_id source (no balance fallback needed, unlike Revolut). Namespace is
read from the parsed root's own tag rather than hardcoded, so a sibling
schema version (e.g. .001.02) with the same shape still parses. Skipped
rows are counted, never silently dropped, and this parser never raises
per-entry.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fuck.model import ParseResult, SkippedRow, Transaction, derive_tx_id

_NAMESPACE_PREFIX = b"urn:iso:std:iso:20022:tech:xsd:camt.052."

_MREF_RE = re.compile(r"MREF: (\S+)")
_CRED_RE = re.compile(r"CRED: (\S+)")


def sniffs(sample: bytes) -> bool:
    # utf-8-sig strips a leading UTF-8 BOM if present; errors="replace"
    # keeps this safe even when the 4096-byte sniff window cuts through
    # non-ASCII bytes deeper in an ISO-8859-1 document -- the prolog and
    # namespace URI we look for are always plain ASCII regardless.
    text = sample.decode("utf-8-sig", errors="replace").lstrip()
    return text.startswith("<?xml") and _NAMESPACE_PREFIX.decode("ascii") in text


def _qpath(path: str, ns: str) -> str:
    return "/".join(f"{{{ns}}}{part}" for part in path.split("/"))


def _text(elem: ET.Element, path: str, ns: str) -> str | None:
    found = elem.find(_qpath(path, ns))
    return found.text if found is not None else None


def parse(path: Path) -> ParseResult:
    tree = ET.parse(path)  # honors the prolog's declared encoding
    root = tree.getroot()
    ns = root.tag[root.tag.index("{") + 1 : root.tag.index("}")]

    transactions: list[Transaction] = []
    skipped: list[SkippedRow] = []

    for rpt in root.findall(_qpath("BkToCstmrAcctRpt/Rpt", ns)):
        iban = _text(rpt, "Acct/Id/IBAN", ns) or ""
        svcr = _text(rpt, "Acct/Svcr/FinInstnId/Nm", ns) or ""
        first_token = svcr.split()[0] if svcr else ""
        source = first_token.lower() if svcr else "camt052"

        if not svcr:
            account = "camt052"
        elif not iban:
            account = source
        else:
            account = f"{first_token} {iban[-4:]}"

        for ntry in rpt.findall(_qpath("Ntry", ns)):
            raw = ET.tostring(ntry, encoding="unicode")

            # 1. Sts checks.
            sts = _text(ntry, "Sts/Cd", ns)
            if sts is None:
                skipped.append(SkippedRow(reason="malformed", raw=raw))
                continue
            if sts != "BOOK":
                skipped.append(SkippedRow(reason=f"state={sts}", raw=raw))
                continue

            # 2. TxDtls count.
            txdtls_list = ntry.findall(_qpath("NtryDtls/TxDtls", ns))
            if len(txdtls_list) > 1:
                skipped.append(
                    SkippedRow(reason="unsupported=multi-txdtls", raw=raw)
                )
                continue
            txdtls = txdtls_list[0] if txdtls_list else None

            # 3. Required fields / malformed.
            amt_elem = ntry.find(_qpath("Amt", ns))
            cdt_dbt_ind = _text(ntry, "CdtDbtInd", ns)
            bookg_dt = _text(ntry, "BookgDt/Dt", ns)
            acct_svcr_ref = _text(ntry, "AcctSvcrRef", ns)

            if (
                amt_elem is None
                or not amt_elem.text
                or "Ccy" not in amt_elem.attrib
                or cdt_dbt_ind not in ("DBIT", "CRDT")
                or not bookg_dt
                or not acct_svcr_ref
            ):
                skipped.append(SkippedRow(reason="malformed", raw=raw))
                continue

            amt_text = amt_elem.text
            currency = amt_elem.attrib["Ccy"]

            try:
                amount = Decimal(amt_text)
                booked_date = date.fromisoformat(bookg_dt[:10])
            except (InvalidOperation, ValueError):
                skipped.append(SkippedRow(reason="malformed", raw=raw))
                continue

            # 4. Sign -- must survive even when amount_eur ends up None.
            is_debit = cdt_dbt_ind == "DBIT"
            if is_debit:
                amount = -amount
                raw_amount = f"-{amt_text}"
            else:
                raw_amount = amt_text

            quality: list[str] = []
            if currency == "EUR":
                amount_eur = amount
            else:
                amount_eur = None
                quality.append("non_eur_unconverted")

            # 5. tx_id -- AcctSvcrRef is the verified rank-1 discriminator.
            tx_id = derive_tx_id(source, iban, acct_svcr_ref)

            # 6. payee_raw -- the *other* party, else AddtlNtryInf, else "".
            addtl_info = _text(ntry, "AddtlNtryInf", ns) or ""
            payee_raw = None
            if txdtls is not None:
                other_party_path = (
                    "RltdPties/Cdtr/Pty/Nm" if is_debit else "RltdPties/Dbtr/Pty/Nm"
                )
                payee_raw = _text(txdtls, other_party_path, ns)
            payee_raw = payee_raw or addtl_info or ""

            # 7. memo -- verbatim join, no strip (bank pre-wraps in-band).
            if txdtls is not None:
                ustrd_elems = txdtls.findall(_qpath("RmtInf/Ustrd", ns))
                memo = "".join(u.text or "" for u in ustrd_elems)
            else:
                memo = ""

            # 8. booking_type.
            booking_type = addtl_info

            # 9. mandate_ref / creditor_id -- dedicated field, else memo regex.
            mandate_ref = _text(txdtls, "Refs/MndtId", ns) if txdtls is not None else None
            if mandate_ref is None:
                m = _MREF_RE.search(memo)
                mandate_ref = m.group(1) if m else None

            creditor_id = (
                _text(txdtls, "RltdPties/Cdtr/Pty/Id/PrvtId/Othr/Id", ns)
                if txdtls is not None
                else None
            )
            if creditor_id is None:
                m = _CRED_RE.search(memo)
                creditor_id = m.group(1) if m else None

            transactions.append(
                Transaction(
                    source=source,
                    account=account,
                    booked_date=booked_date,
                    amount_eur=amount_eur,
                    currency=currency,
                    raw_amount=raw_amount,
                    payee_raw=payee_raw,
                    tx_id=tx_id,
                    payee_norm="",
                    memo=memo,
                    booking_type=booking_type,
                    mandate_ref=mandate_ref,
                    creditor_id=creditor_id,
                    mcc=None,
                    quality=tuple(quality),
                )
            )

    return ParseResult(transactions=transactions, skipped=tuple(skipped))

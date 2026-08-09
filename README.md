# F.U.C.K. — Finances Under Control Kit

A lean, local, privacy-first **personal-finance operating system**: five KPIs,
a cadence stack, a mapped tool chain, and one deliberately small CLI (designed,
not yet built) that will compute the numbers from bank CSV exports.
No cloud aggregator, no server, no weekly discipline.

> **Why V2 looks nothing like V1.** V1 was a CSV transaction categorizer.
> A structured discovery pass (2026-08) showed that its niche is already
> served many times over — GnuCash has learned payee→category since the
> 2000s, Actual Budget auto-generates rules from corrections, and the exact
> standalone-CLI shape plateaued at ~110 GitHub stars in a decade. What
> survived discovery was not the tool but the need behind it: run personal
> finances like a high-functioning startup — lean, evidence-based, minimal
> ongoing effort. V2 is that need, distilled. V1 lives on in git history.

## The operating system

Everything lives in [`docs/finance-os.md`](docs/finance-os.md):

- **KPIs** — savings rate as the headline metric; fixed-cost ratio, recurring
  margin, income streams as its diagnostics; emergency-fund months and net
  worth as stock metrics; FI number and pension gap as annual triggers.
- **Cadence stack** — automation produces the numbers, reviews only audit
  them: payday standing order (no cadence), monthly glance (~5 min),
  quarterly review (~60 min, the anchor), annual deep pass.
- **Tool chain** — buy/adopt before build: Portfolio Performance for net
  worth, bank apps for in-silo categorization, existing tax tools for taxes.
  Exactly one confirmed gap is worth building: the cross-silo audit CLI.

## Status

| Piece | State |
|---|---|
| Process (Finance OS v0.2) | **Live** — see `docs/finance-os.md` |
| Audit/KPI CLI | **Designed, deliberately deferred** — see [`docs/superpowers/specs/2026-08-09-audit-cli-design.md`](docs/superpowers/specs/2026-08-09-audit-cli-design.md). MVP = deterministic core loop only; LLM-assist module explicitly cut from initial scope. |

## Principles

1. **The need is the goal; tools are replaceable links.** Any link that stops
   earning its keep gets cut or swapped.
2. **Buy/adopt before build.** Building is reserved for gaps confirmed by
   evidence, not assumed from enthusiasm.
3. **Automation produces outcomes; reviews audit them.** A standing order
   beats willpower; the quarterly review checks the autopilot.
4. **Lean is elegant.** V1 grew 10× in one day of unrequested features and
   died of it. V2 treats every added line as a liability.
5. **Function-first modules.** Every component exists for the function it
   fulfills; delivery layers (CLI today, maybe a UI someday) are thin,
   replaceable shells around a delivery-agnostic core. New modules are
   built when need presents itself in real use — never in anticipation.

## License

GPL-3.0 — see [LICENSE](LICENSE).

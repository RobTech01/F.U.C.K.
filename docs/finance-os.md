# Finance OS v0.2

The operating model for running personal finances like a high-functioning
startup: lean, evidence-based, minimal ongoing effort. Grounded in
established personal-finance practice (sources at the bottom), not just
startup metaphors.

---

## 1. KPIs

**Level 1 — the headline metric.** Everything else is diagnostics of this
one number.

| KPI | Formula | Target band | Cadence |
|---|---|---|---|
| **Savings rate** (Sparquote) | (net income − expenses) / net income | ≥10% floor · 15–20% solid · 20%+ wealth-building. The MMM table converts it into years-to-FI (25% → ~32y, 50% → ~17y, 65% → ~10.5y) | measured monthly, judged quarterly |

**Level 2 — diagnostics** (they explain *why* the savings rate is what it is):

| KPI | Formula | Target band | Cadence |
|---|---|---|---|
| Fixed-cost ratio (Fixkostenquote) | fixed costs / net income | <30% comfortable · **50% ceiling** · >65% critical | quarterly |
| Recurring margin | recurring income − fixed costs | growing; subscription creep is silent erosion of this number | quarterly (diffed run-over-run) |
| Income streams | composition of income by source | know your concentration risk | quarterly |

**Level 3 — stock metrics:**

| KPI | Formula | Target band | Cadence |
|---|---|---|---|
| Emergency-fund months (Notgroschen) | liquid funds / avg. monthly expenses | **3–6 months as a band, not a maximum** — cash above the band is drag and belongs in the Depot | quarterly |
| Net worth | assets − liabilities (via Portfolio Performance) | trend beats benchmark envy; Bundesbank medians if a reference is wanted | number monthly, goal-check annually |

**Annual triggers** (not quarterly load):

- **FI number** = annual expenses × 25 (inverse 4%-rule; 28–33× for very long horizons)
- **Pension gap** (Rentenlücke) — recompute when the annual Renteninformation letter arrives
- **Money dials review** — consciously overspend on 1–2 chosen categories, cut hard elsewhere; prevents the all-or-nothing budgeting failure mode

## 2. Cadence stack

Automation produces the numbers; reviews only audit them. Tracking and
acting run on different clocks.

1. **Automated (no cadence): payday standing order.** Pay-yourself-first —
   the standing order to savings/Depot on salary day *is* the savings rate.
   One-time setup, the single highest-leverage action in this document.
2. **Monthly-lite (~5 min, optional):** note the net-worth number in
   Portfolio Performance; ambient glance at bank apps. Cheap, motivating,
   skippable.
3. **On-demand review (~60 min — THE ANCHOR):** see agenda below. Usage is
   sporadic and irregular, by need — the nutrition-tracker pattern: check
   in when it itches, then back to autopilot. A quarter is a healthy
   rhythm, not a rule; gaps degrade nothing except freshness.
4. **Annual deep pass:** rebalancing (fixed date or ±5% threshold), FI
   number, pension gap, money dials.

## 3. Tool chain

Buy/adopt before build. Build only confirmed gaps.

| Link | Solution | Notes |
|---|---|---|
| Data acquisition | Manual CSV export from all four sources, quarterly | All four are CSV-capable (cheat sheet below) |
| Net worth + Depot | **Portfolio Performance** | Local, free, actively maintained; the DACH standard |
| Ambient categorization | **Bank apps, in-silo** | They do this well now; no need to rebuild |
| Taxes | Existing tax tools, annual topic | Deliberately outside the OS core (evaluated TaxHacker: architecture reference only, no German tax logic, no audit features) |
| Nudge | Optional safety net (e.g. a gentle reminder if idle >6 months) | Reviews run on demand; the nudge only catches total drift, guilt-free to ignore |
| **Cross-silo audit + KPI computation** | **The one confirmed gap → the audit CLI** (designed, deferred) | Nothing local and trustworthy merges multiple banks + credit sources + PayPal and computes these KPIs |

## 4. Source export cheat sheet

State of 2026-08. Items marked *(unverified)* rest on secondary sources —
spot-check against a real export before relying on them.

| Source | Path | History | Quirks |
|---|---|---|---|
| **BBBank** | Online banking → account → Umsätze → export → CSV or MT940 | ~2y online; 10y as PDF archive | Windows-1252, junk preamble/footer around the real header, amounts as `S`/`H` (debit/credit) suffix instead of signs, embedded line breaks in Verwendungszweck. Booking-type column carries Dauerauftrag/Lastschrift labels. Mandatsreferenz/Gläubiger-ID likely inside Verwendungszweck text *(unverified)* |
| **Revolut** | App/web → account → statement → CSV, per currency pocket | effectively unlimited | English headers (`Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency, State, Balance`), decimal point, filter `State` ≠ COMPLETED, one file per currency |
| **Trade Republic** | Profil → Kontoauszüge → Transaktionsexport → Teilen (native since ~2026-04) | up to full history | Covers brokerage, cash, crypto, interest, Saveback, **card payments with merchant + MCC code**. Delimiter/encoding suspected UTF-16LE + semicolon *(unverified — format is 4 months old, no mature parsers exist anywhere)* |
| **PayPal** | paypal.com → Aktivitäten → Herunterladen → CSV | 7y, in 12-month chunks | Activity CSV verified 2026-08-27 (English headers, decimal comma, `Transaction ID` unique; see the audit-cli spec's PayPal note + issue #6) |

**PayPal insight:** import PayPal's own export as a first-class source (it
names the real merchant) and de-duplicate against the bank-side PayPal
debits — this shrinks the feared memo-parsing problem to a matching problem.

## 5. Review agenda (~60 min, on demand)

Run sporadically, whenever the need arises — the agenda is identical
whether two or eight months have passed. "Quarterly" cadences in §1 read
as "per review".

1. **Export** — pull CSVs from all four sources (paths above). ~10 min.
2. **Run the audit** — *(once the CLI exists; until then: eyeball the
   exports or skip to 4 with bank-app numbers)*.
3. **Read the five numbers** — savings rate, fixed-cost ratio, recurring
   margin, income streams, emergency-fund months.
4. **Verify last quarter's decisions first** (the learning loop): cancelled
   subscriptions actually stopped debiting? Burn actually dropped? Only
   then:
5. **Make 1–3 decisions** — cancel X, resize Y, shift focus Z. More than
   three per quarter don't stick.
6. **Log them** — append to `journal.md` (date, decision, expected effect,
   check-by date). Next review starts at step 4 against this log.

## Sources

- Savings-rate bands & 50/30/20: [Finanztip](https://www.finanztip.de/daily/wie-viel-solltest-du-sparen-die-50-30-20-regel/)
- Fixed-cost ceiling: [finanzen.net](https://www.finanzen.net/nachricht/geld-karriere-lifestyle/private-finanzen-50-30-20-regel-vermoegen-aufbauen-und-fixkosten-im-blick-behalten-13360355)
- Emergency fund: [Bogleheads](https://www.bogleheads.org/wiki/Emergency_fund), 3-Konten-Modell: [Finanzfluss](https://www.finanzfluss.de/banking/kontenmodelle/)
- Savings rate → years to FI: [Mr. Money Mustache](https://www.mrmoneymustache.com/2012/01/13/the-shockingly-simple-math-behind-early-retirement/)
- Rebalancing cadence: [Bogleheads](https://www.bogleheads.org/wiki/Rebalancing)
- Net-worth medians: [Bundesbank](https://www.bundesbank.de/de/aufgaben/themen/monatsbericht-vermoegen-in-deutschland-sind-deutlich-gestiegen-907726)
- Money dials: Ramit Sethi, conscious spending plan

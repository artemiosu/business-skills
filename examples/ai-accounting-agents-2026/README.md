# Live case 001: AI accounting agents for small US firms

**Evidence cutoff:** 2026-09-02  
**Status:** open; forecasts are unresolved  
**Purpose:** demonstrate Horizon Scout on a real, decision-shaped question using publicly available evidence.

> This is an illustrative research case, not personalized investment, accounting, tax, or legal advice. No founder interviews, customer calls, private data, or paid research were used. The author has no disclosed financial position in the companies named below.

## The question

Should a hypothetical three-person US software team spend the next eight weeks and up to **$25,000** validating a standalone AI bookkeeping agent for accounting and tax firms with 2–20 staff?

The proposed wedge is deliberately narrow: review transaction exceptions, prepare reconciliation suggestions, and leave every consequential action behind a human approval gate. It excludes autonomous tax filing, money movement, and unsupervised journal entries.

## Executive decision

**Verdict: MONITOR + bounded probe. Do not fund a full standalone product yet.**

The trend is real enough to investigate: broad US business AI use is material, bookkeeping tasks are exposed to automation, and major incumbents are shipping agent-like accounting workflows. The entrant opportunity is not yet proven. Public evidence does not establish retained, paid, feature-specific adoption; incumbents own the system of record and distribution; security obligations raise integration cost.

Authorize only a six-week discovery and concierge-prototype test capped at **$15,000**. Advance to a product pilot only if at least 4 of 10 qualified firms sign a paid three-month continuation, provide controlled ledger access, and accept the predefined human-review workflow. Stop if fewer than 10 qualified firms enter discovery, fewer than 4 accept the paid continuation, or exception accuracy requires hidden expert labor that destroys the target gross margin.

## Before → Horizon Scout → decision

| Before | Horizon Scout adds | Decision artifact |
|---|---|---|
| “AI agents are coming to accounting.” | Source lineage, adoption stages, incumbent response, regulation, counterevidence, and resolvable forecasts | `MONITOR`: test a narrow wedge; do not commit to a full product |

## Decision contract

| Field | Precommitted value |
|---|---|
| Actor | Hypothetical three-person US B2B SaaS team |
| Decision deadline | 2026-10-15 |
| Initial budget | $15,000 probe; $25,000 absolute validation ceiling |
| Runway assumption | 12 months |
| Required result | Evidence supporting a path to paid retention before a larger build |
| Loss tolerance | The probe budget; no production access to taxpayer data |
| Reversibility | High for interviews/concierge prototype; low after deep platform integration |
| Opportunity cost | Two founder-months that could test a non-regulated workflow |
| Advance threshold | ≥4 of 10 qualified firms sign a paid 3-month continuation under the declared workflow and price floor |
| Stop threshold | Weak recruitment, no paid continuation, unacceptable security boundary, or hidden-service economics |

## Evidence map

The machine-readable records are in [`signals.jsonl`](signals.jsonl). Repeated observations using the same survey or issuer are assigned to a shared independence group and do not count as separate confirmation.

| ID | Observation | Direction | Independence note |
|---|---|---|---|
| `ACC-S01` | Census BTOS found overall US business AI use around 17–20% from Dec. 2025 to May 2026; use among firms with four or fewer employees was below 20% and did not increase significantly in that interval. | Against immediate mass-market readiness | Independent government survey |
| `ACC-S02` | A Federal Reserve synthesis found adoption estimates vary greatly with sampling, weighting, question wording, and unit of analysis. | Against headline-level certainty | Shares some BTOS ancestry with `ACC-S01`; grouped accordingly |
| `ACC-S03` | Intuit announced accounting agents for categorization, anomaly handling, and reconciliation inside QuickBooks. | Supports capability; challenges entrant capture | Primary but financially interested issuer evidence |
| `ACC-S04` | Intuit's FY2026 results tied QuickBooks growth to price, customer growth, and mix—not to a disclosed accounting-agent retention cohort. | Against a strong feature-adoption claim | Same issuer group as `ACC-S03` |
| `ACC-S05` | Sage announced finance agents embedded in its existing systems, with humans retaining final control. | Supports capability; challenges distribution access | Primary but financially interested issuer evidence |
| `ACC-S06` | IRS guidance says tax professionals must maintain written information-security plans and oversee service providers handling customer information. | Against low-friction deployment | Government compliance guidance |
| `ACC-S07` | GAO documented inaccurate output, privacy/security, skills, and authorization barriers in a separate small-business AI setting. | Counterevidence on friction; indirect transfer | Government evidence; adjacent rather than accounting-specific |

### Sources

- [US Census Bureau: business AI use, May 2026](https://www.census.gov/library/stories/2026/05/ai-use-businesses.html)
- [Federal Reserve: Monitoring AI Adoption in the US Economy, April 2026](https://www.federalreserve.gov/econres/notes/feds-notes/monitoring-ai-adoption-in-the-u-s-economy-20260403.html)
- [Intuit: AI accounting agents, July 2025](https://investors.intuit.com/news-events/press-releases/detail/1258/intuit-introduces-ground-breaking-virtual-team-of-ai-agents-to-fuel-growth-for-businesses)
- [Intuit FY2026 results, August 2026](https://investors.intuit.com/sec-filings/all-sec-filings/content/0000896878-26-000029/fy26q4earningspressrelease.htm)
- [Sage: finance agents, April 2026](https://www.sage.com/en-us/news/press-releases/2026/04/sage-expands-ai-agents-across-finance-hr-and-operations-to-automate-workflows/)
- [IRS: information-security plans for tax professionals, July 2025](https://www.irs.gov/newsroom/tips-to-help-tax-professionals-protect-client-information)
- [GAO: AI uses and risks for small-business programs, May 2026](https://www.gao.gov/products/gao-26-107828)
- [BLS: Bookkeeping, Accounting, and Auditing Clerks](https://www.bls.gov/ooh/office-and-administrative-support/bookkeeping-accounting-and-auditing-clerks.htm)

## Anti-hype gate

**Evidence sufficiency: PASS. Business opportunity: MONITOR.**

- Multiple lanes and independent public institutions are represented.
- Intuit observations share one issuer ancestry and count once for independence.
- Vendor claims demonstrate shipping and strategy, not neutral proof of retention.
- Broad “AI use” is not the same denominator as paid accounting-agent production.
- The decisive missing observation is a retained, paid cohort for the exact workflow.
- The trend can succeed while the entrant fails because incumbents own ledgers, permissions, workflow context, and distribution.

## Adoption ladder

| Stage | What public evidence supports | What remains unknown |
|---|---|---|
| Awareness | High; AI is prominent across business software | Not decision-relevant alone |
| Trial | Vendor releases imply availability and experimentation | Comparable trial denominator |
| Pilot | Some issuer examples exist | Selection rule and failure rate |
| Paid production | Agents are bundled into commercial platforms | Incremental willingness to pay for this feature |
| Retained | No independent feature-specific cohort found | 90/180-day retained usage |
| Expanded | No auditable public denominator found | Seat/workflow expansion and realized savings |

**Adoption unit:** accounting or tax firm using the exception/reconciliation workflow in production. A user login, feature availability, survey intent, or generic AI use does not qualify.

## Timing map

| Dimension | Current state | Window-open condition |
|---|---|---|
| Technical readiness | Capabilities are shipping with human approval | Reliable exception handling under firm-controlled tests |
| Cost parity | Plausible, but hidden review labor is unknown | Measured gross margin after expert review and support |
| Complement readiness | Ledger APIs and data exist inside incumbent platforms | Stable permissions, audit trail, and reversible writes |
| Regulatory/security | Material customer-data obligations | Approved security boundary and service-provider controls |
| Buyer urgency | Labor pressure and repetitive work support interest | Budget moves from curiosity to paid continuation |
| Distribution | Strongest for incumbent systems of record | Repeatable channel not controlled by a single platform |
| Financing/runway | An eight-week probe fits; a platform build does not | Evidence arrives before the team sacrifices runway |

## Value-capture gate

**Result: NOT PROVEN.**

- **Customer/user/payer:** small accounting or tax firm; staff use it, owner/partner pays.
- **Job:** reduce exception review and reconciliation time without losing control or auditability.
- **Willingness to pay:** not established by public product announcements.
- **Economics:** inference-time cost may be manageable; onboarding, security, integrations, and human exception handling are unresolved.
- **Bargaining power:** Intuit, Sage, and other system-of-record providers control data access and can bundle similar capability.
- **Defensibility:** generic agent orchestration is weak; proprietary reviewed exception data and a trusted distribution channel could be stronger.
- **Reachable market:** do not use a top-down “accounting software TAM.” For this probe, the reachable universe is 30 named firms, 10 discovery participants, and a threshold of 4 paid continuations.

### Premortem: the trend succeeds, the entrant fails

Incumbents make basic reconciliation agents good enough and bundle them. The startup wins pilots but spends too much on integration and expert review, cannot obtain production permissions, and loses the customer relationship to the ledger platform.

## Competing hypotheses

1. **Narrow-wedge opportunity:** firms will pay for a controlled exception-resolution layer that improves existing ledgers.
2. **Incumbent-bundle outcome:** the capability becomes a feature of systems of record, leaving little standalone margin.
3. **Service-heavy outcome:** demand exists, but accuracy and trust require so much expert review that the business behaves like a service company.
4. **Compliance-delay outcome:** security review and data-access restrictions push time-to-revenue beyond the entrant's runway.

## Analytic-lens disagreement

These are structured lenses produced by one workflow, not endorsements from independent human experts.

| Lens | First-pass position | Crux |
|---|---|---|
| Venture | Uncertain | Is there a wedge incumbents will not bundle quickly? |
| Foresight | Support trend, not timing | Does workflow redesign follow feature availability? |
| Economics | Oppose broad entrant thesis | Who captures surplus when the ledger controls distribution? |
| Product | Support narrow probe | Will firms pay after the novelty period? |
| Data science | Uncertain | No comparable retained-production denominator |
| Intelligence | Uncertain | Issuer announcements dominate workflow-specific evidence |
| AI safety | Oppose autonomy-first framing | Financial data and irreversible actions need tight controls |
| Entrepreneurship | Support bounded learning | A concierge probe can resolve the key unknowns cheaply |

No vote or average is taken. The synthesis follows the decision contract: the cheap probe has positive information value, while the full build does not clear the capture gate.

## Scenarios through September 2027

| Scenario | Causal chain | Signposts | Action |
|---|---|---|---|
| Stalled | Security failures or weak reliability → tighter permissions → long reviews → service-heavy economics | Vendor pullbacks, beta labels persist, no retained metrics | Stop product build; retain research only |
| Base | Human-approved agents spread inside incumbent suites → selective firm adoption → modest standalone openings | Two major platforms ship; buyers pay for narrow exceptions | Partner/integrate; focus on proprietary workflow data |
| Accelerated | Reliability improves + firms face capacity pressure → paid use expands → platforms open distribution | Published retained cohorts, channel partnerships, controlled write access | Scale only after cohort economics clear thresholds |

The scenarios are exploratory and intentionally do not carry additive probabilities.

## Forecast ledger

The preregistered machine-readable forecasts are in [`forecast-ledger.jsonl`](forecast-ledger.jsonl). They must be resolved from the declared sources without rewriting the original lines.

| Forecast | Probability | Review | Resolution |
|---|---:|---|---|
| Two of Intuit, Sage, and Xero offer the defined generally available accounting-agent workflow in the US | 0.72 | 2027-03-31 | 2027-09-30 |
| At least one of those providers publishes a feature-specific retained-usage denominator | 0.30 | 2027-03-31 | 2027-09-30 |
| Census reports ≥20% current AI use among firms with 0–4 employees in a comparable collection period | 0.58 | 2027-01-15 | 2027-06-30 |

These probabilities are judgmental estimates anchored to the public evidence above, rounded to avoid false precision. They are not investment forecasts.

## Next experiment

1. Recruit from a preregistered list of 30 firms; report nonresponse.
2. Run 10 structured workflow interviews split evenly between confirming and disconfirming recruitment paths.
3. Test a read-only concierge prototype on synthetic or properly de-identified records.
4. Offer the same three-month continuation and price floor to all qualified participants.
5. Record paid acceptance, security objections, review minutes per exception, and cohort retention.
6. Stop or advance using the decision thresholds above—never a post-hoc story.

## Limitations and update policy

- This scan uses public English-language sources and is US-focused.
- Broad AI adoption surveys cannot establish accounting-agent adoption.
- Vendor sources are useful for product availability but interested for efficacy and demand.
- No customer interviews or production measurements were available at the cutoff.
- Links may change; a future evaluation release should add lawful source snapshots and hashes.
- Updates append new evidence and forecasts. The cutoff, original probabilities, and rejected evidence are preserved.


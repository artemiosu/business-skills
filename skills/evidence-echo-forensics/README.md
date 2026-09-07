# Evidence Echo Forensics

> Twelve citations can still be one observation.

Evidence Echo Forensics audits the source lineage behind a specific claim. It traces apparent confirmations back to press releases, wire stories, datasets, interviews, filings, experiments, or prior analyses—and shows where the claim changed downstream.

It answers **“Are these confirmations actually independent?”** It does not decide whether a claim is true or accuse anyone of coordination, plagiarism, or misinformation.

## Install

```bash
npx skills add artemiosu/business-skills --skill evidence-echo-forensics
```

Then try:

```text
$evidence-echo-forensics Audit the claim below across these supplied sources.
Trace every repetition to its underlying observation, separate dataset,
method, editorial, and ownership dependence, and run the origin-removal test.
Do not return a true/false verdict.
```

```text
$evidence-echo-forensics Deep open-web audit: where did this market statistic
originate, how did its denominator or qualifiers change, and how many confirmed
independent measurements remain? Declare the cutoff and search stopping rule.
```

```text
$evidence-echo-forensics Audit the decision-critical claims in this memo.
Rank them by materiality first and trace only the declared audit sample.
```

## The 30-second result

The bundled synthetic case contains four apparent confirmations of one performance claim:

```text
CLOSED-CORPUS AUDIT

APPARENT CONSENSUS
ECHO_DOMINATED

4 documents · 4 supporting occurrences
1 confirmed origin · 1 independently countable support unit
plausible support-unit range 1–1

DECISION CONSEQUENCE
Count the four repetitions as one interested evidentiary origin.

THIS DOES NOT ESTABLISH
Whether the original measurement is true or repetition was coordinated.
Reviewer identity is also not cryptographically established by the local JSONL.
```

Inspect the [complete synthetic walkthrough](../../examples/evidence-echo-forensics-synthetic-case.md), read the [independent two-part forward test](../../examples/evidence-echo-forensics-forward-test.md), or reproduce the minimal case:

```bash
python3 scripts/evidence_echo.py validate assets/example_records.jsonl
python3 scripts/evidence_echo.py audit assets/example_records.jsonl \
  --claim claim-processing-time
```

Run those commands from this skill directory. Python is optional for the reasoning workflow and required only for deterministic validation and diagnostics.

## What makes it different

| Tool | Primary question |
|---|---|
| Citation checker | Does the link support the nearby sentence? |
| Fact checker | Is the statement true or false? |
| Plagiarism detector | Is wording reused without proper attribution? |
| **Evidence Echo Forensics** | How many independent evidence-generating origins sit behind the apparent consensus? |
| Horizon Scout | What does the full evidence set imply for a trend, timing, and value capture? |

The skill works at claim level, not document level. One article can repeat a wire claim, independently verify a second claim, and use a shared dataset for a third.

## Five dependency dimensions

```text
asset identity
editorial derivation
evidentiary origin
method dependence
control / financial interest
```

Only confirmed claim-level support units count as independent corroboration. Different URLs, publishers, wording, or multiple analyses of one dataset are not proof of independent observation. Origins remain visible inside each support unit; shared ownership or methodology is reported separately.

The agent may propose semantic lineage only as `inferred_candidate`. A confirmed human judgment requires a separate evidence-linked decision from an actual named reviewer; the tool cannot award itself that status.

## Four modes

- **Quick:** one claim and a small supplied corpus.
- **Deep:** backward source tracing plus independent corroboration and contradiction search.
- **Audit:** decision-critical claims from a memo, deck, report, or thesis.
- **Update:** a versioned follow-up that separates new discovery from new evidence.

Without web access the skill remains useful as a clearly labeled closed-corpus audit. Without Python it returns the same record structure manually. Host-specific UI metadata is optional; the core follows the open Agent Skills format.

## Auditable artifacts

- frozen document/version metadata;
- atomic claim occurrences with precise locators;
- typed lineage and mutation edges;
- underlying-origin assignments with adjudication state;
- confirmed origin and support-unit counts with separate plausible ranges;
- consensus-collapse and Horizon Scout handoff;
- coverage, correction, access, and uncertainty warnings.

See the [runtime instructions](SKILL.md), [workflow](references/workflow.md), [taxonomy](references/taxonomy.md), [record schema](references/schemas.md), [safety boundaries](references/safety.md), and [evaluation protocol](references/evaluation.md).

## Evidence status

**Experimental.** The deterministic core currently passes synthetic record-level and adversarial invariant tests. Field accuracy, exhaustive retrieval, and automatic entity-resolution quality are not yet established. The tool abstains instead of treating missing lineage as independence.

```bash
python3 scripts/eval_harness.py
```

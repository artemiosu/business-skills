# Four articles, one observation

This synthetic case demonstrates the Evidence Echo Forensics output contract without presenting invented facts as a real investigation.

## Question

Should four articles repeating the claim “Northstar's pilot reduced processing time by 40% across participating firms” count as four independent confirmations?

## Corpus contract

**CLOSED-CORPUS AUDIT.** The corpus contains a company release, two downstream articles, and an AI-generated roundup. Cutoff: 2026-08-31. All names, URLs, and results are fictional.

## Claim specification

| Field | Value |
|---|---|
| Population | Firms participating in the Northstar pilot |
| Metric | Processing-time change |
| Denominator | Pilot firms and their measured workflows |
| Geography | Not specified |
| Period | Pilot period ending 2026 |
| Modality | Company-reported observation |

## Lineage

```text
Northstar pilot dataset (interested root)
├── Northstar release
├── Alpha article — explicitly attributes Northstar
├── Beta article — repeats 40%, drops the denominator
└── Alpha article → AI roundup
```

The records contain four documents and four supporting occurrences, but every occurrence is assigned to the same underlying pilot dataset. The Beta transformation is marked `denominator_lost` and `single_source_upgraded_to_consensus`.

## Result

```text
APPARENT CONSENSUS
ECHO_DOMINATED

4 documents · 4 supporting occurrences
1 confirmed origin · 1 independently countable support unit
plausible support-unit range 1–1

ORIGIN-REMOVAL TEST
Remove the Northstar pilot dataset → 0 confirmed support units remain.

DECISION CONSEQUENCE
Treat the visible repetitions as one interested evidentiary origin,
not four independent confirmations.

THIS DOES NOT ESTABLISH
Whether the original measurement is accurate, whether any publisher acted
improperly, whether the examined corpus is complete, or who created a self-attested review record.
```

## Reproduce

From the repository root:

```bash
python3 skills/evidence-echo-forensics/scripts/evidence_echo.py validate \
  skills/evidence-echo-forensics/assets/example_records.jsonl

python3 skills/evidence-echo-forensics/scripts/evidence_echo.py audit \
  skills/evidence-echo-forensics/assets/example_records.jsonl \
  --claim claim-processing-time --format json

python3 skills/evidence-echo-forensics/scripts/evidence_echo.py handoff \
  skills/evidence-echo-forensics/assets/example_records.jsonl \
  --claim claim-processing-time
```

Because this case declares `case_purpose: synthetic_fixture`, the handoff command deliberately quarantines all four occurrences. A real operational case can emit reviewable support-unit `origin_group_id` records only after all lineage gates pass; the command never modifies a Horizon Scout ledger.

# Evaluation protocol

## What the current harness establishes

The bundled harness tests deterministic record validation and hand-calculated lineage diagnostics on synthetic fixtures. It does **not** prove field accuracy, factual truth, exhaustive web coverage, or calibrated automatic entity resolution.

Keep status **Experimental** until a versioned, independently annotated corpus and prospective field results are published.

## Release-blocking invariants

1. Ten press-release or wire repetitions cannot become ten confirmed support units.
2. Different URLs, domains, wording, authors, or hashes do not automatically establish independence.
3. Unresolved occurrences never increase confirmed counts or pass a Horizon handoff gate.
4. A shared dataset and independent analyses remain separate dependency dimensions.
5. Common ownership alone never collapses evidence-root count.
6. Partial dependency is not transitively closed across multi-origin bridges.
7. Contradicting evidence is reported and cannot increase supporting roots.
8. Retracted/superseded material cannot actively support a current claim.
9. Confirmed directional derivation cannot point to a later occurrence.
10. Derivation/supersession cycles, duplicate IDs, orphan references, malformed JSON, duplicate JSON keys, invalid known dates, and non-finite constants fail validation; citation cycles remain visible and force an unresolved conclusion.
11. Provenance never becomes a truth or trust score.
12. Repeated runs on the same records produce byte-identical JSON output.
13. An agent cannot self-assert `human_adjudicated`; confirmation needs a separate evidence-linked human decision.
14. Runtime-required fields and the machine-readable schema remain exactly synchronized.
15. Support-unit counts, origin counts, and analysis/method counts remain distinct.
16. `synthetic_fixture` cases never emit downstream handoff records.
17. Candidate support units, contradictions, overlaps, and mutations remain visible in machine and concise text output.

## Golden and adversarial cases

Maintain fixtures for exact mirrors, wire syndication, press-release paraphrases, independent same-number measurements, shared datasets, multi-origin bridges, common ownership, translations, corrections/retractions, circular citations, missing metadata, dynamic URLs, AI summaries, prompt injection, confidential-text leakage, and historical-cutoff leakage. See [adversarial-cases.md](adversarial-cases.md).

## Future annotated-corpus evaluation

The unit of annotation is a pair of claim occurrences, not a pair of whole documents. Annotate separately:

1. semantic relationship;
2. asset/editorial relationship;
3. evidentiary lineage;
4. method/control correlation.

Use two blinded annotators and a third adjudicator. Require source spans and rationale. Preserve `cannot_determine`; do not force binary labels. Split train/dev/test by origin family and additionally test unseen publishers, topics, time periods, and languages to prevent lineage leakage.

Report, without a single composite score:

- candidate recall@K and reviewer workload;
- per-class precision/recall/F1;
- false-merge and false-split rates;
- abstention coverage-risk curve;
- edge-type precision/recall;
- error in confirmed-root count and coverage of plausible ranges;
- consensus-collapse accuracy;
- downstream Horizon false-PASS rate.

Automatic merges are asymmetric-risk decisions: false merge is more dangerous than false split. Publish precision and coverage together. Only introduce `p_same_origin` after out-of-sample calibration with Brier/log loss, reliability bins, sample size, and an explicit applicability domain.

## Independent forward test

Give an evaluator the skill, an unlabeled realistic corpus, and a user request without the intended answer. Judge the produced lineage graph and claims against a hidden adjudicated reference. Review actual artifacts, not keyword presence or report style.

An AI evaluator must leave semantic links as candidates; it cannot manufacture `human_adjudicated` records. Therefore use two distinct checks:

1. **Behavioral safety run:** agent-produced records should abstain with `LINEAGE_UNRESOLVED` until a person reviews them.
2. **Deterministic golden run:** a clearly synthetic fixture may contain predeclared fictional adjudications to test the expected confirmed graph. It is regression data, not evidence of real human review or field accuracy.

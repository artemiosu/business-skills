# Workflow

Use this reference for deep searches, audits of large materials, and updates. The core question is: **how many independent evidence-generating processes support this exact claim?**

## 1. Frame the investigation

Record:

- atomic claim and decision consequence;
- population, metric, denominator, geography, period, and modality;
- `as_of_date` and `analysis_date`;
- closed-corpus or open-web contract;
- operational or synthetic-fixture purpose;
- inclusion/exclusion rule;
- privacy, archival, and quotation constraints;
- time/search budget and stopping rule.

For a large memo or deck, rank claims by decision materiality before tracing. Do not let easy minor claims crowd out a fragile central claim.

## 2. Build a coverage plan

For open-web work, use several query families rather than a fixed source quota:

1. exact and near-exact claim wording;
2. distinctive number/denominator combinations;
3. named study, dataset, author, organization, wire ID, DOI, or accession;
4. earliest-date and archived-version queries;
5. correction, retraction, update, erratum, or withdrawal queries;
6. counterclaim, replication, critique, and independent-measurement queries;
7. other-language queries when the claim crossed languages.

Balance confirmation and disconfirmation effort. Stop on source saturation or the declared budget, not after collecting an impressive number of citations. Create a `search_log` for every query family with the provider, retrieval date, language, reviewed-result count, included documents, access gaps, exclusions, and a snapshot hash when lawful.

## 3. Separate work, version, and snapshot

- **Work:** the abstract article, study, dataset, interview, or release.
- **Version:** a revision, translation, corrected release, localized edition, or derived dataset.
- **Document snapshot:** the representation actually inspected at a retrieval time.
- **Claim occurrence:** the claim as expressed in that snapshot.

One URL can change over time; one version can appear at many URLs. A canonical URL is a hint, not identity proof. A content hash establishes byte identity only. Record a new snapshot when content changes in place.

## 4. Specify claims before linking them

Split compound statements. Distinguish observed, estimated, projected, alleged, and opinion claims. Preserve qualifiers such as “in the examined sample,” “may,” or “no measured return.”

An occurrence may directly support, partially support, mention, contradict, or be inaccessible for the claim. Do not promote partial support into direct support. An article can have different origins for different claims.

## 5. Trace lineage backward

Prefer evidence in this order:

1. explicit attribution/link plus a matching claim;
2. stable identity or version relations such as DOI, accession, provider GUID, or dataset release ID;
3. identical lawfully captured bytes or an explicit mirror/republication notice;
4. rare quotation, unusual factual bundle, identical non-obvious error, or identical table/rounding combined with valid chronology;
5. lexical/semantic similarity and chronology as candidate-generation signals only.

Ask whether the child actually depends on the parent for this claim. A citation may provide background while the child supplies an independent observation. “Earlier” is not synonymous with “origin,” especially when pages are backdated or a still-earlier common source may exist.

## 6. Adjudicate without false certainty

Use:

- `machine_observed` for directly verifiable identity such as the same hash, stable wire/version ID, or explicit typed relation;
- `human_adjudicated` only after a named human reviewer records a separate evidence-linked `adjudication` decision;
- `inferred_candidate` for a plausible machine/model suggestion;
- `unresolved` when the available material cannot decide;
- `rejected` when the proposed relation was checked and not supported.

Do not express an uncalibrated probability of shared origin. Similarity is not a probability. If later automation produces probabilities, it needs an independently annotated corpus, held-out origin families, calibration metrics, and a published applicability domain.

The agent itself must use `inferred_candidate` for semantic judgments. It cannot act as the human reviewer, invent reviewer identity, or promote its own conclusion to `human_adjudicated`. Machine confirmation is limited to deterministic identity checks encoded by the validator.

For deep or consequential cases, use three separated analytic passes when isolated agent contexts are available:

1. **Dependency tracer:** seeks the smallest plausible set of shared origins and cites record IDs.
2. **Independence defender:** looks for new observation, sampling, interviews, or verification that the first pass could wrongly collapse.
3. **Evidence controller:** checks dates, source access, corrections, conflicts, support-unit semantics, and unresolved alternatives.

Keep first-pass memos blind to one another, then reconcile their cruxes. These are correlated analytic lenses, not independent experts. They create candidates, never human adjudications; do not average votes or confidence.

## 7. Model multi-origin and partial dependence

Assign each occurrence to zero, one, or several origins and to support units. A support unit represents one independently countable evidence-generating process. Repetitions of the same pilot reuse one unit; independent measurements receive different units; inputs that are all necessary for one observation share a unit and use `jointly_necessary`. An article can combine a shared wire story with a new local interview. A paper can reuse a public dataset while contributing an independent analysis, but a new analysis of old observations is not a new observational unit.

Do not merge a chain through partial overlap:

```text
A uses X
B uses X and Y
C uses Y
```

A and C are not thereby one origin. Equivalence clustering is safe only for confirmed exact identity or the same underlying observation. Keep dataset, method, editorial, and control relations as typed graph edges.

## 8. Check version integrity

For each material root, determine whether it is current, corrected, retracted, superseded, withdrawn, or unknown. A retracted or superseded occurrence cannot support a current-state claim. It may remain as a historical object if clearly labeled.

For datasets, distinguish the abstract dataset, release/version, distribution, and derived analysis. Two analyses of one release can be analytically independent but still have one underlying measurement root.

## 9. Test claim mutation

Compare each child occurrence to its upstream expression. Record only material changes, including:

- qualifier or uncertainty removed;
- modality hardened (`may` → `will`, estimate → fact);
- denominator, population, geography, period, unit, or currency changed;
- correlation upgraded to causation;
- precision inflated;
- subgroup cherry-picked;
- correction stripped;
- headline/body mismatch;
- translation drift;
- single source upgraded to consensus.

Mutation is not automatically error or intent. Explain the decision consequence.

## 10. Run consensus-collapse diagnostics

For each claim report:

- raw documents and active occurrences;
- confirmed underlying origins and independently countable support units;
- unresolved occurrences;
- plausible root range;
- root with the largest number of downstream occurrences;
- remaining confirmed support units after removing the dominant origin;
- contradiction roots and whether counterevidence search was completed;
- interested-only, common-control, shared-method, and correction flags.

An origin-removal result describes fragility, not truth. “Consensus collapses” means fewer than two confirmed support units remain after the most-repeated origin is removed; it does not mean the claim is false. Do not rank sources by citation volume.

## 11. Update safely

Never overwrite an earlier audit. A later run should say whether a change came from discovery backfill, world update, version update, or adjudication update. Link the new case to the old result in the narrative and preserve both record sets.

## 12. Handoff to Horizon Scout

Only confirmed underlying-observation assignments may become a claim-specific support-unit `origin_group_id`; preserve the underlying `origin_id` separately. Keep unresolved material in an explicit quarantine. A claim-level unresolved gate suppresses all handoff records. The handoff is evidence for review, not permission to rewrite a ledger or bypass Horizon Scout gates.

## Method foundations

- [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) supplies the underlying distinctions between entities, derivation, revision, quotation, and primary source.
- [C2PA's explainer](https://spec.c2pa.org/specifications/specifications/2.2/explainer/Explainer.html) makes the essential boundary explicit: verifiable provenance alone does not establish that content is true.
- [Crossref's update guidance](https://www.crossref.org/documentation/register-maintain-records/maintaining-your-metadata/registering-updates/) informs correction and retraction handling for scholarly records.
- [Agent Skills](https://agentskills.io/specification) defines the portable package format; host-specific metadata remains additive.

# Record schema and audit semantics

The canonical case format is UTF-8 JSONL: one JSON object per line. It is append-friendly by convention, not tamper-proof. The complete machine-readable schema is [../assets/records.schema.json](../assets/records.schema.json).

## Record types

| Type | Purpose |
|---|---|
| `case` | Corpus contract, purpose, dates, inclusion rule, and limitations |
| `entity` | Publisher, author, producer, sponsor, or organization |
| `document_snapshot` | Inspected representation of a work/version at a retrieval time |
| `claim` | Atomic proposition and its decision-relevant scope |
| `claim_occurrence` | How one document expresses or treats the claim |
| `origin` | Underlying observation, dataset, interview, filing, experiment, or reporting process |
| `origin_assignment` | Claim-occurrence-to-origin link, support unit, and adjudication state |
| `lineage_edge` | Typed relation between two claim occurrences |
| `adjudication` | Review decision and rationale for a candidate record |
| `search_log` | Reproducible query family, reviewed-result count, inclusions, exclusions, and access gaps for open-web work |

Every record has `record_type` and a unique `id`. IDs are stable within a case and use lowercase letters, numbers, dots, underscores, and hyphens.

`case_purpose` is required: use `operational` for real work and `synthetic_fixture` for tests or teaching examples. Synthetic fixtures can exercise audit logic but are always blocked from downstream handoff.

An `open_web` case requires at least one `search_log`. Logs are evidence of search coverage, not proof of corpus completeness. Record reviewed-result counts, included and inaccessible document IDs, excluded-result reasons, and a snapshot hash when one can lawfully be retained.

## Direction

For a `lineage_edge`, `from_occurrence_id` is the downstream/dependent occurrence and `to_occurrence_id` is upstream. Both occurrences must concern the same atomic claim. An edge records a relation, not an automatic whole-document merge.

## Confirmed origin semantics

An origin assignment contributes to a confirmed support unit only when it has:

- `role: underlying_observation`; and
- `support_mode: sufficient`, `jointly_necessary`, or `corroborative`; and
- a stable `support_unit_id`; and
- `status: machine_observed` or `human_adjudicated`.

`support_unit_id` is the independently countable evidence-generating process. Repetitions of one measurement reuse its unit. Inputs that are all required for one observation use the same unit and `jointly_necessary`; independently corroborating observations use different units. Reporting and analysis origins use `contextual` and do not raise the unit count.

`machine_observed` requires deterministic structured identity, such as the same stable identifier present on the inspected document. `human_adjudicated` is valid only with exactly one active `adjudication` record labelled `confirmed`, a named human reviewer, rationale, and existing evidence references. An agent cannot certify its own inference as human-reviewed; its semantic conclusions remain `inferred_candidate` until a person adjudicates them.

This is a structural check, not identity verification. The runtime reports `human_review_assurance: SELF_ATTESTED_NOT_CRYPTOGRAPHICALLY_VERIFIED`; use a signed external approval channel when reviewer identity is consequential.

`inferred_candidate`, `unresolved`, rejected, or missing assignments do not increase confirmed counts. Lack of a discovered dependency never establishes independence.

The audit reports:

- `confirmed_supporting_origin_count`: distinct confirmed supporting origin IDs;
- `confirmed_support_unit_count`: independently countable supporting evidence units;
- `plausible_supporting_origin_range` and `plausible_support_unit_range`: lower/upper logical ranges given candidate and unresolved assignments;
- `verified_origin_count`: supporting origins whose own verification status is `verified`;
- separate reporting/analysis roots and control/method relations.

These ranges are not confidence intervals. A `maximum` of `null` means the available records do not establish a finite upper bound.

## Dates and snapshots

Known dates are ISO `YYYY-MM-DD`. `published_at` and `available_at` may be explicit JSON `null` when only ordering or pre-cutoff availability is known; use `date_notes` and never invent a day. Unknown decision-material availability blocks a clean lineage conclusion.

Use a JSON Schema validator with date-format checking when validating the schema directly. The bundled runtime additionally parses real calendar dates and enforces cross-record and temporal invariants.

- `published_at <= as_of_date`;
- `retrieved_at <= analysis_date`;
- an occurrence cannot be available before its document was published;
- an occurrence cannot become available after the inspected document was retrieved;
- material retrieved after a historical cutoff requires `cutoff_availability: verified_pre_cutoff` or it cannot support a cutoff-safe analysis.

`content_sha256`, when present, uses `sha256:` plus 64 lowercase hexadecimal characters. A hash is a snapshot-integrity aid, not proof of authorship or truth.

## Apparent-consensus labels

- `NO_DIRECT_SUPPORT`: no active direct/partial supporting occurrence.
- `SINGLE_ORIGIN_SUPPORT`: one visible supporting occurrence maps to one support unit; no independent corroboration is established.
- `ECHO_DOMINATED`: several visible supporting occurrences trace to one confirmed support unit.
- `PARTIALLY_DEPENDENT`: at least two confirmed support units exist, but some visible support shares an origin.
- `INDEPENDENTLY_CORROBORATED`: at least two confirmed support units, completed counterevidence search, and no unresolved occurrence, material access/correction/temporal gap, citation cycle, or known shared-origin amplification in the examined set.
- `CONTESTED`: at least one active contradicting support unit is confirmed and no higher-priority lineage gate is unresolved.
- `LINEAGE_UNRESOLVED`: an occurrence, access, date, cutoff, correction, citation-cycle, or counterevidence gate blocks a clean structural conclusion. Confirmed contradictions remain visible in separate fields.

Labels describe evidence structure only. The script never emits `TRUE`, `FALSE`, a source-trust score, or a probability of shared origin.

## Horizon Scout handoff

The CLI emits a handoff only for an `operational` case and active direct/partial support or contradiction with inspectable content, clear correction status, known cutoff availability, exactly one confirmed underlying origin, exactly one support unit, and no claim-level `LINEAGE_UNRESOLVED` gate. It includes both `origin_id` and the support-unit `origin_group_id`. Synthetic, neutral, inaccessible, ambiguous, multi-origin, correction-uncertain, and unresolved records are quarantined. A top-level `independence_gate_eligible` flag is false unless the claim has multiple confirmed support units and no blocking lineage status. The handoff is reviewable input; it never edits Horizon Scout records.

## Append-only corrections

`origin_assignment`, `lineage_edge`, and `adjudication` may use `supersedes_record_id`. A new record must preserve the target/endpoints, supersession cannot fork or cycle, and only unsuperseded leaves affect diagnostics. This is append-only by tool convention, not tamper-evident storage; keep signed release snapshots when stronger integrity is required.

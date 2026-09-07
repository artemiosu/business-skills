# Lineage and mutation taxonomy

Use the narrowest supported relation. A single pair can have several dimensions; record separate edges instead of forcing one label.

## Lineage dimensions

| Dimension | Meaning | Does it collapse evidence-root count? |
|---|---|---|
| `asset` | Same captured bytes, mirror, or format | Only when the claim occurrence is the same |
| `editorial` | Republication, wire pickup, quote, summary, translation | Only when the child relies on the parent for this claim |
| `observation` | Same event, filing, interview, experiment, or direct observation | Yes, for the relevant claim |
| `dataset` | Same underlying dataset/release/sample | Yes for the measurement; analyses may remain distinct |
| `method` | Same model, instrument, sampling frame, or pipeline | No; report correlation separately |
| `ownership` | Common owner, funder, sponsor, author, or control | No; report interest/control separately |

## Relations

- `exact_copy_of`: byte-identical or stable-identifier-equivalent occurrence.
- `version_of`: revision of the same work.
- `republishes`: editorial republication.
- `wire_syndication`: provider item redistributed downstream.
- `translates`: translated expression of the upstream occurrence.
- `quotes`: uses a quotation from the upstream occurrence.
- `summarizes`: restates upstream reporting or analysis.
- `cites`: cites the source; dependency must still be proven separately.
- `uses_dataset`: relies on the same dataset or release.
- `reports_same_observation`: rests on the same event, interview, filing, or measurement.
- `independently_observes`: affirmative evidence of a separate observation; lack of another edge is insufficient.
- `shared_method`: analytical-method correlation without common evidence root.
- `common_owner`: organizational correlation only.
- `common_funder`: funding correlation only.
- `ai_transformation`: AI summary, rewrite, transcript, or transformation of upstream content.
- `supersedes`: replaces an earlier occurrence/version.
- `conflicts_with`: explicit conflict between occurrences.
- `citation_only`: contextual citation with no established evidentiary dependence.
- `possible_common_origin`: candidate common origin requiring review.

## Edge states

- `machine_observed`: stable, directly inspectable identity or typed relation.
- `human_adjudicated`: conclusion approved by a named human in a separate evidence-linked `adjudication` record.
- `inferred_candidate`: suggested by rules, search, similarity, or a model.
- `unresolved`: checked but not determinable from available material.
- `rejected`: proposed relation was checked and rejected.

Only the first two states can support a confirmed origin assignment. Similarity and chronology alone remain candidates.

An agent/model may propose only `inferred_candidate`; it must not impersonate a human reviewer. `machine_observed` is restricted to deterministic structured identity checks. Append-only corrections supersede prior assignments, edges, or adjudications rather than rewriting them.

## Support modes

- `sufficient`: this origin alone supplies the observation represented by its support unit.
- `jointly_necessary`: several origins are all required for one support unit; they are not independent confirmations.
- `corroborative`: this origin belongs to a distinct corroborating support unit.
- `contextual`: reporting or analysis provenance that must not increase evidentiary support.

## Mutation flags

- `attribution_bleaching`
- `qualification_removed`
- `modality_hardened`
- `scope_broadened`
- `scope_narrowed`
- `denominator_lost`
- `timeframe_shifted`
- `geography_shifted`
- `unit_or_currency_changed`
- `precision_inflated`
- `correlation_upgraded_to_causation`
- `opinion_upgraded_to_fact`
- `single_source_upgraded_to_consensus`
- `quote_mined`
- `headline_body_mismatch`
- `translation_semantic_drift`
- `correction_stripped`
- `obsolete_dataset_presented_as_current`
- `subgroup_cherry_pick`
- `fabricated_or_unresolved_citation`

Record the upstream and downstream wording, the changed field, and the consequence. Do not infer deception or intent from a mutation.

## Edge-case rules

- **Wire copy plus local reporting:** split occurrences; shared wire claims retain one root, new local observations receive separate candidates.
- **Anonymous sources:** never deanonymize. Multiple vague descriptions imply a range, not distinct people. Explicit independent confirmation establishes reporting independence, not necessarily distinct human roots.
- **Translations:** retain the original root; treat added reporting as separate occurrences and check modality, negation, numbers, and scope.
- **Dynamic pages:** create a new snapshot per captured representation; a stable URL is not stable content.
- **AI summaries:** the summary contributes no new evidence root; trace cited originals. Missing originals remain unresolved.
- **Primary but interested:** a company release is primary for “the company announced X,” not independent evidence that X works or represents a market.
- **Corrections/retractions:** current claims use the current valid version. Preserve old occurrences for historical lineage only.
- **Circular citation:** preserve the cycle and mark root unresolved. Do not select the earliest timestamp as a root merely to break the cycle.

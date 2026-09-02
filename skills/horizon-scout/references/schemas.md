# Data contracts

Use UTF-8 JSON Lines: one append-only-by-tool-convention object per line. The local file is not tamper-evident and assumes a single writer; use signed/versioned storage for adversarial settings. IDs are stable; dates ISO 8601; unknowns are `null`, never invented.

## Signal

Required: `record_type:"signal"`, `id`, `as_of_date`, `observed_at`, `claim`, `direction` (`supports|contradicts|ambiguous`), `lane`, `source`, `scores`, `independence_group`.

`source`: `title`, `publisher`, `url`, `published_at`, optional `event_at`, `retrieved_at`, `source_type`, `primary`, `reliability_note`.

`scores`: integer 0–5 for the eight positive and three penalty fields defined in workflow.md. Optional: `quote_or_paraphrase`, `tags`, `notes`, `supersedes`.

## Forecast and resolution

Forecast required: `record_type:"forecast"`, `id`, `created_at`, `as_of_date`, `question`, `resolution_date`, `resolution_rule`, `resolution_source`, `probability` (0–1), `status:"open"`. Recommended: `probability_low`, `probability_high`, `reference_class`, `base_rate`, `hypothesis_id`, `evidence_ids`, `assumptions`, `disconfirmers`, `review_at`, `supersedes`, `author`.

Resolution is appended: `record_type:"resolution"`, `forecast_id`, `resolved_at`, `outcome` (0 or 1), `source`, optional `notes`. Never modify the forecast line.

## Integrity invariants

- IDs unique per record type; forecast resolves at most once.
- Backtest evidence dates are on/before cutoff.
- Probabilities are finite [0,1], and bounds bracket the estimate.
- Resolution follows creation; outcome is binary for Brier scoring.
- Independence is not inferred from URL count.

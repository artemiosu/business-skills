# Evaluation and backtesting

Measure over time, not by persuasiveness: Brier score/reliability bins, discrimination, sharpness interpreted with calibration, resolution coverage, predefined decision value, source diversity, primary-source share, counterevidence, independence groups, and missing fields.

Compare with reference-class rate, 50%, and “no change.” Small samples are descriptive; claim no improvement without uncertainty intervals and enough resolved cases.

## Temporal backtest

Select cases without seeing outcomes; freeze cutoff; admit only evidence available then; lock forecasts; reveal later evidence; resolve from predefined sources; compare to baselines. Guard against survivorship/famous-case selection, hindsight leakage, taxonomy drift, and ambiguous resolution. Include failed and boring cases.

## Behavioral rubric (0–2 each)

1. Scope/cutoff defined.
2. Provenance/dates captured.
3. Independent lanes/groups used.
4. Counterevidence/alternatives sought.
5. Base rate used or absence admitted.
6. Anti-hype penalties separate.
7. Measurable falsifiable claims.
8. Probabilities calibrated, not score-derived.
9. Council exposes cruxes without fake authority.
10. Scenarios yield signposts/reversible actions.
11. Ledger immutable/resolvable.
12. Limitations/high-stakes caveats explicit.

Pass: at least 20/24 and no zero on 2, 4, 7, 8, or 11. Run `python3 scripts/eval_harness.py` for structural/adversarial invariants and use [adversarial-cases.md](adversarial-cases.md) for behavioral forward tests. `horizon_scout.py backtest` scores resolved records; it does not by itself establish a leakage-free causal backtest.

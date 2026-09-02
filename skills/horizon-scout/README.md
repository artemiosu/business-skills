# Horizon Scout

Evidence-first horizon scanning for decisions under uncertainty.

## Install

```bash
npx skills add artemiosu/business-skills --skill horizon-scout
```

Then invoke `$horizon-scout` with a topic, market, horizon, and decision.

## Try it

```text
$horizon-scout Quick scan: AI voice agents for independent US dental practices,
18-month horizon. Decision: whether to run a six-week customer pilot.
```

```text
$horizon-scout Challenge this thesis: “warehouse humanoids will reach retained
paid production before 2028.” Separate capability, adoption, timing, and capture.
```

```text
$horizon-scout Update this forecast ledger using only evidence published after
its cutoff. Preserve the original probabilities.
```

## What you get

```text
Decision contract → evidence map → anti-hype gate → competing hypotheses
→ adoption / timing / value capture → scenarios → calibrated forecasts
→ reversible experiments → monitoring and resolution
```

The skill records source lineage, counterevidence, reference classes, disagreement, probabilities, resolution rules, and review dates. Its local tools validate signals, prevent common ledger errors, and score resolved forecasts.

See the [synthetic walkthrough](../../examples/horizon-scout-synthetic-case.md), [runtime instructions](SKILL.md), [methodology](references/workflow.md), and [evaluation limits](references/evaluation.md).

## Evidence status

**Experimental.** Mechanical and adversarial invariants are tested; prospective field calibration is not yet established. This is decision support, not individualized investment advice or a guarantee of prediction.

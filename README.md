<div align="center">
  <img src=".github/assets/social-preview.jpg" alt="Business Skills — Evidence-first judgment for AI agents" width="100%">
  <h1>Business Skills</h1>
  <p><strong>Evidence-first judgment for AI agents.</strong></p>
  <p>Open, evidence-first skills for strategy, markets, forecasting, and business judgment.</p>

  [![CI](https://github.com/artemiosu/business-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/artemiosu/business-skills/actions/workflows/validate.yml)
  [![License](https://img.shields.io/badge/license-Apache--2.0-315c46.svg)](LICENSE)
  [![Agent Skills](https://img.shields.io/badge/format-Agent%20Skills-0b1220.svg)](https://agentskills.io)
  [![Contributions welcome](https://img.shields.io/badge/contributions-welcome-38bdf8.svg)](CONTRIBUTING.md)
  [![skills.sh](https://skills.sh/b/artemiosu/business-skills)](https://skills.sh/artemiosu/business-skills)
</div>

> Business advice is cheap. Auditable judgment is rare.

Business Skills is a growing, cross-agent collection of reusable workflows designed to make consequential business reasoning more explicit, falsifiable, and testable. Every skill should turn uncertainty into evidence, forecasts, decision rules, and learning loops—not confident-sounding prose.

Created and maintained by **[@artemiosu](https://github.com/artemiosu)**.

## See the decision, not just the prompt

| Question | Horizon Scout | Decision artifact |
|---|---|---|
| “Should a three-person team build an AI bookkeeping agent now?” | 7 dated signals · 5 source groups · adoption, timing, capture, and counterfactual gates · 3 resolvable forecasts | **MONITOR + bounded probe** — the trend is real, but standalone value capture is not proven |

**[Read the live, cutoff-dated case →](examples/ai-accounting-agents-2026/README.md)** · [Inspect its evidence](examples/ai-accounting-agents-2026/signals.jsonl) · [Track its forecasts](examples/ai-accounting-agents-2026/forecast-ledger.jsonl)

This is the core promise: replace “AI says this market is growing” with an auditable decision, explicit uncertainty, and a record that can later be scored.

## Start in 60 seconds

### Install with the Agent Skills CLI

```bash
npx skills add artemiosu/business-skills --skill horizon-scout
```

The CLI supports multiple skill-aware agents and records anonymous install telemetry by default; set `DISABLE_TELEMETRY=1` to opt out. A local installer is also available below.

### Codex/manual fallback

```bash
git clone https://github.com/artemiosu/business-skills.git
python3 business-skills/scripts/install.py --agent codex
```

Restart or reload Codex, then try:

```text
$horizon-scout Scan autonomous AI agents in US accounting over 24 months.
Separate real adoption, market timing, and value capture. Create a forecast ledger.
```

The installer supports `--agent codex|claude-code|cursor|copilot|windsurf|gemini|agents`, never overwrites an existing skill unless `--force` is supplied, and requires only Python 3.9+.

## Skills

| Skill | Use it when you need to… | Status |
|---|---|---|
| [Horizon Scout](skills/horizon-scout/README.md) | detect emerging technology or market shifts, challenge hype, build scenarios, and log calibrated forecasts | Experimental — mechanics tested, field calibration in progress |

More skills will follow. Each addition must pass the same evidence, safety, documentation, and evaluation standards.

## Works across agents

The portable source of truth is the open Agent Skills `SKILL.md` format. Codex-specific plugin/UI metadata is additive and never required by the core workflow.

| Host | Supported path |
|---|---|
| Codex / ChatGPT | Agent Skills core + optional Codex plugin metadata |
| Claude Code | Agent Skills core |
| Cursor | Agent Skills core; user or project skill directories |
| GitHub Copilot / Copilot CLI | Agent Skills core; `gh skill` or supported directories |
| Windsurf, Gemini CLI, other compatible hosts | Agent Skills core through the host or Agent Skills CLI |

Exact outputs cannot be identical across models and tool environments. Business Skills targets the same decision contract, evidence rules, safety boundaries, structured artifacts, and deterministic tests on every compatible host. See [Compatibility](docs/COMPATIBILITY.md).

## Why Horizon Scout is different

```text
Weak signals → source lineage → anti-hype gates → competing hypotheses
             → adoption / timing / value capture → scenarios
             → calibrated forecasts → reversible actions → resolution
```

- Treats trend reality, adoption, timing, and profit capture as separate questions.
- Records counterevidence and shared source ancestry instead of counting headlines.
- Uses simulated expert lenses to reveal cruxes—never as fake expert endorsement.
- Keeps scores separate from probabilities.
- Preserves forecasts so calibration can be measured later.
- Includes a dependency-free CLI and adversarial test suite.

## Pick your starting point

- **Founder:** `$horizon-scout Is this market ready inside my 18-month runway, and can a new entrant capture value?`
- **Strategist:** `$horizon-scout Map the stalled, base, and accelerated scenarios for this shift and define monitoring triggers.`
- **Investor or researcher:** `$horizon-scout Build a cutoff-safe evidence map, competing hypotheses, and resolvable forecasts for this thesis.`

Start with the [live AI-accounting case](examples/ai-accounting-agents-2026/README.md), then use the [synthetic walkthrough](examples/horizon-scout-synthetic-case.md) to inspect the minimal artifact shape.

## Use without installing everything

Copy `skills/horizon-scout` to your Codex skills directory. The folder contains the required `SKILL.md`, UI metadata, references, configuration, examples, and deterministic helpers.

```bash
python3 skills/horizon-scout/scripts/eval_harness.py
python3 skills/horizon-scout/scripts/horizon_scout.py assess \
  skills/horizon-scout/assets/example_signals.jsonl
```

## Trust model

These skills improve process; they do not predict the future or guarantee business outcomes. The current evaluation proves mechanics, not forecasting skill. Treat outputs as decision support. Verify important evidence and use qualified professional review for financial, legal, medical, or safety-critical decisions. See [Security](SECURITY.md) and the [Horizon Scout methodology](skills/horizon-scout/references/workflow.md).

## Contribute

Start with [Contributing](CONTRIBUTING.md), propose a skill through the [skill proposal form](https://github.com/artemiosu/business-skills/issues/new?template=skill-proposal.yml), or improve an existing workflow. Small, evidence-backed pull requests are preferred.

## Project

- [Roadmap](ROADMAP.md)
- [Governance](GOVERNANCE.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)
- [Citation](CITATION.cff)

Apache-2.0 licensed. Created and maintained by [@artemiosu](https://github.com/artemiosu). See [Authorship](AUTHORSHIP.md).

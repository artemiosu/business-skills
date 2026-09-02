# Contributing

Thank you for helping make business reasoning more rigorous and reusable.

## Before you start

- For a new skill, open a skill proposal first. Explain the recurring user need, failure modes, expected output, and how quality can be tested.
- For a small fix, open a focused pull request directly.
- Do not include secrets, personal data, proprietary datasets, copied paywalled text, or generated claims without sources.

## Skill quality bar

A skill must have a distinct recurring job, discriminating frontmatter, concise instructions, progressive disclosure, explicit uncertainty, safe defaults, observable verification, and at least one realistic failure test. Scripts should be standard-library-only when practical and deterministic where correctness matters.

Place each skill at `skills/<lowercase-hyphen-name>/`. Required: `SKILL.md`. Recommended: `agents/openai.yaml`. Add only references, scripts, and assets with a concrete runtime purpose.

## Development

```bash
python3 scripts/validate_repository.py
python3 skills/horizon-scout/scripts/eval_harness.py
```

For a new skill, also run the current Codex skill validator when available. Test a realistic request, not just wording or file presence.

## Pull requests

Keep one concern per PR. Describe the user problem, decision changes, test evidence, safety impact, and compatibility. Update the catalog and changelog for user-visible additions. By contributing, you agree that your contribution is licensed under Apache-2.0.

Contributors are responsible for everything they submit, including AI-assisted work. Do not list an AI tool as commit co-author. Disclose material AI assistance in the pull request when it affects provenance, licensing, evaluation, or reviewability.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately as described in [Security](SECURITY.md).

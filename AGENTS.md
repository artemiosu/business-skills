# Repository guidance

Preserve the distinction between repository documentation and runtime skill instructions. Keep each `SKILL.md` concise; route detailed conditional material to one-level-deep references. Do not add a new skill without a distinct recurring job and observable evaluation criteria.

Before finishing changes, run `python3 scripts/validate_repository.py`. Never weaken uncertainty, provenance, safety, or external-action boundaries to make examples look more impressive. Update `catalog.json`, the README catalog, and CHANGELOG together for user-visible skill additions.

Preserve cross-agent portability: use capabilities rather than vendor-specific tool names, tolerate unavailable tools, and keep host adapters additive. Public authorship belongs to the human contributor and repository owner; never add an AI system as author, co-author, maintainer, or copyright holder.

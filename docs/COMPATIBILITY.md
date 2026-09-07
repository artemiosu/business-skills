# Cross-agent compatibility

## Contract

Each skill uses the open Agent Skills core: a folder named after the skill, a `SKILL.md` with portable required frontmatter (`name`, `description`), relative references, and optional `scripts/`, `references/`, and `assets/`. Host-specific metadata lives outside this core contract and must not change the workflow's meaning.

Portable guarantees:

- the same decision workflow and safety boundaries;
- the same data formats and deterministic scripts;
- capability-based wording instead of vendor-specific tool names;
- graceful degradation when browsing, subagents, or execution is unavailable;
- no implicit authorization from a host's broader tool access.

Not guaranteed: identical prose, research coverage, model judgment, tools, latency, or token behavior. Cross-agent compatible means structurally portable and tested against shared behavioral invariants—not identical output.

## Installation

```bash
npx skills add artemiosu/business-skills
# Or select one skill:
npx skills add artemiosu/business-skills --skill evidence-echo-forensics
```

GitHub Copilot CLI (GitHub CLI 2.90+ while `gh skill` is preview):

```bash
gh skill install artemiosu/business-skills evidence-echo-forensics
```

Manual: copy the desired folder from `skills/` to a supported personal/project directory. Common locations include `~/.agents/skills/`, `~/.codex/skills/`, `~/.claude/skills/`, `~/.cursor/skills/`, and `~/.copilot/skills/`; consult current host documentation.

## Release test matrix

1. Validate the Agent Skills structure and every relative reference.
2. Run deterministic scripts under supported Python versions.
3. Run identical behavioral cases on available hosts, recording host/model/version.
4. Compare invariants: cutoff, lineage, counterevidence, gates, resolvability, and action boundary.
5. Publish deviations instead of silently forking behavior.

Status levels: `structural`, `mechanical`, `behavioral`, `field-calibrated`. Horizon Scout and Evidence Echo Forensics are structurally and mechanically tested; broad host behavioral and field results are pending.

## Adapter policy

`.codex-plugin/plugin.json` and `agents/openai.yaml` improve Codex distribution/UI. Other adapters may be added only as thin installation or metadata layers. Do not fork `SKILL.md` into divergent vendor versions unless a documented incompatibility makes a shared core impossible.

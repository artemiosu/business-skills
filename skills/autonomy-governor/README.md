# Autonomy Governor

> A tool may be capable of an action without the agent being authorized to take it.

Autonomy Governor turns an AI-agent workflow into a testable **Authority Contract**: principal, purpose, action, resource, limits, approvals, delegation, enforcement, rollback, logging, expiry, and stop conditions.

It answers **“What may this agent do, under whose authority, and what must stop it?”** It does not grant access or replace IAM, runtime policy enforcement, legal review, or human accountability.

## Install

```bash
npx skills add artemiosu/business-skills --skill autonomy-governor
```

Then try:

```text
$autonomy-governor Convert this customer-support agent workflow and tool list
into an authority contract. Separate autonomous actions, fresh approvals and
hard denials; include cumulative limits, retries, rollback and enforcement owners.
```

```text
$autonomy-governor Review this proposed agent for excessive agency. Find tool
capabilities that exceed delegated business authority, model-only controls,
hidden side effects, delegation expansion and stale approvals.
```

```text
$autonomy-governor Evaluate this single proposed action against the supplied
contract. Return ALLOW, APPROVAL_REQUIRED, DENY or HOLD, but do not execute it.
```

## The 30-second result

For a support agent that may read tickets and draft replies but needs approval to send messages or issue refunds:

```text
AUTHORITY STATUS
APPROVED FOR SIMULATION

AUTONOMY ENVELOPE
ALLOW: read assigned tickets; draft a reply in the case workspace
APPROVAL_REQUIRED: send external email; issue a refund up to USD 50
DENY: delete accounts; export customer data; change access rights

HARD-CONTROL GAPS
The email connector must enforce recipient scope and approval receipts.

STOP / ROLLBACK
Hold after unknown write state, two failed retries, policy expiry or tool drift.
```

Reproduce the bundled scenario suite:

```bash
python3 scripts/autonomy_governor.py validate assets/example_contract.json
python3 scripts/autonomy_governor.py lint assets/example_contract.json
python3 scripts/autonomy_governor.py simulate \
  assets/example_contract.json assets/example_scenarios.jsonl
```

Use `diff old-contract.json new-contract.json` before approving a revision; it exposes new actions, relaxed decisions, wider selectors, higher limits, removed controls, longer expiry, and expanded delegation.

Run those commands from this skill directory. Python is optional for contract design and required only for deterministic validation and simulation.

## What makes it different

| Artifact | What it misses |
|---|---|
| Tool permission list | Capability is not delegated authority or task intent |
| Safety prompt | Model instructions are not a hard enforcement boundary |
| Risk register | Risks are listed but concrete actions are not decided |
| Approval checkbox | Approval may be stale, unbound, self-issued, or overbroad |
| **Autonomy Governor** | Compiles the complete action universe into restrictive, testable decisions and implementation controls |

The core relation is:

```text
principal × agent identity × purpose × action × resource
× context × limits × time × enforcement = authority envelope
```

Remove or change one term and the decision must be recomputed.

## Four outcomes, no fake confidence score

- `ALLOW`
- `APPROVAL_REQUIRED`
- `DENY`
- `HOLD`

The result is deterministic for the supplied contract and request. It is not a probability that an action is safe or lawful.

## Auditable artifacts

- action-universe and side-effect inventory;
- exact allow/approval/deny rules with restrictive precedence;
- per-action and cumulative limits;
- action-bound approval receipts and separation of duties;
- delegation attenuation and maximum depth;
- hard-control versus model-instruction map;
- idempotency, partial-failure, stop and rollback plan;
- expiry, revocation, change control and test scenarios.

See the [runtime instructions](SKILL.md), [workflow](references/workflow.md), [schemas](references/schemas.md), [threat model](references/threat-model.md), [evaluation protocol](references/evaluation.md), and [standards map](references/standards.md).

## Evidence status

**Experimental.** The deterministic utility tests artifact consistency and adversarial invariants. It is not a production authorization server, and broad host or field validation is not yet established. Deployment requires real IAM/tool enforcement, approval infrastructure, monitoring, and accountable review.

```bash
python3 scripts/eval_harness.py
```

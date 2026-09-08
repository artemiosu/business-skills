# Authority-contract workflow

Use this reference for Design, Change, or Incident mode. The purpose is to surface business decisions that ordinary permission lists hide and produce artifacts that engineering, security, legal, operations, and accountable owners can challenge.

## 1. Define the decision boundary

Record:

- workflow and measurable intended outcome;
- accountable owner and delegating principal;
- agent identity, build/version, operator, and execution environment;
- explicit non-goals and affected parties;
- applicable policy, contractual, jurisdictional, and professional-review dependencies;
- effective, expiry, review, and revocation dates.

Do not infer an authority basis from seniority, tool access, a ticket, a prompt, or possession of credentials. If the delegating principal cannot be identified, keep the contract in `draft` and mark deployment blocked.

## 2. Build the action universe before writing rules

Inventory actions from the workflow, tool schemas, credentials, integrations, retries, fallbacks, and error handlers. Include indirect effects.

| Effect | Examples | Often-hidden side effects |
|---|---|---|
| `read` | query, retrieve, inspect | access logging, read receipts, data aggregation |
| `create` | draft, ticket, file, record | notifications, indexing, billing |
| `update` | edit, tag, configure | triggers, downstream sync, lost prior state |
| `delete` | remove, revoke, cancel | cascades, retention/legal hold conflicts |
| `execute` | run code, deploy, invoke workflow | arbitrary downstream effects |
| `communicate` | email, post, publish, call | commitments, disclosure, impersonation |
| `transfer` | purchase, refund, trade, pay | financial/legal commitment |
| `approve` | authorize access or transaction | privilege creation and separation-of-duty failure |

For every action, state the specific resource families, environments, tools, data classes, likely affected parties, side effects, and maximum plausible blast radius. Compare the tool's technical capability with the intended action universe; unused functionality should be removed or hard-denied.

## 3. Classify consequence without fake precision

Use the most severe applicable tier:

- `low`: read-only public or contained analysis with negligible external effect.
- `medium`: bounded, reversible internal state change with known owner and recovery.
- `high`: external communication, confidential data, production change, financial effect, access change, material customer/employee impact, or difficult compensation.
- `critical`: irreversible or large-scale impact; credential/security control change; legal signature; autonomous trading; safety-critical or rights-affecting decision; action prohibited by policy.

Tier is a routing category, not a probability or universal compliance decision. Document why it applies. When impact and likelihood disagree, do not average them into permission.

## 4. Write restrictive rules

Each rule contains:

- explicit action types and effects;
- resource prefixes, tools, environments, and data classes;
- decision: `allow`, `require_approval`, or `deny`;
- risk tier and rationale;
- mandatory request fields;
- per-action, cumulative, rate, and retry limits where applicable;
- required controls and their enforcement layer;
- approval, delegation, and recovery requirements.

`deny` dominates all matching rules, followed by `hold` conditions and then approval. Do not depend on rule ordering. Do not use natural-language exceptions such as “unless reasonable” in a machine decision field.

### Limits

Distinguish:

- per-action amount from cumulative amount;
- count from value;
- rolling window from calendar period;
- tenant/user/resource scope from global scope;
- retry count from repeated business actions;
- tool-call rate from real-world impact rate.

If a cumulative limit exists, the decision point needs authoritative usage state. Missing or delayed state produces `HOLD`, not an assumed zero.

## 5. Design approval as a protocol

A valid approval receipt should bind:

- contract ID and version;
- exact canonical action digest;
- approving identity and authorized role;
- decision and timestamp;
- expiry or single-use semantics;
- independent system of record;
- separation from the requesting agent and, when required, the requesting principal.

Approval for a plan is not automatically approval for every execution step. A materially changed recipient, amount, resource, environment, data set, tool, or side effect changes the action digest and invalidates the old receipt.

The local utility accepts only receipts marked `external_system` for an executable `ALLOW`. It cannot validate the external system's signature or role directory; production enforcement must do so. Human-attested and synthetic receipts remain non-executable.

## 6. Attenuate delegation

Represent the chain from principal through parent and child agents. For each hop require:

- verified parent identity and active contract;
- purpose subset;
- action/effect subset;
- equal or narrower resources, data classes, environment, limits, and duration;
- equal or stricter decision and approval requirements;
- decreasing remaining delegation depth.

Never allow a child to mint a new approver, exception, credential scope, or rollback waiver. If subset relations cannot be proved, deny delegation.

## 7. Map controls to enforcement

Use four layers:

1. `external_enforcement`: IAM/OAuth scope, capability token, tool wrapper, transaction limit, approval service, database policy, sandbox, network control.
2. `workflow`: state machine, queue, checkpoint, reconciler, retry controller, policy decision point.
3. `monitoring`: audit sink, anomaly detection, budget meter, alert and revocation channel.
4. `model_instruction`: prompt, rubric, self-check, explanation.

For high-impact mutations, a model instruction alone is a deployment blocker. Name the control owner, mechanism, status, and evidence of verification. Avoid saying “human in the loop” without specifying who, when, what they see, what action is bound, and whether denial is technically enforced.

## 8. Engineer failure semantics

Before execution, define:

- precondition snapshot and state version;
- idempotency key or explicit non-retryability;
- success receipt and postcondition;
- maximum attempts and backoff;
- partial-failure state reconciliation;
- rollback or compensating action, owner, time objective, and tested status;
- kill switch and credential/token revocation;
- customer/affected-party notification decision path.

Unknown state after a write triggers `HOLD`. Do not retry a payment, message, order, deletion, or deployment merely because the first response timed out.

## 9. Test the contract

At minimum cover:

- ordinary allow, approval, and denial;
- exact amount/count/rate boundaries;
- missing cumulative usage;
- different tenant, recipient, environment, or data class;
- expired contract and approval;
- approval digest mismatch;
- prompt-injected or untrusted authority claim;
- child-agent scope expansion;
- rule conflict;
- tool or identity drift;
- partial failure and duplicate retry;
- unavailable hard control;
- prohibited and rights-affecting actions.

Do not approve the contract if the declared action universe is not fully governed or a critical rule depends only on model compliance.

## 10. Change and incident modes

### Change

Create a new version. Diff authority, not just text:

- newly allowed actions;
- broader resources, environments, recipients, data classes, or limits;
- reduced approval or control requirements;
- longer lifetime or deeper delegation;
- removed stop, audit, or rollback conditions.

Any authority expansion needs explicit accountable approval and fresh tests. Revoke the old version after migration; never silently edit an approved artifact.

### Incident

Return `HOLD`, preserve evidence, identify last known state, revoke or narrow authority through the actual control plane, reconcile side effects, and follow the accountable incident process. The skill may draft the containment plan but may not execute revocation, communication, rollback, or remediation without separate authorization.

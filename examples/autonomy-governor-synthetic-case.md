# Autonomy Governor synthetic walkthrough

> Fictional evaluation fixture. It contains no real organization, approval, identity, credential, customer, or authority grant and cannot authorize execution.

## Decision problem

A customer-support agent is proposed for assigned billing cases. It should read a case and prepare a draft autonomously, pause before external communication or refund, and never delete an account or export customer data.

The ordinary tool list is misleading:

```text
CRM connector: read, create, update, export
Mail connector: draft, send
Billing connector: look up charge, refund
Identity connector: view and delete account
```

Technical capability is wider than the intended business authority. Autonomy Governor therefore starts from the complete action universe, not the happy-path workflow.

## Compiled authority envelope

| Action | Effect | Policy decision | Hard boundary | Recovery |
|---|---|---|---|---|
| Read assigned ticket | confidential read | `ALLOW` | CRM assignment filter | privacy incident path |
| Save internal draft | create | `ALLOW` | draft-only endpoint + idempotency | delete unsent draft |
| Send customer email | external communication | `APPROVAL_REQUIRED` | gateway verifies exact recipient, content digest, role and expiry | correction workflow |
| Refund up to USD 50 | financial transfer | `APPROVAL_REQUIRED` | billing service enforces exact approval, USD 50/action, USD 200/day, five/day, no retry | separate correcting transaction |
| Delete account | irreversible delete | `DENY` | agent credential lacks deletion scope | separate account-governance process |
| Export customer data | restricted read/aggregation | `DENY` by default | no matching rule or credential scope | security review |

The contract also holds all actions when the policy store or a required control is unavailable, the tool changes, or a write outcome becomes unknown.

## Boundary tests

The bundled suite contains 14 scenarios:

- ordinary read and draft;
- message awaiting approval despite an injected “executive approval” claim;
- account deletion and unlisted export;
- refund at USD 50, above USD 50, and after cumulative spend reaches USD 180;
- partial write state and unavailable control;
- wrong agent, forbidden delegation, expired contract, and stop condition.

Expected summary:

```text
14/14 scenario decisions match
ALLOW: 2
APPROVAL_REQUIRED: 2
DENY: 6
HOLD: 4
execution_authorized: false for every synthetic scenario
```

## Reproduce

From `skills/autonomy-governor`:

```bash
python3 scripts/autonomy_governor.py validate assets/example_contract.json
python3 scripts/autonomy_governor.py lint assets/example_contract.json
python3 scripts/autonomy_governor.py coverage assets/example_contract.json
python3 scripts/autonomy_governor.py simulate \
  assets/example_contract.json assets/example_scenarios.jsonl
python3 scripts/eval_harness.py
```

The [contract](../skills/autonomy-governor/assets/example_contract.json) is deliberately marked `case_purpose: synthetic_fixture`. Even a structurally valid external approval receipt can change the simulated policy decision to `ALLOW`, but the utility always reports `execution_authorized: false` because it is not a real policy-enforcement point.

## What this proves—and does not

It proves deterministic rule matching, restrictive precedence, exact-action approval binding, limits, default denial, stop conditions, and fail-closed mechanics on this fixture. It does not prove that a real principal had authority, a real control exists, the policy is legally sufficient, or any real action is safe to execute.

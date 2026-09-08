# Artifact schemas

The machine-readable contract is JSON. The deterministic utility rejects duplicate JSON keys, non-finite numbers, malformed timestamps, unknown top-level fields, wildcard selectors, and unsafe temporal ordering. See the [authority-contract schema](../assets/authority-contract.schema.json) and [action-request schema](../assets/action-request.schema.json) for editor support; the Python validator remains the executable contract for this release.

## Authority contract

Required top-level fields:

```json
{
  "schema_version": "1.0",
  "record_type": "authority_contract",
  "contract_id": "support-agent-v1",
  "version": 1,
  "status": "draft | approved | retired",
  "case_purpose": "operational | synthetic_fixture",
  "title": "Bounded customer-support authority",
  "purpose": "Resolve assigned billing tickets",
  "non_goals": ["Do not change account access"],
  "owner_id": "support-operations",
  "principal": {
    "principal_id": "support-director",
    "kind": "person | role | service",
    "authority_basis": "Approved operating policy GOV-17"
  },
  "agent": {
    "agent_id": "support-agent",
    "build_id": "sha256:...",
    "identity_status": "verified | declared | unknown"
  },
  "issued_at": "2026-09-08T12:00:00Z",
  "effective_at": "2026-09-08T12:00:00Z",
  "expires_at": "2026-10-08T12:00:00Z",
  "review_at": "2026-09-22T12:00:00Z",
  "default_decision": "deny",
  "enforcement_mode": "design_only | partially_enforced | runtime_enforced",
  "action_universe": [],
  "rules": [],
  "stop_conditions": [],
  "delegation": {},
  "audit": {},
  "change_control": {}
}
```

`case_purpose=synthetic_fixture` prevents `execution_authorized=true`, even when a simulated decision is `ALLOW`.

## Action-universe item

```json
{
  "action_type": "send_email",
  "effect": "communicate",
  "resources": ["crm/cases/assigned"],
  "environments": ["production"],
  "tools": ["mail.send"],
  "data_classes": ["internal", "confidential"],
  "side_effects": ["external disclosure", "customer commitment"]
}
```

Allowed effects: `read`, `create`, `update`, `delete`, `execute`, `communicate`, `transfer`, `approve`.

## Rule

```json
{
  "rule_id": "email-send-needs-approval",
  "description": "A support lead approves the exact outbound message",
  "decision": "require_approval",
  "risk_tier": "high",
  "action_types": ["send_email"],
  "effects": ["communicate"],
  "resource_prefixes": ["crm/cases/assigned/"],
  "environments": ["production"],
  "tools": ["mail.send"],
  "data_classes": ["internal", "confidential"],
  "required_context": ["target", "purpose", "idempotency_key"],
  "limits": {
    "max_actions": 20,
    "window_seconds": 3600,
    "max_retries": 1
  },
  "controls": [
    {
      "control_id": "recipient-scope",
      "layer": "external_enforcement",
      "mechanism": "Mail gateway checks customer address against assigned case",
      "owner_id": "platform-security",
      "status": "verified"
    }
  ],
  "approval": {
    "mode": "fresh",
    "approver_roles": ["support-lead"],
    "separation_of_duties": true,
    "max_age_seconds": 900
  },
  "rollback": {
    "classification": "compensatable",
    "procedure": "Open correction workflow and notify support lead",
    "owner_id": "support-operations",
    "tested_status": "tested | untested | not_applicable"
  }
}
```

Selectors are exact strings except `resource_prefixes`, which use literal prefixes. `*`, `?`, regex, and path traversal are rejected. An empty selector array is invalid. Omitting a selector means “not restricted on this dimension” and is linted when risky.

### Limits

Supported keys:

- `max_amount` and `currency`;
- `max_cumulative_amount` and `currency`;
- `max_actions` and `window_seconds`;
- `max_retries`.

Requests must include authoritative `usage` when a cumulative/count limit applies. Bounds are inclusive. Negative values, booleans masquerading as numbers, and mixed currencies are invalid.

## Delegation

```json
{
  "allowed": false,
  "max_depth": 0,
  "allowed_agent_ids": [],
  "attenuation_required": true
}
```

The current utility verifies identity, depth, and allow-list membership. It cannot prove semantic subset relations across separate contracts; production delegation requires an external policy engine or explicit human review of the contract diff.

## Action request

```json
{
  "record_type": "action_request",
  "request_id": "req-001",
  "timestamp": "2026-09-09T10:00:00Z",
  "principal_id": "support-director",
  "agent_id": "support-agent",
  "action_type": "send_email",
  "effect": "communicate",
  "resource": "crm/cases/assigned/CASE-42",
  "environment": "production",
  "tool_id": "mail.send",
  "data_class": "confidential",
  "target": "customer on CASE-42",
  "purpose": "Send approved resolution",
  "state_status": "known",
  "retry_count": 0,
  "idempotency_key": "CASE-42-resolution-v1",
  "delegation_chain": [],
  "triggered_stop_conditions": [],
  "usage": {"actions_in_window": 3, "cumulative_amount": 0, "currency": "USD"}
}
```

Optional `amount`:

```json
{"value": 25, "currency": "USD"}
```

Optional approval receipt:

```json
{
  "approval_receipt": {
    "receipt_id": "approval-123",
    "source": "external_system | human_attested | synthetic_fixture",
    "approver_id": "lead-7",
    "approver_role": "support-lead",
    "decision": "approved",
    "issued_at": "2026-09-09T09:58:00Z",
    "expires_at": "2026-09-09T10:13:00Z",
    "contract_id": "support-agent-v1",
    "contract_version": 1,
    "action_digest": "sha256:..."
  }
}
```

Compute the digest with `digest-request` before seeking approval. The digest excludes only `approval_receipt`; changing any action field invalidates the receipt.

## Version diff

`diff old.json new.json` requires the same contract ID, a higher version, and `new.change_control.previous_version == old.version`. It reports authority expansions, reductions, and changes that need manual subset review. New permissive rules, relaxed decisions, broader selectors, increased or removed limits, removed controls, longer expiry, and expanded delegation are never treated as routine text edits.

## Scenario suite

One JSON object per line:

```json
{
  "name": "external email pauses for approval",
  "request": {"record_type": "action_request"},
  "expected_decision": "APPROVAL_REQUIRED"
}
```

Allowed expected decisions: `ALLOW`, `APPROVAL_REQUIRED`, `DENY`, `HOLD`.

## Decision result

```json
{
  "decision": "APPROVAL_REQUIRED",
  "execution_authorized": false,
  "matched_rule_ids": ["email-send-needs-approval"],
  "reasons": ["fresh external approval is required"],
  "action_digest": "sha256:...",
  "contract_digest": "sha256:...",
  "required_controls": ["recipient-scope"],
  "warnings": []
}
```

`execution_authorized` is always false in this local utility. The decision is a policy-test result, not a runtime authorization. A production policy-enforcement point must independently verify identity, signatures, revocation, single use, limits, controls, and the current user's authority.

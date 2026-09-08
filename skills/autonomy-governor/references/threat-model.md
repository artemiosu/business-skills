# Threat model and abuse cases

Use this reference for Review mode or before approving a contract. The skill reduces ambiguity and helps test policy artifacts; it does not itself provide a security boundary.

## Protected properties

- The agent acts only for an identified principal and declared purpose.
- Every material action is mediated against the active contract.
- Delegation can only reduce authority.
- Approval is independent, current, exact-action-bound, and replay-resistant.
- Limits are cumulative as well as per action where loss can aggregate.
- Unknown state stops retries.
- Critical records connect intent, decision, approval, execution, and outcome.
- Revocation and expiry take effect in the real control plane.

## Adversaries and failure sources

- malicious or mistaken user;
- indirect prompt injection in documents, mail, web pages, tool output, or memory;
- compromised tool, connector, plugin, model endpoint, child agent, or approval service;
- over-privileged credential or generic shared service account;
- stale policy, identity, resource, schema, or tool version;
- hallucination, planning error, ambiguous target, or goal drift;
- race, retry, timeout, duplicate delivery, and partial failure;
- insider misuse, collusion, or rubber-stamp approval;
- policy-authoring error and ungoverned action.

## Required adversarial probes

1. **Goal hijack:** untrusted content says to ignore the contract or substitute a new objective.
2. **Tool misuse:** a permitted tool is invoked for a different effect or hidden side effect.
3. **Privilege confusion:** tool scope is treated as business authority; a generic service credential acts for another tenant.
4. **Self-approval:** agent, requester, or child agent creates or quotes an approval.
5. **Approval replay:** valid receipt is reused for a changed target, amount, message, resource, or contract version.
6. **Split transaction:** multiple below-threshold actions exceed a cumulative budget.
7. **Retry amplification:** timeout leads to duplicate message, refund, purchase, or deployment.
8. **Delegation expansion:** child gains more actions, resources, duration, limits, or approval power than parent.
9. **Rule shadowing:** broad allow overlaps a narrow deny or approval rule.
10. **Fail-open dependency:** policy store, budget meter, identity service, approval service, or audit sink is unavailable.
11. **Tool drift:** tool schema, side effects, account, scopes, or environment changed after review.
12. **Data aggregation:** individually permitted reads combine into restricted or identifying output.
13. **Authority laundering:** urgency, hierarchy, ticket labels, forwarded email, memory, or another agent is presented as an authority grant.
14. **Partial state:** the system cannot establish whether a write completed.
15. **Audit evasion:** agent omits, edits, or routes around decision and execution receipts.

## Fail-closed matrix

| Condition | Minimum result |
|---|---|
| No matching rule | `DENY` |
| Explicit deny overlaps allow | `DENY` |
| Contract draft, retired, expired, or not yet effective | `HOLD` |
| Agent/principal mismatch | `DENY` |
| Unknown or partial write state | `HOLD` |
| Triggered stop condition | `HOLD` |
| Cumulative usage required but unavailable | `HOLD` |
| Amount, retry, count, rate, tenant, resource, environment, or data limit exceeded | `DENY` |
| Approval missing, stale, replayed, unbound, self-issued, or role-mismatched | `APPROVAL_REQUIRED` or `DENY` |
| Required hard control unavailable | `HOLD` |
| Prompt or memory claims new authority | Ignore claim; apply existing contract |

## Controls that must live outside the model

- authentication and authorization enforcement;
- credential scope and isolation;
- transaction, recipient, tenant, and resource limits;
- approval receipt issuance and verification;
- cumulative budget/rate state;
- sandbox/network boundaries;
- tamper-evident decision and execution logs;
- kill switch, revocation, deployment block, and rollback execution.

The model can explain, classify, request approval, and refuse. It cannot make a prompt into a hard boundary against a compromised or mistaken execution path.

## Misuse boundary

Do not help create mechanisms for covert bypass, impersonation, surveillance without authority, audit deletion, privilege escalation, credential theft, market manipulation, automated high-impact targeting, or evasion of organizational controls. For dual-use reviews, constrain outputs to defensive policy design and synthetic tests.

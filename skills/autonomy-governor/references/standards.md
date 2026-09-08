# Standards and guidance map

This skill is informed by the following public sources as retrieved on 2026-09-08. It does not claim certification, legal compliance, or conformance to a runtime-control specification.

## Agent Skills

- [Agent Skills specification](https://agentskills.io/specification): portable `SKILL.md` structure and progressive disclosure.

## Identity, authorization, and AI governance

- [NIST NCCoE draft concept paper: Software and AI Agent Identity and Authorization](https://www.nccoe.nist.gov/publications/other/accelerating-adoption-software-and-ai-agent-identity-and-authorization-concept): agent identification, authentication, least privilege, dynamic authorization, delegation, binding human and agent identities, auditing, and prompt-injection containment. It is a February 2026 draft concept paper, not a completed practice guide.
- [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/): governance, roles, lifecycle risk management, human oversight, measurement, monitoring, incident response, and decommissioning. NIST states AI RMF 1.0 is being updated.
- [NIST AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/): voluntary implementation suggestions; not a universal checklist.

## Agent security and runtime control

- [OWASP Agent Control Standard](https://genai.owasp.org/resource/agent-control-standard-acs/): inspectable, traceable, instrumentable agents and portable runtime policy hooks. ACS joined the OWASP GenAI Security Project on 2026-09-01 and is in public-preview development. Autonomy Governor produces a design artifact and policy-test oracle; it is not an ACS middleware implementation.
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/): goal hijacking, tool misuse, identity/privilege abuse, supply-chain risk, unexpected code execution, memory/context poisoning, insecure inter-agent communication, cascading failure, human-agent trust exploitation, and rogue behavior.
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/): minimize functionality, permissions, and autonomy; execute in user context; require approval for high-impact actions; enforce complete mediation downstream.

## Practical agent design

- [OpenAI: A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/): rate tool risk by access, reversibility, permissions, and financial impact; combine guardrails with authentication, authorization, strict access control, and standard software security; trigger human intervention for high-risk actions and exceeded failure thresholds.

## Mapping used by this skill

| Source concept | Autonomy Governor artifact |
|---|---|
| least privilege / complete mediation | action universe, exact selectors, default deny |
| agent and principal identity | principal, agent build, delegation chain |
| human oversight | action-bound approval protocol and separation of duties |
| traceability / observability | decision, approval, execution, and outcome receipts |
| runtime controls | enforcement-layer map and deployment blockers |
| risk lifecycle | issue, review, expiry, revocation, change and incident modes |
| excessive agency | capability-versus-authority gap and adversarial scenarios |
| cascading/partial failure | stop conditions, idempotency, reconciliation, rollback |

Where an external standard changes, update this map and re-run the contract's threat model. Do not silently reinterpret an approved contract to follow a newer standard.

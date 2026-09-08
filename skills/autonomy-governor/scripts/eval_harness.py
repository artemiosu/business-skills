#!/usr/bin/env python3
"""Adversarial mechanical evaluation for Autonomy Governor."""

import copy
import datetime as dt
import json
import pathlib
import subprocess
import sys
import tempfile


SKILL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import autonomy_governor as ag  # noqa: E402


CONTRACT_PATH = SKILL / "assets" / "example_contract.json"
SCENARIOS_PATH = SKILL / "assets" / "example_scenarios.jsonl"
BASE = ag.load_json(CONTRACT_PATH)
SCENARIOS = ag.load_jsonl(SCENARIOS_PATH)
REQUESTS = {item["request"]["request_id"]: item["request"] for item in SCENARIOS}
TESTS = []


def test(name):
    def decorator(function):
        TESTS.append((name, function))
        return function
    return decorator


def clone(value):
    return copy.deepcopy(value)


def request(request_id):
    return clone(REQUESTS[request_id])


def next_version(contract):
    updated = clone(contract)
    updated["version"] = contract["version"] + 1
    updated["change_control"]["previous_version"] = contract["version"]
    return updated


def external_receipt(contract, req, approver_id="lead-7", role="support-lead", source="external_system"):
    timestamp = dt.datetime.fromisoformat(req["timestamp"].replace("Z", "+00:00"))
    return {
        "receipt_id": "approval-123",
        "source": source,
        "approver_id": approver_id,
        "approver_role": role,
        "decision": "approved",
        "issued_at": (timestamp - dt.timedelta(minutes=2)).isoformat().replace("+00:00", "Z"),
        "expires_at": (timestamp + dt.timedelta(minutes=13)).isoformat().replace("+00:00", "Z"),
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "action_digest": ag.action_digest(req),
    }


@test("example contract validates")
def _():
    assert ag.validate_contract(BASE) == []


@test("example contract lints without blocking errors")
def _():
    report = ag.lint_contract(BASE)
    assert report["valid"] and report["mechanically_complete"]
    assert report["deployment_ready"] is False


@test("bundled scenario suite passes")
def _():
    report = ag.simulate(BASE, SCENARIOS)
    assert report["all_passed"] and report["passed"] == 14


@test("canonical contract digest is deterministic")
def _():
    reordered = {key: BASE[key] for key in reversed(list(BASE))}
    assert ag.digest(BASE) == ag.digest(reordered)


@test("approval receipt is excluded from action digest")
def _():
    req = request("req-email")
    before = ag.action_digest(req)
    req["approval_receipt"] = external_receipt(BASE, req)
    assert ag.action_digest(req) == before


@test("rule order cannot change a decision")
def _():
    req = request("req-read")
    first = ag.decide(BASE, req)
    altered = clone(BASE)
    altered["rules"] = list(reversed(altered["rules"]))
    second = ag.decide(altered, req)
    assert first["decision"] == second["decision"] == "ALLOW"


@test("explicit deny overrides a triggered hold")
def _():
    req = request("req-delete")
    req["triggered_stop_conditions"] = ["tool-drift"]
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("no matching rule denies even when the contract is expired")
def _():
    req = request("req-unlisted")
    req["timestamp"] = "2026-10-09T10:00:00Z"
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("unknown post-write state holds")
def _():
    assert ag.decide(BASE, request("req-unknown"))["decision"] == "HOLD"


@test("prompt text cannot manufacture approval")
def _():
    result = ag.decide(BASE, request("req-email"))
    assert result["decision"] == "APPROVAL_REQUIRED"


@test("human-attested receipt does not satisfy executable approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req, source="human_attested")
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("synthetic receipt does not satisfy executable approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req, source="synthetic_fixture")
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("agent self-approval is denied")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req, approver_id="support-agent")
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("principal approval is denied when duties must be separate")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req, approver_id="support-director")
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("valid external receipt satisfies policy simulation")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req)
    result = ag.decide(BASE, req)
    assert result["decision"] == "ALLOW"
    assert result["execution_authorized"] is False


@test("changed target invalidates an approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req)
    req["target"] = "different customer"
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("changed contract version invalidates an approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req)
    req["approval_receipt"]["contract_version"] = 2
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("expired receipt requires fresh approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req)
    req["approval_receipt"]["expires_at"] = "2026-09-09T09:59:00Z"
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("stale receipt requires fresh approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req)
    req["approval_receipt"]["issued_at"] = "2026-09-09T09:00:00Z"
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("wrong approver role requires approval")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req, role="marketing-lead")
    assert ag.decide(BASE, req)["decision"] == "APPROVAL_REQUIRED"


@test("malformed receipt is rejected before decision")
def _():
    req = request("req-read")
    req["approval_receipt"] = {"claim": "approved"}
    assert any("approval_receipt missing fields" in item for item in ag.validate_request(req, BASE))


@test("refund boundary is inclusive")
def _():
    assert ag.decide(BASE, request("req-refund-50"))["decision"] == "APPROVAL_REQUIRED"


@test("per-action amount excess is denied")
def _():
    assert ag.decide(BASE, request("req-refund-51"))["decision"] == "DENY"


@test("split transactions cannot evade cumulative amount")
def _():
    assert ag.decide(BASE, request("req-refund-cumulative"))["decision"] == "DENY"


@test("missing authoritative usage holds a limited action")
def _():
    req = request("req-refund-50")
    del req["usage"]
    assert ag.decide(BASE, req)["decision"] == "HOLD"


@test("action count limit is enforced")
def _():
    req = request("req-refund-50")
    req["usage"]["actions_in_window"] = 5
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("retry limit is enforced")
def _():
    req = request("req-email")
    req["retry_count"] = 1
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("currency mismatch is denied")
def _():
    req = request("req-refund-50")
    req["amount"]["currency"] = "EUR"
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("boolean amount is rejected")
def _():
    req = request("req-refund-50")
    req["amount"]["value"] = True
    assert any("amount.value" in item for item in ag.validate_request(req, BASE))


@test("boolean limit is rejected")
def _():
    contract = clone(BASE)
    contract["rules"][3]["limits"]["max_amount"] = True
    assert any("max_amount" in item for item in ag.validate_contract(contract))


@test("duplicate JSON keys are rejected")
def _():
    try:
        ag.parse_json_text('{"a":1,"a":2}')
    except ag.ContractError:
        return
    raise AssertionError("duplicate key accepted")


@test("NaN is rejected")
def _():
    try:
        ag.parse_json_text('{"value":NaN}')
    except ag.ContractError:
        return
    raise AssertionError("NaN accepted")


@test("wildcard selector is rejected")
def _():
    contract = clone(BASE)
    contract["rules"][0]["resource_prefixes"] = ["crm/*"]
    assert any("wildcard" in item for item in ag.validate_contract(contract))


@test("resource traversal is rejected")
def _():
    req = request("req-read")
    req["resource"] = "crm/cases/assigned/../all"
    assert any("traversal" in item for item in ag.validate_request(req, BASE))


@test("resource prefixes require a boundary")
def _():
    contract = clone(BASE)
    contract["rules"][0]["resource_prefixes"] = ["crm/cases/assigned"]
    assert any("resource boundary" in item for item in ag.validate_contract(contract))


@test("different tool does not match a rule")
def _():
    req = request("req-read")
    req["tool_id"] = "crm.export"
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("different tenant-like resource does not match prefix")
def _():
    req = request("req-read")
    req["resource"] = "crm/cases/unassigned/CASE-42"
    assert ag.decide(BASE, req)["decision"] == "DENY"


@test("action universe gap blocks lint")
def _():
    contract = clone(BASE)
    contract["action_universe"].append({
        "action_type": "grant_access", "effect": "approve", "resources": ["identity/access/"],
        "environments": ["production"], "tools": ["identity.grant"],
        "data_classes": ["restricted"], "side_effects": ["privilege creation"],
    })
    assert any("has no governing rule" in item for item in ag.lint_contract(contract)["errors"])


@test("high-risk autonomous allow blocks lint")
def _():
    contract = clone(BASE)
    contract["rules"][2]["decision"] = "allow"
    del contract["rules"][2]["approval"]
    assert any("cannot autonomously allow high" in item for item in ag.lint_contract(contract)["errors"])


@test("critical approval is blocked")
def _():
    contract = clone(BASE)
    rule = contract["rules"][4]
    rule["decision"] = "require_approval"
    rule["approval"] = {"mode": "fresh", "approver_roles": ["identity-governor"], "separation_of_duties": True, "max_age_seconds": 300}
    assert any("critical actions must be denied" in item for item in ag.lint_contract(contract)["errors"])


@test("model-only state control blocks lint")
def _():
    contract = clone(BASE)
    contract["rules"][1]["controls"] = [{
        "control_id": "prompt-check", "layer": "model_instruction", "mechanism": "Agent checks itself",
        "owner_id": "agent-platform", "status": "verified",
    }]
    assert any("without a verified external_enforcement" in item for item in ag.lint_contract(contract)["errors"])


@test("sensitive read without hard scope blocks lint")
def _():
    contract = clone(BASE)
    contract["rules"][0]["controls"] = [contract["rules"][0]["controls"][1]]
    assert any("non-public data" in item for item in ag.lint_contract(contract)["errors"])


@test("per-action money cap without cumulative cap blocks lint")
def _():
    contract = clone(BASE)
    del contract["rules"][3]["limits"]["max_cumulative_amount"]
    assert any("no cumulative amount" in item for item in ag.lint_contract(contract)["errors"])


@test("missing required hard control holds decision")
def _():
    assert ag.decide(BASE, request("req-control-down"))["decision"] == "HOLD"


@test("draft contract holds otherwise matching action")
def _():
    contract = clone(BASE)
    contract["status"] = "draft"
    assert ag.decide(contract, request("req-read"))["decision"] == "HOLD"


@test("future-effective contract holds")
def _():
    contract = clone(BASE)
    contract["effective_at"] = "2026-09-10T12:00:00Z"
    contract["review_at"] = "2026-09-22T12:00:00Z"
    assert ag.decide(contract, request("req-read"))["decision"] == "HOLD"


@test("invalid temporal order is rejected")
def _():
    contract = clone(BASE)
    contract["expires_at"] = "2026-09-01T12:00:00Z"
    assert any("timestamps must satisfy" in item for item in ag.validate_contract(contract))


@test("unknown stop condition is rejected")
def _():
    req = request("req-read")
    req["triggered_stop_conditions"] = ["invented-stop"]
    assert any("unknown IDs" in item for item in ag.validate_request(req, BASE))


@test("disabled delegation denies child chain")
def _():
    assert ag.decide(BASE, request("req-delegated"))["decision"] == "DENY"


@test("delegation depth is enforced")
def _():
    contract = clone(BASE)
    contract["delegation"] = {"allowed": True, "max_depth": 1, "allowed_agent_ids": ["parent-agent", "other-agent"], "attenuation_required": True}
    req = request("req-delegated")
    req["delegation_chain"] = ["parent-agent", "other-agent"]
    assert ag.decide(contract, req)["decision"] == "DENY"


@test("delegation allow list is enforced")
def _():
    contract = clone(BASE)
    contract["delegation"] = {"allowed": True, "max_depth": 1, "allowed_agent_ids": ["approved-parent"], "attenuation_required": True}
    assert ag.decide(contract, request("req-delegated"))["decision"] == "DENY"


@test("conflicting allow and deny resolves to deny")
def _():
    contract = clone(BASE)
    deny = clone(contract["rules"][0])
    deny["rule_id"] = "deny-read-during-review"
    deny["decision"] = "deny"
    contract["rules"].append(deny)
    assert ag.decide(contract, request("req-read"))["decision"] == "DENY"
    contract["rules"] = list(reversed(contract["rules"]))
    assert ag.decide(contract, request("req-read"))["decision"] == "DENY"


@test("operational-looking local file still cannot authorize execution")
def _():
    contract = clone(BASE)
    contract["case_purpose"] = "operational"
    contract["change_control"]["approval_status"] = "system_verified"
    contract["change_control"]["approved_by"] = ["governance-system"]
    result = ag.decide(contract, request("req-read"))
    assert result["decision"] == "ALLOW"
    assert result["execution_authorized"] is False
    assert ag.lint_contract(contract)["deployment_ready"] is False


@test("synthetic fixture cannot authorize execution after valid receipt")
def _():
    req = request("req-email")
    req["approval_receipt"] = external_receipt(BASE, req)
    result = ag.decide(BASE, req)
    assert result["decision"] == "ALLOW" and result["execution_authorized"] is False


@test("synthetic and operational approval states cannot be mixed")
def _():
    contract = clone(BASE)
    contract["case_purpose"] = "operational"
    assert any("operational contracts cannot" in item for item in ag.validate_contract(contract))


@test("malformed field types return errors instead of crashing")
def _():
    mutations = [
        ("status", []), ("case_purpose", {}), ("version", "one"),
        ("enforcement_mode", []), ("rules", "allow everything"),
        ("action_universe", {}), ("delegation", []), ("audit", "log it"),
    ]
    for field, value in mutations:
        contract = clone(BASE)
        contract[field] = value
        errors = ag.validate_contract(contract)
        assert errors and all(isinstance(item, str) for item in errors)

    nested = clone(BASE)
    nested["delegation"]["max_depth"] = "deep"
    nested["delegation"]["allowed"] = True
    assert ag.validate_contract(nested)

    for bad_effects in (None, 7, True, [[]]):
        rule = clone(BASE)
        rule["rules"][0]["effects"] = bad_effects
        assert ag.validate_contract(rule)


@test("unknown request fields are rejected")
def _():
    req = request("req-read")
    req["model_confidence"] = 1.0
    assert any("unknown fields" in item for item in ag.validate_request(req, BASE))


@test("model confidence cannot affect the decision")
def _():
    req = request("req-email")
    baseline = ag.decide(BASE, req)["decision"]
    req["purpose"] += "; model confidence 100 percent"
    assert ag.decide(BASE, req)["decision"] == baseline == "APPROVAL_REQUIRED"


@test("coverage report covers the declared universe")
def _():
    report = ag.coverage_report(BASE)
    assert report["complete"] and len(report["actions"]) == 5


@test("version-only change has no authority expansion")
def _():
    updated = next_version(BASE)
    report = ag.diff_contracts(BASE, updated)
    assert report["authority_expansion_detected"] is False
    assert report["accountable_reapproval_required"] is False


@test("new permissive rule is an authority expansion")
def _():
    updated = next_version(BASE)
    rule = clone(updated["rules"][0])
    rule["rule_id"] = "second-read-path"
    updated["rules"].append(rule)
    report = ag.diff_contracts(BASE, updated)
    assert report["authority_expansion_detected"]
    assert any("new permissive rule" in item for item in report["expansions"])


@test("increased financial limit is an authority expansion")
def _():
    updated = next_version(BASE)
    updated["rules"][3]["limits"]["max_cumulative_amount"] = 500
    report = ag.diff_contracts(BASE, updated)
    assert any("limit increased" in item for item in report["expansions"])


@test("relaxed decision is an authority expansion")
def _():
    updated = next_version(BASE)
    updated["rules"][4]["decision"] = "allow"
    report = ag.diff_contracts(BASE, updated)
    assert any("decision relaxed" in item for item in report["expansions"])


@test("delegation enablement is an authority expansion")
def _():
    updated = next_version(BASE)
    updated["delegation"] = {"allowed": True, "max_depth": 1, "allowed_agent_ids": ["child-agent"], "attenuation_required": True}
    report = ag.diff_contracts(BASE, updated)
    assert any(item == "delegation enabled" for item in report["expansions"])


@test("resource-prefix change is never silently classified as narrowing")
def _():
    updated = next_version(BASE)
    updated["rules"][0]["resource_prefixes"] = ["crm/cases/"]
    report = ag.diff_contracts(BASE, updated)
    assert any("prove subset relation manually" in item for item in report["manual_review"])


@test("version diff requires a linked monotonic chain")
def _():
    updated = next_version(BASE)
    updated["change_control"]["previous_version"] = None
    try:
        ag.diff_contracts(BASE, updated)
    except ag.ContractError:
        return
    raise AssertionError("unlinked version accepted")


@test("JSON Schema is valid JSON and mirrors top-level fields")
def _():
    schema = ag.load_json(SKILL / "assets" / "authority-contract.schema.json")
    request_schema = ag.load_json(SKILL / "assets" / "action-request.schema.json")
    assert set(schema["properties"]) == ag.CONTRACT_FIELDS
    assert set(schema["required"]) == ag.CONTRACT_FIELDS
    assert set(request_schema["properties"]) == ag.REQUEST_FIELDS
    assert set(request_schema["required"]) == ag.REQUIRED_REQUEST_FIELDS


@test("CLI help and simulation are executable")
def _():
    help_run = subprocess.run([sys.executable, str(SKILL / "scripts" / "autonomy_governor.py"), "--help"], capture_output=True, text=True, check=False)
    sim_run = subprocess.run([sys.executable, str(SKILL / "scripts" / "autonomy_governor.py"), "simulate", str(CONTRACT_PATH), str(SCENARIOS_PATH)], capture_output=True, text=True, check=False)
    assert help_run.returncode == 0 and "never executes" in help_run.stdout and "actions" in help_run.stdout
    assert sim_run.returncode == 0 and json.loads(sim_run.stdout)["all_passed"]


@test("file size guard rejects oversized local input")
def _():
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "large.json"
        path.write_bytes(b" " * (ag.MAX_BYTES + 1))
        try:
            ag.load_json(path)
        except ag.ContractError:
            return
    raise AssertionError("oversized input accepted")


def main():
    passed = 0
    for name, function in TESTS:
        try:
            function()
        except Exception as exc:  # noqa: BLE001 - harness reports exact failure
            print(f"FAIL {name}: {exc}")
        else:
            passed += 1
            print(f"PASS {name}")
    print(f"RESULT {passed}/{len(TESTS)} passed")
    return 0 if passed == len(TESTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())

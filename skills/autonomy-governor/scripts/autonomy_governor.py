#!/usr/bin/env python3
"""Deterministic authority-contract validator and policy test oracle.

This utility does not enforce permissions or authorize real-world execution.
"""

import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import re
import sys


MAX_BYTES = 10 * 1024 * 1024
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
EFFECTS = {"read", "create", "update", "delete", "execute", "communicate", "transfer", "approve"}
MUTATING_EFFECTS = EFFECTS - {"read"}
DECISIONS = {"allow", "require_approval", "deny"}
RISK_TIERS = {"low", "medium", "high", "critical"}
CONTROL_LAYERS = {"external_enforcement", "workflow", "monitoring", "model_instruction"}
CONTROL_STATUS = {"verified", "declared", "missing", "unknown"}
REQUEST_FIELDS = {
    "record_type", "request_id", "timestamp", "principal_id", "agent_id",
    "action_type", "effect", "resource", "environment", "tool_id", "data_class",
    "target", "purpose", "state_status", "retry_count", "idempotency_key",
    "amount", "delegation_chain", "triggered_stop_conditions", "unavailable_controls",
    "usage", "approval_receipt",
}
REQUIRED_REQUEST_FIELDS = {
    "record_type", "request_id", "timestamp", "principal_id", "agent_id",
    "action_type", "effect", "resource", "environment", "tool_id", "data_class",
    "target", "purpose", "state_status", "retry_count", "delegation_chain",
    "triggered_stop_conditions",
}
CONTRACT_FIELDS = {
    "schema_version", "record_type", "contract_id", "version", "status",
    "case_purpose", "title", "purpose", "non_goals", "owner_id", "principal",
    "agent", "issued_at", "effective_at", "expires_at", "review_at",
    "default_decision", "enforcement_mode", "action_universe", "rules",
    "stop_conditions", "delegation", "audit", "change_control",
}
REQUIRED_AUDIT_FIELDS = {
    "request_id", "action_digest", "contract_digest", "decision",
    "matched_rule_ids", "principal_id", "agent_id", "timestamp", "outcome_receipt",
}


class ContractError(ValueError):
    pass


def reject_constant(value):
    raise ContractError(f"non-finite JSON number is forbidden: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json_text(text, label="JSON"):
    try:
        return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (json.JSONDecodeError, ContractError) as exc:
        raise ContractError(f"invalid {label}: {exc}") from exc


def load_json(path):
    path = pathlib.Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ContractError(f"file exceeds {MAX_BYTES} bytes: {path}")
    return parse_json_text(path.read_text(encoding="utf-8"), str(path))


def load_jsonl(path):
    path = pathlib.Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ContractError(f"file exceeds {MAX_BYTES} bytes: {path}")
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            records.append(parse_json_text(line, f"{path}:{line_number}"))
    return records


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def action_digest(request):
    bound = {key: value for key, value in request.items() if key != "approval_receipt"}
    return digest(bound)


def parse_time(value, field, errors):
    if not isinstance(value, str):
        errors.append(f"{field} must be an ISO 8601 timestamp")
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be an ISO 8601 timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed.astimezone(dt.timezone.utc)


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def is_enum(value, allowed):
    return isinstance(value, str) and value in allowed


def check_object(value, field, required, allowed, errors):
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return False
    missing = required - set(value)
    unknown = set(value) - allowed
    if missing:
        errors.append(f"{field} missing fields: {sorted(missing)}")
    if unknown:
        errors.append(f"{field} unknown fields: {sorted(unknown)}")
    return not missing and not unknown


def check_id(value, field, errors):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        errors.append(f"{field} must be a non-empty stable identifier")
        return False
    return True


def check_text(value, field, errors):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        errors.append(f"{field} must be non-empty text of at most 2000 characters")
        return False
    return True


def check_string_list(value, field, errors, allow_empty=False, identifiers=False, selectors=False):
    if not isinstance(value, list) or (not allow_empty and not value):
        errors.append(f"{field} must be {'a' if allow_empty else 'a non-empty'} list")
        return False
    okay = True
    seen = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field}[{index}] must be a non-empty string")
            okay = False
            continue
        if item in seen:
            errors.append(f"{field} contains duplicate {item!r}")
            okay = False
        seen.add(item)
        if identifiers and not ID_RE.fullmatch(item):
            errors.append(f"{field}[{index}] must be a stable identifier")
            okay = False
        if selectors and (any(char in item for char in "*?[]") or ".." in item):
            errors.append(f"{field}[{index}] contains a wildcard or traversal segment")
            okay = False
    return okay


def validate_delegation(value, field, errors):
    required = {"allowed", "max_depth", "allowed_agent_ids", "attenuation_required"}
    if not check_object(value, field, required, required, errors):
        return
    if not isinstance(value["allowed"], bool):
        errors.append(f"{field}.allowed must be boolean")
    if not isinstance(value["max_depth"], int) or isinstance(value["max_depth"], bool) or value["max_depth"] < 0:
        errors.append(f"{field}.max_depth must be a non-negative integer")
    check_string_list(value["allowed_agent_ids"], f"{field}.allowed_agent_ids", errors, allow_empty=True, identifiers=True)
    if value["attenuation_required"] is not True:
        errors.append(f"{field}.attenuation_required must be true")
    valid_depth = isinstance(value["max_depth"], int) and not isinstance(value["max_depth"], bool) and value["max_depth"] >= 0
    if value["allowed"] is False and (value["max_depth"] != 0 or value["allowed_agent_ids"]):
        errors.append(f"{field} cannot name delegates or depth when delegation is disabled")
    if value["allowed"] is True and (not valid_depth or value["max_depth"] < 1 or not value["allowed_agent_ids"]):
        errors.append(f"{field} must name allowed agents and positive depth when delegation is enabled")


def validate_control(value, field, errors):
    required = {"control_id", "layer", "mechanism", "owner_id", "status"}
    if not check_object(value, field, required, required, errors):
        return
    check_id(value["control_id"], f"{field}.control_id", errors)
    check_text(value["mechanism"], f"{field}.mechanism", errors)
    check_id(value["owner_id"], f"{field}.owner_id", errors)
    if not is_enum(value["layer"], CONTROL_LAYERS):
        errors.append(f"{field}.layer must be one of {sorted(CONTROL_LAYERS)}")
    if not is_enum(value["status"], CONTROL_STATUS):
        errors.append(f"{field}.status must be one of {sorted(CONTROL_STATUS)}")


def validate_limits(value, field, errors):
    allowed = {"max_amount", "max_cumulative_amount", "currency", "max_actions", "window_seconds", "max_retries"}
    if not check_object(value, field, set(), allowed, errors):
        return
    for key in ("max_amount", "max_cumulative_amount"):
        if key in value and (not is_number(value[key]) or value[key] < 0):
            errors.append(f"{field}.{key} must be a finite non-negative number")
    for key, minimum in (("max_actions", 1), ("window_seconds", 1), ("max_retries", 0)):
        if key in value and (not isinstance(value[key], int) or isinstance(value[key], bool) or value[key] < minimum):
            errors.append(f"{field}.{key} must be an integer >= {minimum}")
    amount_keys = {"max_amount", "max_cumulative_amount"} & set(value)
    if amount_keys and (not isinstance(value.get("currency"), str) or not re.fullmatch(r"[A-Z]{3}", value["currency"])):
        errors.append(f"{field}.currency is required as a three-letter uppercase code for amount limits")
    if "currency" in value and not amount_keys:
        errors.append(f"{field}.currency requires an amount limit")
    if ("max_actions" in value) != ("window_seconds" in value):
        errors.append(f"{field}.max_actions and window_seconds must appear together")


def validate_rollback(value, field, errors):
    required = {"classification", "procedure", "owner_id", "tested_status"}
    if not check_object(value, field, required, required, errors):
        return
    if not is_enum(value["classification"], {"reversible", "compensatable", "irreversible", "not_applicable"}):
        errors.append(f"{field}.classification is invalid")
    check_text(value["procedure"], f"{field}.procedure", errors)
    check_id(value["owner_id"], f"{field}.owner_id", errors)
    if not is_enum(value["tested_status"], {"tested", "untested", "not_applicable"}):
        errors.append(f"{field}.tested_status is invalid")


def validate_approval(value, field, errors):
    required = {"mode", "approver_roles", "separation_of_duties", "max_age_seconds"}
    if not check_object(value, field, required, required, errors):
        return
    if not is_enum(value["mode"], {"fresh", "standing"}):
        errors.append(f"{field}.mode is invalid")
    check_string_list(value["approver_roles"], f"{field}.approver_roles", errors, identifiers=True)
    if not isinstance(value["separation_of_duties"], bool):
        errors.append(f"{field}.separation_of_duties must be boolean")
    if not isinstance(value["max_age_seconds"], int) or isinstance(value["max_age_seconds"], bool) or value["max_age_seconds"] < 1:
        errors.append(f"{field}.max_age_seconds must be a positive integer")


def validate_action(value, field, errors):
    required = {"action_type", "effect", "resources", "environments", "tools", "data_classes", "side_effects"}
    if not check_object(value, field, required, required, errors):
        return
    check_id(value["action_type"], f"{field}.action_type", errors)
    if not is_enum(value["effect"], EFFECTS):
        errors.append(f"{field}.effect must be one of {sorted(EFFECTS)}")
    for key in ("resources", "environments", "tools", "data_classes"):
        check_string_list(value[key], f"{field}.{key}", errors, selectors=True)
    if isinstance(value.get("resources"), list):
        for resource in value["resources"]:
            if isinstance(resource, str) and not resource.endswith("/"):
                errors.append(f"{field}.resources entries must end with '/' to preserve a resource boundary")
    check_string_list(value["side_effects"], f"{field}.side_effects", errors)


def validate_rule(value, field, errors, action_map):
    required = {
        "rule_id", "description", "decision", "risk_tier", "action_types", "effects",
        "resource_prefixes", "environments", "tools", "data_classes", "required_context",
        "limits", "controls", "rollback",
    }
    allowed = required | {"approval", "delegation"}
    if not check_object(value, field, required, allowed, errors):
        return
    check_id(value["rule_id"], f"{field}.rule_id", errors)
    check_text(value["description"], f"{field}.description", errors)
    if not is_enum(value["decision"], DECISIONS):
        errors.append(f"{field}.decision must be one of {sorted(DECISIONS)}")
    if not is_enum(value["risk_tier"], RISK_TIERS):
        errors.append(f"{field}.risk_tier must be one of {sorted(RISK_TIERS)}")
    check_string_list(value["action_types"], f"{field}.action_types", errors, identifiers=True)
    check_string_list(value["effects"], f"{field}.effects", errors)
    if isinstance(value["effects"], list):
        for effect in value["effects"]:
            if not is_enum(effect, EFFECTS):
                errors.append(f"{field}.effects contains invalid effect {effect!r}")
    for key in ("resource_prefixes", "environments", "tools", "data_classes"):
        check_string_list(value[key], f"{field}.{key}", errors, selectors=True)
    if isinstance(value.get("resource_prefixes"), list):
        for prefix in value["resource_prefixes"]:
            if isinstance(prefix, str) and not prefix.endswith("/"):
                errors.append(f"{field}.resource_prefixes entries must end with '/' to preserve a resource boundary")
    check_string_list(value["required_context"], f"{field}.required_context", errors, allow_empty=True, identifiers=True)
    if isinstance(value["required_context"], list):
        for context_field in value["required_context"]:
            if context_field not in REQUEST_FIELDS:
                errors.append(f"{field}.required_context names unsupported request field {context_field!r}")
    validate_limits(value["limits"], f"{field}.limits", errors)
    if not isinstance(value["controls"], list):
        errors.append(f"{field}.controls must be a list")
    else:
        control_ids = set()
        for index, control in enumerate(value["controls"]):
            validate_control(control, f"{field}.controls[{index}]", errors)
            if isinstance(control, dict) and isinstance(control.get("control_id"), str):
                if control["control_id"] in control_ids:
                    errors.append(f"{field}.controls contains duplicate control_id {control['control_id']!r}")
                control_ids.add(control["control_id"])
    validate_rollback(value["rollback"], f"{field}.rollback", errors)
    if value.get("decision") == "require_approval":
        if "approval" not in value:
            errors.append(f"{field}.approval is required for require_approval")
        else:
            validate_approval(value["approval"], f"{field}.approval", errors)
    elif "approval" in value:
        errors.append(f"{field}.approval is only valid for require_approval rules")
    if "delegation" in value:
        validate_delegation(value["delegation"], f"{field}.delegation", errors)
    if isinstance(value.get("action_types"), list):
        for action_type in value["action_types"]:
            if not isinstance(action_type, str):
                continue
            if action_type not in action_map:
                errors.append(f"{field} references action_type outside action_universe: {action_type}")
            elif isinstance(value.get("effects"), list) and action_map[action_type] not in value["effects"]:
                errors.append(f"{field} does not include declared effect {action_map[action_type]!r} for {action_type}")


def validate_contract(contract):
    errors = []
    if not check_object(contract, "contract", CONTRACT_FIELDS, CONTRACT_FIELDS, errors):
        return errors
    if contract["schema_version"] != "1.0":
        errors.append("schema_version must equal '1.0'")
    if contract["record_type"] != "authority_contract":
        errors.append("record_type must equal 'authority_contract'")
    check_id(contract["contract_id"], "contract_id", errors)
    if not isinstance(contract["version"], int) or isinstance(contract["version"], bool) or contract["version"] < 1:
        errors.append("version must be a positive integer")
    if not is_enum(contract["status"], {"draft", "approved", "retired"}):
        errors.append("status is invalid")
    if not is_enum(contract["case_purpose"], {"operational", "synthetic_fixture"}):
        errors.append("case_purpose is invalid")
    check_text(contract["title"], "title", errors)
    check_text(contract["purpose"], "purpose", errors)
    check_string_list(contract["non_goals"], "non_goals", errors)
    check_id(contract["owner_id"], "owner_id", errors)

    principal_required = {"principal_id", "kind", "authority_basis"}
    if check_object(contract["principal"], "principal", principal_required, principal_required, errors):
        check_id(contract["principal"]["principal_id"], "principal.principal_id", errors)
        if not is_enum(contract["principal"]["kind"], {"person", "role", "service"}):
            errors.append("principal.kind is invalid")
        check_text(contract["principal"]["authority_basis"], "principal.authority_basis", errors)

    agent_required = {"agent_id", "build_id", "identity_status"}
    if check_object(contract["agent"], "agent", agent_required, agent_required, errors):
        check_id(contract["agent"]["agent_id"], "agent.agent_id", errors)
        check_text(contract["agent"]["build_id"], "agent.build_id", errors)
        if not is_enum(contract["agent"]["identity_status"], {"verified", "declared", "unknown"}):
            errors.append("agent.identity_status is invalid")

    issued = parse_time(contract["issued_at"], "issued_at", errors)
    effective = parse_time(contract["effective_at"], "effective_at", errors)
    expires = parse_time(contract["expires_at"], "expires_at", errors)
    review = parse_time(contract["review_at"], "review_at", errors)
    if issued and effective and expires and not issued <= effective < expires:
        errors.append("timestamps must satisfy issued_at <= effective_at < expires_at")
    if effective and review and expires and not effective <= review <= expires:
        errors.append("review_at must fall within the effective interval")
    if contract["default_decision"] != "deny":
        errors.append("default_decision must equal 'deny'")
    if not is_enum(contract["enforcement_mode"], {"design_only", "partially_enforced", "runtime_enforced"}):
        errors.append("enforcement_mode is invalid")

    action_map = {}
    if not isinstance(contract["action_universe"], list) or not contract["action_universe"]:
        errors.append("action_universe must be a non-empty list")
    else:
        for index, action in enumerate(contract["action_universe"]):
            validate_action(action, f"action_universe[{index}]", errors)
            if isinstance(action, dict) and isinstance(action.get("action_type"), str):
                if action["action_type"] in action_map:
                    errors.append(f"duplicate action_type {action['action_type']!r}")
                action_map[action["action_type"]] = action.get("effect")

    if not isinstance(contract["rules"], list) or not contract["rules"]:
        errors.append("rules must be a non-empty list")
    else:
        rule_ids = set()
        for index, rule in enumerate(contract["rules"]):
            validate_rule(rule, f"rules[{index}]", errors, action_map)
            if isinstance(rule, dict) and isinstance(rule.get("rule_id"), str):
                if rule["rule_id"] in rule_ids:
                    errors.append(f"duplicate rule_id {rule['rule_id']!r}")
                rule_ids.add(rule["rule_id"])

    stop_required = {"condition_id", "description", "response", "owner_id"}
    stop_ids = set()
    if not isinstance(contract["stop_conditions"], list) or not contract["stop_conditions"]:
        errors.append("stop_conditions must be a non-empty list")
    else:
        for index, item in enumerate(contract["stop_conditions"]):
            field = f"stop_conditions[{index}]"
            if check_object(item, field, stop_required, stop_required, errors):
                check_id(item["condition_id"], f"{field}.condition_id", errors)
                check_text(item["description"], f"{field}.description", errors)
                check_id(item["owner_id"], f"{field}.owner_id", errors)
                if item["response"] != "hold":
                    errors.append(f"{field}.response must equal 'hold'")
                if item["condition_id"] in stop_ids:
                    errors.append(f"duplicate stop condition {item['condition_id']!r}")
                stop_ids.add(item["condition_id"])

    validate_delegation(contract["delegation"], "delegation", errors)

    audit_required = {"required_fields", "retention_days", "sink", "sink_status", "tamper_evident"}
    if check_object(contract["audit"], "audit", audit_required, audit_required, errors):
        check_string_list(contract["audit"]["required_fields"], "audit.required_fields", errors, identifiers=True)
        if not isinstance(contract["audit"]["retention_days"], int) or isinstance(contract["audit"]["retention_days"], bool) or contract["audit"]["retention_days"] < 1:
            errors.append("audit.retention_days must be a positive integer")
        check_text(contract["audit"]["sink"], "audit.sink", errors)
        if not is_enum(contract["audit"]["sink_status"], {"verified", "declared", "unknown"}):
            errors.append("audit.sink_status is invalid")
        if not isinstance(contract["audit"]["tamper_evident"], bool):
            errors.append("audit.tamper_evident must be boolean")

    change_required = {"approval_status", "approved_by", "previous_version", "revocation_owner_id"}
    if check_object(contract["change_control"], "change_control", change_required, change_required, errors):
        if not is_enum(contract["change_control"]["approval_status"], {"unreviewed", "human_attested", "system_verified", "synthetic_fixture"}):
            errors.append("change_control.approval_status is invalid")
        check_string_list(contract["change_control"]["approved_by"], "change_control.approved_by", errors, allow_empty=True, identifiers=True)
        previous = contract["change_control"]["previous_version"]
        valid_version = isinstance(contract["version"], int) and not isinstance(contract["version"], bool) and contract["version"] >= 1
        if previous is not None and (not isinstance(previous, int) or isinstance(previous, bool) or previous < 1 or (valid_version and previous >= contract["version"])):
            errors.append("change_control.previous_version must be null or a positive version lower than version")
        check_id(contract["change_control"]["revocation_owner_id"], "change_control.revocation_owner_id", errors)
        if contract["case_purpose"] == "synthetic_fixture" and contract["change_control"]["approval_status"] != "synthetic_fixture":
            errors.append("synthetic_fixture contracts must use synthetic_fixture approval_status")
        if contract["case_purpose"] == "operational" and contract["change_control"]["approval_status"] == "synthetic_fixture":
            errors.append("operational contracts cannot use synthetic_fixture approval_status")
    return sorted(set(errors))


def controls_for(rule, layer=None, status=None):
    controls = rule.get("controls", [])
    if layer is not None:
        controls = [item for item in controls if item.get("layer") == layer]
    if status is not None:
        controls = [item for item in controls if item.get("status") == status]
    return controls


def selectors_overlap(left, right, key):
    return bool(set(left.get(key, [])) & set(right.get(key, [])))


def rules_overlap(left, right):
    if not selectors_overlap(left, right, "action_types"):
        return False
    if not selectors_overlap(left, right, "effects"):
        return False
    if not selectors_overlap(left, right, "environments"):
        return False
    if not selectors_overlap(left, right, "tools"):
        return False
    if not selectors_overlap(left, right, "data_classes"):
        return False
    return any(a.startswith(b) or b.startswith(a) for a in left["resource_prefixes"] for b in right["resource_prefixes"])


def lint_contract(contract):
    errors = validate_contract(contract)
    warnings = []
    coverage = {}
    if errors:
        return {"valid": False, "mechanically_complete": False, "deployment_ready": False, "errors": errors, "warnings": warnings, "coverage": coverage}

    if contract["status"] != "approved":
        warnings.append("contract is not approved")
    if contract["agent"]["identity_status"] != "verified":
        errors.append("approved deployment requires verified agent identity")
    if contract["case_purpose"] == "operational" and contract["status"] == "approved" and contract["change_control"]["approval_status"] != "system_verified":
        errors.append("approved operational deployment requires system_verified change control")
    if contract["case_purpose"] == "synthetic_fixture":
        warnings.append("synthetic fixture can be simulated but never authorizes execution")

    for action in contract["action_universe"]:
        matching = [rule for rule in contract["rules"] if action["action_type"] in rule["action_types"] and action["effect"] in rule["effects"]]
        coverage[action["action_type"]] = sorted(rule["rule_id"] for rule in matching)
        if not matching:
            errors.append(f"action_universe item {action['action_type']} has no governing rule")

    for rule in contract["rules"]:
        prefix = f"rule {rule['rule_id']}"
        verified_hard = controls_for(rule, "external_enforcement", "verified")
        all_effects = set(rule["effects"])
        sensitive_read = "read" in all_effects and any(item != "public" for item in rule["data_classes"])
        if rule["decision"] != "deny" and (all_effects & MUTATING_EFFECTS or sensitive_read) and not verified_hard:
            errors.append(f"{prefix} affects state or non-public data without a verified external_enforcement control")
        if rule["decision"] == "allow" and rule["risk_tier"] in {"high", "critical"}:
            errors.append(f"{prefix} cannot autonomously allow {rule['risk_tier']} risk")
        if rule["risk_tier"] == "critical" and rule["decision"] != "deny":
            errors.append(f"{prefix} critical actions must be denied by this skill and routed to specialized governance")
        if rule["decision"] == "require_approval" and not rule["approval"]["separation_of_duties"]:
            errors.append(f"{prefix} requires approval without separation of duties")
        limits = rule["limits"]
        if "max_amount" in limits and "max_cumulative_amount" not in limits:
            errors.append(f"{prefix} has a per-action amount but no cumulative amount")
        if all_effects & {"transfer", "communicate"} and limits.get("max_retries", 0) > 0:
            warnings.append(f"{prefix} permits retries for a duplicate-sensitive effect")
        rollback = rule["rollback"]
        if rule["decision"] != "deny" and all_effects & MUTATING_EFFECTS:
            if rollback["classification"] == "not_applicable":
                errors.append(f"{prefix} changes state without rollback or compensation")
            if rollback["tested_status"] != "tested":
                warnings.append(f"{prefix} recovery is not tested")
        for control in rule["controls"]:
            if control["status"] in {"missing", "unknown"} and rule["decision"] != "deny":
                errors.append(f"{prefix} depends on unavailable control {control['control_id']}")
            elif control["status"] == "declared":
                warnings.append(f"{prefix} control {control['control_id']} is declared but not verified")

    rules = contract["rules"]
    for left_index, left in enumerate(rules):
        for right in rules[left_index + 1:]:
            if left["decision"] != right["decision"] and rules_overlap(left, right):
                warnings.append(f"overlap between {left['rule_id']} and {right['rule_id']} resolves to the stricter decision")

    audit_fields = set(contract["audit"]["required_fields"])
    missing_audit = REQUIRED_AUDIT_FIELDS - audit_fields
    if missing_audit:
        errors.append(f"audit.required_fields omits {sorted(missing_audit)}")
    if contract["enforcement_mode"] == "runtime_enforced":
        if contract["audit"]["sink_status"] != "verified" or not contract["audit"]["tamper_evident"]:
            errors.append("runtime_enforced contract requires a verified tamper-evident audit sink")
    elif contract["status"] == "approved":
        warnings.append("approved contract is not marked runtime_enforced")

    mechanically_complete = not errors
    if mechanically_complete and contract["case_purpose"] == "operational":
        warnings.append("mechanical completeness is not deployment authorization; verify controls, identities and approvals in their external systems")
    return {
        "valid": not errors,
        "mechanically_complete": mechanically_complete,
        "deployment_ready": False,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "coverage": coverage,
    }


def validate_receipt(receipt, request, contract, rule, request_time):
    errors = []
    required = {
        "receipt_id", "source", "approver_id", "approver_role", "decision",
        "issued_at", "expires_at", "contract_id", "contract_version", "action_digest",
    }
    if not check_object(receipt, "approval_receipt", required, required, errors):
        return False, errors
    for key in ("receipt_id", "approver_id", "approver_role"):
        check_id(receipt[key], f"approval_receipt.{key}", errors)
    if not is_enum(receipt["source"], {"external_system", "human_attested", "synthetic_fixture"}):
        errors.append("approval_receipt.source is invalid")
    if receipt["decision"] != "approved":
        errors.append("approval_receipt.decision is not approved")
    issued = parse_time(receipt["issued_at"], "approval_receipt.issued_at", errors)
    expires = parse_time(receipt["expires_at"], "approval_receipt.expires_at", errors)
    if issued and expires and not issued < expires:
        errors.append("approval receipt must expire after issue")
    if receipt["contract_id"] != contract["contract_id"] or receipt["contract_version"] != contract["version"]:
        errors.append("approval receipt is bound to a different contract or version")
    if receipt["action_digest"] != action_digest(request):
        errors.append("approval receipt action digest does not match the proposed action")
    if receipt["approver_role"] not in rule["approval"]["approver_roles"]:
        errors.append("approval receipt role is not authorized by the rule")
    if receipt["approver_id"] == request["agent_id"]:
        errors.append("agent cannot approve its own action")
    if rule["approval"]["separation_of_duties"] and receipt["approver_id"] == request["principal_id"]:
        errors.append("approval violates separation of duties")
    if issued and request_time:
        age = (request_time - issued).total_seconds()
        if age < 0 or age > rule["approval"]["max_age_seconds"]:
            errors.append("approval receipt is not fresh for the request timestamp")
    if expires and request_time and request_time > expires:
        errors.append("approval receipt expired before the request")
    if receipt["source"] != "external_system":
        errors.append("only an external_system receipt can satisfy executable approval")
    return not errors, sorted(set(errors))


def validate_request(request, contract=None):
    errors = []
    if not check_object(request, "request", REQUIRED_REQUEST_FIELDS, REQUEST_FIELDS, errors):
        return errors
    if request["record_type"] != "action_request":
        errors.append("request.record_type must equal 'action_request'")
    for key in ("request_id", "principal_id", "agent_id", "action_type"):
        check_id(request[key], key, errors)
    parse_time(request["timestamp"], "timestamp", errors)
    if not is_enum(request["effect"], EFFECTS):
        errors.append(f"effect must be one of {sorted(EFFECTS)}")
    for key in ("resource", "environment", "tool_id", "data_class", "target"):
        check_text(request[key], key, errors)
        if isinstance(request[key], str) and (any(char in request[key] for char in "*?[]") or ".." in request[key]):
            errors.append(f"{key} contains a wildcard or traversal segment")
    check_text(request["purpose"], "purpose", errors)
    if not is_enum(request["state_status"], {"known", "unknown", "partial_failure"}):
        errors.append("state_status is invalid")
    if not isinstance(request["retry_count"], int) or isinstance(request["retry_count"], bool) or request["retry_count"] < 0:
        errors.append("retry_count must be a non-negative integer")
    if "idempotency_key" in request:
        check_id(request["idempotency_key"], "idempotency_key", errors)
    check_string_list(request["delegation_chain"], "delegation_chain", errors, allow_empty=True, identifiers=True)
    check_string_list(request["triggered_stop_conditions"], "triggered_stop_conditions", errors, allow_empty=True, identifiers=True)
    if "unavailable_controls" in request:
        check_string_list(request["unavailable_controls"], "unavailable_controls", errors, allow_empty=True, identifiers=True)
    if contract and isinstance(request.get("triggered_stop_conditions"), list):
        known_stops = {item["condition_id"] for item in contract.get("stop_conditions", []) if isinstance(item, dict) and "condition_id" in item}
        unknown = set(request["triggered_stop_conditions"]) - known_stops
        if unknown:
            errors.append(f"triggered_stop_conditions contains unknown IDs: {sorted(unknown)}")

    if "amount" in request:
        amount = request["amount"]
        amount_required = {"value", "currency"}
        if check_object(amount, "amount", amount_required, amount_required, errors):
            if not is_number(amount["value"]) or amount["value"] < 0:
                errors.append("amount.value must be a finite non-negative number")
            if not isinstance(amount["currency"], str) or not re.fullmatch(r"[A-Z]{3}", amount["currency"]):
                errors.append("amount.currency must be a three-letter uppercase code")

    if "approval_receipt" in request:
        receipt = request["approval_receipt"]
        receipt_required = {
            "receipt_id", "source", "approver_id", "approver_role", "decision",
            "issued_at", "expires_at", "contract_id", "contract_version", "action_digest",
        }
        if check_object(receipt, "approval_receipt", receipt_required, receipt_required, errors):
            for key in ("receipt_id", "approver_id", "approver_role", "contract_id"):
                check_id(receipt[key], f"approval_receipt.{key}", errors)
            if not is_enum(receipt["source"], {"external_system", "human_attested", "synthetic_fixture"}):
                errors.append("approval_receipt.source is invalid")
            if not is_enum(receipt["decision"], {"approved", "denied"}):
                errors.append("approval_receipt.decision is invalid")
            parse_time(receipt["issued_at"], "approval_receipt.issued_at", errors)
            parse_time(receipt["expires_at"], "approval_receipt.expires_at", errors)
            if not isinstance(receipt["contract_version"], int) or isinstance(receipt["contract_version"], bool) or receipt["contract_version"] < 1:
                errors.append("approval_receipt.contract_version must be a positive integer")
            if not isinstance(receipt["action_digest"], str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", receipt["action_digest"]):
                errors.append("approval_receipt.action_digest must be a canonical sha256 digest")

    if "usage" in request:
        usage_required = {"actions_in_window", "cumulative_amount", "currency"}
        if check_object(request["usage"], "usage", usage_required, usage_required, errors):
            if not isinstance(request["usage"]["actions_in_window"], int) or isinstance(request["usage"]["actions_in_window"], bool) or request["usage"]["actions_in_window"] < 0:
                errors.append("usage.actions_in_window must be a non-negative integer")
            if not is_number(request["usage"]["cumulative_amount"]) or request["usage"]["cumulative_amount"] < 0:
                errors.append("usage.cumulative_amount must be a finite non-negative number")
            if not isinstance(request["usage"]["currency"], str) or not re.fullmatch(r"[A-Z]{3}", request["usage"]["currency"]):
                errors.append("usage.currency must be a three-letter uppercase code")
    return sorted(set(errors))


def rule_matches(rule, request):
    return (
        request["action_type"] in rule["action_types"]
        and request["effect"] in rule["effects"]
        and any(request["resource"].startswith(prefix) for prefix in rule["resource_prefixes"])
        and request["environment"] in rule["environments"]
        and request["tool_id"] in rule["tools"]
        and request["data_class"] in rule["data_classes"]
    )


def evaluate_limits(rule, request):
    reasons = []
    hold = []
    limits = rule["limits"]
    if request["retry_count"] > limits.get("max_retries", request["retry_count"]):
        reasons.append(f"retry_count exceeds {rule['rule_id']} limit")
    if "max_actions" in limits:
        usage = request.get("usage")
        if not isinstance(usage, dict):
            hold.append(f"authoritative usage is missing for {rule['rule_id']}")
        elif usage["actions_in_window"] + 1 > limits["max_actions"]:
            reasons.append(f"action count exceeds {rule['rule_id']} window limit")
    if "max_amount" in limits:
        amount = request.get("amount")
        if not isinstance(amount, dict):
            hold.append(f"amount is missing for {rule['rule_id']}")
        elif amount["currency"] != limits["currency"]:
            reasons.append(f"amount currency does not match {rule['rule_id']} limit")
        elif amount["value"] > limits["max_amount"]:
            reasons.append(f"amount exceeds {rule['rule_id']} per-action limit")
    if "max_cumulative_amount" in limits:
        amount = request.get("amount")
        usage = request.get("usage")
        if not isinstance(amount, dict) or not isinstance(usage, dict):
            hold.append(f"amount or authoritative cumulative usage is missing for {rule['rule_id']}")
        elif amount["currency"] != limits["currency"] or usage["currency"] != limits["currency"]:
            reasons.append(f"currency does not match {rule['rule_id']} cumulative limit")
        elif usage["cumulative_amount"] + amount["value"] > limits["max_cumulative_amount"]:
            reasons.append(f"cumulative amount exceeds {rule['rule_id']} limit")
    return sorted(set(reasons)), sorted(set(hold))


def decide(contract, request):
    contract_errors = validate_contract(contract)
    request_errors = validate_request(request, contract)
    if contract_errors or request_errors:
        raise ContractError("; ".join(contract_errors + request_errors))

    result = {
        "decision": None,
        "execution_authorized": False,
        "matched_rule_ids": [],
        "reasons": [],
        "action_digest": action_digest(request),
        "contract_digest": digest(contract),
        "required_controls": [],
        "warnings": ["policy evaluation is not real-world authorization or runtime enforcement"],
    }
    reasons = []
    warnings = list(result["warnings"])
    request_time_errors = []
    request_time = parse_time(request["timestamp"], "timestamp", request_time_errors)
    effective_errors = []
    effective = parse_time(contract["effective_at"], "effective_at", effective_errors)
    expires = parse_time(contract["expires_at"], "expires_at", effective_errors)

    if request["principal_id"] != contract["principal"]["principal_id"]:
        result["decision"] = "DENY"
        reasons.append("principal does not match the contract")
    elif request["agent_id"] != contract["agent"]["agent_id"]:
        result["decision"] = "DENY"
        reasons.append("agent identity does not match the contract")
    elif request["delegation_chain"]:
        delegation = contract["delegation"]
        if not delegation["allowed"]:
            result["decision"] = "DENY"
            reasons.append("delegation is disabled")
        elif len(request["delegation_chain"]) > delegation["max_depth"]:
            result["decision"] = "DENY"
            reasons.append("delegation depth exceeds the contract")
        elif any(agent_id not in delegation["allowed_agent_ids"] for agent_id in request["delegation_chain"]):
            result["decision"] = "DENY"
            reasons.append("delegation chain contains an unauthorized agent")

    if result["decision"] is None:
        if contract["status"] != "approved":
            result["decision"] = "HOLD"
            reasons.append("contract is not approved")
        elif request_time < effective or request_time > expires:
            result["decision"] = "HOLD"
            reasons.append("contract is not active at the request timestamp")
        elif request["state_status"] != "known":
            result["decision"] = "HOLD"
            reasons.append("execution state is unknown or partially failed")
        elif request["triggered_stop_conditions"]:
            result["decision"] = "HOLD"
            reasons.append("stop condition triggered: " + ", ".join(sorted(request["triggered_stop_conditions"])))

    matches = sorted((rule for rule in contract["rules"] if rule_matches(rule, request)), key=lambda item: item["rule_id"])
    result["matched_rule_ids"] = [rule["rule_id"] for rule in matches]
    result["required_controls"] = sorted({control["control_id"] for rule in matches for control in rule["controls"]})

    if not matches:
        result["decision"] = "DENY"
        reasons.append("no rule matches the complete action context")
    elif any(rule["decision"] == "deny" for rule in matches):
        result["decision"] = "DENY"
        reasons.append("an explicit deny rule matches")

    limit_denials = []
    limit_holds = []
    missing_context = []
    unavailable = set(request.get("unavailable_controls", []))
    control_holds = []
    for rule in matches:
        if rule["decision"] == "deny":
            continue
        for field in rule["required_context"]:
            if field not in request or request[field] in (None, "", [], {}):
                missing_context.append(f"{rule['rule_id']} requires {field}")
        denials, holds = evaluate_limits(rule, request)
        limit_denials.extend(denials)
        limit_holds.extend(holds)
        required_hard = controls_for(rule, "external_enforcement")
        sensitive_read = request["effect"] == "read" and request["data_class"] != "public"
        if (request["effect"] in MUTATING_EFFECTS or sensitive_read) and not any(control["status"] == "verified" for control in required_hard):
            control_holds.append(f"{rule['rule_id']} lacks verified external enforcement")
        for control in rule["controls"]:
            if control["status"] in {"missing", "unknown"} or control["control_id"] in unavailable:
                control_holds.append(f"required control unavailable: {control['control_id']}")

    if limit_denials:
        result["decision"] = "DENY"
        reasons.extend(limit_denials)
    if result["decision"] is None and (missing_context or limit_holds or control_holds):
        result["decision"] = "HOLD"
        reasons.extend(missing_context + limit_holds + control_holds)
    if any(rule["risk_tier"] == "critical" for rule in matches):
        result["decision"] = "DENY"
        reasons.append("critical action cannot be authorized by this skill")
    if result["decision"] is None and any(rule["decision"] == "allow" and rule["risk_tier"] == "high" for rule in matches):
        result["decision"] = "HOLD"
        reasons.append("high-risk autonomous allow rule requires policy remediation")

    approval_rules = [rule for rule in matches if rule["decision"] == "require_approval"]
    receipt_valid = True
    if result["decision"] is None and approval_rules:
        receipt = request.get("approval_receipt")
        if not isinstance(receipt, dict):
            receipt_valid = False
            result["decision"] = "APPROVAL_REQUIRED"
            reasons.append("fresh external approval is required")
        else:
            for rule in approval_rules:
                valid, receipt_errors = validate_receipt(receipt, request, contract, rule, request_time)
                if not valid:
                    receipt_valid = False
                    if any("cannot approve its own" in item or "separation of duties" in item for item in receipt_errors):
                        result["decision"] = "DENY"
                    else:
                        result["decision"] = "APPROVAL_REQUIRED"
                    reasons.extend(receipt_errors)
            if receipt_valid:
                warnings.append("external approval receipt fields are self-asserted in this local file; production must verify signature, identity, role, revocation and single use")

    if result["decision"] is None:
        result["decision"] = "ALLOW"
        reasons.append("request satisfies every matching rule and no stricter rule applies")

    lint = lint_contract(contract)
    if lint["errors"] and result["decision"] == "ALLOW":
        result["decision"] = "HOLD"
        reasons.append("contract has deployment-blocking lint errors")
        warnings.extend(lint["errors"])

    # This local utility is never an authorization or enforcement point. A runtime
    # integration may consume the policy decision only after independently verifying
    # identity, signatures, revocation, single use, limits, controls, and current user authority.
    result["execution_authorized"] = False
    if contract["case_purpose"] == "synthetic_fixture":
        warnings.append("synthetic fixture: execution_authorized is always false")
    result["reasons"] = sorted(set(reasons))
    result["warnings"] = sorted(set(warnings))
    return result


def coverage_report(contract):
    errors = validate_contract(contract)
    if errors:
        raise ContractError("; ".join(errors))
    items = []
    for action in contract["action_universe"]:
        rules = [rule for rule in contract["rules"] if action["action_type"] in rule["action_types"] and action["effect"] in rule["effects"]]
        items.append({
            "action_type": action["action_type"],
            "effect": action["effect"],
            "rule_ids": sorted(rule["rule_id"] for rule in rules),
            "decisions": sorted({rule["decision"] for rule in rules}),
            "covered": bool(rules),
        })
    return {"contract_id": contract["contract_id"], "contract_version": contract["version"], "actions": items, "complete": all(item["covered"] for item in items)}


def diff_contracts(old, new):
    old_errors = validate_contract(old)
    new_errors = validate_contract(new)
    if old_errors or new_errors:
        raise ContractError("; ".join([f"old: {item}" for item in old_errors] + [f"new: {item}" for item in new_errors]))
    if old["contract_id"] != new["contract_id"]:
        raise ContractError("contract IDs differ; authority cannot be compared as one version chain")
    if new["version"] <= old["version"]:
        raise ContractError("new contract version must be greater than old contract version")
    if new["change_control"]["previous_version"] != old["version"]:
        raise ContractError("new change_control.previous_version must equal the old version")

    expansions = []
    reductions = []
    review = []
    old_actions = {item["action_type"]: item for item in old["action_universe"]}
    new_actions = {item["action_type"]: item for item in new["action_universe"]}
    for action_type in sorted(set(new_actions) - set(old_actions)):
        expansions.append(f"new action in universe: {action_type}")
    for action_type in sorted(set(old_actions) - set(new_actions)):
        reductions.append(f"removed action from universe: {action_type}")
    for action_type in sorted(set(old_actions) & set(new_actions)):
        for key in ("effect", "resources", "environments", "tools", "data_classes", "side_effects"):
            if old_actions[action_type][key] != new_actions[action_type][key]:
                review.append(f"action universe changed for {action_type}.{key}")

    old_rules = {item["rule_id"]: item for item in old["rules"]}
    new_rules = {item["rule_id"]: item for item in new["rules"]}
    for rule_id in sorted(set(new_rules) - set(old_rules)):
        rule = new_rules[rule_id]
        if rule["decision"] in {"allow", "require_approval"}:
            expansions.append(f"new permissive rule: {rule_id} ({rule['decision']})")
        else:
            reductions.append(f"new deny rule: {rule_id}")
    for rule_id in sorted(set(old_rules) - set(new_rules)):
        rule = old_rules[rule_id]
        if rule["decision"] == "deny":
            expansions.append(f"deny rule removed: {rule_id}")
        else:
            review.append(f"non-deny rule removed: {rule_id}")

    restrictiveness = {"allow": 1, "require_approval": 2, "deny": 3}
    risk_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    for rule_id in sorted(set(old_rules) & set(new_rules)):
        before = old_rules[rule_id]
        after = new_rules[rule_id]
        if restrictiveness[after["decision"]] < restrictiveness[before["decision"]]:
            expansions.append(f"decision relaxed for {rule_id}: {before['decision']} -> {after['decision']}")
        elif restrictiveness[after["decision"]] > restrictiveness[before["decision"]]:
            reductions.append(f"decision tightened for {rule_id}: {before['decision']} -> {after['decision']}")
        if risk_rank[after["risk_tier"]] < risk_rank[before["risk_tier"]]:
            expansions.append(f"risk tier lowered for {rule_id}: {before['risk_tier']} -> {after['risk_tier']}")

        for key in ("action_types", "effects", "environments", "tools", "data_classes"):
            added = sorted(set(after[key]) - set(before[key]))
            removed = sorted(set(before[key]) - set(after[key]))
            if added:
                expansions.append(f"selector broadened for {rule_id}.{key}: added {added}")
            if removed:
                reductions.append(f"selector narrowed for {rule_id}.{key}: removed {removed}")
        if before["resource_prefixes"] != after["resource_prefixes"]:
            review.append(f"resource prefixes changed for {rule_id}; prove subset relation manually")

        before_limits = before["limits"]
        after_limits = after["limits"]
        for key in ("max_amount", "max_cumulative_amount", "max_actions", "max_retries"):
            if key in before_limits and key not in after_limits:
                expansions.append(f"limit removed for {rule_id}.{key}")
            elif key in before_limits and key in after_limits and after_limits[key] > before_limits[key]:
                expansions.append(f"limit increased for {rule_id}.{key}: {before_limits[key]} -> {after_limits[key]}")
            elif key in before_limits and key in after_limits and after_limits[key] < before_limits[key]:
                reductions.append(f"limit reduced for {rule_id}.{key}: {before_limits[key]} -> {after_limits[key]}")
        if "max_actions" in before_limits and "max_actions" in after_limits:
            before_rate = before_limits["max_actions"] / before_limits["window_seconds"]
            after_rate = after_limits["max_actions"] / after_limits["window_seconds"]
            if after_rate > before_rate and not any(f"{rule_id}.max_actions" in item for item in expansions):
                expansions.append(f"action rate increased for {rule_id}")
        before_controls = {item["control_id"] for item in before["controls"]}
        after_controls = {item["control_id"] for item in after["controls"]}
        for control_id in sorted(before_controls - after_controls):
            expansions.append(f"control removed from {rule_id}: {control_id}")
        for control_id in sorted(after_controls - before_controls):
            review.append(f"control added to {rule_id}: {control_id}; verify external implementation")
        if "approval" in before and "approval" not in after:
            expansions.append(f"approval requirement removed from {rule_id}")
        elif before.get("approval") != after.get("approval"):
            review.append(f"approval protocol changed for {rule_id}")
        if before["rollback"] != after["rollback"]:
            review.append(f"rollback changed for {rule_id}")

    old_delegation = old["delegation"]
    new_delegation = new["delegation"]
    if not old_delegation["allowed"] and new_delegation["allowed"]:
        expansions.append("delegation enabled")
    if new_delegation["max_depth"] > old_delegation["max_depth"]:
        expansions.append(f"delegation depth increased: {old_delegation['max_depth']} -> {new_delegation['max_depth']}")
    added_delegates = sorted(set(new_delegation["allowed_agent_ids"]) - set(old_delegation["allowed_agent_ids"]))
    if added_delegates:
        expansions.append(f"delegates added: {added_delegates}")
    old_expires_errors = []
    old_expires = parse_time(old["expires_at"], "old.expires_at", old_expires_errors)
    new_expires = parse_time(new["expires_at"], "new.expires_at", old_expires_errors)
    if new_expires > old_expires:
        expansions.append("contract expiry extended")

    return {
        "contract_id": old["contract_id"],
        "old_version": old["version"],
        "new_version": new["version"],
        "old_digest": digest(old),
        "new_digest": digest(new),
        "authority_expansion_detected": bool(expansions),
        "accountable_reapproval_required": bool(expansions or review),
        "expansions": sorted(set(expansions)),
        "reductions": sorted(set(reductions)),
        "manual_review": sorted(set(review)),
    }


def simulate(contract, scenarios):
    details = []
    passed = 0
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict) or set(scenario) != {"name", "request", "expected_decision"}:
            raise ContractError(f"scenario {index + 1} must contain exactly name, request, expected_decision")
        if not isinstance(scenario["name"], str) or not scenario["name"].strip():
            raise ContractError(f"scenario {index + 1} name must be non-empty")
        if not is_enum(scenario["expected_decision"], {"ALLOW", "APPROVAL_REQUIRED", "DENY", "HOLD"}):
            raise ContractError(f"scenario {index + 1} expected_decision is invalid")
        result = decide(contract, scenario["request"])
        okay = result["decision"] == scenario["expected_decision"]
        passed += int(okay)
        details.append({
            "name": scenario["name"],
            "expected": scenario["expected_decision"],
            "actual": result["decision"],
            "passed": okay,
            "execution_authorized": result["execution_authorized"],
            "matched_rule_ids": result["matched_rule_ids"],
        })
    return {"passed": passed, "total": len(details), "all_passed": passed == len(details), "details": details}


def emit(value):
    print(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate and test an Autonomy Governor authority contract; never executes actions.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "lint", "coverage"):
        sub = subparsers.add_parser(name)
        sub.add_argument("contract")
    decide_parser = subparsers.add_parser("decide")
    decide_parser.add_argument("contract")
    decide_parser.add_argument("request")
    simulate_parser = subparsers.add_parser("simulate")
    simulate_parser.add_argument("contract")
    simulate_parser.add_argument("scenarios")
    diff_parser = subparsers.add_parser("diff")
    diff_parser.add_argument("old_contract")
    diff_parser.add_argument("new_contract")
    digest_parser = subparsers.add_parser("digest-request")
    digest_parser.add_argument("request")
    fingerprint_parser = subparsers.add_parser("fingerprint")
    fingerprint_parser.add_argument("path")
    args = parser.parse_args(argv)

    try:
        if args.command == "fingerprint":
            path = pathlib.Path(args.path)
            if path.stat().st_size > MAX_BYTES:
                raise ContractError(f"file exceeds {MAX_BYTES} bytes")
            emit({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            return 0
        if args.command == "digest-request":
            request = load_json(args.request)
            errors = validate_request(request)
            if errors:
                emit({"valid": False, "errors": errors})
                return 2
            emit({"request_id": request["request_id"], "action_digest": action_digest(request)})
            return 0
        if args.command == "diff":
            emit(diff_contracts(load_json(args.old_contract), load_json(args.new_contract)))
            return 0

        contract = load_json(args.contract)
        if args.command == "validate":
            errors = validate_contract(contract)
            emit({"valid": not errors, "errors": errors, "contract_digest": digest(contract) if not errors else None})
            return 0 if not errors else 2
        if args.command == "lint":
            report = lint_contract(contract)
            report["contract_digest"] = digest(contract) if not validate_contract(contract) else None
            emit(report)
            return 0 if report["valid"] else 2
        if args.command == "coverage":
            emit(coverage_report(contract))
            return 0
        if args.command == "decide":
            emit(decide(contract, load_json(args.request)))
            return 0
        if args.command == "simulate":
            report = simulate(contract, load_jsonl(args.scenarios))
            emit(report)
            return 0 if report["all_passed"] else 1
    except (OSError, ContractError, TypeError, KeyError) as exc:
        emit({"error": str(exc)})
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())

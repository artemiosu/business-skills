#!/usr/bin/env python3
"""Deterministic, offline validation and diagnostics for evidence lineage records."""

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

MAX_BYTES = 5_000_000
MAX_RECORDS = 20_000
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
CONFIRMED = {"machine_observed", "human_adjudicated"}

ENUMS = {
    "mode": {"quick", "deep", "audit", "update"},
    "corpus_contract": {"closed_corpus", "open_web"},
    "case_purpose": {"operational", "synthetic_fixture"},
    "entity_kind": {"person", "organization", "publisher", "data_producer", "other"},
    "source_type": {"press_release", "news_report", "research_paper", "dataset", "filing", "official_record", "survey", "interview", "social_post", "transcript", "ai_summary", "other"},
    "access_status": {"full", "partial", "metadata_only", "inaccessible"},
    "provenance_status": {"verified", "partially_verified", "unverified"},
    "correction_status": {"checked_none_found", "corrected", "retracted", "superseded", "withdrawn", "not_checked", "not_applicable", "unknown"},
    "directness": {"primary", "secondary", "unknown"},
    "interest": {"interested", "disinterested", "unknown"},
    "cutoff_availability": {"contemporary_retrieval", "verified_pre_cutoff", "unknown"},
    "materiality": {"critical", "important", "context"},
    "claim_type": {"observation", "measurement", "estimate", "inference", "forecast", "opinion", "allegation"},
    "counterevidence_search": {"completed", "limited", "not_run"},
    "stance": {"supports", "contradicts", "neutral", "inaccessible"},
    "support_relation": {"direct", "partial", "mentions", "inaccessible"},
    "text_kind": {"quote", "paraphrase"},
    "evidence_status": {"active", "superseded", "withdrawn", "uncertain"},
    "origin_type": {"direct_observation", "dataset", "experiment", "survey", "interview", "filing", "official_statement", "press_release", "wire_report", "analysis", "transaction", "other", "unknown"},
    "verification_status": {"verified", "partially_verified", "unverified"},
    "origin_role": {"underlying_observation", "reporting_origin", "analysis_origin"},
    "support_mode": {"sufficient", "jointly_necessary", "corroborative", "contextual"},
    "link_status": {"machine_observed", "human_adjudicated", "inferred_candidate", "unresolved", "rejected"},
    "dimension": {"asset", "editorial", "observation", "dataset", "method", "ownership", "claim"},
    "relation": {"exact_copy_of", "version_of", "republishes", "wire_syndication", "translates", "quotes", "summarizes", "cites", "uses_dataset", "reports_same_observation", "independently_observes", "shared_method", "common_owner", "common_funder", "ai_transformation", "supersedes", "conflicts_with", "citation_only", "possible_common_origin"},
    "adjudication_label": {"confirmed", "rejected", "unresolved", "superseded"},
    "query_family": {"exact_phrase", "distinctive_bundle", "named_identifier", "earliest_archive", "corrections", "counterevidence", "multilingual", "other"},
}

DISTORTIONS = {
    "attribution_bleaching", "qualification_removed", "modality_hardened",
    "scope_broadened", "scope_narrowed", "denominator_lost",
    "timeframe_shifted", "geography_shifted", "unit_or_currency_changed",
    "precision_inflated", "correlation_upgraded_to_causation",
    "opinion_upgraded_to_fact", "single_source_upgraded_to_consensus",
    "quote_mined", "headline_body_mismatch", "translation_semantic_drift",
    "correction_stripped", "obsolete_dataset_presented_as_current",
    "subgroup_cherry_pick", "fabricated_or_unresolved_citation",
}

RELATION_DIMENSIONS = {
    "exact_copy_of": {"asset"}, "version_of": {"asset"},
    "republishes": {"editorial"}, "wire_syndication": {"editorial"},
    "translates": {"editorial"}, "quotes": {"editorial"},
    "summarizes": {"editorial"}, "cites": {"editorial"},
    "uses_dataset": {"dataset"}, "reports_same_observation": {"observation"},
    "independently_observes": {"observation"}, "shared_method": {"method"},
    "common_owner": {"ownership"}, "common_funder": {"ownership"},
    "ai_transformation": {"editorial"}, "supersedes": {"asset"},
    "conflicts_with": {"claim"}, "citation_only": {"editorial"},
    "possible_common_origin": {"editorial", "observation", "dataset"},
}

DIRECTIONAL = {
    "exact_copy_of", "version_of", "republishes", "wire_syndication",
    "translates", "quotes", "summarizes", "ai_transformation", "supersedes",
}
TEMPORAL_DIRECTIONAL = DIRECTIONAL | {"cites", "citation_only", "uses_dataset"}

ALLOWED = {
    "case": {"record_type", "id", "schema_version", "title", "mode", "corpus_contract", "case_purpose", "as_of_date", "analysis_date", "inclusion_rule", "stopping_rule", "decision_context", "limitations", "supersedes_case_id"},
    "entity": {"record_type", "id", "kind", "canonical_name", "stable_ids", "aliases", "notes"},
    "document_snapshot": {"record_type", "id", "work_id", "version_id", "title", "publisher_entity_id", "author_entity_ids", "locator", "canonical_locator", "published_at", "retrieved_at", "source_type", "language", "access_status", "provenance_status", "correction_status", "directness", "interest", "cutoff_availability", "stable_identifiers", "content_sha256", "conflict_notes", "date_notes", "notes"},
    "claim": {"record_type", "id", "text", "materiality", "claim_type", "scope", "counterevidence_search", "decision_use", "notes"},
    "claim_occurrence": {"record_type", "id", "claim_id", "document_id", "stance", "support_relation", "expressed_text", "text_kind", "source_locator", "available_at", "evidence_status", "method_family", "date_notes", "notes"},
    "origin": {"record_type", "id", "origin_type", "description", "producer_entity_id", "stable_identifier", "observed_period", "version", "verification_status", "interest", "notes"},
    "origin_assignment": {"record_type", "id", "occurrence_id", "origin_id", "role", "support_mode", "support_unit_id", "status", "basis", "notes", "supersedes_record_id"},
    "lineage_edge": {"record_type", "id", "from_occurrence_id", "to_occurrence_id", "relation", "dimension", "status", "basis", "distortion_flags", "notes", "supersedes_record_id"},
    "adjudication": {"record_type", "id", "target_id", "label", "rationale", "evidence_refs", "reviewer", "created_at", "supersedes_record_id"},
    "search_log": {"record_type", "id", "query_family", "query_text", "searched_at", "provider", "language", "result_count_reviewed", "included_document_ids", "access_gap_document_ids", "excluded_result_notes", "search_snapshot_sha256", "notes"},
}

REQUIRED = {
    "case": {"record_type", "id", "schema_version", "title", "mode", "corpus_contract", "case_purpose", "as_of_date", "analysis_date", "inclusion_rule", "stopping_rule", "limitations"},
    "entity": {"record_type", "id", "kind", "canonical_name", "stable_ids", "aliases"},
    "document_snapshot": {"record_type", "id", "work_id", "version_id", "title", "publisher_entity_id", "author_entity_ids", "locator", "published_at", "retrieved_at", "source_type", "language", "access_status", "provenance_status", "correction_status", "directness", "interest", "cutoff_availability", "stable_identifiers", "conflict_notes"},
    "claim": {"record_type", "id", "text", "materiality", "claim_type", "scope", "counterevidence_search"},
    "claim_occurrence": {"record_type", "id", "claim_id", "document_id", "stance", "support_relation", "expressed_text", "text_kind", "source_locator", "available_at", "evidence_status", "method_family"},
    "origin": {"record_type", "id", "origin_type", "description", "verification_status", "interest"},
    "origin_assignment": {"record_type", "id", "occurrence_id", "origin_id", "role", "support_mode", "support_unit_id", "status", "basis"},
    "lineage_edge": {"record_type", "id", "from_occurrence_id", "to_occurrence_id", "relation", "dimension", "status", "basis", "distortion_flags"},
    "adjudication": {"record_type", "id", "target_id", "label", "rationale", "evidence_refs", "reviewer", "created_at"},
    "search_log": {"record_type", "id", "query_family", "query_text", "searched_at", "provider", "language", "result_count_reviewed", "included_document_ids", "access_gap_document_ids", "excluded_result_notes"},
}


class DuplicateKeyError(ValueError):
    pass


def _pairs_no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _reject_constant(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def load_jsonl(path):
    path = pathlib.Path(path)
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"input exceeds {MAX_BYTES} bytes")
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            if len(raw.encode("utf-8")) > 500_000:
                raise ValueError(f"line {lineno}: record too large")
            if not raw.strip():
                continue
            try:
                record = json.loads(raw, object_pairs_hook=_pairs_no_duplicates, parse_constant=_reject_constant)
            except (json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
                raise ValueError(f"line {lineno}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"line {lineno}: record must be an object")
            records.append(record)
            if len(records) > MAX_RECORDS:
                raise ValueError(f"input exceeds {MAX_RECORDS} records")
    return records


def effective_records(records):
    """Return append-only leaf records after explicit supersession."""
    superseded = {
        record.get("supersedes_record_id")
        for record in records
        if isinstance(record.get("supersedes_record_id"), str) and record.get("supersedes_record_id")
    }
    return [record for record in records if record.get("id") not in superseded]


def strongly_connected_components(nodes, directed_edges):
    """Iterative Kosaraju implementation safe for large valid inputs."""
    adjacency = {node: [] for node in nodes}
    reverse = {node: [] for node in nodes}
    for child, parent in directed_edges:
        adjacency.setdefault(child, []).append(parent)
        adjacency.setdefault(parent, [])
        reverse.setdefault(parent, []).append(child)
        reverse.setdefault(child, [])
    for values in adjacency.values():
        values.sort()
    for values in reverse.values():
        values.sort()

    seen, order = set(), []
    for start in sorted(adjacency):
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, 0)]
        while stack:
            node, index = stack[-1]
            neighbors = adjacency[node]
            if index < len(neighbors):
                nxt = neighbors[index]
                stack[-1] = (node, index + 1)
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, 0))
            else:
                stack.pop()
                order.append(node)

    seen.clear()
    components = []
    for start in reversed(order):
        if start in seen:
            continue
        component, stack = [], [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for nxt in reverse[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if len(component) > 1:
            components.append(sorted(component))
    return sorted(components)


def parse_date(value, path, errors):
    if not isinstance(value, str):
        errors.append(f"{path}: expected ISO date string")
        return None
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path}: invalid ISO date")
        return None
    if parsed.isoformat() != value:
        errors.append(f"{path}: date must use YYYY-MM-DD")
        return None
    return parsed


def parse_optional_date(value, path, errors):
    """Parse a documented date when known; None represents explicit uncertainty."""
    if value is None:
        return None
    return parse_date(value, path, errors)


def need_string(record, key, path, errors, max_len=4000):
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{key}: non-empty string required")
        return None
    if len(value) > max_len:
        errors.append(f"{path}.{key}: exceeds {max_len} characters")
    return value


def need_enum(record, key, enum_name, path, errors):
    value = record.get(key)
    if value not in ENUMS[enum_name]:
        errors.append(f"{path}.{key}: expected one of {sorted(ENUMS[enum_name])}")
    return value


def optional_string(record, key, path, errors, max_len=4000):
    if key not in record:
        return None
    value = record[key]
    if not isinstance(value, str):
        errors.append(f"{path}.{key}: string required when present")
        return None
    if len(value) > max_len:
        errors.append(f"{path}.{key}: exceeds {max_len} characters")
    return value


def need_string_list(record, key, path, errors, max_items=100):
    value = record.get(key)
    if not isinstance(value, list) or len(value) > max_items or any(not isinstance(x, str) or not x.strip() for x in value):
        errors.append(f"{path}.{key}: expected a list of at most {max_items} non-empty strings")
        return []
    return value


def validate_records(records):
    errors, warnings = [], []
    by_type = defaultdict(list)
    ids = {}

    for index, record in enumerate(records, 1):
        path = f"record[{index}]"
        rtype = record.get("record_type")
        if not isinstance(rtype, str) or rtype not in ALLOWED:
            errors.append(f"{path}.record_type: unknown type {rtype!r}")
            continue
        by_type[rtype].append(record)
        missing = REQUIRED[rtype] - set(record)
        unknown = set(record) - ALLOWED[rtype]
        if missing:
            errors.append(f"{path}: missing fields {sorted(missing)}")
        if unknown:
            errors.append(f"{path}: unknown fields {sorted(unknown)}")
        rid = record.get("id")
        if not isinstance(rid, str) or not ID_RE.fullmatch(rid):
            errors.append(f"{path}.id: invalid stable ID")
        elif rid in ids:
            errors.append(f"{path}.id: duplicate ID {rid}")
        else:
            ids[rid] = record

    if len(by_type["case"]) != 1:
        errors.append("records: exactly one case record is required")
        case = None
    else:
        case = by_type["case"][0]

    entities = {r.get("id"): r for r in by_type["entity"]}
    documents = {r.get("id"): r for r in by_type["document_snapshot"]}
    claims = {r.get("id"): r for r in by_type["claim"]}
    occurrences = {r.get("id"): r for r in by_type["claim_occurrence"]}
    origins = {r.get("id"): r for r in by_type["origin"]}

    successor_by_prior = defaultdict(list)
    supersession_edges = []
    for record in records:
        prior_id = record.get("supersedes_record_id")
        if not prior_id:
            continue
        path = f"{record.get('record_type')}[{record.get('id')}]"
        if not isinstance(prior_id, str) or not ID_RE.fullmatch(prior_id):
            errors.append(f"{path}.supersedes_record_id: invalid stable ID")
            continue
        prior = ids.get(prior_id)
        if prior_id == record.get("id"):
            errors.append(f"{path}.supersedes_record_id: self-supersession is not allowed")
        elif not prior:
            errors.append(f"{path}.supersedes_record_id: orphan reference {prior_id!r}")
        elif prior.get("record_type") != record.get("record_type"):
            errors.append(f"{path}.supersedes_record_id: record types must match")
        else:
            if record.get("record_type") == "origin_assignment" and (record.get("occurrence_id"), record.get("role")) != (prior.get("occurrence_id"), prior.get("role")):
                errors.append(f"{path}: superseding assignment must preserve occurrence and role")
            if record.get("record_type") == "lineage_edge" and (record.get("from_occurrence_id"), record.get("to_occurrence_id")) != (prior.get("from_occurrence_id"), prior.get("to_occurrence_id")):
                errors.append(f"{path}: superseding edge must preserve endpoints")
            if record.get("record_type") == "adjudication" and record.get("target_id") != prior.get("target_id"):
                errors.append(f"{path}: superseding adjudication must preserve target")
        successor_by_prior[prior_id].append(record.get("id"))
        supersession_edges.append((record.get("id"), prior_id))
    for prior_id, successors in successor_by_prior.items():
        if len(successors) > 1:
            errors.append(f"supersession fork at {prior_id}: {sorted(successors)}")
    if strongly_connected_components(ids, supersession_edges):
        errors.append("supersession cycle detected")

    as_of = analysis_date = None
    if case:
        path = f"case[{case.get('id')}]"
        need_string(case, "title", path, errors, 500)
        need_string(case, "inclusion_rule", path, errors, 2000)
        need_string(case, "stopping_rule", path, errors, 2000)
        need_enum(case, "mode", "mode", path, errors)
        need_enum(case, "corpus_contract", "corpus_contract", path, errors)
        need_enum(case, "case_purpose", "case_purpose", path, errors)
        need_string_list(case, "limitations", path, errors)
        if case.get("schema_version") != "1.0.0":
            errors.append(f"{path}.schema_version: expected 1.0.0")
        as_of = parse_date(case.get("as_of_date"), f"{path}.as_of_date", errors)
        analysis_date = parse_date(case.get("analysis_date"), f"{path}.analysis_date", errors)
        if as_of and analysis_date and as_of > analysis_date:
            errors.append(f"{path}: as_of_date cannot follow analysis_date")
        parent = case.get("supersedes_case_id")
        if case.get("mode") == "update" and not parent:
            errors.append(f"{path}.supersedes_case_id: required for update mode")
        if parent is not None and (not isinstance(parent, str) or not ID_RE.fullmatch(parent)):
            errors.append(f"{path}.supersedes_case_id: invalid stable ID")
        if parent == case.get("id"):
            errors.append(f"{path}.supersedes_case_id: case cannot supersede itself")
        optional_string(case, "decision_context", path, errors, 2000)

    if case and case.get("corpus_contract") == "open_web" and not by_type["search_log"]:
        errors.append("records: open_web corpus requires at least one search_log record")

    for record in by_type["entity"]:
        path = f"entity[{record.get('id')}]"
        need_enum(record, "kind", "entity_kind", path, errors)
        need_string(record, "canonical_name", path, errors, 500)
        need_string_list(record, "stable_ids", path, errors)
        need_string_list(record, "aliases", path, errors)
        optional_string(record, "notes", path, errors)

    for record in by_type["search_log"]:
        path = f"search_log[{record.get('id')}]"
        need_enum(record, "query_family", "query_family", path, errors)
        for key in ("query_text", "provider", "language"):
            need_string(record, key, path, errors, 2000)
        searched = parse_date(record.get("searched_at"), f"{path}.searched_at", errors)
        if searched and analysis_date and searched > analysis_date:
            errors.append(f"{path}.searched_at: cannot follow analysis_date")
        reviewed = record.get("result_count_reviewed")
        if isinstance(reviewed, bool) or not isinstance(reviewed, int) or not 0 <= reviewed <= 100_000:
            errors.append(f"{path}.result_count_reviewed: integer from 0 to 100000 required")
        included = need_string_list(record, "included_document_ids", path, errors)
        gaps = need_string_list(record, "access_gap_document_ids", path, errors)
        need_string_list(record, "excluded_result_notes", path, errors)
        for document_id in included + gaps:
            if document_id not in documents:
                errors.append(f"{path}: orphan document reference {document_id!r}")
        if isinstance(reviewed, int) and not isinstance(reviewed, bool) and reviewed < len(set(included + gaps)):
            errors.append(f"{path}.result_count_reviewed: cannot be smaller than recorded included/access-gap documents")
        digest = record.get("search_snapshot_sha256")
        if digest is not None and (not isinstance(digest, str) or not SHA_RE.fullmatch(digest)):
            errors.append(f"{path}.search_snapshot_sha256: expected sha256:<64 lowercase hex>")
        optional_string(record, "notes", path, errors)

    document_dates, retrieval_dates = {}, {}
    snapshot_identities = defaultdict(list)
    invalid_current = {"retracted", "superseded", "withdrawn"}
    for record in by_type["document_snapshot"]:
        path = f"document_snapshot[{record.get('id')}]"
        for key in ("work_id", "version_id", "title", "locator", "language"):
            need_string(record, key, path, errors, 1000)
        need_enum(record, "source_type", "source_type", path, errors)
        need_enum(record, "access_status", "access_status", path, errors)
        need_enum(record, "provenance_status", "provenance_status", path, errors)
        need_enum(record, "correction_status", "correction_status", path, errors)
        need_enum(record, "directness", "directness", path, errors)
        need_enum(record, "interest", "interest", path, errors)
        need_enum(record, "cutoff_availability", "cutoff_availability", path, errors)
        author_ids = need_string_list(record, "author_entity_ids", path, errors)
        stable_identifiers = need_string_list(record, "stable_identifiers", path, errors)
        need_string_list(record, "conflict_notes", path, errors)
        pub = parse_optional_date(record.get("published_at"), f"{path}.published_at", errors)
        ret = parse_date(record.get("retrieved_at"), f"{path}.retrieved_at", errors)
        document_dates[record.get("id")] = pub
        retrieval_dates[record.get("id")] = ret
        if pub and ret and pub > ret:
            errors.append(f"{path}: published_at cannot follow retrieved_at")
        if pub and as_of and pub > as_of:
            errors.append(f"{path}: published_at exceeds case cutoff")
        if ret and analysis_date and ret > analysis_date:
            errors.append(f"{path}: retrieved_at exceeds analysis_date")
        if ret and as_of and ret > as_of and record.get("cutoff_availability") != "verified_pre_cutoff":
            errors.append(f"{path}: post-cutoff retrieval requires verified_pre_cutoff availability")
        publisher = record.get("publisher_entity_id")
        if not isinstance(publisher, str) or publisher not in entities:
            errors.append(f"{path}.publisher_entity_id: orphan reference {publisher!r}")
        for author in author_ids:
            if author not in entities:
                errors.append(f"{path}.author_entity_ids: orphan reference {author!r}")
        digest = record.get("content_sha256")
        if digest is not None and (not isinstance(digest, str) or not SHA_RE.fullmatch(digest)):
            errors.append(f"{path}.content_sha256: expected sha256:<64 lowercase hex>")
        if digest is None and record.get("access_status") in {"full", "partial"}:
            warnings.append(f"{path}: no content hash recorded")
        snapshot_identity = (record.get("work_id"), record.get("version_id"), digest)
        if digest and all(isinstance(item, str) and item for item in snapshot_identity):
            snapshot_identities[snapshot_identity].append(record.get("id"))
        if record.get("provenance_status") == "unverified":
            warnings.append(f"{path}: provenance unverified")
        if record.get("correction_status") in {"not_checked", "unknown"}:
            warnings.append(f"{path}: correction status unresolved")
        optional_string(record, "canonical_locator", path, errors, 2000)
        optional_string(record, "date_notes", path, errors, 2000)
        optional_string(record, "notes", path, errors)
    for duplicate_ids in snapshot_identities.values():
        if len(duplicate_ids) > 1:
            warnings.append(f"duplicate document snapshot identity: {sorted(duplicate_ids)}")

    for record in by_type["claim"]:
        path = f"claim[{record.get('id')}]"
        need_string(record, "text", path, errors, 2000)
        need_enum(record, "materiality", "materiality", path, errors)
        need_enum(record, "claim_type", "claim_type", path, errors)
        need_enum(record, "counterevidence_search", "counterevidence_search", path, errors)
        scope = record.get("scope")
        scope_keys = {"population", "metric", "denominator", "geography", "period", "modality"}
        if not isinstance(scope, dict) or set(scope) != scope_keys:
            errors.append(f"{path}.scope: expected exactly {sorted(scope_keys)}")
        else:
            for key in sorted(scope_keys):
                need_string(scope, key, f"{path}.scope", errors, 500)
        if record.get("counterevidence_search") != "completed":
            warnings.append(f"{path}: counterevidence search not completed")
        optional_string(record, "decision_use", path, errors, 2000)
        optional_string(record, "notes", path, errors)

    occurrence_dates = {}
    for record in by_type["claim_occurrence"]:
        path = f"claim_occurrence[{record.get('id')}]"
        need_enum(record, "stance", "stance", path, errors)
        need_enum(record, "support_relation", "support_relation", path, errors)
        need_enum(record, "text_kind", "text_kind", path, errors)
        need_enum(record, "evidence_status", "evidence_status", path, errors)
        for key in ("expressed_text", "source_locator", "method_family"):
            need_string(record, key, path, errors, 2000)
        claim_id, document_id = record.get("claim_id"), record.get("document_id")
        if not isinstance(claim_id, str) or claim_id not in claims:
            errors.append(f"{path}.claim_id: orphan reference {claim_id!r}")
        if not isinstance(document_id, str) or document_id not in documents:
            errors.append(f"{path}.document_id: orphan reference {document_id!r}")
        available = parse_optional_date(record.get("available_at"), f"{path}.available_at", errors)
        occurrence_dates[record.get("id")] = available
        pub = document_dates.get(document_id) if isinstance(document_id, str) else None
        ret = retrieval_dates.get(document_id) if isinstance(document_id, str) else None
        if available and pub and available < pub:
            errors.append(f"{path}: available_at cannot precede document publication")
        if available and as_of and available > as_of:
            errors.append(f"{path}: available_at exceeds case cutoff")
        if available and ret and available > ret:
            errors.append(f"{path}: available_at cannot follow document retrieval")
        stance, relation = record.get("stance"), record.get("support_relation")
        if stance == "inaccessible" and relation != "inaccessible":
            errors.append(f"{path}: inaccessible stance requires inaccessible support_relation")
        if stance in {"supports", "contradicts"} and relation not in {"direct", "partial"}:
            errors.append(f"{path}: supporting/contradicting stance requires direct or partial relation")
        doc = documents.get(document_id, {}) if isinstance(document_id, str) else {}
        if record.get("evidence_status") == "active" and doc.get("correction_status") in invalid_current:
            errors.append(f"{path}: active occurrence cannot rely on {doc.get('correction_status')} document")
        if record.get("evidence_status") == "active" and stance in {"supports", "contradicts"} and doc.get("access_status") not in {"full", "partial"}:
            errors.append(f"{path}: active semantic evidence requires full or partial source access")
        if record.get("evidence_status") == "active" and available is None:
            warnings.append(f"{path}: exact availability date is unknown; temporal gate will remain unresolved")
        optional_string(record, "date_notes", path, errors, 2000)
        optional_string(record, "notes", path, errors)

    origin_identities = {}
    for record in by_type["origin"]:
        path = f"origin[{record.get('id')}]"
        need_enum(record, "origin_type", "origin_type", path, errors)
        need_enum(record, "verification_status", "verification_status", path, errors)
        need_enum(record, "interest", "interest", path, errors)
        need_string(record, "description", path, errors, 2000)
        producer = record.get("producer_entity_id")
        if producer is not None and (not isinstance(producer, str) or producer not in entities):
            errors.append(f"{path}.producer_entity_id: orphan reference {producer!r}")
        for key in ("stable_identifier", "observed_period", "version", "notes"):
            optional_string(record, key, path, errors, 2000)
        if isinstance(record.get("stable_identifier"), str) and record.get("stable_identifier").strip():
            identity = (record.get("origin_type"), record["stable_identifier"].strip().casefold(), str(record.get("version", "")).strip().casefold())
            if identity in origin_identities:
                errors.append(f"{path}: duplicate stable origin identity also used by {origin_identities[identity]}")
            else:
                origin_identities[identity] = record.get("id")

    for record in by_type["origin_assignment"]:
        path = f"origin_assignment[{record.get('id')}]"
        need_enum(record, "role", "origin_role", path, errors)
        need_enum(record, "support_mode", "support_mode", path, errors)
        support_unit = record.get("support_unit_id")
        if not isinstance(support_unit, str) or not ID_RE.fullmatch(support_unit):
            errors.append(f"{path}.support_unit_id: invalid stable ID")
        if record.get("role") != "underlying_observation" and record.get("support_mode") != "contextual":
            errors.append(f"{path}.support_mode: reporting/analysis origins must be contextual")
        need_enum(record, "status", "link_status", path, errors)
        need_string(record, "basis", path, errors, 2000)
        occurrence_id = record.get("occurrence_id")
        origin_id = record.get("origin_id")
        if not isinstance(occurrence_id, str) or occurrence_id not in occurrences:
            errors.append(f"{path}.occurrence_id: orphan reference {record.get('occurrence_id')!r}")
        if not isinstance(origin_id, str) or origin_id not in origins:
            errors.append(f"{path}.origin_id: orphan reference {record.get('origin_id')!r}")
        origin = origins.get(origin_id, {}) if isinstance(origin_id, str) else {}
        if record.get("status") == "machine_observed" and not origin.get("stable_identifier"):
            errors.append(f"{path}: machine_observed assignment requires a stable origin identifier")
        if record.get("status") == "machine_observed":
            occurrence = occurrences.get(occurrence_id, {}) if isinstance(occurrence_id, str) else {}
            document = documents.get(occurrence.get("document_id"), {})
            document_identifiers = document.get("stable_identifiers", [])
            if not isinstance(document_identifiers, list) or origin.get("stable_identifier") not in document_identifiers:
                errors.append(f"{path}: machine_observed assignment requires the same stable identifier on the inspected document")
        optional_string(record, "notes", path, errors)

    directional_graph = defaultdict(set)
    for record in by_type["lineage_edge"]:
        path = f"lineage_edge[{record.get('id')}]"
        relation = need_enum(record, "relation", "relation", path, errors)
        dimension = need_enum(record, "dimension", "dimension", path, errors)
        status = need_enum(record, "status", "link_status", path, errors)
        need_string(record, "basis", path, errors, 2000)
        flags = need_string_list(record, "distortion_flags", path, errors)
        for flag in flags:
            if flag not in DISTORTIONS:
                errors.append(f"{path}.distortion_flags: unknown flag {flag!r}")
        if relation in RELATION_DIMENSIONS and dimension not in RELATION_DIMENSIONS[relation]:
            errors.append(f"{path}: relation {relation!r} is incompatible with dimension {dimension!r}")
        child, parent = record.get("from_occurrence_id"), record.get("to_occurrence_id")
        if not isinstance(child, str) or not isinstance(parent, str) or child not in occurrences or parent not in occurrences:
            errors.append(f"{path}: orphan occurrence reference")
            continue
        if child == parent:
            errors.append(f"{path}: self-loop is not allowed")
        if occurrences[child].get("claim_id") != occurrences[parent].get("claim_id"):
            errors.append(f"{path}: edges must be claim-specific")
        if relation in TEMPORAL_DIRECTIONAL and status in CONFIRMED:
            child_date, parent_date = occurrence_dates.get(child), occurrence_dates.get(parent)
            if child_date and parent_date and child_date < parent_date:
                errors.append(f"{path}: confirmed downstream occurrence predates upstream occurrence")
        if relation in DIRECTIONAL and status in CONFIRMED:
            directional_graph[child].add(parent)
        if status == "machine_observed":
            child_doc = documents.get(occurrences.get(child, {}).get("document_id"), {})
            parent_doc = documents.get(occurrences.get(parent, {}).get("document_id"), {})
            shared_ids = set(child_doc.get("stable_identifiers", [])) & set(parent_doc.get("stable_identifiers", []))
            same_hash = child_doc.get("content_sha256") and child_doc.get("content_sha256") == parent_doc.get("content_sha256")
            if relation == "exact_copy_of" and not same_hash:
                errors.append(f"{path}: machine-observed exact copy requires matching content hashes")
            elif relation in {"version_of", "wire_syndication", "supersedes"} and not (shared_ids or child_doc.get("work_id") == parent_doc.get("work_id")):
                errors.append(f"{path}: machine-observed version/syndication relation requires shared structured identity")
            elif relation not in {"exact_copy_of", "version_of", "wire_syndication", "supersedes"}:
                errors.append(f"{path}: semantic relation cannot be machine_observed without human adjudication")
        optional_string(record, "notes", path, errors)

    if strongly_connected_components(occurrences, [(child, parent) for child, parents in directional_graph.items() for parent in parents]):
        errors.append("lineage_edge: confirmed directional derivation cycle detected")

    adjudications_by_target = defaultdict(list)
    effective_adjudications = effective_records(by_type["adjudication"])
    for record in by_type["adjudication"]:
        path = f"adjudication[{record.get('id')}]"
        target_id = record.get("target_id")
        if not isinstance(target_id, str) or target_id not in ids:
            errors.append(f"{path}.target_id: orphan reference {record.get('target_id')!r}")
        elif ids[target_id].get("record_type") not in {"origin_assignment", "lineage_edge"}:
            errors.append(f"{path}.target_id: adjudication must target an assignment or edge")
        if record in effective_adjudications and isinstance(target_id, str):
            adjudications_by_target[target_id].append(record)
        need_enum(record, "label", "adjudication_label", path, errors)
        for key in ("label", "rationale", "reviewer"):
            need_string(record, key, path, errors, 2000)
        refs = need_string_list(record, "evidence_refs", path, errors)
        if not refs:
            errors.append(f"{path}.evidence_refs: at least one evidence record is required")
        for ref in refs:
            if ref not in ids:
                errors.append(f"{path}.evidence_refs: orphan reference {ref!r}")
        if refs and not any(ids.get(ref, {}).get("record_type") in {"document_snapshot", "claim_occurrence"} for ref in refs):
            errors.append(f"{path}.evidence_refs: include at least one document_snapshot or claim_occurrence")
        created = parse_date(record.get("created_at"), f"{path}.created_at", errors)
        if created and analysis_date and created > analysis_date:
            errors.append(f"{path}.created_at: cannot follow analysis_date")
        target_record = ids.get(target_id, {}) if isinstance(target_id, str) else {}
        if record in effective_adjudications and record.get("label") == "confirmed" and target_record.get("status") != "human_adjudicated":
            errors.append(f"{path}: confirmed adjudication requires a human_adjudicated target")

    effective_targets = effective_records(by_type["origin_assignment"]) + effective_records(by_type["lineage_edge"])
    for target in effective_targets:
        if target.get("status") != "human_adjudicated":
            continue
        target_id = target.get("id")
        reviews = adjudications_by_target.get(target_id, []) if isinstance(target_id, str) else []
        if len(reviews) != 1 or reviews[0].get("label") != "confirmed":
            errors.append(f"{target.get('record_type')}[{target.get('id')}]: human_adjudicated requires exactly one confirmed human adjudication record")
    if any(target.get("status") == "human_adjudicated" for target in effective_targets):
        warnings.append("human reviewer identity is self-attested in this file, not cryptographically verified")

    effective_assignments = effective_records(by_type["origin_assignment"])
    confirmed_assignments = [record for record in effective_assignments if record.get("status") in CONFIRMED]
    assignments_by_occurrence = defaultdict(list)
    assignments_by_unit = defaultdict(list)
    for record in confirmed_assignments:
        if record.get("role") != "underlying_observation" or record.get("support_mode") == "contextual":
            continue
        assignments_by_occurrence[record.get("occurrence_id")].append(record)
        assignments_by_unit[record.get("support_unit_id")].append(record)
    for unit_id, unit_assignments in assignments_by_unit.items():
        unit_origins = {record.get("origin_id") for record in unit_assignments}
        if len(unit_origins) > 1 and {record.get("support_mode") for record in unit_assignments} != {"jointly_necessary"}:
            errors.append(f"support unit {unit_id}: multiple origins require jointly_necessary mode; corroborative origins need distinct support units")
        if {record.get("support_mode") for record in unit_assignments} == {"jointly_necessary"} and len(unit_origins) < 2:
            errors.append(f"support unit {unit_id}: jointly_necessary requires at least two distinct confirmed origins")

    for edge in effective_records(by_type["lineage_edge"]):
        if edge.get("status") not in CONFIRMED:
            continue
        child_units = {record.get("support_unit_id") for record in assignments_by_occurrence[edge.get("from_occurrence_id")]}
        parent_units = {record.get("support_unit_id") for record in assignments_by_occurrence[edge.get("to_occurrence_id")]}
        if edge.get("relation") == "reports_same_observation" and child_units and parent_units and child_units.isdisjoint(parent_units):
            errors.append(f"lineage_edge[{edge.get('id')}]: reports_same_observation requires a shared support_unit_id")
        if edge.get("relation") == "independently_observes" and child_units & parent_units:
            errors.append(f"lineage_edge[{edge.get('id')}]: independently_observes cannot share a support_unit_id")

    return errors, sorted(set(warnings)), by_type


def canonical_digest(records):
    ordered = sorted(records, key=lambda r: (str(r.get("record_type")), str(r.get("id"))))
    payload = json.dumps(ordered, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def audit_claim(case, claim, occurrences, documents, origins, assignments, edges):
    claim_occurrences = [o for o in occurrences if o.get("claim_id") == claim["id"]]
    active = [o for o in claim_occurrences if o.get("evidence_status") == "active"]
    uncertain = sorted(o["id"] for o in claim_occurrences if o.get("evidence_status") == "uncertain")
    superseded = sorted(o["id"] for o in claim_occurrences if o.get("evidence_status") == "superseded")
    withdrawn = sorted(o["id"] for o in claim_occurrences if o.get("evidence_status") == "withdrawn")
    support = [o for o in active if o.get("stance") == "supports" and o.get("support_relation") in {"direct", "partial"}]
    contradict = [o for o in active if o.get("stance") == "contradicts" and o.get("support_relation") in {"direct", "partial"}]
    inaccessible = [o for o in active if o.get("stance") == "inaccessible" or documents.get(o.get("document_id"), {}).get("access_status") == "inaccessible"]
    confirmed_by_occurrence = defaultdict(lambda: defaultdict(set))
    confirmed_units_by_occurrence = defaultdict(set)
    candidate_origins_by_occurrence = defaultdict(set)
    candidate_units_by_occurrence = defaultdict(set)
    open_unknown_occurrences = set()
    support_unit_roots = defaultdict(set)
    for assignment in assignments:
        role = assignment.get("role")
        if assignment.get("status") in CONFIRMED and not (role == "underlying_observation" and assignment.get("support_mode") == "contextual"):
            confirmed_by_occurrence[assignment.get("occurrence_id")][assignment.get("role")].add(assignment.get("origin_id"))
            if role == "underlying_observation":
                confirmed_units_by_occurrence[assignment.get("occurrence_id")].add(assignment.get("support_unit_id"))
                support_unit_roots[assignment.get("support_unit_id")].add(assignment.get("origin_id"))
        elif role == "underlying_observation" and assignment.get("status") in {"inferred_candidate", "unresolved"}:
            candidate_origins_by_occurrence[assignment.get("occurrence_id")].add(assignment.get("origin_id"))
            candidate_units_by_occurrence[assignment.get("occurrence_id")].add(assignment.get("support_unit_id"))
            if assignment.get("status") == "unresolved":
                open_unknown_occurrences.add(assignment.get("occurrence_id"))

    def roots(items, role="underlying_observation"):
        return set().union(*(confirmed_by_occurrence[o["id"]][role] for o in items)) if items else set()

    support_roots = roots(support)
    contradict_roots = roots(contradict)
    support_units = set().union(*(confirmed_units_by_occurrence[o["id"]] for o in support)) if support else set()
    contradict_units = set().union(*(confirmed_units_by_occurrence[o["id"]] for o in contradict)) if contradict else set()
    supporting_reporting_roots = roots(support, "reporting_origin")
    supporting_analysis_roots = roots(support, "analysis_origin")
    contradicting_reporting_roots = roots(contradict, "reporting_origin")
    contradicting_analysis_roots = roots(contradict, "analysis_origin")

    def has_live_alternative(occurrence):
        return bool(candidate_origins_by_occurrence[occurrence["id"]] - confirmed_by_occurrence[occurrence["id"]]["underlying_observation"])

    unresolved_support = [o["id"] for o in support if not confirmed_by_occurrence[o["id"]]["underlying_observation"] or has_live_alternative(o)]
    unresolved_contradict = [o["id"] for o in contradict if not confirmed_by_occurrence[o["id"]]["underlying_observation"] or has_live_alternative(o)]
    candidate_support_origins = set().union(*(candidate_origins_by_occurrence[o["id"]] for o in support)) if support else set()
    candidate_contradict_origins = set().union(*(candidate_origins_by_occurrence[o["id"]] for o in contradict)) if contradict else set()
    candidate_support_units = set().union(*(candidate_units_by_occurrence[o["id"]] for o in support)) if support else set()
    candidate_contradict_units = set().union(*(candidate_units_by_occurrence[o["id"]] for o in contradict)) if contradict else set()
    has_open_unknown = any(
        (not confirmed_by_occurrence[o["id"]]["underlying_observation"] and not candidate_origins_by_occurrence[o["id"]])
        or o["id"] in open_unknown_occurrences
        for o in support
    )
    origin_range_max = None if has_open_unknown else len(support_roots | candidate_support_origins)
    unit_range_max = None if has_open_unknown else len(support_units | candidate_support_units)

    root_counts = Counter()
    for occurrence in support:
        for root in confirmed_by_occurrence[occurrence["id"]]["underlying_observation"]:
            root_counts[root] += 1
    dominant = None
    if root_counts:
        dominant = sorted(root_counts.items(), key=lambda pair: (-pair[1], pair[0]))[0]
    roots_after_removal = len(support_roots - ({dominant[0]} if dominant else set()))
    units_after_removal = len({unit for unit in support_units if not dominant or dominant[0] not in support_unit_roots[unit]})
    shared_amplification = any(count > 1 for count in root_counts.values())

    relevant_edges = []
    occurrence_ids = {o["id"] for o in active}
    for edge in edges:
        if edge.get("from_occurrence_id") in occurrence_ids or edge.get("to_occurrence_id") in occurrence_ids:
            relevant_edges.append(edge)
    method_relations = sorted(e["id"] for e in relevant_edges if e.get("dimension") == "method" and e.get("status") in CONFIRMED)
    control_relations = sorted(e["id"] for e in relevant_edges if e.get("dimension") == "ownership" and e.get("status") in CONFIRMED)
    citation_pairs = [
        (edge.get("from_occurrence_id"), edge.get("to_occurrence_id"))
        for edge in relevant_edges
        if edge.get("relation") in {"cites", "citation_only"} and edge.get("status") in CONFIRMED
    ]
    citation_cycles = strongly_connected_components(occurrence_ids, citation_pairs)
    distortions = sorted({flag for e in relevant_edges if e.get("status") in CONFIRMED for flag in e.get("distortion_flags", [])})
    candidate_distortions = sorted({flag for e in relevant_edges if e.get("status") not in CONFIRMED and e.get("status") != "rejected" for flag in e.get("distortion_flags", [])})
    support_methods = sorted({o.get("method_family") for o in support if o.get("method_family") and o.get("method_family") != "unknown"})
    contradict_methods = sorted({o.get("method_family") for o in contradict if o.get("method_family") and o.get("method_family") != "unknown"})
    verified_roots = sorted(root for root in support_roots if origins.get(root, {}).get("verification_status") == "verified")
    root_interests = [origins.get(root, {}).get("interest", "unknown") for root in support_roots]
    if not root_interests:
        supporting_interest_profile = "unknown"
    elif all(x == "interested" for x in root_interests):
        supporting_interest_profile = "interested_only"
    elif all(x == "disinterested" for x in root_interests):
        supporting_interest_profile = "disinterested_only"
    else:
        supporting_interest_profile = "mixed_or_unknown"

    correction_risks = sorted({
        o["document_id"] for o in support + contradict
        if documents.get(o.get("document_id"), {}).get("correction_status") in {"not_checked", "unknown", "corrected"}
    })

    lineage_blockers = []
    if unresolved_support:
        lineage_blockers.append("unresolved supporting origins")
    if unresolved_contradict:
        lineage_blockers.append("unresolved contradicting origins")
    if uncertain:
        lineage_blockers.append("decision-material occurrences have uncertain status")
    if correction_risks:
        lineage_blockers.append("correction status requires review")
    if inaccessible and claim.get("materiality") != "context":
        lineage_blockers.append("decision-material sources are inaccessible")
    if claim.get("counterevidence_search") != "completed" and claim.get("materiality") != "context":
        lineage_blockers.append("counterevidence search is incomplete")
    if any(o.get("available_at") is None for o in support + contradict) and claim.get("materiality") != "context":
        lineage_blockers.append("exact availability date is unknown")
    if citation_cycles:
        lineage_blockers.append("circular citation component requires review")

    if lineage_blockers:
        label = "LINEAGE_UNRESOLVED"
    elif contradict_units:
        label = "CONTESTED"
    elif not support:
        label = "NO_DIRECT_SUPPORT"
    elif len(support_units) == 1 and len(support) == 1:
        label = "SINGLE_ORIGIN_SUPPORT"
    elif len(support_units) == 1:
        label = "ECHO_DOMINATED"
    elif len(support_units) >= 2 and shared_amplification:
        label = "PARTIALLY_DEPENDENT"
    elif len(support_units) >= 2:
        label = "INDEPENDENTLY_CORROBORATED"
    else:
        label = "LINEAGE_UNRESOLVED"

    consequence = {
        "NO_DIRECT_SUPPORT": "Do not represent the examined corpus as direct support for this claim.",
        "ECHO_DOMINATED": "Count the visible repetitions as one confirmed evidentiary origin, not as independent confirmations.",
        "SINGLE_ORIGIN_SUPPORT": "Treat this as one evidentiary chain; no independent corroboration is established.",
        "PARTIALLY_DEPENDENT": "Count confirmed origins rather than documents and preserve the shared-origin amplification warning.",
        "INDEPENDENTLY_CORROBORATED": "The examined corpus contains multiple confirmed origins; separately assess validity, scope, and relevance before relying on the claim.",
        "CONTESTED": "Do not present an unqualified consensus; inspect the independently rooted contradiction and its scope.",
        "LINEAGE_UNRESOLVED": "Do not claim independent corroboration until the listed lineage, access, cutoff, or correction gaps are resolved.",
    }[label]

    return {
        "apparent_consensus": label,
        "claim_id": claim["id"],
        "claim_text": claim["text"],
        "candidate_distortion_flags": candidate_distortions,
        "candidate_contradicting_origin_ids": sorted(candidate_contradict_origins),
        "candidate_contradicting_support_unit_ids": sorted(candidate_contradict_units),
        "candidate_supporting_origin_ids": sorted(candidate_support_origins),
        "candidate_supporting_support_unit_ids": sorted(candidate_support_units),
        "candidate_support_unit_overlap": sorted(candidate_support_units & candidate_contradict_units),
        "canonical_asset_count": len({
            (
                documents[o["document_id"]].get("work_id"),
                documents[o["document_id"]].get("version_id"),
                documents[o["document_id"]].get("content_sha256") or o["document_id"],
            )
            for o in active
        }),
        "circular_citation_components": citation_cycles,
        "confirmed_contradicting_analysis_roots": sorted(contradicting_analysis_roots),
        "confirmed_contradicting_roots": sorted(contradict_roots),
        "confirmed_contradicting_reporting_roots": sorted(contradicting_reporting_roots),
        "confirmed_contradicting_support_unit_count": len(contradict_units),
        "confirmed_supporting_origin_count": len(support_roots),
        "confirmed_support_unit_count": len(support_units),
        "confirmed_support_unit_ids": sorted(support_units),
        "confirmed_supporting_analysis_roots": sorted(supporting_analysis_roots),
        "confirmed_supporting_reporting_roots": sorted(supporting_reporting_roots),
        "contradicting_method_families": contradict_methods,
        "contradicting_support_unit_ids": sorted(contradict_units),
        "control_relation_ids": control_relations,
        "correction_risk_document_ids": correction_risks,
        "counterevidence_search": claim["counterevidence_search"],
        "decision_consequence": consequence,
        "distortion_flags": distortions,
        "document_count": len({o["document_id"] for o in active}),
        "dominant_origin": ({"origin_id": dominant[0], "supporting_occurrences": dominant[1]} if dominant else None),
        "inaccessible_occurrences": sorted(o["id"] for o in inaccessible),
        "origin_overlap_between_support_and_contradiction": sorted(support_roots & contradict_roots),
        "support_unit_overlap_between_support_and_contradiction": sorted(support_units & contradict_units),
        "supporting_origin_interest_profile": supporting_interest_profile,
        "lineage_blockers": sorted(set(lineage_blockers)),
        "method_families_all": sorted(set(support_methods) | set(contradict_methods)),
        "method_relation_ids": method_relations,
        "origin_removal": {
            "confirmed_roots_after_removing_dominant": roots_after_removal,
            "confirmed_support_units_after_removing_dominant": units_after_removal,
            "consensus_collapses": bool(dominant and units_after_removal < 2),
            "independent_corroboration_survives": bool(dominant and units_after_removal >= 2),
        },
        "plausible_supporting_origin_range": {"minimum": len(support_roots), "maximum": origin_range_max},
        "plausible_support_unit_range": {"minimum": len(support_units), "maximum": unit_range_max},
        "supporting_occurrence_count": len(support),
        "supporting_method_families": support_methods,
        "superseded_occurrence_ids": superseded,
        "truth_assessment": "NOT_ASSESSED",
        "uncertain_occurrence_ids": uncertain,
        "unresolved_contradicting_occurrences": sorted(unresolved_contradict),
        "unresolved_supporting_occurrences": sorted(unresolved_support),
        "verified_origin_count": len(verified_roots),
        "verified_origin_ids": verified_roots,
        "withdrawn_occurrence_ids": withdrawn,
        "what_this_does_not_establish": ["factual truth", "intent", "coordination", "plagiarism", "corpus completeness", "reviewer identity"],
    }


def build_audit(records, claim_id=None):
    errors, warnings, by_type = validate_records(records)
    if errors:
        raise ValueError("\n".join(errors))
    case = by_type["case"][0]
    claims = sorted(by_type["claim"], key=lambda r: r["id"])
    if claim_id:
        claims = [claim for claim in claims if claim["id"] == claim_id]
        if not claims:
            raise ValueError(f"unknown claim: {claim_id}")
    documents = {r["id"]: r for r in by_type["document_snapshot"]}
    origins = {r["id"]: r for r in by_type["origin"]}
    assignments = effective_records(by_type["origin_assignment"])
    edges = effective_records(by_type["lineage_edge"])
    human_review_assurance = (
        "SELF_ATTESTED_NOT_CRYPTOGRAPHICALLY_VERIFIED"
        if any(record.get("status") == "human_adjudicated" for record in assignments + edges)
        else "NOT_APPLICABLE"
    )
    results = [audit_claim(case, claim, by_type["claim_occurrence"], documents, origins, assignments, edges) for claim in claims]
    return {
        "analysis_date": case["analysis_date"],
        "as_of_date": case["as_of_date"],
        "case_id": case["id"],
        "case_purpose": case["case_purpose"],
        "corpus_contract": "CLOSED-CORPUS AUDIT" if case["corpus_contract"] == "closed_corpus" else "OPEN-WEB SEARCH",
        "inclusion_rule": case["inclusion_rule"],
        "human_review_assurance": human_review_assurance,
        "limitations": case["limitations"],
        "mode": case["mode"],
        "record_digest": canonical_digest(records),
        "results": results,
        "schema_version": "1.0.0",
        "stopping_rule": case["stopping_rule"],
        "truth_assessment": "NOT_ASSESSED",
        "warnings": warnings,
    }


def build_handoff(records, claim_id):
    audit = build_audit(records, claim_id)
    _, _, by_type = validate_records(records)
    case = by_type["case"][0]
    occurrences = {r["id"]: r for r in by_type["claim_occurrence"]}
    documents = {r["id"]: r for r in by_type["document_snapshot"]}
    confirmed_roots, confirmed_units, roots_by_unit = defaultdict(set), defaultdict(set), defaultdict(set)
    effective_assignments = effective_records(by_type["origin_assignment"])
    for assignment in effective_assignments:
        if assignment["role"] == "underlying_observation" and assignment["support_mode"] != "contextual" and assignment["status"] in CONFIRMED:
            confirmed_roots[assignment["occurrence_id"]].add(assignment["origin_id"])
            confirmed_units[assignment["occurrence_id"]].add(assignment["support_unit_id"])
            roots_by_unit[assignment["support_unit_id"]].add(assignment["origin_id"])
    records_out, omitted = [], []
    audit_result = audit["results"][0]
    for occurrence in sorted(occurrences.values(), key=lambda r: r["id"]):
        if occurrence["claim_id"] != claim_id or occurrence["evidence_status"] != "active":
            continue
        document = documents[occurrence["document_id"]]
        if case["case_purpose"] == "synthetic_fixture":
            omitted.append({"occurrence_id": occurrence["id"], "reason": "synthetic fixtures cannot produce downstream handoff records"})
            continue
        if audit_result["apparent_consensus"] == "LINEAGE_UNRESOLVED":
            omitted.append({"occurrence_id": occurrence["id"], "reason": "claim-level lineage gate is unresolved"})
            continue
        if occurrence["stance"] not in {"supports", "contradicts"} or occurrence["support_relation"] not in {"direct", "partial"}:
            omitted.append({"occurrence_id": occurrence["id"], "reason": "not active semantic support or contradiction"})
            continue
        if document["access_status"] not in {"full", "partial"}:
            omitted.append({"occurrence_id": occurrence["id"], "reason": "source content was not inspectable"})
            continue
        if document["correction_status"] not in {"checked_none_found", "not_applicable"}:
            omitted.append({"occurrence_id": occurrence["id"], "reason": "correction status is not clear"})
            continue
        if document["cutoff_availability"] == "unknown":
            omitted.append({"occurrence_id": occurrence["id"], "reason": "cutoff availability is unresolved"})
            continue
        roots = sorted(confirmed_roots[occurrence["id"]])
        units = sorted(confirmed_units[occurrence["id"]])
        live_alternatives = [
            assignment for assignment in effective_assignments
            if assignment["occurrence_id"] == occurrence["id"]
            and assignment["role"] == "underlying_observation"
            and assignment["status"] in {"inferred_candidate", "unresolved"}
        ]
        if live_alternatives:
            omitted.append({"occurrence_id": occurrence["id"], "reason": "unresolved alternative origin assignment"})
            continue
        if len(roots) != 1 or len(units) != 1 or len(roots_by_unit[units[0]]) != 1:
            omitted.append({"occurrence_id": occurrence["id"], "reason": "requires exactly one confirmed origin and support unit"})
            continue
        records_out.append({
            "claim_id": claim_id,
            "document_id": occurrence["document_id"],
            "lineage_case_id": case["id"],
            "occurrence_id": occurrence["id"],
            "origin_group_id": units[0],
            "origin_id": roots[0],
            "record_type": "horizon_independence_handoff",
            "stance": occurrence["stance"],
        })
    return {
        "apparent_consensus": audit_result["apparent_consensus"],
        "case_id": case["id"],
        "case_purpose": case["case_purpose"],
        "claim_id": claim_id,
        "independence_gate_eligible": case["case_purpose"] == "operational" and audit_result["apparent_consensus"] in {"PARTIALLY_DEPENDENT", "INDEPENDENTLY_CORROBORATED"},
        "human_review_assurance": audit["human_review_assurance"],
        "handoff_records": records_out,
        "omitted": omitted,
        "review_required": True,
        "truth_assessment": "NOT_ASSESSED",
    }


def print_text(audit):
    print(audit["corpus_contract"])
    print(f"CASE {audit['case_id']} · cutoff {audit['as_of_date']}")
    for result in audit["results"]:
        print(f"\nCLAIM {result['claim_id']}\n{result['claim_text']}")
        print(f"APPARENT CONSENSUS {result['apparent_consensus']}")
        low = result["plausible_support_unit_range"]["minimum"]
        high = result["plausible_support_unit_range"]["maximum"]
        high_text = "unknown" if high is None else str(high)
        documents_word = "document" if result["document_count"] == 1 else "documents"
        occurrences_word = "occurrence" if result["supporting_occurrence_count"] == 1 else "occurrences"
        origins_word = "origin" if result["confirmed_supporting_origin_count"] == 1 else "origins"
        units_word = "unit" if result["confirmed_support_unit_count"] == 1 else "units"
        contradictions = result["confirmed_contradicting_support_unit_count"]
        contradiction_word = "unit" if contradictions == 1 else "units"
        overlap = len(result["support_unit_overlap_between_support_and_contradiction"])
        unresolved = len(result["unresolved_supporting_occurrences"])
        unresolved_word = "occurrence" if unresolved == 1 else "occurrences"
        unresolved_contradictions = len(result["unresolved_contradicting_occurrences"])
        unresolved_contradiction_word = "occurrence" if unresolved_contradictions == 1 else "occurrences"
        print(f"{result['document_count']} {documents_word} · {result['supporting_occurrence_count']} supporting {occurrences_word}")
        print(f"{result['confirmed_supporting_origin_count']} confirmed supporting {origins_word} · {result['confirmed_support_unit_count']} support {units_word} · plausible unit range {low}-{high_text}")
        print(f"{contradictions} contradicting support {contradiction_word} ({overlap} overlaps supporting evidence) · {unresolved} unresolved support {unresolved_word}")
        print(f"{unresolved_contradictions} unresolved contradicting {unresolved_contradiction_word} · {len(result['candidate_supporting_origin_ids'])} candidate supporting origins")
        if result["candidate_distortion_flags"]:
            print(f"CANDIDATE MUTATIONS {', '.join(result['candidate_distortion_flags'])}")
        print(f"DECISION CONSEQUENCE {result['decision_consequence']}")
        print("THIS DOES NOT ESTABLISH truth, intent, coordination, plagiarism, corpus completeness, or reviewer identity.")
    if audit["warnings"]:
        print("\nWARNINGS")
        for warning in audit["warnings"]:
            print(f"- {warning}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_validate = sub.add_parser("validate", help="validate JSONL records")
    p_validate.add_argument("records")
    p_audit = sub.add_parser("audit", help="audit claim lineage without network access")
    p_audit.add_argument("records")
    p_audit.add_argument("--claim")
    p_audit.add_argument("--format", choices=("text", "json"), default="text")
    p_handoff = sub.add_parser("handoff", help="create conservative Horizon Scout handoff")
    p_handoff.add_argument("records")
    p_handoff.add_argument("--claim", required=True)
    p_fingerprint = sub.add_parser("fingerprint", help="print SHA-256 of a local file")
    p_fingerprint.add_argument("file")
    args = parser.parse_args(argv)

    try:
        if args.command == "fingerprint":
            path = pathlib.Path(args.file)
            if not path.is_file() or path.stat().st_size > MAX_BYTES:
                raise ValueError("file missing or exceeds local safety limit")
            print("sha256:" + hashlib.sha256(path.read_bytes()).hexdigest())
            return 0
        records = load_jsonl(args.records)
        if args.command == "validate":
            errors, warnings, _ = validate_records(records)
            if errors:
                raise ValueError("\n".join(errors))
            for warning in warnings:
                print(f"WARNING {warning}")
            print(f"OK records={len(records)} digest={canonical_digest(records)}")
            return 0
        if args.command == "audit":
            audit = build_audit(records, args.claim)
            if args.format == "json":
                print(json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
            else:
                print_text(audit)
            return 0
        handoff = build_handoff(records, args.claim)
        print(json.dumps(handoff, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

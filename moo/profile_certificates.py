"""Compare declared profile certificates without inferring independent evidence.

Directed arithmetic requests are compared exactly, including explicit premise
roles and recursively named dependencies. Retained edge occurrences are a
separate comparison, bound to the one source snapshot of the supplied index.
No new expression quotient or graph-wide proof search is performed here.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Callable


RequestKey = tuple[str, str, str, str]
VERSION = "moo_profile_certificate_comparison.v1"


def _request_key(request: dict[str, Any]) -> RequestKey:
    op = str(request["op"])
    if op not in {"+", "-", "*", "/"}:
        raise ValueError(f"Unsupported certificate operation: {op}")
    return (
        str(Fraction(request["left"])), op,
        str(Fraction(request["right"])), str(Fraction(request["result"])),
    )


def _request_payload(key: RequestKey) -> dict[str, str]:
    return dict(zip(("left", "op", "right", "result"), key))


def _certificate_summary(certificate: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in certificate.items() if key != "support"},
        "support": {key: value for key, value in certificate["support"].items()
                    if key != "requests"},
    }


def _expand(
    root_ref: str,
    load: Callable[[str], dict[str, Any]],
    source_sha256: str,
) -> tuple[dict[str, Any], dict[RequestKey, dict[str, Any]], dict[int, dict[str, Any]]]:
    certificates: dict[str, dict[str, Any]] = {}
    active: list[str] = []
    dependency_links: list[dict[str, Any]] = []

    def visit(reference: str) -> None:
        if reference in active:
            raise ValueError("Certificate dependency cycle: " + " -> ".join([*active, reference]))
        if reference in certificates:
            return
        certificate = load(reference)
        certificates[reference] = certificate
        active.append(reference)
        for dependency in certificate["support"].get("dependencies", []):
            child = dependency.get("ref")
            if not isinstance(child, str) or not child:
                raise ValueError(f"Certificate {reference} has a dependency without a certificate ref")
            dependency_links.append({"from": reference, "to": child,
                                     "declared_support": dict(dependency)})
            visit(child)
        active.pop()

    visit(root_ref)
    requests: dict[RequestKey, dict[str, Any]] = {}
    edges: dict[int, dict[str, Any]] = {}
    role_count = 0
    for reference, certificate in certificates.items():
        for position, request in enumerate(certificate["support"].get("requests", [])):
            key = _request_key(request)
            witnessed = bool(request.get("witnessed", False))
            role = {"certificate_ref": reference, "request_role": request["role"],
                    "request_index": position, "witnessed": witnessed,
                    "source_edge_count": request.get("source_edge_count"),
                    "source_edge_refs_truncated": request.get("source_edge_refs_truncated"),
                    "materialized_edge_reference_count": len(request.get("edge_refs", []))}
            role_count += 1
            group = requests.setdefault(key, {**_request_payload(key), "role_links": [],
                                              "witnessed": False, "retained_edge_refs": []})
            group["role_links"].append(role)
            group["witnessed"] = group["witnessed"] or witnessed
            # Partial certificates can contain real witnessed requests. Conversely,
            # a physically present but out-of-aperture request is not observed here.
            if not witnessed:
                continue
            known_ids = {item["edge_id"] for item in group["retained_edge_refs"]}
            for edge in request.get("edge_refs", []):
                edge_id = int(edge["edge_id"])
                retained = {"source_sha256": source_sha256, "edge_id": edge_id,
                            "stage": edge.get("stage")}
                if edge_id not in known_ids:
                    group["retained_edge_refs"].append(retained)
                    known_ids.add(edge_id)
                occurrence = edges.setdefault(edge_id, {
                    **retained, "request": _request_payload(key), "role_links": [],
                })
                if occurrence["request"] != _request_payload(key) or occurrence["stage"] != edge.get("stage"):
                    raise ValueError(f"Conflicting request or stage for retained edge {edge_id}")
                if role not in occurrence["role_links"]:
                    occurrence["role_links"].append(role)

    for request in requests.values():
        request["retained_edge_refs"].sort(key=lambda item: item["edge_id"])
        request["occurrence_references_exhaustive"] = all(
            role["source_edge_refs_truncated"] is False
            for role in request["role_links"] if role["witnessed"]
        )
    incomplete_reference_requests = [
        _request_payload(key) for key in sorted(requests)
        if not requests[key]["occurrence_references_exhaustive"]
    ]
    payload = {
        "ref": root_ref,
        "certificate": _certificate_summary(certificates[root_ref]),
        "dependency_closure": [_certificate_summary(certificate) for certificate in certificates.values()],
        "dependency_links": dependency_links,
        "directed_requests": [requests[key] for key in sorted(requests)],
        "retained_edge_refs": [edges[key] for key in sorted(edges)],
        "occurrence_reference_coverage": {
            "exhaustive_for_witnessed_requests": not incomplete_reference_requests,
            "requests_without_exhaustive_references": incomplete_reference_requests,
            "source_counts_scope": "Reported source_edge_count spans the saved source; it is not a selected-checkpoint total.",
        },
        "counts": {
            "certificates_including_root": len(certificates),
            "request_roles": role_count,
            "unique_directed_requests": len(requests),
            "witnessed_directed_requests": sum(bool(request["witnessed"]) for request in requests.values()),
            "materialized_retained_edge_occurrences": len(edges),
        },
    }
    return payload, requests, edges


def compare_certificates(index_path: Path, left_ref: str, right_ref: str) -> dict[str, Any]:
    """Compare two certificate references within one saved association index.

The dependency closure includes each selected root. Repeated request roles and
dependency links remain visible, while arithmetic requests and observed edge
occurrences are deduplicated separately. No source corpus is opened or changed.
    """
    # Imported locally so the profile CLI can delegate here without a cycle.
    from moo.node_profiles import index_manifest, load_certificate

    index_path = Path(index_path)
    manifest = index_manifest(index_path)
    source = manifest["source"]
    source_sha256 = source.get("sha256")
    if not isinstance(source_sha256, str) or not source_sha256:
        raise ValueError("Certificate comparison requires a source snapshot SHA-256")
    cache: dict[str, dict[str, Any]] = {}

    def load(reference: str) -> dict[str, Any]:
        if reference not in cache:
            cache[reference] = load_certificate(index_path, reference)
        return cache[reference]

    left, left_requests, left_edges = _expand(left_ref, load, source_sha256)
    right, right_requests, right_edges = _expand(right_ref, load, source_sha256)
    shared_keys = set(left_requests) & set(right_requests)
    shared_edge_ids = set(left_edges) & set(right_edges)
    shared_requests = []
    for key in sorted(shared_keys):
        a, b = left_requests[key], right_requests[key]
        common_edges = ({ref["edge_id"] for ref in a["retained_edge_refs"]}
                        & {ref["edge_id"] for ref in b["retained_edge_refs"]})
        shared_requests.append({
            **_request_payload(key),
            "left_role_links": a["role_links"], "right_role_links": b["role_links"],
            "left_witnessed": a["witnessed"], "right_witnessed": b["witnessed"],
            "shared_retained_edge_refs": [
                {field: left_edges[edge_id][field] for field in ("source_sha256", "edge_id", "stage")}
                for edge_id in sorted(common_edges)
            ],
        })
    shared_edges = []
    for edge_id in sorted(shared_edge_ids):
        a, b = left_edges[edge_id], right_edges[edge_id]
        if a["request"] != b["request"] or a["stage"] != b["stage"]:
            raise ValueError(f"Conflicting request or stage for shared retained edge {edge_id}")
        shared_edges.append({
            **{field: a[field] for field in ("source_sha256", "edge_id", "stage", "request")},
            "left_role_links": a["role_links"], "right_role_links": b["role_links"],
        })

    left_parameters = left["certificate"].get("parameters", {})
    right_parameters = right["certificate"].get("parameters", {})
    left_expression = left_parameters.get("ac_expression")
    right_expression = right_parameters.get("ac_expression")
    shared_tags = sorted(set(left_parameters.get("dependency_tags", []))
                         & set(right_parameters.get("dependency_tags", [])))
    occurrence_references_exhaustive = (
        left["occurrence_reference_coverage"]["exhaustive_for_witnessed_requests"]
        and right["occurrence_reference_coverage"]["exhaustive_for_witnessed_requests"]
    )
    return {
        "schema_version": VERSION,
        "source": source, "scope": manifest.get("scope", {}),
        "left": left, "right": right,
        "shared_directed_requests": shared_requests,
        "left_only_directed_requests": [left_requests[key] for key in sorted(set(left_requests) - shared_keys)],
        "right_only_directed_requests": [right_requests[key] for key in sorted(set(right_requests) - shared_keys)],
        "shared_retained_edge_refs": shared_edges,
        "same_directed_request_set": set(left_requests) == set(right_requests),
        "same_materialized_retained_edge_set": set(left_edges) == set(right_edges),
        "same_retained_edge_set": (
            set(left_edges) == set(right_edges) if occurrence_references_exhaustive else None),
        "occurrence_reference_coverage": {
            "left": left["occurrence_reference_coverage"],
            "right": right["occurrence_reference_coverage"],
            "shared_occurrence_references_exhaustive": occurrence_references_exhaustive,
            "counts_scope": "Occurrence counts below count materialized retained references only, not unsampled source occurrences.",
        },
        "counts": {
            "shared_directed_requests": len(shared_keys),
            "shared_materialized_retained_edge_occurrences": len(shared_edge_ids),
            "left_only_directed_requests": len(set(left_requests) - shared_keys),
            "right_only_directed_requests": len(set(right_requests) - shared_keys),
        },
        "declared_ac_expression_equal": (
            left_expression == right_expression
            if left_expression is not None and right_expression is not None else None),
        "shared_declared_dependency_tags": shared_tags,
        "declared_expression_scope": {
            "left": left_parameters.get("expression_scope"),
            "right": right_parameters.get("expression_scope"),
            "metadata_from": "Selected certificate roots only; all requests and premises remain in the overlap comparison.",
        },
        "interpretation": {
            "requests": "Exact directed arithmetic requests, expanded through named certificate dependencies; repeated roles remain linked.",
            "occurrences": "Observed edge IDs are bound to this source snapshot and selected aperture; partial certificates may share recorded requests. Reference coverage records truncation, and materialized overlap need not exhaust all occurrences.",
            "independence": "No independence claim. Empty overlap means only no shared items within these declared certificate boundaries.",
            "quotients": "No new AC quotient is computed. Optional AC equality only compares metadata supplied by existing declared route schemas; it does not merge their certificates or completion stages.",
            "timing": "Each certificate retains its own support and named completion stage; shared requests do not establish a separate timing law.",
        },
    }

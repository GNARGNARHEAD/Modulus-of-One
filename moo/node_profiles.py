"""A bounded, rebuildable association index over an unchanged MoO corpus.

Mathematical membership, a literal witness bundle, and a linked spiral lineage
are separate facts.  The index records one named source snapshot and never
changes graph nodes, operand eligibility, or confirmation rules.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path
from moo.paths import PROJECT_ROOT
import sqlite3
from typing import Any, Sequence

from moo.association_families import generate_associations
from moo.graph_evidence import GraphEvidence
from moo.research_utils import connect_readonly, file_sha256, require_strict_alignment

VERSION = "moo_node_profiles.v3"
READABLE_VERSIONS = {"moo_node_profiles.v1", "moo_node_profiles.v2", VERSION}
FAMILIES = ("square", "shell", "spiral")
# Search names for existing participant roles; these add no new associations.
ROLE_FILTERS = {
    "square": {"root": "root", "result": "square"},
    "shell": {"x": "x", "y": "y", "radius": "r", "x_square": "x_square",
              "y_square": "y_square", "radius_square": "r_square"},
    "spiral": {"x": "x", "y": "y", "radius": "r", "previous_x": "previous_x",
               "previous_y": "previous_y", "previous_radius": "previous_r"},
}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _fits_sqlite(value: str) -> bool:
    q = Fraction(value)
    return -(2**63) <= q.numerator < 2**63 and q.denominator < 2**63


def _require_checkpointed_source(db_path: Path) -> None:
    # A main-file digest cannot identify committed rows still held in a WAL.
    # Require a frozen artifact instead of checkpointing or mutating the source.
    wal = Path(str(Path(db_path).resolve()) + "-wal")
    try:
        size = wal.stat().st_size
    except FileNotFoundError:
        return
    if size:
        raise ValueError("Source has an uncheckpointed WAL; use a closed, checkpointed corpus artifact")


def _checkpoint_node(payload: dict[str, Any], stage: int) -> dict[str, Any]:
    """Keep whole-source facts separate from observations at the selected stage.

    Applied on read as well as build so existing v1/v2 files need no migration.
    Stored confirmed_stage is a threshold, including future positive integers;
    it is not by itself evidence that confirmation has occurred.
    """
    raw = dict(payload.get("saved_source_node", payload))
    raw["present"] = bool(raw.get("in_saved_corpus", raw.get("present", False)))
    for key in ("in_saved_corpus", "status_at_checkpoint", "checkpoint"):
        raw.pop(key, None)
    value = Fraction(raw["label"])
    threshold = value.numerator if value.denominator == 1 and value >= 1 else None
    visible = bool(raw["present"] and raw.get("first_stage") is not None
                   and int(raw["first_stage"]) <= stage)
    status = "not_observed"
    if visible:
        status = (
            "certainty" if value == 1 else
            "confirmed" if threshold is not None and threshold <= stage else
            "speculative"
        )
    return {
        "label": str(value), "p": value.numerator, "q": value.denominator,
        "key": [value.numerator, value.denominator],
        "checkpoint": stage, "present": visible, "in_saved_corpus": raw["present"],
        "status": status, "status_at_checkpoint": status,
        "node_id": raw.get("node_id") if visible else None,
        "kind": raw.get("kind") if visible else None,
        "first_stage": raw.get("first_stage") if visible else None,
        "first_edge_id": raw.get("first_edge_id") if visible else None,
        "confirmed_stage": threshold if visible and threshold is not None and threshold <= stage else None,
        "confirmation_threshold": threshold,
        "confirmation_threshold_scope": "Positive-spine schedule; not an observed confirmation until the checkpoint reaches it.",
        "saved_source_node": raw,
        **({"reason": raw["reason"]} if "reason" in raw else {}),
    }


def _node_snapshot(evidence: GraphEvidence, value: str) -> dict[str, Any]:
    value = str(Fraction(value))
    raw = (evidence.node_payload(value) if _fits_sqlite(value)
           else {"label": value, "present": False, "reason": "outside_sqlite_integer_range"})
    return _checkpoint_node(raw, evidence.corpus_stage)


def _audit_request(evidence: GraphEvidence, request: dict[str, str]) -> dict[str, Any]:
    left, right = Fraction(request["left"]), Fraction(request["right"])
    op = request["op"]
    result = {"+": lambda: left + right, "-": lambda: left - right,
              "*": lambda: left * right, "/": lambda: left / right}[op]()
    if result != Fraction(request["result"]):
        raise ValueError(f"Incorrect arithmetic request: {request}")
    if not all(_fits_sqlite(request[key]) for key in ("left", "right", "result")):
        return {**request, "witnessed": False, "first_stage": None,
                "edge_refs": [], "blocker": "outside_sqlite_integer_range"}
    raw = evidence.edge_witness(left=request["left"], op=op,
                                right=request["right"], result=request["result"])
    # GraphEvidence's stored-edge lookup spans the entire saved corpus.  Its
    # aperture describes eligibility; apply the requested checkpoint separately.
    stage = evidence.corpus_stage
    refs = [r for r in raw["edge_refs"] if stage is not None and r["stage"] <= stage]
    witnessed = bool(raw["eligible"] and refs)
    blocker = None
    if not witnessed:
        blocker = raw["stage_aperture"].get("blocker")
        if blocker is None:
            blocker = "witness_after_checkpoint" if raw["present"] else raw["blocker"]
    return {
        **request, "witnessed": witnessed,
        "first_stage": raw["first_edge_stage"] if witnessed else None,
        "candidate_stage": raw["candidate_stage"], "blocker": blocker,
        "edge_refs": refs if witnessed else [],
        "source_edge_count": raw["edge_count"],
        "source_edge_refs_truncated": raw["edge_refs_truncated"],
        "eligible_by_stage": raw["eligible_by_stage"],
        "eligible_by_retention": raw["eligible_by_retention"],
    }


def _certificate_support(spec: dict[str, Any], evidence: GraphEvidence,
                         resolved: dict[str, dict[str, Any]]) -> dict[str, Any]:
    requests = [_audit_request(evidence, request) for request in spec["requests"]]
    dependencies = []
    for reference in spec.get("dependencies", []):
        dep = resolved[reference]["support"]
        dependencies.append({"ref": reference, "status": dep["status"],
                             "first_supported_stage": dep["first_supported_stage"]})
    local_complete = all(request["witnessed"] for request in requests)
    complete = local_complete and all(dep["status"] == "witnessed" for dep in dependencies)
    any_support = (any(request["witnessed"] for request in requests)
                   or any(dep["status"] != "unwitnessed" for dep in dependencies))
    stages = [r["first_stage"] for r in requests if r["witnessed"]]
    stages += [d["first_supported_stage"] for d in dependencies if d["status"] == "witnessed"]
    return {
        "status": "witnessed" if complete else "partial" if any_support else "unwitnessed",
        "criterion": spec["criterion"],
        "clock": "positive_spine_stage",
        "first_supported_stage": max(stages) if complete and stages else None,
        "local_requests_complete": local_complete if requests else None,
        "local_first_supported_stage": (
            max(r["first_stage"] for r in requests) if requests and local_complete else None),
        "requests": requests, "dependencies": dependencies,
        "blockers": sorted({str(r["blocker"]) for r in requests if r["blocker"]}
                           | {f"dependency_not_witnessed:{d['ref']}" for d in dependencies
                              if d["status"] != "witnessed"}),
    }


def _association_support(certificates: list[dict[str, Any]]) -> dict[str, Any]:
    witnessed = [c for c in certificates if c["support"]["status"] == "witnessed"]
    partial = any(c["support"]["status"] == "partial" for c in certificates)
    return {
        "mathematical_membership": "exact",
        "criterion": "at_least_one_complete_named_certificate",
        "status": "witnessed" if witnessed else "partial" if partial else "unwitnessed",
        "first_supported_stage": min(c["support"]["first_supported_stage"] for c in witnessed) if witnessed else None,
        "clock": "positive_spine_stage",
        "certificate_count": len(certificates),
        "witnessed_certificates": [c["ref"] for c in witnessed],
        "stage_scope": "Earliest among the selected named certificates, not all possible proofs.",
    }


def _resolve_certificates(specs: list[dict[str, Any]], evidence: GraphEvidence) -> dict[str, dict[str, Any]]:
    pending, resolved, visiting = {}, {}, set()
    association_ids = set()
    for spec in specs:
        if spec["id"] in association_ids or "#" in spec["id"]:
            raise ValueError(f"Invalid or repeated association ID: {spec['id']}")
        association_ids.add(spec["id"])
        if not spec["certificates"]:
            raise ValueError(f"No certificates specified for {spec['id']}")
        for certificate in spec["certificates"]:
            reference = f"{spec['id']}#{certificate['id']}"
            if reference in pending or "#" in certificate["id"]:
                raise ValueError(f"Invalid or repeated certificate ID: {reference}")
            roles = [request["role"] for request in certificate["requests"]]
            if len(roles) != len(set(roles)):
                raise ValueError(f"Repeated request role in {reference}")
            if not roles and not certificate.get("dependencies"):
                raise ValueError(f"Empty certificate cannot establish support: {reference}")
            pending[reference] = (spec["id"], certificate)

    def resolve(reference: str) -> None:
        if reference in resolved:
            return
        if reference in visiting:
            raise ValueError(f"Cyclic certificate dependency: {reference}")
        if reference not in pending:
            raise ValueError(f"Unknown certificate dependency: {reference}")
        visiting.add(reference)
        association_id, certificate = pending[reference]
        for dependency in certificate.get("dependencies", []):
            resolve(dependency)
        support = _certificate_support(certificate, evidence, resolved)
        resolved[reference] = {
            **{key: value for key, value in certificate.items() if key not in ("requests", "dependencies")},
            "association_id": association_id, "ref": reference, "support": support,
        }
        visiting.remove(reference)

    for reference in pending:
        resolve(reference)
    return resolved


def build_index(db_path: Path, index_path: Path, *, square_height: int = 25,
                max_radius: int = 25, spiral_steps: int = 5,
                stage: int | None = None,
                spiral_seed: tuple[int, int, int] = (4, 3, 5)) -> dict[str, Any]:
    """Create a new snapshot index. Existing files, including corpora, are never overwritten."""
    db_path, index_path = Path(db_path).resolve(), Path(index_path).resolve()
    if index_path.exists():
        raise ValueError(f"Refusing to overwrite existing file: {index_path}")
    if stage is not None and (isinstance(stage, bool) or not isinstance(stage, int) or stage < 1):
        raise ValueError("stage must be a positive integer")
    specs = generate_associations(square_height=square_height, max_radius=max_radius,
                                  spiral_steps=spiral_steps, spiral_seed=spiral_seed)
    _require_checkpointed_source(db_path)
    before_hash = file_sha256(db_path)
    records, nodes = [], {}
    with closing(connect_readonly(db_path)) as source:
        source.execute("BEGIN")
        alignment = require_strict_alignment(source)
        evidence = GraphEvidence(source, corpus_stage=stage)
        if evidence.complete_corpus_stage is None or evidence.corpus_stage is None:
            raise ValueError("A verified complete frontier is required")
        resolved = _resolve_certificates(specs, evidence)
        for spec in specs:
            certificates = [resolved[f"{spec['id']}#{c['id']}"] for c in spec["certificates"]]
            support = _association_support(certificates)
            records.append((spec, support, certificates))
            for member in spec["participants"]:
                value = member["value"]
                if value not in nodes:
                    nodes[value] = _node_snapshot(evidence, value)
        config_row = source.execute("SELECT value FROM meta WHERE key='config_json'").fetchone()
        research_paths = {path for spec in specs for path in spec.get("sources", [])}
        research_paths.update(path for c in resolved.values() for path in c.get("sources", []))
        metadata = {
            "schema_version": VERSION,
            "source": {"path": str(db_path), "sha256": before_hash,
                       "requested_stage": stage, "checkpoint": evidence.corpus_stage,
                       "complete_stage": evidence.complete_corpus_stage,
                       "recorded_stage": evidence.recorded_corpus_stage,
                       "config": json.loads(config_row[0]) if config_row else None,
                       "alignment": alignment},
            "scope": {
                "square_height": square_height, "max_radius": max_radius,
                "spiral_steps": spiral_steps, "spiral_seed": list(spiral_seed),
                "squares": "Nonnegative reduced roots p/q with p,q <= square_height; q >= 1.",
                "shells": "Ordered positive integer shells up to max_radius; their unit normalizations; plus selected signed spiral shells and their unit normalizations.",
                "spiral": f"Fixed-seed pair powers ({spiral_seed[0]}{spiral_seed[1]:+}i)^n, n=1..spiral_steps; radius {spiral_seed[2]}^n. No general spiral discovery.",
                "certificates": "Literal requests plus reduced positive rational-square integer encodings; selected positive integer shell normalizations; fixed existing Pascal-shell routes for square:9 and square:25 when selected.",
            },
            "interpretation": {
                "membership": "Exact arithmetic in the selected external families.",
                "witnessed": "At least one named certificate is complete. Inspect its criterion; this does not assert a literal fractional-input edge.",
                "partial": "No named certificate is complete, but at least one has some supporting requests or dependencies.",
                "unwitnessed": "No named certificate has supporting witnesses; mathematical membership remains exact.",
                "certificate": "All of that certificate's directed requests and explicit certificate dependencies must be witnessed; alternative routes never supply missing requests to each other.",
                "identity": "Repeated roles may share retained occurrences. Certificate counts and empty overlap do not establish independent evidence.",
                "clocks": "Witness stages use the positive-spine clock; spiral iteration and raw normalization scale remain separate parameters. Bundle completion is not a causal execution trace or a minimum over all proofs.",
                "spiral": "A witnessed scalar lineage does not require the later direct target-shell certificate; complex multiplication remains an external interpretation.",
                "absence": "No association means no match in this bounded selection, not mathematical nonmembership. Unknown/uninspected qualities are not negative tags.",
                "snapshot": "Queries read this saved snapshot; they do not silently recompute against a changed or missing source.",
                "node_scope": "Public node observations are scoped to the checkpoint. saved_source_node preserves the full source record; confirmation_threshold is a schedule, not an observed event.",
            },
            "source_hashes": {name: file_sha256((PROJECT_ROOT / name)) for name in (
                'moo/node_profiles.py', 'moo/association_families.py', 'moo/graph_evidence.py',
                'moo/graph_corpus.py', 'moo/research_utils.py', 'moo/profile_certificates.py')},
            "research_source_hashes": {name: file_sha256(PROJECT_ROOT / name)
                                       for name in sorted(research_paths)},
        }
    if file_sha256(db_path) != before_hash:
        raise RuntimeError("Source corpus changed during inspection")
    _require_checkpointed_source(db_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects against a target appearing after the first check.
    with index_path.open("xb"):
        pass
    try:
        with closing(sqlite3.connect(index_path)) as index:
            index.execute("PRAGMA foreign_keys=ON")
            index.executescript("""
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE nodes(value TEXT PRIMARY KEY, snapshot TEXT NOT NULL);
                CREATE TABLE associations(
                    id TEXT PRIMARY KEY, family TEXT NOT NULL, label TEXT NOT NULL,
                    parameters TEXT NOT NULL, support TEXT NOT NULL, status TEXT NOT NULL,
                    first_supported_stage INTEGER, sources TEXT NOT NULL, relations TEXT NOT NULL);
                CREATE TABLE certificates(
                    ref TEXT PRIMARY KEY, association_id TEXT NOT NULL REFERENCES associations(id),
                    id TEXT NOT NULL, data TEXT NOT NULL,
                    UNIQUE(association_id, id));
                CREATE TABLE participants(
                    association_id TEXT NOT NULL REFERENCES associations(id),
                    role TEXT NOT NULL, value TEXT NOT NULL REFERENCES nodes(value),
                    PRIMARY KEY(association_id, role));
                CREATE INDEX participants_by_value ON participants(value, association_id);
                CREATE INDEX associations_by_family_status ON associations(family, status);
            """)
            index.execute("INSERT INTO metadata VALUES('manifest', ?)", (_json(metadata),))
            index.executemany("INSERT INTO nodes VALUES(?, ?)",
                              [(value, _json(payload)) for value, payload in nodes.items()])
            for spec, support, certificates in records:
                index.execute("INSERT INTO associations VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (spec["id"], spec["family"], spec["label"], _json(spec["parameters"]),
                               _json(support), support["status"], support["first_supported_stage"],
                               _json(spec.get("sources", [])), _json(spec.get("relations", []))))
                index.executemany("INSERT INTO certificates VALUES(?, ?, ?, ?)",
                                  [(c["ref"], spec["id"], c["id"], _json(c)) for c in certificates])
                index.executemany("INSERT INTO participants VALUES(?, ?, ?)",
                                  [(spec["id"], p["role"], p["value"]) for p in spec["participants"]])
            index.commit()
    except BaseException:
        index_path.unlink(missing_ok=True)
        raise
    return {"index": str(index_path), "manifest": metadata,
            "association_counts": dict(Counter(s["family"] for s, _, _ in records)),
            "certificate_count": len(resolved),
            "certificate_support_counts": dict(Counter(c["support"]["status"] for c in resolved.values())),
            "support_counts": {family: dict(Counter(support["status"] for spec, support, _ in records
                                                   if spec["family"] == family)) for family in FAMILIES},
            "indexed_values": len(nodes)}


def _manifest(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT value FROM metadata WHERE key='manifest'").fetchone()
    manifest = json.loads(row[0]) if row else {}
    if manifest.get("schema_version") not in READABLE_VERSIONS:
        raise ValueError("Unsupported association index")
    return manifest


def index_manifest(index_path: Path) -> dict[str, Any]:
    with closing(connect_readonly(index_path)) as conn:
        return _manifest(conn)


def verify_source(index_path: Path, db_path: Path) -> None:
    _require_checkpointed_source(db_path)
    source_hash = file_sha256(db_path)
    _require_checkpointed_source(db_path)
    if source_hash != index_manifest(index_path)["source"]["sha256"]:
        raise ValueError("Association index belongs to a different source snapshot")


def _association(conn: sqlite3.Connection, row: sqlite3.Row, *, details: bool) -> dict[str, Any]:
    support = json.loads(row["support"])
    if "sources" in row.keys():
        sources, relations = json.loads(row["sources"]), json.loads(row["relations"])
        certificates = [json.loads(c["data"]) for c in conn.execute(
            "SELECT data FROM certificates WHERE association_id=? ORDER BY rowid", (row["id"],))]
    else:
        # Existing v1 indexes remain readable as the literal-only snapshots they were.
        sources, relations = [], []
        identifier = "scalar_lineage" if row["family"] == "spiral" else "literal"
        legacy_support = json.loads(row["support"])
        legacy_support["dependencies"] = [
            {"ref": f"{d['id']}#{'scalar_lineage' if d['id'].startswith('spiral:') else 'literal'}",
             "status": d["status"], "first_supported_stage": d["first_supported_stage"]}
            for d in legacy_support.get("dependencies", [])]
        certificates = [{"id": identifier, "ref": f"{row['id']}#{identifier}",
                         "association_id": row["id"], "label": "Original v1 certificate",
                         "criterion": legacy_support["criterion"], "parameters": {}, "sources": [],
                         "support": legacy_support, "legacy_snapshot": True}]
    if not details:
        support.pop("requests", None)
        for certificate in certificates:
            certificate["support"].pop("requests", None)
    return {
        "id": row["id"], "family": row["family"], "label": row["label"],
        "parameters": json.loads(row["parameters"]), "support": support,
        "certificates": certificates, "sources": sources, "relations": relations,
        "participants": [dict(member) for member in conn.execute(
            "SELECT role,value FROM participants WHERE association_id=? ORDER BY role", (row["id"],))],
    }


def load_association(index_path: Path, identifier: str) -> dict[str, Any]:
    with closing(connect_readonly(index_path)) as conn:
        _manifest(conn)
        row = conn.execute("SELECT * FROM associations WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError(f"Association not indexed: {identifier}")
        return _association(conn, row, details=True)


def load_certificate(index_path: Path, reference: str) -> dict[str, Any]:
    if reference.count("#") != 1:
        raise ValueError("Certificate reference must be association_id#certificate_id")
    association_id, certificate_id = reference.split("#")
    association = load_association(index_path, association_id)
    for certificate in association["certificates"]:
        if certificate["id"] == certificate_id:
            return certificate
    raise ValueError(f"Certificate not indexed: {reference}")


def node_profile(index_path: Path, value: str, *, family: str | None = None,
                 witnessed_only: bool = False, details: bool = False) -> dict[str, Any]:
    value = str(Fraction(value))
    if family is not None and family not in FAMILIES:
        raise ValueError(f"Unknown family: {family}")
    with closing(connect_readonly(index_path)) as conn:
        manifest = _manifest(conn)
        node = conn.execute("SELECT snapshot FROM nodes WHERE value=?", (value,)).fetchone()
        rows = conn.execute("""
            SELECT DISTINCT a.* FROM associations a
            JOIN participants p ON p.association_id=a.id
            WHERE p.value=? AND (? IS NULL OR a.family=?) AND (?=0 OR a.status='witnessed')
            ORDER BY CASE a.family WHEN 'square' THEN 0 WHEN 'shell' THEN 1 ELSE 2 END,a.id
        """, (value, family, family, int(witnessed_only))).fetchall()
        associations = [_association(conn, row, details=details) for row in rows]
        for association in associations:
            association["roles"] = [p["role"] for p in association["participants"] if p["value"] == value]
        return {"value": value, "source": manifest["source"], "scope": manifest["scope"],
                "interpretation": manifest["interpretation"],
                "node": _checkpoint_node(json.loads(node[0]), manifest["source"]["checkpoint"]) if node else {"label": value, "present": None,
                                                        "reason": "not_in_indexed_participants"},
                "filters": {"family": family, "witnessed_only": witnessed_only},
                "association_count": len(associations), "associations": associations}


def compare_profiles(index_path: Path, values: Sequence[str], *, witnessed_only: bool = False) -> dict[str, Any]:
    canonical = list(dict.fromkeys(str(Fraction(value)) for value in values))
    if len(canonical) < 2:
        raise ValueError("Comparison needs at least two distinct values")
    profiles = [node_profile(index_path, value, witnessed_only=witnessed_only) for value in canonical]
    family_sets = [{a["family"] for a in p["associations"]} for p in profiles]
    association_sets = [{a["id"] for a in p["associations"]} for p in profiles]
    role_sets = [{(a["family"], role) for a in p["associations"] for role in a["roles"]} for p in profiles]
    return {"values": canonical, "source": profiles[0]["source"], "scope": profiles[0]["scope"],
            "witnessed_only": witnessed_only,
            "common_families": sorted(set.intersection(*family_sets)),
            "common_associations": sorted(set.intersection(*association_sets)),
            "common_family_roles": [{"family": f, "role": r} for f, r in sorted(set.intersection(*role_sets))],
            "profiles": profiles}


def find_members(index_path: Path, families: Sequence[str], *, witnessed_only: bool = False,
                 by_stage: int | None = None) -> dict[str, Any]:
    """Find values satisfying every family/role selector in this saved index.

    A selector is a family or family:role, e.g. square:result. Different roles
    of the same family must each match. A stage cutoff requires every selected
    relationship to have complete support by that stage, within the snapshot.
    """
    selectors = sorted(set(families))
    if not selectors:
        raise ValueError(f"Choose one or more families from {FAMILIES}")
    parsed = []
    for selector in selectors:
        family, separator, role = selector.partition(":")
        if family not in FAMILIES:
            raise ValueError(f"Choose a family from {FAMILIES}: {selector}")
        if separator and role not in ROLE_FILTERS[family]:
            raise ValueError(f"Choose a {family} role from {tuple(ROLE_FILTERS[family])}: {role}")
        parsed.append((selector, family, ROLE_FILTERS[family][role] if separator else None))
    if by_stage is not None:
        if isinstance(by_stage, bool) or not isinstance(by_stage, int) or by_stage < 1:
            raise ValueError("by_stage must be a positive integer")
        witnessed_only = True
    with closing(connect_readonly(index_path)) as conn:
        manifest = _manifest(conn)
        if by_stage is not None and by_stage > manifest["source"]["checkpoint"]:
            raise ValueError("by_stage exceeds the saved index checkpoint")
        matches: dict[str, list[dict[str, Any]]] = {}
        selected_values = []
        for selector, family, role in parsed:
            rows = conn.execute("""
                SELECT p.value,p.role,a.id,a.status,a.first_supported_stage
                FROM participants p JOIN associations a ON a.id=p.association_id
                WHERE a.family=? AND (? IS NULL OR p.role=?)
                  AND (?=0 OR a.status='witnessed')
                  AND (? IS NULL OR a.first_supported_stage<=?)
                ORDER BY a.id,p.role
            """, (family, role, role, int(witnessed_only), by_stage, by_stage)).fetchall()
            selected_values.append({row["value"] for row in rows})
            for row in rows:
                matches.setdefault(row["value"], []).append({
                    "selector": selector, "association_id": row["id"], "role": row["role"],
                    "status": row["status"], "first_supported_stage": row["first_supported_stage"],
                })
        values = sorted(set.intersection(*selected_values), key=Fraction)
        return {"families": sorted({family for _, family, _ in parsed}),
                "selectors": selectors, "witnessed_only": witnessed_only, "by_stage": by_stage,
                "source": manifest["source"], "scope": manifest["scope"],
                "values": values, "count": len(values),
                "matches": {value: matches[value] for value in values},
                "interpretation": "Every selector must match the same value through its specified role, or any role when omitted. Sharing a scalar value does not establish the same configuration or a construction dependency; inspect the matched association references. A stage cutoff requires complete relationship support by that stage. Results are bounded selections, not statistical correlations or a complete branch discovery."}


def _print_profile(profile: dict[str, Any], *, details: bool = False) -> None:
    role_names = {"root": "square source", "square": "square result", "r": "radius",
                  "r_square": "squared radius", "x": "x coordinate", "y": "y coordinate",
                  "x_square": "x squared", "y_square": "y squared",
                  "previous_x": "previous x", "previous_y": "previous y", "previous_r": "previous radius"}
    print(f"Node {profile['value']} | U{profile['source']['checkpoint']} | "
          f"{profile['node'].get('status_at_checkpoint', 'not indexed')}")
    for association in profile["associations"]:
        support = association["support"]
        when = f" U{support['first_supported_stage']}" if support["first_supported_stage"] is not None else ""
        roles = ", ".join(role_names.get(role, role) for role in association["roles"])
        print(f"  {association['family']}: {association['label']} | "
              f"{roles} | {support['status']}{when}")
        if details:
            for certificate in association["certificates"]:
                route = certificate["support"]
                stage = route["first_supported_stage"]
                timing = f" U{stage}" if stage is not None else ""
                print(f"    via {certificate['id']}: {route['status']}{timing}")
    if not profile["associations"]:
        print("  No associations in this bounded selection and filter; this is not nonmembership.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Create a new derived index from a read-only corpus")
    build.add_argument("--db", type=Path, required=True)
    build.add_argument("--index", type=Path, required=True)
    build.add_argument("--square-height", type=int, default=25)
    build.add_argument("--max-radius", type=int, default=25)
    build.add_argument("--spiral-steps", type=int, default=5)
    build.add_argument("--spiral-seed", type=int, nargs=3, metavar=("X", "Y", "R"),
                       default=(4, 3, 5), help="Ordered integer shell seed (default: 4 3 5)")
    build.add_argument("--stage", type=int)
    for name in ("profile", "compare", "find", "association", "certificate", "compare-certificates"):
        query = sub.add_parser(name)
        query.add_argument("--index", type=Path, required=True)
        query.add_argument("--json", action="store_true", help="Print full structured output")
        if name in ("profile", "compare", "find"):
            query.add_argument("--witnessed-only", action="store_true")
        if name == "profile":
            query.add_argument("values", nargs="+")
            query.add_argument("--family", choices=FAMILIES)
            query.add_argument("--details", action="store_true",
                               help="Show construction certificates; with --json, include individual request evidence")
        elif name == "compare":
            query.add_argument("values", nargs="+")
        elif name == "find":
            query.add_argument("families", nargs="+", metavar="FAMILY[:ROLE]",
                               help="Intersect families or roles, e.g. square:result spiral:radius")
            query.add_argument("--by-stage", type=int,
                               help="Require every selected relationship to be supported by this stage")
        elif name == "compare-certificates":
            query.add_argument("left", help="association_id#certificate_id")
            query.add_argument("right", help="association_id#certificate_id")
        else:
            query.add_argument("identifier")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            payload = build_index(args.db, args.index, square_height=args.square_height,
                                  max_radius=args.max_radius, spiral_steps=args.spiral_steps, stage=args.stage,
                                  spiral_seed=tuple(args.spiral_seed))
        elif args.command == "profile":
            payload = [node_profile(args.index, value, family=args.family,
                                    witnessed_only=args.witnessed_only, details=args.details) for value in args.values]
            if not args.json:
                for profile in payload:
                    _print_profile(profile, details=args.details)
                return 0
        elif args.command == "compare":
            payload = compare_profiles(args.index, args.values, witnessed_only=args.witnessed_only)
            if not args.json:
                print("Common families:", ", ".join(payload["common_families"]) or "none in selection")
                print("Common associations:", ", ".join(payload["common_associations"]) or "none in selection")
                for profile in payload["profiles"]:
                    _print_profile(profile)
                return 0
        elif args.command == "find":
            payload = find_members(args.index, args.families, witnessed_only=args.witnessed_only,
                                   by_stage=args.by_stage)
            if not args.json:
                print(f"{payload['count']} matching values in bounded selection: {', '.join(payload['values'])}")
                if any(":" in selector for selector in payload["selectors"]) or args.by_stage is not None:
                    for value, matches in payload["matches"].items():
                        for match in matches:
                            stage = match["first_supported_stage"]
                            timing = f" U{stage}" if stage is not None else ""
                            print(f"  {value}: {match['selector']} | {match['association_id']} | "
                                  f"{match['status']}{timing}")
                return 0
        elif args.command == "certificate":
            payload = load_certificate(args.index, args.identifier)
        elif args.command == "compare-certificates":
            from moo.profile_certificates import compare_certificates
            payload = compare_certificates(args.index, args.left, args.right)
        else:
            payload = load_association(args.index, args.identifier)
    except (ValueError, TypeError, FileNotFoundError) as exc:
        parser.error(str(exc))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

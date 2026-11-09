from __future__ import annotations

import json
import sqlite3
from fractions import Fraction
from typing import Dict, List, Optional, Tuple, Union

from moo.graph_corpus import (
    GraphCorpusConfig,
    STRICT_STAGE_OPERATIONS,
    format_key,
    normalize_key,
    strict_stage_expected_candidate_events,
    strict_stage_retains_result,
)


Key = Tuple[int, int]
KeyLike = Union[int, str, Fraction, Key]
COMMUTATIVE_OPS = {"+", "*"}


def normalize_keylike(value: KeyLike) -> Key:
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError("tuple keys must be (p, q)")
        return normalize_key(int(value[0]), int(value[1]))
    if isinstance(value, Fraction):
        return normalize_key(int(value.numerator), int(value.denominator))
    if isinstance(value, int):
        return normalize_key(int(value), 1)
    frac = Fraction(str(value))
    return normalize_key(int(frac.numerator), int(frac.denominator))


def node_status(row: sqlite3.Row) -> str:
    p = int(row["p"])
    q = int(row["q"])
    confirmed_stage = row["confirmed_stage"]
    if (p, q) == (1, 1):
        return "certainty"
    if confirmed_stage is None:
        return "speculative"
    if int(row["first_stage"]) < int(confirmed_stage):
        return "speculative_until_confirmed"
    return "confirmed_by_core_loop"


def is_positive_spine_key(key: Key) -> bool:
    p, q = key
    return q == 1 and p >= 1


def expected_directed_edges(
    left_key: Key,
    right_key: Key,
    op: str,
    *,
    allow_commuted: bool,
) -> int:
    if bool(allow_commuted) and op in COMMUTATIVE_OPS and left_key != right_key:
        return 2
    return 1


def edge_status(edge_count: int, expected_directed: int) -> str:
    count = int(edge_count)
    if count == 0:
        return "absent"
    if count == int(expected_directed):
        return "complete_directed"
    return "partial_or_unexpected"


class GraphEvidence:
    def __init__(self, conn: sqlite3.Connection, *, corpus_stage: Optional[int] = None) -> None:
        self.conn = conn
        self._node_cache: Dict[Key, Optional[sqlite3.Row]] = {}
        self._edge_cache: Dict[Tuple[Key, str, Key, Key, bool], Dict[str, object]] = {}
        (
            self.recorded_corpus_stage,
            self.complete_corpus_stage,
        ) = self._stage_coverage()
        self.requested_corpus_stage = (
            int(corpus_stage) if corpus_stage is not None else None
        )
        if self.complete_corpus_stage is None:
            # A caller-supplied stage remains useful for legacy fixtures without
            # stage telemetry, but it is explicitly marked unverified below.
            self.corpus_stage = self.requested_corpus_stage
        elif self.requested_corpus_stage is None:
            self.corpus_stage = int(self.complete_corpus_stage)
        else:
            self.corpus_stage = min(
                int(self.requested_corpus_stage),
                int(self.complete_corpus_stage),
            )
        self._config, self._config_status = self._load_config()

    def _stage_coverage(self) -> Tuple[Optional[int], Optional[int]]:
        try:
            rows = self.conn.execute(
                "SELECT stage, candidate_events FROM stages ORDER BY stage"
            ).fetchall()
        except sqlite3.OperationalError:
            return None, None
        if not rows:
            return 0, 0

        recorded_stage = max(int(row["stage"]) for row in rows)
        complete_stage = 0
        expected_stage = 1
        for row in rows:
            stage = int(row["stage"])
            if stage != expected_stage:
                break
            if int(row["candidate_events"]) != strict_stage_expected_candidate_events(stage):
                break
            complete_stage = stage
            expected_stage += 1
        return recorded_stage, complete_stage

    def _load_config(self) -> Tuple[Optional[GraphCorpusConfig], str]:
        try:
            row = self.conn.execute(
                "SELECT value FROM meta WHERE key = 'config_json'"
            ).fetchone()
        except sqlite3.OperationalError:
            return None, "missing"
        if row is None:
            return None, "missing"
        try:
            raw = json.loads(str(row["value"]))
            if not isinstance(raw, dict):
                return None, "invalid"
            config = GraphCorpusConfig(
                generator=str(raw["generator"]),
                max_stage=int(raw["max_stage"]),
                max_abs_p=int(raw["max_abs_p"]),
                max_abs_q=int(raw["max_abs_q"]),
                max_abs_value=(
                    float(raw["max_abs_value"])
                    if raw.get("max_abs_value") is not None
                    else None
                ),
                retain_confirmed_edges=bool(raw.get("retain_confirmed_edges", True)),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None, "invalid"
        if config.generator != "strict_stage_moo_graph":
            return None, "unsupported_generator"
        return config, "available"

    def retains_result(self, key: KeyLike, *, stage: int) -> Optional[bool]:
        """Result-bound eligibility at a stage, not evidence that an edge exists.

        None means the saved generator configuration cannot establish the rule.
        Operand and completed-frontier eligibility must be checked separately.
        """
        if self._config is None:
            return None
        return strict_stage_retains_result(
            normalize_keylike(key), stage=stage,
            max_abs_p=self._config.max_abs_p, max_abs_q=self._config.max_abs_q,
            max_abs_value=self._config.max_abs_value,
            retain_confirmed_edges=self._config.retain_confirmed_edges,
        )

    def node_row(self, key: KeyLike) -> Optional[sqlite3.Row]:
        normalized = normalize_keylike(key)
        if normalized not in self._node_cache:
            self._node_cache[normalized] = self.conn.execute(
                "SELECT * FROM nodes WHERE p = ? AND q = ?",
                (int(normalized[0]), int(normalized[1])),
            ).fetchone()
        return self._node_cache[normalized]

    def node_payload(self, key: KeyLike) -> Dict[str, object]:
        normalized = normalize_keylike(key)
        row = self.node_row(normalized)
        if row is None:
            return {
                "present": False,
                "key": [int(normalized[0]), int(normalized[1])],
                "label": format_key(normalized),
                "p": int(normalized[0]),
                "q": int(normalized[1]),
            }
        payload: Dict[str, object] = {
            "present": True,
            "node_id": int(row["node_id"]),
            "key": [int(row["p"]), int(row["q"])],
            "label": row["label"] if "label" in row.keys() else format_key(normalized),
            "p": int(row["p"]),
            "q": int(row["q"]),
            "kind": str(row["kind"]),
            "status": node_status(row),
            "first_stage": int(row["first_stage"]),
            "confirmed_stage": int(row["confirmed_stage"])
            if row["confirmed_stage"] is not None
            else None,
        }
        if "first_edge_id" in row.keys():
            payload["first_edge_id"] = (
                int(row["first_edge_id"]) if row["first_edge_id"] is not None else None
            )
        return payload

    def edge_witness(
        self,
        *,
        left: KeyLike,
        op: str,
        right: KeyLike,
        result: KeyLike,
        allow_commuted: bool = False,
        claim_id: Optional[str] = None,
        relation: Optional[str] = None,
        edge_limit: int = 8,
    ) -> Dict[str, object]:
        left_key = normalize_keylike(left)
        right_key = normalize_keylike(right)
        result_key = normalize_keylike(result)
        cache_key = (left_key, str(op), right_key, result_key, bool(allow_commuted))
        left_row = self.node_row(left_key)
        right_row = self.node_row(right_key)
        result_row = self.node_row(result_key)
        missing_nodes: List[str] = []
        if left_row is None:
            missing_nodes.append("left")
        if right_row is None:
            missing_nodes.append("right")
        if result_row is None:
            missing_nodes.append("result")

        cached = self._edge_cache.get(cache_key)
        if cached is None:
            expected = expected_directed_edges(
                left_key,
                right_key,
                str(op),
                allow_commuted=bool(allow_commuted),
            )
            stage_aperture = self._stage_aperture(
                left_key,
                right_key,
                result_key,
                str(op),
            )
            edge_count = 0
            first_edge_stage: Optional[int] = None
            if not missing_nodes:
                assert left_row is not None
                assert right_row is not None
                assert result_row is not None
                edge_count, first_edge_stage = self._edge_aggregate(
                    left_node_id=int(left_row["node_id"]),
                    right_node_id=int(right_row["node_id"]),
                    result_node_id=int(result_row["node_id"]),
                    op=str(op),
                    allow_commuted=bool(allow_commuted),
                )

            status = edge_status(edge_count, expected)
            blocker = self._blocker(
                status=status,
                missing_nodes=missing_nodes,
                stage_aperture=stage_aperture,
            )
            cached = {
                "op": str(op),
                "left": self.node_payload(left_key),
                "right": self.node_payload(right_key),
                "result": self.node_payload(result_key),
                "allow_commuted": bool(allow_commuted),
                "expected_directed_edges": expected,
                "present": edge_count > 0,
                "edge_count": edge_count,
                "count": edge_count,
                "first_edge_stage": first_edge_stage,
                "first_stage": first_edge_stage,
                "missing_nodes": missing_nodes,
                "candidate_stage": stage_aperture["candidate_stage"],
                "corpus_stage": self.corpus_stage,
                "recorded_corpus_stage": self.recorded_corpus_stage,
                "complete_corpus_stage": self.complete_corpus_stage,
                "eligible_by_stage": stage_aperture["eligible_by_stage"],
                "eligible_by_retention": stage_aperture["eligible_by_retention"],
                "eligible": stage_aperture["eligible"],
                "stage_aperture": stage_aperture,
                "status": status,
                "edge_status": status,
                "blocker": blocker,
            }
            self._edge_cache[cache_key] = dict(cached)

        payload = dict(cached)
        edge_refs: List[Dict[str, int]] = []
        display_limit = max(1, int(edge_limit))
        if not missing_nodes and int(payload["edge_count"]) > 0:
            assert left_row is not None
            assert right_row is not None
            assert result_row is not None
            rows = self._edge_rows(
                left_node_id=int(left_row["node_id"]),
                right_node_id=int(right_row["node_id"]),
                result_node_id=int(result_row["node_id"]),
                op=str(op),
                allow_commuted=bool(allow_commuted),
                edge_limit=display_limit,
            )
            edge_refs = [
                {"edge_id": int(row["edge_id"]), "stage": int(row["stage"])}
                for row in rows
            ]
        payload["claim_id"] = claim_id
        payload["relation"] = relation
        payload["edge_refs"] = edge_refs
        payload["edge_refs_truncated"] = int(payload["edge_count"]) > len(edge_refs)
        return payload

    def _edge_match_params(
        self,
        *,
        left_node_id: int,
        right_node_id: int,
        result_node_id: int,
        op: str,
        allow_commuted: bool,
    ) -> Tuple[object, ...]:
        include_reverse = bool(allow_commuted) and left_node_id != right_node_id
        return (
            int(result_node_id),
            str(op),
            int(left_node_id),
            int(right_node_id),
            int(include_reverse),
            int(right_node_id),
            int(left_node_id),
        )

    def _edge_aggregate(
        self,
        *,
        left_node_id: int,
        right_node_id: int,
        result_node_id: int,
        op: str,
        allow_commuted: bool,
    ) -> Tuple[int, Optional[int]]:
        params = self._edge_match_params(
            left_node_id=left_node_id,
            right_node_id=right_node_id,
            result_node_id=result_node_id,
            op=op,
            allow_commuted=allow_commuted,
        )
        indexed_sql = """
            SELECT COUNT(*) AS edge_count, MIN(stage) AS first_stage
            FROM edges INDEXED BY idx_edges_result
            WHERE result_node_id = ?
              AND op = ?
              AND (
                (left_node_id = ? AND right_node_id = ?)
                OR (? = 1 AND left_node_id = ? AND right_node_id = ?)
              )
        """
        fallback_sql = indexed_sql.replace(
            "FROM edges INDEXED BY idx_edges_result",
            "FROM edges",
        )
        try:
            row = self.conn.execute(indexed_sql, params).fetchone()
        except sqlite3.OperationalError as exc:
            if "idx_edges_result" not in str(exc):
                raise
            row = self.conn.execute(fallback_sql, params).fetchone()
        if row is None:
            return 0, None
        return (
            int(row["edge_count"]),
            int(row["first_stage"]) if row["first_stage"] is not None else None,
        )

    def _edge_rows(
        self,
        *,
        left_node_id: int,
        right_node_id: int,
        result_node_id: int,
        op: str,
        allow_commuted: bool,
        edge_limit: int,
    ) -> List[sqlite3.Row]:
        params = self._edge_match_params(
            left_node_id=left_node_id,
            right_node_id=right_node_id,
            result_node_id=result_node_id,
            op=op,
            allow_commuted=allow_commuted,
        ) + (int(edge_limit),)
        return self._fetch_edge_rows(
            """
            SELECT edge_id, stage
            FROM edges INDEXED BY idx_edges_result
            WHERE result_node_id = ?
              AND op = ?
              AND (
                (left_node_id = ? AND right_node_id = ?)
                OR (? = 1 AND left_node_id = ? AND right_node_id = ?)
              )
            ORDER BY stage, edge_id
            LIMIT ?
            """,
            """
            SELECT edge_id, stage
            FROM edges
            WHERE result_node_id = ?
              AND op = ?
              AND (
                (left_node_id = ? AND right_node_id = ?)
                OR (? = 1 AND left_node_id = ? AND right_node_id = ?)
              )
            ORDER BY stage, edge_id
            LIMIT ?
            """,
            params,
        )

    def _fetch_edge_rows(
        self,
        indexed_sql: str,
        fallback_sql: str,
        params: Tuple[object, ...],
    ) -> List[sqlite3.Row]:
        try:
            return list(self.conn.execute(indexed_sql, params).fetchall())
        except sqlite3.OperationalError as exc:
            if "idx_edges_result" not in str(exc):
                raise
            return list(self.conn.execute(fallback_sql, params).fetchall())

    def _stage_aperture(
        self,
        left_key: Key,
        right_key: Key,
        result_key: Key,
        op: str,
    ) -> Dict[str, object]:
        aperture: Dict[str, object] = {
            "candidate_stage": None,
            "corpus_stage": self.corpus_stage,
            "requested_corpus_stage": self.requested_corpus_stage,
            "recorded_corpus_stage": self.recorded_corpus_stage,
            "complete_corpus_stage": self.complete_corpus_stage,
            "complete_stage_verified": self.complete_corpus_stage is not None,
            "eligible_by_stage": False,
            "eligible_by_operation": str(op) in STRICT_STAGE_OPERATIONS,
            "eligible_by_retention": None,
            "retention_config_status": self._config_status,
            "eligible": False,
            "blocker": None,
        }
        if not is_positive_spine_key(left_key) or not is_positive_spine_key(right_key):
            aperture["blocker"] = "operand_not_positive_spine"
            return aperture

        candidate_stage = max(int(left_key[0]), int(right_key[0]))
        aperture["candidate_stage"] = candidate_stage
        eligible_by_stage = (
            self.corpus_stage is not None
            and candidate_stage <= int(self.corpus_stage)
        )
        aperture["eligible_by_stage"] = bool(eligible_by_stage)
        if not eligible_by_stage:
            if self.corpus_stage is None:
                aperture["blocker"] = "complete_stage_unavailable"
            elif (
                self.requested_corpus_stage is None
                or candidate_stage <= int(self.requested_corpus_stage)
            ) and (
                self.complete_corpus_stage is not None
                and self.recorded_corpus_stage is not None
                and int(self.complete_corpus_stage) < candidate_stage
                <= int(self.recorded_corpus_stage)
            ):
                aperture["blocker"] = "candidate_stage_in_incomplete_frontier"
            else:
                aperture["blocker"] = "candidate_stage_beyond_corpus"
            return aperture

        if str(op) not in STRICT_STAGE_OPERATIONS:
            aperture["blocker"] = "operation_not_in_strict_stage"
            return aperture

        if self._config is None:
            # An absent result node can be indistinguishable from intentional
            # generator filtering when the retention configuration is missing.
            # Stay conservative instead of labelling that absence eligible.
            aperture["blocker"] = "retention_config_unavailable"
            return aperture

        retained = self.retains_result(result_key, stage=candidate_stage)
        aperture["eligible_by_retention"] = bool(retained)
        aperture["retention_aperture"] = {
            "max_abs_p": int(self._config.max_abs_p),
            "max_abs_q": int(self._config.max_abs_q),
            "max_abs_value": self._config.max_abs_value,
            "retain_confirmed_edges": bool(self._config.retain_confirmed_edges),
            "result_retained": bool(retained),
        }
        if not retained:
            aperture["blocker"] = "result_outside_retention_aperture"
            return aperture

        aperture["eligible"] = True
        return aperture

    def _blocker(
        self,
        *,
        status: str,
        missing_nodes: List[str],
        stage_aperture: Dict[str, object],
    ) -> Optional[str]:
        if status != "absent":
            return None
        aperture_blocker = stage_aperture.get("blocker")
        if aperture_blocker is not None:
            return str(aperture_blocker)
        if missing_nodes:
            return "missing_nodes"
        return "edge_absent"

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ygg.continuity_corpus import ContinuityRecord, load_continuity_corpus
from ygg.continuity_topology import build_continuity_topology


AUTHORITY_WEIGHTS = {
    "program": 1.0,
    "idea": 0.9,
    "checkpoint": 0.8,
    "promotion-log": 0.55,
    "runtime-event": 0.35,
}

DEFAULT_STRATEGY = "topology"
VALID_STRATEGIES = {"keyword", "recency", "topology"}
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "into", "from", "what", "which",
    "about", "have", "has", "would", "should", "could", "where", "when", "need",
    "ygg", "continuity", "state", "show", "find", "lookup",
}


@dataclass(frozen=True)
class RetrievalResult:
    record: ContinuityRecord
    score: float
    explanation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record": self.record.to_dict(),
            "score": round(self.score, 6),
            "explanation": self.explanation,
        }


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9._/-]{1,}", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def retrieve_continuity(
    root: str | Path,
    query: str,
    *,
    strategy: str = DEFAULT_STRATEGY,
    limit: int = 5,
) -> dict[str, Any]:
    strategy_name = strategy.lower()
    if strategy_name not in VALID_STRATEGIES:
        raise ValueError(f"Unknown retrieval strategy: {strategy}")
    records = load_continuity_corpus(root)
    topology = build_continuity_topology(records)
    results = rank_records(query, records, topology, strategy=strategy_name, limit=limit)
    return {
        "query": query,
        "strategy": strategy_name,
        "limit": limit,
        "recordCount": len(records),
        "results": [result.to_dict() for result in results],
    }


def rank_records(
    query: str,
    records: list[ContinuityRecord],
    topology: dict[str, Any],
    *,
    strategy: str,
    limit: int = 5,
) -> list[RetrievalResult]:
    query_tokens = tokenize(query)
    if not records:
        return []
    if strategy == "keyword":
        scored = [_score_keyword(record, query_tokens) for record in records]
    elif strategy == "recency":
        scored = [_score_recency(record, query_tokens) for record in records]
    else:
        scored = _score_topology(records, topology, query_tokens)
    filtered = [result for result in scored if result.score > 0]
    filtered.sort(key=lambda item: (item.score, item.record.timestamp or "", item.record.id), reverse=True)
    return filtered[:limit]


def _score_keyword(record: ContinuityRecord, query_tokens: list[str]) -> RetrievalResult:
    record_tokens = tokenize(record.text)
    overlap = Counter(record_tokens)
    hits = sum(min(overlap[token], 1) for token in set(query_tokens))
    density = hits / max(len(set(query_tokens)), 1)
    score = density + (0.15 if _contains_phrase(record, query_tokens) else 0.0)
    return RetrievalResult(
        record=record,
        score=score,
        explanation={"strategy": "keyword", "lexicalHits": hits, "queryTokens": query_tokens},
    )


def _score_recency(record: ContinuityRecord, query_tokens: list[str]) -> RetrievalResult:
    lexical = _score_keyword(record, query_tokens)
    recency = _recency_score(record.timestamp)
    score = 0.35 * lexical.score + 0.9 * recency
    explanation = {
        "strategy": "recency",
        "lexical": round(lexical.score, 6),
        "recency": round(recency, 6),
    }
    return RetrievalResult(record=record, score=score, explanation=explanation)


def _score_topology(records: list[ContinuityRecord], topology: dict[str, Any], query_tokens: list[str]) -> list[RetrievalResult]:
    lexical_map: dict[str, float] = {}
    seed_scores: dict[str, float] = {}
    for record in records:
        lexical = _score_keyword(record, query_tokens)
        lexical_map[record.id] = lexical.score
        seed_scores[record.id] = lexical.score
    adjacency = topology.get("adjacency") or {}
    results: list[RetrievalResult] = []
    for record in records:
        authority = AUTHORITY_WEIGHTS.get(record.authority, 0.4)
        recency = _recency_score(record.timestamp)
        shared_bonus = _shared_structure_bonus(record, query_tokens)
        topology_bonus, evidence = _neighborhood_bonus(record.id, seed_scores, adjacency)
        topology_bonus *= 0.35 + min(lexical_map[record.id], 1.0)
        score = (
            1.35 * lexical_map[record.id]
            + 0.35 * authority
            + 0.55 * recency
            + shared_bonus
            + topology_bonus
        )
        results.append(
            RetrievalResult(
                record=record,
                score=score,
                explanation={
                    "strategy": "topology",
                    "lexical": round(lexical_map[record.id], 6),
                    "authority": authority,
                    "recency": round(recency, 6),
                    "sharedStructure": round(shared_bonus, 6),
                    "topologyBonus": round(topology_bonus, 6),
                    "neighborEvidence": evidence,
                },
            )
        )
    return results


def _contains_phrase(record: ContinuityRecord, query_tokens: list[str]) -> bool:
    query = " ".join(query_tokens)
    return bool(query and query in record.text.lower())


def _shared_structure_bonus(record: ContinuityRecord, query_tokens: list[str]) -> float:
    bonus = 0.0
    tags = {tag.lower() for tag in record.tags}
    links = {link.lower() for link in record.links}
    for token in query_tokens:
        if token in tags:
            bonus += 0.18
        if f"lane:{token}" in links or f"task:{token}" in links or f"domain:{token}" in links:
            bonus += 0.25
    return bonus


def _neighborhood_bonus(record_id: str, seed_scores: dict[str, float], adjacency: dict[str, list[dict[str, Any]]]) -> tuple[float, list[dict[str, Any]]]:
    bonus = 0.0
    evidence: list[dict[str, Any]] = []
    for edge in adjacency.get(record_id, []):
        neighbor_score = seed_scores.get(str(edge.get("target")), 0.0)
        if neighbor_score <= 0:
            continue
        edge_weight = float(edge.get("weight") or 0.0)
        contribution = edge_weight * neighbor_score * 0.45
        bonus += contribution
        evidence.append(
            {
                "neighborId": edge.get("target"),
                "edgeType": edge.get("type"),
                "reason": edge.get("reason"),
                "contribution": round(contribution, 6),
            }
        )
    evidence.sort(key=lambda item: item["contribution"], reverse=True)
    return bonus, evidence[:5]


def _recency_score(timestamp: str | None) -> float:
    if not timestamp:
        return 0.0
    try:
        dt = datetime.fromisoformat(timestamp)
    except ValueError:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    age_days = max((datetime.now(UTC) - dt.astimezone(UTC)).total_seconds() / 86400.0, 0.0)
    return math.exp(-age_days / 30.0)


def load_benchmark_cases(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"Benchmark file `{path}` is missing `cases` list.")
    return cases


def run_benchmark(
    root: str | Path,
    benchmark_path: str | Path,
    *,
    limit: int = 5,
    strategies: tuple[str, ...] = ("keyword", "recency", "topology"),
) -> dict[str, Any]:
    records = load_continuity_corpus(root)
    topology = build_continuity_topology(records)
    cases = load_benchmark_cases(benchmark_path)
    strategy_summaries: dict[str, dict[str, Any]] = {}
    for strategy in strategies:
        case_results = []
        score_total = 0.0
        for case in cases:
            ranked = rank_records(case["query"], records, topology, strategy=strategy, limit=limit)
            ranked_ids = [result.record.id for result in ranked]
            score = _case_score(ranked_ids, case)
            score_total += score
            case_results.append(
                {
                    "query": case["query"],
                    "category": case.get("category"),
                    "score": round(score, 6),
                    "rankedIds": ranked_ids,
                    "expectedIds": case.get("expectedIds", []),
                    "acceptableIds": case.get("acceptableIds", []),
                }
            )
        strategy_summaries[strategy] = {
            "strategy": strategy,
            "cases": case_results,
            "averageScore": round(score_total / max(len(cases), 1), 6),
            "hitCount": sum(1 for item in case_results if item["score"] >= 1.0),
            "partialHitCount": sum(1 for item in case_results if item["score"] > 0),
        }
    return {
        "root": str(Path(root).expanduser().resolve()),
        "benchmarkPath": str(Path(benchmark_path).expanduser().resolve()),
        "caseCount": len(cases),
        "recordCount": len(records),
        "strategies": strategy_summaries,
    }


def _case_score(ranked_ids: list[str], case: dict[str, Any]) -> float:
    expected = set(case.get("expectedIds") or [])
    acceptable = set(case.get("acceptableIds") or [])
    if not ranked_ids:
        return 0.0
    top_id = ranked_ids[0]
    if top_id in expected:
        return 1.0
    if top_id in acceptable:
        return 0.5
    if expected.intersection(ranked_ids):
        return 0.75
    if acceptable.intersection(ranked_ids):
        return 0.25
    return 0.0

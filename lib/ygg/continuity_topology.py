from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ygg.continuity_corpus import ContinuityRecord


@dataclass(frozen=True)
class TopologyEdge:
    source_id: str
    target_id: str
    edge_type: str
    weight: float
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type,
            "weight": self.weight,
            "reason": self.reason,
        }


def build_continuity_topology(records: list[ContinuityRecord]) -> dict[str, object]:
    by_id = {record.id: record for record in records}
    edges: list[TopologyEdge] = []
    emitted: set[tuple[str, str, str]] = set()
    link_index: dict[str, list[str]] = defaultdict(list)
    lane_index: dict[str, list[str]] = defaultdict(list)
    tag_index: dict[str, list[str]] = defaultdict(list)
    artifact_index: dict[str, list[str]] = defaultdict(list)

    for record in records:
        for link in record.links:
            link_index[link].append(record.id)
            if link.startswith("lane:"):
                lane_index[link.split(":", 1)[1]].append(record.id)
        for tag in record.tags:
            tag_index[tag].append(record.id)
        for artifact in _artifact_refs(record):
            artifact_index[artifact].append(record.id)

    def add_edge(source_id: str, target_id: str, edge_type: str, weight: float, reason: str) -> None:
        if source_id == target_id:
            return
        key = (source_id, target_id, edge_type)
        if key in emitted:
            return
        emitted.add(key)
        edges.append(TopologyEdge(source_id, target_id, edge_type, weight, reason))

    for link, record_ids in link_index.items():
        for source_id in record_ids:
            for target_id in record_ids:
                if source_id == target_id:
                    continue
                add_edge(source_id, target_id, "explicit-link", 1.0, f"shared link {link}")
        if link.startswith("checkpoint:") and link in by_id:
            checkpoint_id = link
            for source_id in record_ids:
                if source_id.startswith("idea:"):
                    add_edge(source_id, checkpoint_id, "idea-checkpoint", 1.0, f"{source_id} references {checkpoint_id}")
        if link.startswith("program:") and link in by_id:
            program_id = link
            for source_id in record_ids:
                if source_id.startswith("idea:"):
                    add_edge(source_id, program_id, "idea-program", 1.0, f"{source_id} references {program_id}")

    for lane, record_ids in lane_index.items():
        for source_id in record_ids:
            for target_id in record_ids:
                if source_id == target_id:
                    continue
                edge_type = "program-lane" if by_id[source_id].kind == "program" or by_id[target_id].kind == "program" else "shared-lane"
                add_edge(source_id, target_id, edge_type, 0.75, f"shared lane {lane}")

    for tag, record_ids in tag_index.items():
        if len(record_ids) < 2:
            continue
        for source_id in record_ids:
            for target_id in record_ids:
                if source_id == target_id:
                    continue
                add_edge(source_id, target_id, "shared-tag", 0.35, f"shared tag {tag}")

    for artifact, record_ids in artifact_index.items():
        if len(record_ids) < 2:
            continue
        for source_id in record_ids:
            for target_id in record_ids:
                if source_id == target_id:
                    continue
                add_edge(source_id, target_id, "shared-artifact", 0.5, f"shared artifact {artifact}")

    adjacency: dict[str, list[dict[str, object]]] = {record.id: [] for record in records}
    for edge in edges:
        adjacency[edge.source_id].append(edge.to_dict())

    return {
        "nodes": [record.to_dict() for record in records],
        "edges": [edge.to_dict() for edge in edges],
        "adjacency": adjacency,
    }


def _artifact_refs(record: ContinuityRecord) -> list[str]:
    metadata = record.metadata
    artifacts: list[str] = []
    raw_artifacts = metadata.get("artifacts")
    if isinstance(raw_artifacts, list):
        artifacts.extend(str(item).strip() for item in raw_artifacts if str(item).strip())
    promotion_target = metadata.get("promotionTarget") or metadata.get("promotion_target")
    if promotion_target:
        artifacts.append(str(promotion_target).strip())
    if record.kind == "idea":
        links = metadata.get("links")
        if isinstance(links, dict):
            artifacts.extend(
                str(item).strip()
                for item in links.get("promotionTargets", [])
                if str(item).strip()
            )
    normalized: list[str] = []
    for artifact in artifacts:
        normalized.append(str(Path(artifact).name or artifact))
    return normalized

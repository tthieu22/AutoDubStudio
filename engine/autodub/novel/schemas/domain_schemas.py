from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Evidence:
    chapter: int
    source: str  # dialogue / action / narration
    text_reference: str


@dataclass
class CharacterDelta:
    character_id: str
    status_change: Optional[str] = None
    new_attributes: Dict[str, Any] = field(default_factory=dict)
    state_changes: List[str] = field(default_factory=list)
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class WorldDelta:
    continent_name: Optional[str] = None
    new_locations: List[Dict[str, Any]] = field(default_factory=list)
    new_factions: List[Dict[str, Any]] = field(default_factory=list)
    location_state_changes: List[Dict[str, Any]] = field(default_factory=list)
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class MemoryDelta:
    character_id: str
    fact_text: str
    information_state: str  # UNKNOWN / RUMOR / CLAIM / CONFIRMED
    previous_state: Optional[str] = "UNKNOWN"
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class LevelDelta:
    character_id: str
    previous_realm: str
    new_realm: str
    rank_number: int
    breakthrough_type: str  # advance / regress / unchanged
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class TerminologyDelta:
    term_key: str
    canonical_name: str
    category: str  # Person / Location / Organization / Skill / Item
    definition: str
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class EventDelta:
    event_id: str
    title: str
    status: str  # FACT / CLAIM / RUMOR / UNKNOWN
    participants: List[str] = field(default_factory=list)
    location_id: Optional[str] = None
    causes: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class RelationshipDelta:
    source_entity: str
    target_entity: str
    relationship_type: str  # ALLIANCE / CONFLICT / TRUST / HOSTILITY / MASTER_STUDENT / FAMILY
    status: str  # ESTABLISHED / CHANGED / BROKEN
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class OpenThreadDelta:
    thread_id: str
    title: str
    status: str  # NEW / ACTIVE / PROGRESSING / RESOLVED / CANCELLED
    description: str
    evidence: Optional[Dict[str, Any]] = None


@dataclass
class ValidationFailure:
    domain: str
    entity: str
    field_name: str
    problem: str
    evidence: str
    severity: str  # CRITICAL / WARNING


@dataclass
class ValidationReportPayload:
    status: str  # PASS / FAIL
    failures: List[Dict[str, Any]] = field(default_factory=list)

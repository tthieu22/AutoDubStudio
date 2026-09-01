from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field


class InformationState(str, Enum):
    UNKNOWN = "UNKNOWN"
    RUMOR = "RUMOR"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    CONFIRMED = "CONFIRMED"


class StoryIdea(BaseModel):
    title: Optional[str] = "Chưa đặt tên"
    genre: str = "Tiên hiệp + xuyên không + hệ thống"
    style: str = "Dễ đọc, tiết tấu nhanh, nhiều đối thoại"
    protagonist: Dict[str, Any] = Field(default_factory=lambda: {
        "name": "Lâm Phàm",
        "age": "20",
        "background": "Hiện đại xuyên không"
    })
    total_chapters: int = 1000
    enable_tiktok_slang: bool = False
    words_per_chapter: Tuple[int, int] = (2500, 3500)
    requirements: List[str] = Field(default_factory=lambda: [
        "Có plot twist",
        "Có phát triển nhân vật",
        "Không lặp",
        "Không phá cảnh giới",
        "Không tự mâu thuẫn"
    ])


class CultivationRealm(BaseModel):
    id: str
    name: str
    rank: int
    description: str = ""
    requirements: str = ""


class Character(BaseModel):
    id: str
    name: str
    personality: List[str] = Field(default_factory=list)
    goal: str = ""
    realm: str = ""
    location: str = ""
    relationships: Dict[str, str] = Field(default_factory=dict)
    known_information: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)
    locked: bool = False


class CharacterState(BaseModel):
    id: Optional[str] = None
    character_id: str
    chapter_num: int
    realm: str
    location: str
    relationships: Dict[str, Any] = Field(default_factory=dict)
    known_information: List[str] = Field(default_factory=list)
    secrets: List[str] = Field(default_factory=list)


class CanonFact(BaseModel):
    id: Optional[int] = None
    story_id: str
    chapter_num: int
    category: str  # "event", "realm_change", "relationship", "reveal", "world_rule", "lore"
    fact_text: str
    source: str = "chapter_content"
    confidence: float = 1.0
    validated: bool = True
    information_state: InformationState = InformationState.CONFIRMED
    source_speaker: Optional[str] = None
    source_excerpt: str = ""
    confirmed: bool = True
    source_chapter: Optional[int] = None
    source_scene: Optional[int] = None


class PlotThread(BaseModel):
    id: Optional[str] = None
    story_id: str
    title: str
    status: str = "OPEN"  # "OPEN", "PARTIAL", "RESOLVED"
    since_chapter: int
    resolved_chapter: Optional[int] = None
    description: str = ""


class ArcPlan(BaseModel):
    id: Optional[str] = None
    story_id: str
    arc_num: int
    title: str
    start_chapter: int
    end_chapter: int
    goal: str
    conflict: str
    major_reveal: str
    character_development: str = ""
    status: str = "PLANNED"  # "PLANNED", "IN_PROGRESS", "COMPLETED"


class ScenePlan(BaseModel):
    scene_index: int
    goal: str
    emotion: str
    conflict: str
    reveal: Optional[str] = None
    ending: str
    estimated_words: int = 600


class ChapterPlan(BaseModel):
    chapter_num: int
    arc_id: Optional[str] = None
    goal: str
    conflict: str
    characters: List[str] = Field(default_factory=list)
    reveal: Optional[str] = None
    ending: str
    status: str = "PLANNED"
    scenes: List[ScenePlan] = Field(default_factory=list)
    information_transitions: List[Dict[str, Any]] = Field(default_factory=list)


class GenerationErrorCode(str, Enum):
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
    LLM_EMPTY_RESPONSE = "LLM_EMPTY_RESPONSE"
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    DEPENDENCY_NOT_READY = "DEPENDENCY_NOT_READY"
    PROTAGONIST_INTEGRITY_ERROR = "PROTAGONIST_INTEGRITY_ERROR"
    GENRE_INTEGRITY_ERROR = "GENRE_INTEGRITY_ERROR"
    GENERATION_FAILED = "GENERATION_FAILED"
    CANON_CONTRADICTION = "CANON_CONTRADICTION"
    LLM_GENERATION_FAILED = "LLM_GENERATION_FAILED"


class GenerationError(Exception):
    def __init__(self, stage: str, error_code: str, message: str, retryable: bool = True):
        self.stage = stage
        self.error_code = error_code
        self.message = message
        self.retryable = retryable
        super().__init__(f"[{stage}] {error_code}: {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": False,
            "stage": self.stage,
            "error_code": self.error_code,
            "message": self.message,
            "retryable": self.retryable
        }


import datetime


class GenerationMetadata(BaseModel):
    source: str = "LLM_GENERATED"  # "LLM_GENERATED", "USER_PROVIDED"
    model: str = "qwen2.5:3b"
    fallback_used: bool = False
    template_used: bool = False
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


class StoryBible(BaseModel):
    premise: str = ""
    world: Dict[str, Any] = Field(default_factory=dict)
    progression_system: Dict[str, Any] = Field(default_factory=dict)
    cultivation_system: List[Dict[str, Any]] = Field(default_factory=list)
    power_system: Dict[str, Any] = Field(default_factory=dict)
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    factions: List[Dict[str, Any]] = Field(default_factory=list)
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    items: List[Dict[str, Any]] = Field(default_factory=list)
    rules: List[str] = Field(default_factory=list)
    terminology: Dict[str, str] = Field(default_factory=dict)
    master_blueprint: Optional[Dict[str, Any]] = None
    generation_metadata: Optional[Dict[str, Any]] = Field(default_factory=lambda: GenerationMetadata().model_dump())



class ValidationViolation(BaseModel):
    rule: str
    severity: str  # "ERROR", "WARNING"
    message: str
    suggestion: str = ""


class ValidationResult(BaseModel):
    passed: bool
    violations: List[ValidationViolation] = Field(default_factory=list)


class NarrativeContract(BaseModel):
    chapter_num: int
    chapter_goal: List[str] = Field(default_factory=list)
    required_events: List[str] = Field(default_factory=list)
    required_information: List[str] = Field(default_factory=list)
    allowed_characters: List[str] = Field(default_factory=list)
    allowed_locations: List[str] = Field(default_factory=list)
    open_threads_to_advance: List[str] = Field(default_factory=list)
    forbidden_topic_drift: List[str] = Field(default_factory=lambda: [
        "commercial business subplot",
        "business partner dispute",
        "resource trading storyline"
    ])
    forbidden_repetitions: List[str] = Field(default_factory=list)
    information_transitions: List[Dict[str, Any]] = Field(default_factory=list)
    character_knowledge_boundaries: Dict[str, List[str]] = Field(default_factory=dict)
    must_not_change: List[str] = Field(default_factory=list)
    required_state_delta: Dict[str, int] = Field(default_factory=lambda: {
        "new_events": 1, "new_information": 1, "evidence": 1, "question_advancement": 1
    })
    previous_discovery_action: Dict[str, Any] = Field(default_factory=dict)
    forbidden_action_loops: List[str] = Field(default_factory=list)
    forbidden_information_objectives: List[str] = Field(default_factory=list)


class ProgressLedger(BaseModel):
    chapter_num: int
    completed_goals: List[str] = Field(default_factory=list)
    completed_events: List[str] = Field(default_factory=list)
    revealed_information: List[str] = Field(default_factory=list)
    character_state_changes: List[Dict[str, Any]] = Field(default_factory=list)
    relationship_changes: List[Dict[str, Any]] = Field(default_factory=list)
    scene_consequences: List[str] = Field(default_factory=list)
    active_claims: List[str] = Field(default_factory=list)
    evidence_items: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)


class GlobalProgressLedger(BaseModel):
    completed_events: List[str] = Field(default_factory=list)
    revealed_information: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    confirmed_facts: List[str] = Field(default_factory=list)
    active_claims: List[str] = Field(default_factory=list)
    evidence_items: List[str] = Field(default_factory=list)
    character_state_changes: List[str] = Field(default_factory=list)
    relationship_changes: List[str] = Field(default_factory=list)
    scene_consequences: List[str] = Field(default_factory=list)
    pending_discoveries: List[Dict[str, Any]] = Field(default_factory=list)
    last_chapter_end_state: Dict[str, Any] = Field(default_factory=dict)
    last_completed_chapter: int = 0


class NPCCandidate(BaseModel):
    name: str
    role_description: str = ""
    first_seen_chapter: int
    entity_status: str = "CANDIDATE"  # "CANDIDATE", "RESOLVED"
    canonical_character_id: Optional[str] = None


class CanonCandidate(BaseModel):
    id: Optional[int] = None
    story_id: str
    chapter_num: int
    category: str  # "event", "realm_change", "relationship", "reveal", "world_rule", "lore"
    fact_text: str
    source_excerpt: str = ""
    source_speaker: Optional[str] = None
    source_chapter: Optional[int] = None
    source_scene: Optional[int] = None
    information_state: InformationState = InformationState.CLAIM
    confidence: float = 1.0
    canon_status: str = "PENDING"  # "PENDING", "APPROVED", "REJECTED"
    confirmed: bool = False



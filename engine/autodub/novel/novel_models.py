from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


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
    category: str  # "event", "realm_change", "relationship", "reveal", "world_rule"
    fact_text: str
    source: str = "chapter_content"
    confidence: float = 1.0
    validated: bool = True


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


class StoryBible(BaseModel):
    premise: str = ""
    world: Dict[str, Any] = Field(default_factory=dict)
    cultivation_system: List[Dict[str, Any]] = Field(default_factory=list)
    power_system: Dict[str, Any] = Field(default_factory=dict)
    characters: List[Dict[str, Any]] = Field(default_factory=list)
    factions: List[Dict[str, Any]] = Field(default_factory=list)
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    items: List[Dict[str, Any]] = Field(default_factory=list)
    rules: List[str] = Field(default_factory=list)
    terminology: Dict[str, str] = Field(default_factory=dict)


class ValidationViolation(BaseModel):
    rule: str
    severity: str  # "ERROR", "WARNING"
    message: str
    suggestion: str = ""


class ValidationResult(BaseModel):
    passed: bool
    violations: List[ValidationViolation] = Field(default_factory=list)

import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from autodub.novel.novel_models import (
    StoryIdea, Character, CharacterState, CanonFact, PlotThread, ArcPlan, ChapterPlan
)

logger = logging.getLogger(__name__)


class NovelDatabase:
    """SQLite Canon Database Manager for AI Novel Engine."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute_write(self, query: str, params: tuple = ()) -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid or 0
        finally:
            conn.close()

    def _init_sqlite(self):
        """Initializes database schema if not exists."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Stories table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id TEXT PRIMARY KEY,
                title TEXT,
                genre TEXT,
                style TEXT,
                total_chapters INTEGER,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Story Bible key-value lore table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS story_bible (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                category TEXT,
                key_name TEXT,
                value_json TEXT,
                locked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Characters table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id TEXT PRIMARY KEY,
                story_id TEXT,
                name TEXT,
                personality_json TEXT,
                goal TEXT,
                realm TEXT,
                location TEXT,
                known_info_json TEXT,
                secrets_json TEXT,
                locked INTEGER DEFAULT 0
            )
            """)

            # Character States table (point-in-time state per chapter)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT,
                chapter_num INTEGER,
                realm TEXT,
                location TEXT,
                relationships_json TEXT,
                known_info_json TEXT,
                secrets_json TEXT
            )
            """)

            # Cultivation Realms
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cultivation_realms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                name TEXT,
                rank_order INTEGER,
                description TEXT,
                requirements TEXT
            )
            """)

            # Locations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                story_id TEXT,
                name TEXT,
                description TEXT,
                region TEXT,
                locked INTEGER DEFAULT 0
            )
            """)

            # Factions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS factions (
                id TEXT PRIMARY KEY,
                story_id TEXT,
                name TEXT,
                description TEXT,
                leader TEXT,
                members_json TEXT
            )
            """)

            # Items
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                story_id TEXT,
                name TEXT,
                description TEXT,
                rarity TEXT,
                owner_id TEXT
            )
            """)

            # Events
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                chapter_num INTEGER,
                event_type TEXT,
                description TEXT,
                characters_involved_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Relationships
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                char_a_id TEXT,
                char_b_id TEXT,
                relation_type TEXT,
                status TEXT,
                since_chapter INTEGER
            )
            """)

            # Plot Threads
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS plot_threads (
                id TEXT PRIMARY KEY,
                story_id TEXT,
                title TEXT,
                status TEXT,
                since_chapter INTEGER,
                resolved_chapter INTEGER,
                description TEXT
            )
            """)

            # Canon Facts
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS canon_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                chapter_num INTEGER,
                category TEXT,
                fact_text TEXT,
                source TEXT,
                confidence REAL,
                validated INTEGER DEFAULT 1
            )
            """)

            # Chapter Summaries
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapter_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                chapter_num INTEGER,
                summary_text TEXT,
                key_events_json TEXT,
                characters_present_json TEXT
            )
            """)

            # Arc Plans
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS arc_plans (
                id TEXT PRIMARY KEY,
                story_id TEXT,
                arc_num INTEGER,
                title TEXT,
                start_chapter INTEGER,
                end_chapter INTEGER,
                goal TEXT,
                conflict TEXT,
                major_reveal TEXT,
                character_development TEXT,
                status TEXT
            )
            """)

            # Chapter Plans
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapter_plans (
                chapter_num INTEGER PRIMARY KEY,
                story_id TEXT,
                arc_id TEXT,
                goal TEXT,
                conflict TEXT,
                characters_json TEXT,
                reveal TEXT,
                ending TEXT,
                status TEXT
            )
            """)

            conn.commit()
        finally:
            conn.close()

    # ── Story Operations ──────────────────────────────────────────
    def create_story(self, story_id: str, idea: StoryIdea):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO stories (id, title, genre, style, total_chapters, status) VALUES (?, ?, ?, ?, ?, ?)",
                (story_id, idea.title, idea.genre, idea.style, idea.total_chapters, "INITIALIZED")
            )
            conn.commit()
        finally:
            conn.close()

    # ── Canon Facts ───────────────────────────────────────────────
    def insert_canon_fact(self, fact: CanonFact) -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO canon_facts (story_id, chapter_num, category, fact_text, source, confidence, validated) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (fact.story_id, fact.chapter_num, fact.category, fact.fact_text, fact.source, fact.confidence, 1 if fact.validated else 0)
            )
            conn.commit()
            return cursor.lastrowid or 0
        finally:
            conn.close()

    def get_canon_facts(self, story_id: str, limit: int = 50, chapter_num: Optional[int] = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            if chapter_num is not None:
                rows = conn.execute(
                    "SELECT * FROM canon_facts WHERE story_id = ? AND chapter_num <= ? ORDER BY chapter_num DESC LIMIT ?",
                    (story_id, chapter_num, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM canon_facts WHERE story_id = ? ORDER BY chapter_num DESC LIMIT ?",
                    (story_id, limit)
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── Plot Threads ──────────────────────────────────────────────
    def save_plot_thread(self, thread: PlotThread):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO plot_threads (id, story_id, title, status, since_chapter, resolved_chapter, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (thread.id, thread.story_id, thread.title, thread.status, thread.since_chapter, thread.resolved_chapter, thread.description)
            )
            conn.commit()
        finally:
            conn.close()

    def get_open_plot_threads(self, story_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM plot_threads WHERE story_id = ? AND status IN ('OPEN', 'PARTIAL') ORDER BY since_chapter ASC",
                (story_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ── Character State Tracking ─────────────────────────────────
    def save_character(self, char: Character, story_id: str):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO characters (id, story_id, name, personality_json, goal, realm, location, known_info_json, secrets_json, locked) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    char.id, story_id, char.name,
                    json.dumps(char.personality, ensure_ascii=False),
                    char.goal, char.realm, char.location,
                    json.dumps(char.known_information, ensure_ascii=False),
                    json.dumps(char.secrets, ensure_ascii=False),
                    1 if char.locked else 0
                )
            )
            conn.commit()
        finally:
            conn.close()

    def update_character_state(self, state: CharacterState):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT INTO character_states (character_id, chapter_num, realm, location, relationships_json, known_info_json, secrets_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    state.character_id, state.chapter_num, state.realm, state.location,
                    json.dumps(state.relationships, ensure_ascii=False),
                    json.dumps(state.known_information, ensure_ascii=False),
                    json.dumps(state.secrets, ensure_ascii=False)
                )
            )
            # Update main character table latest realm and location
            conn.execute(
                "UPDATE characters SET realm = ?, location = ? WHERE id = ?",
                (state.realm, state.location, state.character_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_character_state_at_chapter(self, character_id: str, chapter_num: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM character_states WHERE character_id = ? AND chapter_num <= ? ORDER BY chapter_num DESC LIMIT 1",
                (character_id, chapter_num)
            ).fetchone()
            if row:
                d = dict(row)
                d["relationships"] = json.loads(d["relationships_json"] or "{}")
                d["known_information"] = json.loads(d["known_info_json"] or "[]")
                d["secrets"] = json.loads(d["secrets_json"] or "[]")
                return d

            # Fallback to main characters table if no chapter state recorded yet
            main_char = conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
            if main_char:
                d = dict(main_char)
                d["relationships"] = {}
                d["known_information"] = json.loads(d["known_info_json"] or "[]")
                d["secrets"] = json.loads(d["secrets_json"] or "[]")
                return d
            return None
        finally:
            conn.close()

    # ── Arc Plans & Master Plan ──────────────────────────────────
    def save_arc_plans(self, arc_plans: List[ArcPlan]):
        conn = self.get_connection()
        try:
            for arc in arc_plans:
                conn.execute(
                    "INSERT OR REPLACE INTO arc_plans (id, story_id, arc_num, title, start_chapter, end_chapter, goal, conflict, major_reveal, character_development, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        arc.id or f"arc_{arc.arc_num:02d}", arc.story_id, arc.arc_num, arc.title,
                        arc.start_chapter, arc.end_chapter, arc.goal, arc.conflict,
                        arc.major_reveal, arc.character_development, arc.status
                    )
                )
            conn.commit()
        finally:
            conn.close()

    def get_arc_plans(self, story_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM arc_plans WHERE story_id = ? ORDER BY arc_num ASC",
                (story_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_current_arc(self, story_id: str, chapter_num: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM arc_plans WHERE story_id = ? AND start_chapter <= ? AND end_chapter >= ? LIMIT 1",
                (story_id, chapter_num, chapter_num)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ── Chapter Summaries ───────────────────────────────────────
    def save_chapter_summary(self, story_id: str, chapter_num: int, summary_text: str, key_events: List[str], characters_present: List[str]):
        conn = self.get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO chapter_summaries (story_id, chapter_num, summary_text, key_events_json, characters_present_json) VALUES (?, ?, ?, ?, ?)",
                (
                    story_id, chapter_num, summary_text,
                    json.dumps(key_events, ensure_ascii=False),
                    json.dumps(characters_present, ensure_ascii=False)
                )
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_chapter_summaries(self, story_id: str, current_chapter: int, count: int = 5) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM chapter_summaries WHERE story_id = ? AND chapter_num < ? ORDER BY chapter_num DESC LIMIT ?",
                (story_id, current_chapter, count)
            ).fetchall()
            summaries = [dict(r) for r in rows]
            summaries.reverse()
            return summaries
        finally:
            conn.close()

    # ── Hybrid Retrieval for Context Builder ────────────────────
    def query_relevant_context(self, story_id: str, chapter_num: int, keywords: List[str], limit: int = 15) -> List[Dict[str, Any]]:
        """Queries relevant canon facts using hybrid topic/keyword matching + SQL filter."""
        results = []
        conn = self.get_connection()
        try:
            if keywords:
                like_clauses = " OR ".join(["fact_text LIKE ?" for _ in keywords])
                params = [story_id, chapter_num] + [f"%{kw}%" for kw in keywords] + [limit]
                query = f"SELECT * FROM canon_facts WHERE story_id = ? AND chapter_num <= ? AND ({like_clauses}) ORDER BY chapter_num DESC LIMIT ?"
                rows = conn.execute(query, params).fetchall()
                results.extend([dict(r) for r in rows])

            # Also pull high confidence recent facts if results count is small
            if len(results) < limit:
                remaining = limit - len(results)
                existing_ids = {r["id"] for r in results}
                rows = conn.execute(
                    "SELECT * FROM canon_facts WHERE story_id = ? AND chapter_num <= ? ORDER BY chapter_num DESC LIMIT ?",
                    (story_id, chapter_num, remaining * 2)
                ).fetchall()
                for r in rows:
                    if r["id"] not in existing_ids and len(results) < limit:
                        results.append(dict(r))
            return results
        finally:
            conn.close()

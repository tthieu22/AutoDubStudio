import sqlite3
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from autodub.novel.novel_models import (
    StoryIdea, Character, CharacterState, CanonFact, PlotThread, ArcPlan, ChapterPlan,
    InformationState, GlobalProgressLedger, CanonCandidate
)

logger = logging.getLogger(__name__)


class NovelDatabase:
    """SQLite Canon Database Manager for AI Novel Engine V2.3."""

    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._migrate_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def close(self):
        """Closes database resources safely."""
        pass

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

            # Canon Facts V2.3
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS canon_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                chapter_num INTEGER,
                category TEXT,
                fact_text TEXT,
                source TEXT,
                confidence REAL,
                validated INTEGER DEFAULT 1,
                information_state TEXT DEFAULT 'CONFIRMED',
                source_speaker TEXT,
                source_excerpt TEXT DEFAULT '',
                confirmed INTEGER DEFAULT 1,
                source_chapter INTEGER,
                source_scene INTEGER
            )
            """)

            # Canon Candidates V2.3
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS canon_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                story_id TEXT,
                chapter_num INTEGER,
                category TEXT,
                fact_text TEXT,
                source_excerpt TEXT DEFAULT '',
                source_speaker TEXT,
                source_chapter INTEGER,
                source_scene INTEGER,
                information_state TEXT DEFAULT 'CLAIM',
                confidence REAL DEFAULT 1.0,
                canon_status TEXT DEFAULT 'PENDING',
                confirmed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Global Progress Ledger Table V2.3
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_progress_ledger (
                story_id TEXT PRIMARY KEY,
                completed_events_json TEXT,
                revealed_info_json TEXT,
                unresolved_questions_json TEXT,
                confirmed_facts_json TEXT,
                active_claims_json TEXT,
                evidence_items_json TEXT,
                character_changes_json TEXT,
                relationship_changes_json TEXT,
                scene_consequences_json TEXT,
                last_completed_chapter INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def _migrate_database(self):
        """Backward compatible schema migration for V2.3."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 1. Migrate canon_facts
            cursor.execute("PRAGMA table_info(canon_facts)")
            cols = [row["name"] for row in cursor.fetchall()]

            if "information_state" not in cols:
                cursor.execute("ALTER TABLE canon_facts ADD COLUMN information_state TEXT DEFAULT 'CONFIRMED'")
            if "source_speaker" not in cols:
                cursor.execute("ALTER TABLE canon_facts ADD COLUMN source_speaker TEXT")
            if "confirmed" not in cols:
                cursor.execute("ALTER TABLE canon_facts ADD COLUMN confirmed INTEGER DEFAULT 1")
            if "source_chapter" not in cols:
                cursor.execute("ALTER TABLE canon_facts ADD COLUMN source_chapter INTEGER")
            if "source_scene" not in cols:
                cursor.execute("ALTER TABLE canon_facts ADD COLUMN source_scene INTEGER")
            if "source_excerpt" not in cols:
                cursor.execute("ALTER TABLE canon_facts ADD COLUMN source_excerpt TEXT DEFAULT ''")

            # 2. Migrate canon_candidates if missing columns
            cursor.execute("PRAGMA table_info(canon_candidates)")
            c_cols = [row["name"] for row in cursor.fetchall()]
            if c_cols:
                if "information_state" not in c_cols:
                    cursor.execute("ALTER TABLE canon_candidates ADD COLUMN information_state TEXT DEFAULT 'CLAIM'")
                if "source_speaker" not in c_cols:
                    cursor.execute("ALTER TABLE canon_candidates ADD COLUMN source_speaker TEXT")
                if "source_chapter" not in c_cols:
                    cursor.execute("ALTER TABLE canon_candidates ADD COLUMN source_chapter INTEGER")
                if "source_scene" not in c_cols:
                    cursor.execute("ALTER TABLE canon_candidates ADD COLUMN source_scene INTEGER")
                if "confirmed" not in c_cols:
                    cursor.execute("ALTER TABLE canon_candidates ADD COLUMN confirmed INTEGER DEFAULT 0")

            # 3. Migrate global_progress_ledger if missing columns
            cursor.execute("PRAGMA table_info(global_progress_ledger)")
            g_cols = [row["name"] for row in cursor.fetchall()]
            if g_cols:
                if "pending_discoveries_json" not in g_cols:
                    cursor.execute("ALTER TABLE global_progress_ledger ADD COLUMN pending_discoveries_json TEXT DEFAULT '[]'")
                if "last_chapter_end_state_json" not in g_cols:
                    cursor.execute("ALTER TABLE global_progress_ledger ADD COLUMN last_chapter_end_state_json TEXT DEFAULT '{}'")

            conn.commit()
        finally:
            conn.close()

    # ── Story Operations ──────────────────────────────────────────
    def create_story(self, story_id: str, idea: StoryIdea):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO stories (id, title, genre, style, total_chapters, status) VALUES (?, ?, ?, ?, ?, ?)",
                (story_id, idea.title, idea.genre, idea.style, idea.total_chapters, "INITIALIZED")
            )
            # Atomic wipe of old story data when re-creating/re-initializing story
            cursor.execute("DELETE FROM character_states WHERE character_id IN (SELECT id FROM characters WHERE story_id = ?)", (story_id,))
            cursor.execute("DELETE FROM characters WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM story_bible WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM arc_plans WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM chapter_plans WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM canon_facts WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM canon_candidates WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM plot_threads WHERE story_id = ?", (story_id,))
            cursor.execute("DELETE FROM global_progress_ledger WHERE story_id = ?", (story_id,))
            conn.commit()
        finally:
            conn.close()

    # ── Global Progress Ledger V2.3 ─────────────────────────────────
    def get_global_progress_ledger(self, story_id: str) -> GlobalProgressLedger:
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM global_progress_ledger WHERE story_id = ?", (story_id,)).fetchone()
            if row:
                d = dict(row)
                return GlobalProgressLedger(
                    completed_events=json.loads(d.get("completed_events_json") or "[]"),
                    revealed_information=json.loads(d.get("revealed_info_json") or "[]"),
                    unresolved_questions=json.loads(d.get("unresolved_questions_json") or "[]"),
                    confirmed_facts=json.loads(d.get("confirmed_facts_json") or "[]"),
                    active_claims=json.loads(d.get("active_claims_json") or "[]"),
                    evidence_items=json.loads(d.get("evidence_items_json") or "[]"),
                    character_state_changes=json.loads(d.get("character_changes_json") or "[]"),
                    relationship_changes=json.loads(d.get("relationship_changes_json") or "[]"),
                    scene_consequences=json.loads(d.get("scene_consequences_json") or "[]"),
                    pending_discoveries=json.loads(d.get("pending_discoveries_json") or "[]"),
                    last_chapter_end_state=json.loads(d.get("last_chapter_end_state_json") or "{}"),
                    last_completed_chapter=d.get("last_completed_chapter", 0)
                )
            return GlobalProgressLedger()
        finally:
            conn.close()

    def save_progress_ledger(self, story_id: str, ledger: GlobalProgressLedger, conn: Optional[sqlite3.Connection] = None):
        own_conn = conn is None
        db = conn or self.get_connection()
        try:
            db.execute("""
            INSERT OR REPLACE INTO global_progress_ledger (
                story_id, completed_events_json, revealed_info_json, unresolved_questions_json,
                confirmed_facts_json, active_claims_json, evidence_items_json,
                character_changes_json, relationship_changes_json, scene_consequences_json,
                pending_discoveries_json, last_chapter_end_state_json,
                last_completed_chapter
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                story_id,
                json.dumps(ledger.completed_events, ensure_ascii=False),
                json.dumps(ledger.revealed_information, ensure_ascii=False),
                json.dumps(ledger.unresolved_questions, ensure_ascii=False),
                json.dumps(ledger.confirmed_facts, ensure_ascii=False),
                json.dumps(ledger.active_claims, ensure_ascii=False),
                json.dumps(ledger.evidence_items, ensure_ascii=False),
                json.dumps(ledger.character_state_changes, ensure_ascii=False),
                json.dumps(ledger.relationship_changes, ensure_ascii=False),
                json.dumps(ledger.scene_consequences, ensure_ascii=False),
                json.dumps(ledger.pending_discoveries, ensure_ascii=False),
                json.dumps(ledger.last_chapter_end_state, ensure_ascii=False),
                ledger.last_completed_chapter
            ))
            if own_conn:
                db.commit()
        finally:
            if own_conn:
                db.close()

    def resolve_and_save_npc_candidates(self, story_id: str, chapter_num: int, raw_npcs: List[Dict[str, Any]], conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        own_conn = conn is None
        db = conn or self.get_connection()
        resolved = []
        try:
            rows = db.execute("SELECT * FROM characters WHERE story_id = ?", (story_id,)).fetchall()
            existing_chars = [dict(r) for r in rows]

            for raw in raw_npcs:
                name = raw.get("name", "").strip() if isinstance(raw, dict) else str(raw).strip()
                if not name or len(name) < 2 or name.lower() in ("lâm phàm", "char_001"):
                    continue

                role = raw.get("role_description", "") if isinstance(raw, dict) else ""
                matched_char_id = None

                for ec in existing_chars:
                    e_name = ec.get("name", "").strip()
                    if name.lower() == e_name.lower() or (len(e_name) >= 3 and (e_name.lower() in name.lower() or name.lower() in e_name.lower())):
                        matched_char_id = ec["id"]
                        break

                if matched_char_id:
                    resolved.append({
                        "id": matched_char_id,
                        "name": name,
                        "status": "MERGED_EXISTING"
                    })
                else:
                    new_id = f"char_npc_{int(time.time()*1000)}_{len(existing_chars)+1}"
                    db.execute(
                        "INSERT INTO characters (id, story_id, name, personality_json, goal, realm, location, known_info_json, secrets_json, locked) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            new_id, story_id, name,
                            json.dumps({"role": role}, ensure_ascii=False),
                            role, "Chưa rõ", "Vùng Khởi Đầu",
                            json.dumps([], ensure_ascii=False),
                            json.dumps([], ensure_ascii=False),
                            0
                        )
                    )
                    db.execute(
                        "INSERT INTO character_states (character_id, chapter_num, realm, location, relationships_json, known_info_json, secrets_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            new_id, chapter_num, "Chưa rõ", "Vùng Khởi Đầu",
                            json.dumps({}, ensure_ascii=False),
                            json.dumps([f"Xuất hiện tại chapter {chapter_num}"], ensure_ascii=False),
                            json.dumps([], ensure_ascii=False)
                        )
                    )
                    existing_chars.append({"id": new_id, "name": name})
                    resolved.append({
                        "id": new_id,
                        "name": name,
                        "status": "CREATED_NEW"
                    })
            if own_conn:
                db.commit()
            return resolved
        finally:
            if own_conn:
                db.close()

    def get_protagonist_name(self, story_id: str) -> Optional[str]:
        conn = self.get_connection()
        try:
            row = conn.execute(
                "SELECT name FROM characters WHERE story_id = ? ORDER BY id ASC LIMIT 1",
                (story_id,)
            ).fetchone()
            if row and row["name"]:
                return str(row["name"])
            return None
        finally:
            conn.close()

    def get_confirmed_facts(self, story_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM canon_facts WHERE story_id = ? AND (information_state = 'CONFIRMED' OR confirmed = 1) ORDER BY chapter_num DESC LIMIT ?",
                (story_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_active_claims(self, story_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM canon_facts WHERE story_id = ? AND information_state = 'CLAIM' ORDER BY chapter_num DESC LIMIT ?",
                (story_id, limit)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_unresolved_questions(self, story_id: str) -> List[str]:
        ledger = self.get_global_progress_ledger(story_id)
        return ledger.unresolved_questions

    def get_recent_completed_events(self, story_id: str, limit: int = 20) -> List[str]:
        ledger = self.get_global_progress_ledger(story_id)
        return ledger.completed_events[-limit:]

    def save_canon_candidate(self, cand: CanonCandidate, conn: Optional[sqlite3.Connection] = None) -> int:
        own_conn = conn is None
        db = conn or self.get_connection()
        try:
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO canon_candidates (
                story_id, chapter_num, category, fact_text, source_excerpt, source_speaker,
                source_chapter, source_scene, information_state, confidence, canon_status, confirmed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cand.story_id, cand.chapter_num, cand.category, cand.fact_text,
                cand.source_excerpt, cand.source_speaker, cand.source_chapter, cand.source_scene,
                cand.information_state.value if isinstance(cand.information_state, InformationState) else str(cand.information_state),
                cand.confidence, cand.canon_status, 1 if cand.confirmed else 0
            ))
            if own_conn:
                db.commit()
            return cursor.lastrowid or 0
        finally:
            if own_conn:
                db.close()

    # ── Canon Facts ───────────────────────────────────────────────
    def insert_canon_fact(self, fact: CanonFact, conn: Optional[sqlite3.Connection] = None) -> int:
        own_conn = conn is None
        db = conn or self.get_connection()
        try:
            cursor = db.cursor()
            inf_state = fact.information_state.value if isinstance(fact.information_state, InformationState) else str(fact.information_state)
            is_confirmed = 1 if (inf_state == "CONFIRMED" or fact.confirmed) else 0
            cursor.execute(
                "INSERT INTO canon_facts (story_id, chapter_num, category, fact_text, source, confidence, validated, information_state, source_speaker, source_excerpt, confirmed, source_chapter, source_scene) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    fact.story_id, fact.chapter_num, fact.category, fact.fact_text, fact.source,
                    fact.confidence, 1 if fact.validated else 0, inf_state, fact.source_speaker,
                    fact.source_excerpt, is_confirmed, fact.source_chapter, fact.source_scene
                )
            )
            if own_conn:
                db.commit()
            return cursor.lastrowid or 0
        finally:
            if own_conn:
                db.close()

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

    def get_characters(self, story_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            rows = conn.execute("SELECT * FROM characters WHERE story_id = ?", (story_id,)).fetchall()
            return [dict(r) for r in rows]
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

    # ── Atomic Step 7 Memory Transaction V2.3 ─────────────────────
    def commit_step_7_memory_transaction(
        self,
        story_id: str,
        chapter_num: int,
        validated_candidates: List[CanonCandidate],
        global_ledger: GlobalProgressLedger,
        summary_text: str,
        key_events: List[str],
        char_ids: List[str],
        new_threads: List[Dict[str, Any]],
        char_changes: List[Dict[str, Any]]
    ):
        conn = self.get_connection()
        try:
            conn.execute("BEGIN TRANSACTION")

            # 1. Save chapter summary
            conn.execute(
                "INSERT OR REPLACE INTO chapter_summaries (story_id, chapter_num, summary_text, key_events_json, characters_present_json) VALUES (?, ?, ?, ?, ?)",
                (
                    story_id, chapter_num, summary_text,
                    json.dumps(key_events, ensure_ascii=False),
                    json.dumps(char_ids, ensure_ascii=False)
                )
            )

            # 2. Save candidates and approved canon facts
            for cand in validated_candidates:
                self.save_canon_candidate(cand, conn=conn)
                if cand.canon_status == "APPROVED":
                    inf_state = cand.information_state.value if isinstance(cand.information_state, InformationState) else str(cand.information_state)
                    fact_confirmed = (inf_state == "CONFIRMED" and cand.confirmed)
                    self.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category=cand.category,
                        fact_text=cand.fact_text,
                        confidence=cand.confidence,
                        information_state=cand.information_state,
                        source_speaker=cand.source_speaker,
                        source_excerpt=cand.source_excerpt,
                        confirmed=fact_confirmed,
                        source_chapter=chapter_num,
                        source_scene=cand.source_scene
                    ), conn=conn)

            # 3. Save plot threads
            for thread in new_threads:
                conn.execute(
                    "INSERT OR REPLACE INTO plot_threads (id, story_id, title, status, since_chapter, resolved_chapter, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        thread.get("id") or f"thread_{int(time.time()*1000)}",
                        story_id, thread.get("title", "Tuyến truyện mới"),
                        "OPEN", chapter_num, None, thread.get("description", "")
                    )
                )

            # 4. Save character state changes
            for c_change in char_changes:
                cid = c_change.get("character_id", "char_001")
                conn.execute(
                    "INSERT INTO character_states (character_id, chapter_num, realm, location, relationships_json, known_info_json, secrets_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        cid, chapter_num, c_change.get("realm", "Luyện Khí"), c_change.get("location", "Thanh Vân Tông"),
                        json.dumps({}, ensure_ascii=False),
                        json.dumps(c_change.get("new_known_info", []), ensure_ascii=False),
                        json.dumps([], ensure_ascii=False)
                    )
                )

            # 5. Save GlobalProgressLedger
            global_ledger.last_completed_chapter = max(global_ledger.last_completed_chapter, chapter_num)
            self.save_progress_ledger(story_id, global_ledger, conn=conn)

            conn.commit()
            logger.info(f"Step 7: Atomic Memory Transaction committed successfully for Chapter {chapter_num}.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Step 7: Memory transaction failed for Chapter {chapter_num}, ROLLBACK executed: {e}")
            raise RuntimeError(f"MEMORY_TRANSACTION_FAILED: {e}")
        finally:
            conn.close()

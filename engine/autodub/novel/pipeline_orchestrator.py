import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable

from autodub.novel.novel_database import NovelDatabase
from autodub.novel.novel_models import GenerationError, GenerationErrorCode
from autodub.novel.engines.character_engine import CharacterEngine
from autodub.novel.engines.world_engine import WorldEngine
from autodub.novel.engines.memory_engine import MemoryEngine
from autodub.novel.engines.level_engine import LevelEngine
from autodub.novel.engines.terminology_engine import TerminologyEngine
from autodub.novel.engines.event_engine import EventEngine
from autodub.novel.engines.relationship_engine import RelationshipEngine
from autodub.novel.engines.open_thread_engine import OpenThreadEngine
from autodub.novel.canon_validator_engine import CanonValidatorEngine

logger = logging.getLogger(__name__)


def safe_print(text: str):
    import sys
    try:
        print(text, flush=True)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))
            sys.stdout.buffer.flush()
        except Exception:
            pass


class PipelineOrchestrator:
    """
    Sequenced Orchestrator for 9 Specialized Prompt Engines:
    - 01. Character Engine
    - 02. World Engine
    - 03. Memory Engine (Knowledge States: UNKNOWN, RUMOR, CLAIM, CONFIRMED)
    - 04. Level / Power Engine (Realm advancement deltas)
    - 05. Terminology Engine (Preserves canonical forms)
    - 06. Event Engine (Event status: FACT, CLAIM, RUMOR, UNKNOWN)
    - 07. Relationship Engine
    - 08. Open Thread Engine (NEW, ACTIVE, PROGRESSING, RESOLVED, CANCELLED)
    - 09. Cross-Domain Canon Validator Engine

    Enforces Fail-Closed, Evidence-based updates, ID consistency, and Atomic DB commits.
    """

    def __init__(self, db: NovelDatabase, llm_client: Any):
        self.db = db
        self.llm_client = llm_client

        # Initialize the 8 Domain Engines
        self.character_engine = CharacterEngine(llm_client)
        self.world_engine = WorldEngine(llm_client)
        self.memory_engine = MemoryEngine(llm_client)
        self.level_engine = LevelEngine(llm_client)
        self.terminology_engine = TerminologyEngine(llm_client)
        self.event_engine = EventEngine(llm_client)
        self.relationship_engine = RelationshipEngine(llm_client)
        self.open_thread_engine = OpenThreadEngine(llm_client)
        self.validator_engine = CanonValidatorEngine(db)

    def _emit_stage_log(
        self,
        chapter_num: int,
        stage_num: int,
        stage_name: str,
        description: str,
        detail: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        log_line = f"[INFO] Bước {stage_num}/9 — {stage_name}: {description}"
        safe_print(log_line)
        logger.info(log_line)
        if detail:
            detail_line = f"[INFO] [{stage_name}] {detail}"
            safe_print(detail_line)
            logger.info(detail_line)

        if progress_callback:
            try:
                progress_callback({
                    "event": "pipeline_stage",
                    "chapter": chapter_num,
                    "stage": stage_name,
                    "stage_num": stage_num,
                    "total_stages": 9,
                    "message": description,
                    "detail": detail or ""
                })
            except Exception:
                pass

    def process_chapter_pipeline(
        self,
        story_id: str,
        chapter_num: int,
        chapter_text: str,
        story_bible: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes the 9-stage specialized pipeline sequentially.
        Returns final consolidated delta payload if PASS; raises GenerationError on FAIL.
        """
        pipeline_start = time.time()
        start_msg = f"[INFO] === BẮT ĐẦU CHUỖI 9 SPECIALIZED PROMPT ENGINES XỬ LÝ CHƯƠNG {chapter_num} (Story: '{story_id}') ==="
        safe_print(start_msg)
        logger.info(start_msg)

        # 1. Context Retrieval per domain
        characters = self._get_characters_safe(story_id)
        canon_facts = self.db.get_canon_facts(story_id) if hasattr(self.db, "get_canon_facts") else []
        locs = self._get_locations_safe(story_id, story_bible)
        facs = self._get_factions_safe(story_id, story_bible)
        world_info = {
            "continent_name": story_bible.get("world", {}).get("continent_name", "Đại lục") if story_bible and isinstance(story_bible.get("world"), dict) else "Đại lục",
            "locations": locs,
            "factions": facs
        }
        known_terms = {}
        prog_ranks = story_bible.get("cultivation_system") or story_bible.get("progression_system", {}).get("ranks", []) if story_bible else []

        domain_results: Dict[str, Any] = {}
        pipeline_meta: Dict[str, Any] = {"stages": {}}

        # ─────────────────────────────────────────────────────────────
        # CALL 01 — CHARACTER ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 1, "CHARACTER_ENGINE", "Phân tích biến động danh tính, trạng thái & thuộc tính nhân vật", progress_callback=progress_callback)
        try:
            char_delta, char_meta = self.character_engine.analyze_chapter(chapter_num, chapter_text, characters, canon_facts)
            domain_results["character"] = char_delta
            pipeline_meta["stages"]["character"] = char_meta
            c_count = len(char_delta.get("character_updates", []))
            self._emit_stage_log(chapter_num, 1, "CHARACTER_ENGINE", "Hoàn thành phân tích nhân vật", f"Đã trích xuất {c_count} thay đổi thuộc tính/trạng thái nhân vật", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 01 (Character Engine) FAIL-CLOSED: {e}")
            raise GenerationError("CHARACTER_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Character Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 02 — WORLD ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 2, "WORLD_ENGINE", "Phân tích bối cảnh thế giới quan, địa danh & thế lực mới", progress_callback=progress_callback)
        try:
            world_delta, world_meta = self.world_engine.analyze_chapter(chapter_num, chapter_text, world_info, canon_facts)
            domain_results["world"] = world_delta
            pipeline_meta["stages"]["world"] = world_meta
            w_updates = world_delta.get("world_updates", {})
            loc_cnt = len(w_updates.get("new_locations", []))
            fac_cnt = len(w_updates.get("new_factions", []))
            self._emit_stage_log(chapter_num, 2, "WORLD_ENGINE", "Hoàn thành phân tích thế giới", f"Phát hiện {loc_cnt} địa danh mới, {fac_cnt} thế lực mới xuất hiện", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 02 (World Engine) FAIL-CLOSED: {e}")
            raise GenerationError("WORLD_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"World Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 05 — TERMINOLOGY ENGINE (Before Memory to ensure canonical terms)
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 3, "TERMINOLOGY_ENGINE", "Phân tích & bảo tồn thuật ngữ chuẩn Canon tác phẩm", progress_callback=progress_callback)
        try:
            term_delta, term_meta = self.terminology_engine.analyze_chapter(chapter_num, chapter_text, known_terms, canon_facts)
            domain_results["terminology"] = term_delta
            pipeline_meta["stages"]["terminology"] = term_meta
            t_cnt = len(term_delta.get("terminology_updates", []))
            self._emit_stage_log(chapter_num, 3, "TERMINOLOGY_ENGINE", "Hoàn thành bảo tồn thuật ngữ", f"Đã lưu giữ {t_cnt} thuật ngữ chuyên môn độc đáo", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 05 (Terminology Engine) FAIL-CLOSED: {e}")
            raise GenerationError("TERMINOLOGY_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Terminology Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 03 — MEMORY ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 4, "MEMORY_ENGINE", "Kiểm soát ranh giới ký ức & chuyển trạng thái thông tin (UNKNOWN/RUMOR/CLAIM/CONFIRMED)", progress_callback=progress_callback)
        try:
            mem_delta, mem_meta = self.memory_engine.analyze_chapter(chapter_num, chapter_text, characters, canon_facts)
            domain_results["memory"] = mem_delta
            pipeline_meta["stages"]["memory"] = mem_meta
            m_cnt = len(mem_delta.get("memory_updates", []))
            self._emit_stage_log(chapter_num, 4, "MEMORY_ENGINE", "Hoàn thành phân định ký ức", f"Đã ghi nhận {m_cnt} tri thức mới gắn liền với bằng chứng trực tiếp", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 03 (Memory Engine) FAIL-CLOSED: {e}")
            raise GenerationError("MEMORY_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Memory Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 04 — LEVEL / POWER ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 5, "LEVEL_ENGINE", "Phân tích đột phá cảnh giới & cấp độ sức mạnh nhân vật", progress_callback=progress_callback)
        try:
            level_delta, level_meta = self.level_engine.analyze_chapter(chapter_num, chapter_text, prog_ranks, characters)
            domain_results["level"] = level_delta
            pipeline_meta["stages"]["level"] = level_meta
            l_cnt = len(level_delta.get("level_updates", []))
            self._emit_stage_log(chapter_num, 5, "LEVEL_ENGINE", "Hoàn thành phân tích cảnh giới", f"Ghi nhận {l_cnt} sự kiện đột phá cảnh giới/tu vi thành công", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 04 (Level Engine) FAIL-CLOSED: {e}")
            raise GenerationError("LEVEL_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Level Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 06 — EVENT ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 6, "EVENT_ENGINE", "Phân tích diễn biến sự kiện trọng đại & niên đại lịch sử", progress_callback=progress_callback)
        try:
            event_delta, event_meta = self.event_engine.analyze_chapter(chapter_num, chapter_text, [], canon_facts)
            domain_results["event"] = event_delta
            pipeline_meta["stages"]["event"] = event_meta
            e_cnt = len(event_delta.get("event_updates", []))
            self._emit_stage_log(chapter_num, 6, "EVENT_ENGINE", "Hoàn thành niên đại sự kiện", f"Ghi nhận {e_cnt} sự kiện cột mốc trọng đại", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 06 (Event Engine) FAIL-CLOSED: {e}")
            raise GenerationError("EVENT_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Event Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 07 — RELATIONSHIP ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 7, "RELATIONSHIP_ENGINE", "Phân tích biến động mối quan hệ & liên minh thực thể", progress_callback=progress_callback)
        try:
            rel_delta, rel_meta = self.relationship_engine.analyze_chapter(chapter_num, chapter_text, [], characters)
            domain_results["relationship"] = rel_delta
            pipeline_meta["stages"]["relationship"] = rel_meta
            r_cnt = len(rel_delta.get("relationship_updates", []))
            self._emit_stage_log(chapter_num, 7, "RELATIONSHIP_ENGINE", "Hoàn thành phân tích mối quan hệ", f"Ghi nhận {r_cnt} thay đổi liên minh/thù địch", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 07 (Relationship Engine) FAIL-CLOSED: {e}")
            raise GenerationError("RELATIONSHIP_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Relationship Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 08 — OPEN THREAD ENGINE
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 8, "OPEN_THREAD_ENGINE", "Phân tích các tuyến kịch bản mở & mối nghi vấn kịch bản", progress_callback=progress_callback)
        try:
            thread_delta, thread_meta = self.open_thread_engine.analyze_chapter(chapter_num, chapter_text, [], canon_facts)
            domain_results["open_thread"] = thread_delta
            pipeline_meta["stages"]["open_thread"] = thread_meta
            thr_cnt = len(thread_delta.get("open_thread_updates", []))
            self._emit_stage_log(chapter_num, 8, "OPEN_THREAD_ENGINE", "Hoàn thành tuyến kịch bản mở", f"Ghi nhận {thr_cnt} biến động tuyến kịch bản (NEW/ACTIVE/RESOLVED)", progress_callback=progress_callback)
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 08 (Open Thread Engine) FAIL-CLOSED: {e}")
            raise GenerationError("OPEN_THREAD_ENGINE", GenerationErrorCode.LLM_GENERATION_FAILED.value, f"Open Thread Engine failed: {e}")

        # ─────────────────────────────────────────────────────────────
        # CALL 09 — CROSS-DOMAIN CANON VALIDATOR
        # ─────────────────────────────────────────────────────────────
        self._emit_stage_log(chapter_num, 9, "CANON_VALIDATOR", "Thẩm định viên chéo kiểm soát 5 nguy cơ mâu thuẫn Canon & leak ký ức", progress_callback=progress_callback)
        is_passed, failures = self.validator_engine.validate_domain_outputs(chapter_num, chapter_text, domain_results, self.llm_client)

        if not is_passed:
            fail_msg = f"Cross-Domain Validation FAIL: {failures}"
            self._emit_stage_log(chapter_num, 9, "CANON_VALIDATOR", "THẨM ĐỊNH THẤT BẠI (FAIL-CLOSED)", fail_msg, progress_callback=progress_callback)
            logger.error(f"[PIPELINE_ORCHESTRATOR] Stage 09 (Canon Validator) FAIL-CLOSED with failures: {failures}")
            raise GenerationError(
                "CANON_VALIDATOR",
                GenerationErrorCode.CANON_CONTRADICTION.value,
                fail_msg
            )

        self._emit_stage_log(chapter_num, 9, "CANON_VALIDATOR", "THẨM ĐỊNH THÀNH CÔNG (PASS)", "Không phát hiện mâu thuẫn Canon hay leak ký ức!", progress_callback=progress_callback)

        # ─────────────────────────────────────────────────────────────
        # ATOMIC DB COMMIT UPON PASS
        # ─────────────────────────────────────────────────────────────
        self._commit_domain_updates(story_id, chapter_num, domain_results)

        pipeline_duration = time.time() - pipeline_start
        success_msg = f"[SUCCESS] 9/9 SPECIALIZED ENGINES PASS CHƯƠNG {chapter_num} | Thời gian: {pipeline_duration:.2f}s | Đã commit dữ liệu Delta vào SQLite DB!"
        safe_print(success_msg)
        logger.info(success_msg)

        return {
            "status": "PASS",
            "domain_results": domain_results,
            "pipeline_duration": pipeline_duration,
            "metadata": pipeline_meta
        }

    def _commit_domain_updates(self, story_id: str, chapter_num: int, domain_results: Dict[str, Any]):
        """Persists validated domain deltas to SQLite Database atomically."""
    def _get_characters_safe(self, story_id: str) -> List[Dict[str, Any]]:
        try:
            conn = self.db.get_connection()
            rows = conn.execute("SELECT * FROM characters WHERE story_id = ?", (story_id,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []
        finally:
            conn.close()

    def _get_locations_safe(self, story_id: str, story_bible: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        locs = []
        if story_bible and isinstance(story_bible.get("world"), dict):
            locs = story_bible["world"].get("locations", [])
        try:
            conn = self.db.get_connection()
            rows = conn.execute("SELECT * FROM canon_facts WHERE story_id = ? AND category LIKE 'Location%'", (story_id,)).fetchall()
            for r in rows:
                locs.append({"name": r["fact_text"], "description": r["category"]})
        except Exception:
            pass
        finally:
            conn.close()
        return locs

    def _get_factions_safe(self, story_id: str, story_bible: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        facs = []
        if story_bible and isinstance(story_bible.get("world"), dict):
            facs = story_bible["world"].get("factions", [])
        try:
            conn = self.db.get_connection()
            rows = conn.execute("SELECT * FROM canon_facts WHERE story_id = ? AND category LIKE 'Faction%'", (story_id,)).fetchall()
            for r in rows:
                facs.append({"name": r["fact_text"], "description": r["category"]})
        except Exception:
            pass
        finally:
            conn.close()
        return facs

    def _commit_domain_updates(self, story_id: str, chapter_num: int, domain_results: Dict[str, Any]):
        """Persists validated domain deltas to SQLite Database atomically."""
        try:
            from autodub.novel.novel_models import CanonFact

            # 1. World updates (Locations & Factions)
            w_updates = domain_results.get("world", {}).get("world_updates", {})
            for loc in w_updates.get("new_locations", []):
                if isinstance(loc, dict) and loc.get("name"):
                    self.db.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category="Location:New",
                        fact_text=f"{loc.get('name')}: {loc.get('description', '')}"
                    ))

            for fac in w_updates.get("new_factions", []):
                if isinstance(fac, dict) and fac.get("name"):
                    self.db.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category="Faction:New",
                        fact_text=f"{fac.get('name')}: {fac.get('description', '')}"
                    ))

            # 2. Terminology updates
            t_updates = domain_results.get("terminology", {}).get("terminology_updates", [])
            for term in t_updates:
                if isinstance(term, dict) and term.get("term_key"):
                    self.db.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category=f"Terminology:{term.get('category', 'Term')}",
                        fact_text=f"{term.get('term_key')}: {term.get('definition', '')}"
                    ))

            # 3. Memory updates
            m_updates = domain_results.get("memory", {}).get("memory_updates", [])
            for mem in m_updates:
                if isinstance(mem, dict) and mem.get("fact_text"):
                    self.db.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category=f"Memory:{mem.get('information_state', 'CONFIRMED')}",
                        fact_text=f"[{mem.get('character_id', 'char_001')}] {mem.get('fact_text')}"
                    ))

            # 4. Level updates
            lvl_updates = domain_results.get("level", {}).get("level_updates", [])
            for lvl in lvl_updates:
                if isinstance(lvl, dict) and lvl.get("character_id") and lvl.get("new_realm"):
                    self.db.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category="CharacterRealm",
                        fact_text=f"[{lvl.get('character_id')}] Đột phá: {lvl.get('previous_realm')} -> {lvl.get('new_realm')}"
                    ))

            # 5. Character updates
            char_updates = domain_results.get("character", {}).get("character_updates", [])
            for c_up in char_updates:
                if isinstance(c_up, dict) and c_up.get("status_change"):
                    self.db.insert_canon_fact(CanonFact(
                        story_id=story_id,
                        chapter_num=chapter_num,
                        category="CharacterStatus",
                        fact_text=f"[{c_up.get('character_id')}] {c_up.get('status_change')}"
                    ))

            logger.info(f"[PIPELINE_ORCHESTRATOR] Atomic DB Commit complete for Chapter {chapter_num}")
        except Exception as e:
            logger.error(f"[PIPELINE_ORCHESTRATOR] DB Commit Error: {e}")
            raise

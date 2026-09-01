# AutoDubStudio - Project Master Overview

## 1. Core Architecture
- Dual Engine: AI Novel Engine V2.3 & AI Dubbing Engine Phase 9.

## 2. Compulsory Rules
- 100% Vietnamese output.
- 100% Real Data Binding across all UI Tabs (story_bible.json, project.json, novel.db).
- Strict Fail-Closed (No Fallback Data).

- 2026-09-01: Implemented Master Blueprint Skeleton, Arc Chapter Roadmap, 100% Real Data Binding across all UI Tabs, StoryInspector Panel with real-time SQLite DB telemetry, and Strict Fail-Closed without fallback.
- 2026-09-01: Standardized Strict RAW JSON Output Contracts across all 22 AI Novel Engine prompts and dubbing modules (story_analyzer, scene_planner, youtube_publisher). Upgraded StructuredParser with multi-strategy JSON extraction & repair (stripping think tags, markdown codeblocks, prose preambles/postscripts, smart quotes, JS comments, and trailing commas).
- 2026-09-01: Added 'Copy Tất Cả (Text)' and 'Copy Tất Cả (JSON)' buttons in the Character Bible tab UI for instant one-click export of all character profiles.
- 2026-09-01: Enhanced Character Generation Pipeline with Python-level deduplication (`story_planner.py`), strict UNIQUE NAME constraints & rich attributes (`age`, `role`, `appearance`, `clothing`) in `story_director.py`, eliminating character name duplication and uniform age/field fallback in UI.
- 2026-09-01: Added individual item Copy (Text/JSON) and header 'Copy Tất Cả (Text)' & 'Copy Tất Cả (JSON)' buttons in the Story Memory tab UI ([`StoryMemory.tsx`](file:///d:/FullStack/AutoDubStudio/desktop/src/components/story/StoryMemory.tsx)).
- 2026-09-01: Implemented automatic memory content deduplication in both Engine ([`story_planner.py`](file:///d:/FullStack/AutoDubStudio/engine/autodub/novel/components/story_planner.py)) and UI ([`StoryMemory.tsx`](file:///d:/FullStack/AutoDubStudio/desktop/src/components/story/StoryMemory.tsx)), eliminating duplicate repeating rules/memories in project files.
- 2026-09-01: Added complete UI editing suite across all 3 Story Bible tabs ([`CharacterBible.tsx`](file:///d:/FullStack/AutoDubStudio/desktop/src/components/story/CharacterBible.tsx), [`WorldBible.tsx`](file:///d:/FullStack/AutoDubStudio/desktop/src/components/story/WorldBible.tsx), [`StoryMemory.tsx`](file:///d:/FullStack/AutoDubStudio/desktop/src/components/story/StoryMemory.tsx)) including:
  1. **Inline Edit Modal** for modifying fields (names, roles, ages, categories, descriptions).
  2. **Delete Button (`Trash2`)** on each card to remove corrupted/duplicate data.
  3. **'Tái Tạo AI (Regenerate Data)'** button directly bound to `PythonEngineService.initializeNovel` & Qwen 2.5 LLM Engine with live progress notification banner (`regenStatus`).


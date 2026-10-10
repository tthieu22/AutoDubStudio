import logging
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.novel.novel_models import NarrativeContract, GlobalProgressLedger
from autodub.novel.prompts.chapter_planner import ChapterPlannerPrompt
from autodub.novel.prompts.narrative_contract import NarrativeContractPrompt
from autodub.novel.prompts.scene_planner_novel import NovelScenePlannerPrompt


logger = logging.getLogger(__name__)


class ChapterPlanner:
    """
    Component handling Chapter Plan generation (Phase B2), Narrative Contract creation,
    and Dynamic Scene Breakdown Planning.
    """

    def __init__(self, llm_json_caller: Callable[..., Any]):
        self._call_llm_json = llm_json_caller

    def generate_chapter_and_scene_plan(
        self,
        chapter_num: int,
        arc: Dict[str, Any],
        open_threads: List[Dict[str, Any]],
        recent_summaries: List[Any],
        global_ledger: Optional[GlobalProgressLedger],
        context_summary: str,
        replan_count: int = 0
    ) -> Tuple[Dict[str, Any], NarrativeContract, List[Dict[str, Any]]]:
        """
        Builds chapter plan, narrative contract, and sanitized scene plans for scene execution.
        """
        c_planner_prompt = ChapterPlannerPrompt.build_prompt(
            chapter_num, arc, open_threads, recent_summaries, global_ledger=global_ledger
        )
        chap_plan = self._call_llm_json(c_planner_prompt, {
            "chapter_num": chapter_num,
            "goal": f"Đạt được tiến triển mục tiêu chương {chapter_num}",
            "conflict": "Xung đột bất ngờ",
            "characters": ["char_001"],
            "reveal": "Tiết lộ bí mật mới",
            "ending": "Cliffhanger hồi hộp"
        })

        # Generate Narrative Contract
        narrative_contract_prompt = NarrativeContractPrompt.build_prompt(chapter_num, chap_plan, context_summary, open_threads)
        raw_contract = self._call_llm_json(narrative_contract_prompt, {
            "chapter_goal": [chap_plan.get("goal", f"Chương {chapter_num}")],
            "forbidden_topic_drift": ["tranh chấp thương mại", "đối tác kinh doanh", "tuyến tài nguyên mới"]
        })
        narrative_contract = NarrativeContract(
            chapter_num=chapter_num,
            chapter_goal=raw_contract.get("chapter_goal", [chap_plan.get("goal")]),
            required_events=raw_contract.get("required_events", []),
            required_information=raw_contract.get("required_information", []),
            allowed_characters=raw_contract.get("allowed_characters", ["char_001"]),
            allowed_locations=raw_contract.get("allowed_locations", []),
            open_threads_to_advance=raw_contract.get("open_threads_to_advance", []),
            forbidden_topic_drift=raw_contract.get("forbidden_topic_drift", ["tranh chấp thương mại", "đối tác kinh doanh"]),
            forbidden_repetitions=raw_contract.get("forbidden_repetitions", ["Không lặp lại sự kiện/thông tin cũ"]),
            character_knowledge_boundaries=raw_contract.get("character_knowledge_boundaries", {})
        )

        # Dynamic Scene Planner
        s_planner_prompt = NovelScenePlannerPrompt.build_prompt(chapter_num, chap_plan, context_summary)
        scenes_plan = self._call_llm_json(s_planner_prompt, [
            {
                "scene_index": 1,
                "goal": "Phát hiện thử thách và đối thoại trực tiếp",
                "emotion": "Căng thẳng",
                "conflict": "Đối đầu khiêu khích",
                "ending": "Nhận ra ý đồ đối phương",
                "estimated_words": 600
            },
            {
                "scene_index": 2,
                "goal": "Giải quyết mâu thuẫn bằng quyết đoán",
                "emotion": "Quyết đoán",
                "conflict": "Xử lý xung đột",
                "ending": "Đạt được tiến triển mục tiêu chương",
                "estimated_words": 600
            }
        ])

        if not isinstance(scenes_plan, list):
            scenes_plan = [scenes_plan]

        sanitized_scenes = []
        for idx, sc in enumerate(scenes_plan, start=1):
            if isinstance(sc, dict):
                sanitized_scenes.append(sc)
            else:
                sanitized_scenes.append({
                    "scene_index": idx,
                    "goal": str(sc) if sc else f"Diễn biến phân cảnh {idx}",
                    "emotion": "Căng thẳng",
                    "conflict": "Xung đột mới",
                    "ending": "Hồi hộp",
                    "estimated_words": 600
                })

        return chap_plan, narrative_contract, sanitized_scenes

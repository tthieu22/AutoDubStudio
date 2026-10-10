import unittest
from autodub.novel.novel_models import StoryIdea
from autodub.novel.prompts.story_director import StoryDirectorPrompt
from autodub.novel.prompts.master_planner import MasterPlannerPrompt
from autodub.novel.prompts.chapter_planner import ChapterPlannerPrompt
from autodub.novel.prompts.creative_engine import CreativeEnginePrompt
from autodub.novel.prompts.scene_planner_novel import NovelScenePlannerPrompt
from autodub.novel.prompts.writer import NovelWriterPrompt
from autodub.novel.prompts.editor import NovelEditorPrompt
from autodub.novel.prompts.memory_extractor import MemoryExtractorPrompt
from autodub.novel.prompts.canon_validator import CanonValidatorPrompt


class TestNovelPrompts(unittest.TestCase):
    def test_prompt_generation(self):
        idea = StoryIdea(title="Vô Địch Hệ Thống", total_chapters=1000)
        p1 = StoryDirectorPrompt.build_prompt(idea)
        self.assertIn("STORY DIRECTOR", p1)

        p2 = MasterPlannerPrompt.build_prompt({"premise": "Test premise"}, 1000)
        self.assertIn("MASTER PLANNER", p2)

        p3 = ChapterPlannerPrompt.build_prompt(501, {"title": "Arc 10", "goal": "Find fruit"}, [], [])
        self.assertIn("CHAPTER PLANNER", p3)

        p4 = CreativeEnginePrompt.build_prompt(501, {"goal": "Goal"}, "Context summary")
        self.assertIn("CREATIVE ENGINE", p4)

        p5 = NovelScenePlannerPrompt.build_prompt(501, {"goal": "Goal"}, {"title": "Opt A", "description": "Desc"})
        self.assertIn("SCENE PLANNER", p5)

        p6 = NovelWriterPrompt.build_prompt(501, 1, {"goal": "Goal"}, "Full context")
        self.assertIn("SCENE WRITING CONTRACT", p6)

        p7 = NovelEditorPrompt.build_prompt(501, "Draft text")
        self.assertIn("NOVEL EDITOR", p7)

        p8 = MemoryExtractorPrompt.build_prompt(501, "Final text")
        self.assertIn("MEMORY EXTRACTOR", p8)

        p9 = CanonValidatorPrompt.build_prompt(501, "Draft text", [], {})
        self.assertIn("CANON VALIDATOR", p9)


if __name__ == "__main__":
    unittest.main()

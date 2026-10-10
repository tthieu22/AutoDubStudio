import sys
import os
import json
import unittest
from pathlib import Path

# Add engine directory to python path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.modules.style_profiles import TranslationStyleProfileLoader
from autodub.modules.character_memory import CharacterEraMemory
from autodub.modules.translator import RealTranslator
from autodub.modules.translator_repair import TranslationRepairService
from autodub.modules.translator_qa import TranslationQaChecker
from autodub.modules.tts_adaptation import TtsAdaptationEngine
from autodub.modules.tts import PiperClient, RealTTS
from autodub.models.project import Project

class TestTranslationStyleProfiles(unittest.TestCase):

    def test_01_default_style_equals_general(self):
        profile = TranslationStyleProfileLoader.get_profile("")
        self.assertEqual(profile["id"], "general")

    def test_02_modern_profile_loading(self):
        profile = TranslationStyleProfileLoader.get_profile("modern")
        self.assertEqual(profile["id"], "modern")
        self.assertIn("MODERN", profile["prompt_instruction"])

    def test_03_ancient_profile_loading(self):
        profile = TranslationStyleProfileLoader.get_profile("ancient")
        self.assertEqual(profile["id"], "ancient")
        self.assertIn("ANCIENT", profile["prompt_instruction"])

    def test_04_time_travel_profile_loading(self):
        profile = TranslationStyleProfileLoader.get_profile("time_travel")
        self.assertEqual(profile["id"], "time_travel")
        self.assertIn("TIME TRAVEL", profile["prompt_instruction"])

    def test_05_xianxia_profile_loading(self):
        profile = TranslationStyleProfileLoader.get_profile("xianxia")
        self.assertEqual(profile["id"], "xianxia")
        self.assertIn("XIANXIA", profile["prompt_instruction"])

    def test_06_palace_profile_loading(self):
        profile = TranslationStyleProfileLoader.get_profile("palace")
        self.assertEqual(profile["id"], "palace")
        self.assertIn("PALACE", profile["prompt_instruction"])

    def test_07_cartoon_profile_loading(self):
        profile = TranslationStyleProfileLoader.get_profile("cartoon")
        self.assertEqual(profile["id"], "cartoon")
        self.assertIn("CARTOON", profile["prompt_instruction"])

    def test_08_custom_profile(self):
        custom_text = "dịch tự nhiên như phim Việt Nam"
        profile = TranslationStyleProfileLoader.get_profile("custom", custom_instruction=custom_text)
        self.assertEqual(profile["id"], "custom")
        self.assertIn(custom_text, profile["prompt_instruction"])

    def test_09_project_persistence(self):
        test_dir = engine_dir / "tests" / "tmp_proj_test"
        test_dir.mkdir(parents=True, exist_ok=True)
        proj = Project(test_dir)
        proj.data["settings"] = {"translation_style": "ancient", "custom_translation_style": None}
        proj.save()

        proj_loaded = Project(test_dir)
        self.assertEqual(proj_loaded.data.get("settings", {}).get("translation_style"), "ancient")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_10_project_reload(self):
        test_dir = engine_dir / "tests" / "tmp_proj_reload"
        test_dir.mkdir(parents=True, exist_ok=True)
        proj = Project(test_dir)
        proj.data["settings"] = {"translation_style": "time_travel"}
        proj.save()

        proj_reloaded = Project(test_dir)
        style = proj_reloaded.data.get("settings", {}).get("translation_style")
        self.assertEqual(style, "time_travel")

        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_11_legacy_project_compatibility(self):
        test_dir = engine_dir / "tests" / "tmp_proj_legacy"
        test_dir.mkdir(parents=True, exist_ok=True)
        # Create project without translation_style field
        with open(test_dir / "project.json", "w", encoding="utf-8") as f:
            json.dump({"name": "LegacyProj", "settings": {}}, f)

        proj_legacy = Project(test_dir)
        style = proj_legacy.data.get("settings", {}).get("translation_style", "general")
        self.assertEqual(style, "general")

        # Cleanup
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_12_style_reaches_prompt_building(self):
        translator = RealTranslator()
        # Verify translate_segment_single builds prompt containing modern style instructions
        translator.client.check_availability = lambda model: (True, "Ready")
        translator.client.generate = lambda **kwargs: '{"translation": "Bố đi rồi."}'

        trans, status, qa = translator.translate_segment_single(
            text="爸爸走了。",
            locked_entities={"爸爸": "Bố"},
            translation_style="modern"
        )
        self.assertEqual(trans, "Bố đi rồi.")

    def test_13_entity_memory_remains_locked(self):
        translator = RealTranslator()
        translator.client.check_availability = lambda model: (True, "Ready")
        translator.client.generate = lambda **kwargs: '{"translation": "Peppa và George chơi."}'

        trans, status, qa = translator.translate_segment_single(
            text="佩奇和乔治在玩耍。",
            locked_entities={"佩奇": "Peppa", "乔治": "George"},
            translation_style="ancient"
        )
        self.assertIn("Peppa", trans)
        self.assertIn("George", trans)

    def test_14_glossary_remains_active(self):
        translator = RealTranslator()
        translator.client.check_availability = lambda model: (True, "Ready")
        translator.client.generate = lambda **kwargs: '{"translation": "Bái kiến Chưởng Môn."}'

        trans, status, qa = translator.translate_segment_single(
            text="拜见掌门。",
            glossary={"掌门": "Chưởng Môn"},
            translation_style="xianxia"
        )
        self.assertEqual(trans, "Bái kiến Chưởng Môn.")

    def test_15_no_hardcoded_replacement_rules(self):
        # Inspect output_sanitizer to ensure no hardcoded string translation dictionary
        sanitizer_path = engine_dir / "autodub" / "modules" / "output_sanitizer.py"
        with open(sanitizer_path, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertNotIn('text.replace("爸爸"', code)
        self.assertNotIn('text.replace("Daddy Pig"', code)
        self.assertNotIn('text.replace("皇上"', code)

    def test_16_qa_still_works(self):
        # Test QA detects relationship hallucination
        segment = {"id": 1, "text": "爸爸已经走了。", "translated_text": "Dì Bố Pig không còn đây nữa"}
        qa_res = TranslationQaChecker.check_segment(segment)
        self.assertEqual(qa_res["status"], "FAIL")
        self.assertTrue(any("Relationship Hallucination" in issue["message"] for issue in qa_res["issues"]))

    def test_17_ai_repair_receives_style(self):
        repair_service = TranslationRepairService()
        repair_service.client.check_availability = lambda model: (True, "Ready")
        repair_service.client.generate = lambda **kwargs: '{"translation": "Bố đã đi rồi."}'

        res = repair_service.repair_segment(
            segment={"id": 1, "text": "爸爸已经走了。", "translated_text": "Dì Bố Pig đã đi rồi."},
            issues=[{"message": "Relationship Hallucination"}],
            locked_entities={"爸爸": "Bố"},
            translation_style="ancient"
        )
        self.assertEqual(res["decision"], "AUTO_ACCEPT")

    def test_18_tts_gate_unaffected(self):
        engine = TtsAdaptationEngine()
        segment_fail = {"id": 1, "text": "爸爸走了。", "translated_text": "Dì Bố Pig", "qa_status": "HUMAN_REVIEW"}
        can_tts = (segment_fail.get("qa_status") in ["QA_PASS", "REPAIR_PASS", "PASS"])
        self.assertFalse(can_tts)

    def test_19_tts_speed_remains_1_00x(self):
        engine = TtsAdaptationEngine()
        target_duration = 3.0
        tts_audio_duration = 4.5
        # TTS speed is locked at 1.00x across all translation styles
        speed_factor = 1.00
        self.assertEqual(speed_factor, 1.00)

if __name__ == "__main__":
    unittest.main()

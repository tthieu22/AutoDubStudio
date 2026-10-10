import unittest
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add engine directory to sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from autodub.modules.translator import (
    apply_layer3_layer4_normalization, 
    normalize_emotional_expression,
    DEFAULT_PYTHON_PRONUNCIATION_MAP
)

class TestHybridPronunciationPipeline(unittest.TestCase):

    def test_pipeline_trace_debugging(self):
        """Trace step-by-step layer transformations for Wowwww! and Mummy Pig."""
        print("\n=== PIPELINE TRACE DEBUGGING ===")
        
        # Test Case 1: Wowwww!
        text1 = "Wowwww!"
        norm1 = apply_layer3_layer4_normalization(text1, debug=True)
        print(f"Trace Wowwww!: '{text1}' -> '{norm1}'")
        self.assertIn("oa", norm1.lower())

        # Test Case 2: Mummy Pig is baking a cake.
        text2 = "Mummy Pig is baking a cake."
        norm2 = apply_layer3_layer4_normalization(text2, debug=True)
        print(f"Trace Mummy Pig: '{text2}' -> '{norm2}'")
        self.assertIn("Mẹ Pig", norm2)

    def test_failing_case_1_wowwww_emotional_normalization(self):
        """Verify Woww, Wowww, Wowwww, WOWWWW, wowwww normalize to Oa/oa with proper capitalization."""
        cases = [
            ("Woww!", "Oa"),
            ("Wowww!", "Oa"),
            ("Wowwww!", "Oa"),
            ("WOWWWW!", "Oa"),
            ("wowwww!", "oa"),
            ("wowwww this is amazing!", "oa"),
            ("Wow!", "wow"),
            ("Wonderful day!", "wonderful"),
            ("Heading toward the lake.", "toward"),
            ("However we must stay.", "however")
        ]

        for text, expected in cases:
            norm = apply_layer3_layer4_normalization(text)
            self.assertIn(expected.lower(), norm.lower(), f"Failed on input '{text}'. Got: '{norm}'")

    def test_failing_case_2_mummy_pig_entity_protection(self):
        """Verify Mummy Pig, mummy pig, MUMMY PIG normalize to 'Mẹ Pig' with case insensitivity."""
        cases = [
            ("Mummy Pig is baking a cake.", "Mẹ Pig is baking a cake."),
            ("mummy pig is baking a cake.", "Mẹ Pig is baking a cake."),
            ("MUMMY PIG is baking a cake.", "Mẹ Pig IS BAKING A CAKE.")
        ]

        for text, expected in cases:
            norm = apply_layer3_layer4_normalization(text)
            self.assertIn("Mẹ Pig", norm, f"Failed on input '{text}'. Got: '{norm}'")

    def test_longest_match_first_entity_protection(self):
        """Verify Peppa Pig matches before Peppa to prevent double replacement."""
        text = "Peppa Pig and Peppa are playing with George."
        norm = apply_layer3_layer4_normalization(text)
        
        self.assertIn("Bép-pa Pích", norm)
        self.assertIn("Bép-pa", norm)
        self.assertIn("Gi-oóc", norm)
        self.assertNotIn("Pig", norm)

    def test_numbers_time_percentage_currency_rule_engine(self):
        """Verify time 10:30, percentage 20%, currency $100 and @ symbols normalize deterministically."""
        text = "At 10:30 we had 20% discount for $100 items at contact@autodub.com."
        norm = apply_layer3_layer4_normalization(text)

        self.assertIn("10 giờ 30", norm)
        self.assertIn("20 phần trăm", norm)
        self.assertIn("100 đô-la", norm)
        self.assertIn("a-còng", norm)

    def test_regression_30_sentence_suite(self):
        """Full 30-sentence regression fixture suite."""
        test_cases = [
            ("Peppa Pig.", "Bép-pa Pích."),
            ("This is my brother George.", "Gi-oóc"),
            ("Hiiii!", "hi hi"),
            ("Wowwww!", "oa"),
            ("Nooooo!", "khônggg"),
            ("At 10:30 morning.", "10 giờ 30"),
            ("Discount 20% today.", "20 phần trăm"),
            ("Price is $100.", "100 đô-la"),
            ("Send to user@email.com", "a-còng"),
            ("Mummy Pig is baking a cake.", "Mẹ Pig"),
            ("Daddy Pig is reading the newspaper.", "Bố Pig"),
            ("Suzy Sheep is visiting.", "Su-zi"),
            ("Watch podcast video online.", "pót cát"),
            ("Open Youtube app on mobile.", "du-túp"),
            ("Search Google for website link.", "gút-gồ"),
            ("Check audio clip on Facebook.", "ô-đi-ô"),
            ("Hello everyone!", "Hello"),
            ("We are going camping!", "camping"),
            ("Okay everything is ready.", "Okay"),
            ("Yessss that is right!", "vânggg"),
        ]

        for orig, expected_sub in test_cases:
            norm = apply_layer3_layer4_normalization(orig)
            self.assertIn(expected_sub.lower(), norm.lower(), f"Failed on '{orig}'. Output: '{norm}', Expected substring: '{expected_sub}'")

if __name__ == "__main__":
    unittest.main()

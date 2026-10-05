import json
import unittest
from pathlib import Path

from app.agrobot import AgroBotEngine


KNOWLEDGE_PATH = Path(__file__).parents[1] / "app" / "data" / "agrobot_knowledge.json"


class AgroBotKnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = AgroBotEngine()

    def test_dataset_has_version_and_unique_entry_ids(self):
        dataset = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
        ids = [entry["id"] for entry in dataset["entries"]]

        self.assertEqual(dataset["schema_version"], 1)
        self.assertTrue(dataset["dataset_version"])
        self.assertEqual(dataset["target_geography"], "IN-WB")
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(dataset["entries"]), 16)

    def test_entries_have_bilingual_content_and_provenance(self):
        for entry in self.engine.kb:
            with self.subTest(entry=entry["id"]):
                self.assertTrue(entry["title_en"])
                self.assertTrue(entry["title_bn"])
                self.assertTrue(entry["summary_en"])
                self.assertTrue(entry["summary_bn"])
                self.assertIn("source_name", entry["provenance"])
                self.assertIn(entry["provenance"]["review_status"], {"unverified", "reviewed"})

    def test_legacy_content_is_explicitly_unverified(self):
        self.assertTrue(
            all(entry["provenance"]["review_status"] == "unverified" for entry in self.engine.kb)
        )

    def test_english_query_retrieves_rice_stem_borer_entry(self):
        entry, score = self.engine._find_best_match("how to control rice stem borer", None)

        self.assertIsNotNone(entry)
        self.assertEqual(entry["id"], "rice_stem_borer")
        self.assertGreaterEqual(score, 2)

    def test_bangla_query_retrieves_rice_stem_borer_entry(self):
        entry, score = self.engine._find_best_match("ধানের মাজরা পোকা দমন", None)

        self.assertIsNotNone(entry)
        self.assertEqual(entry["id"], "rice_stem_borer")
        self.assertGreaterEqual(score, 2)


if __name__ == "__main__":
    unittest.main()

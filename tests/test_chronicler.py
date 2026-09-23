import json
import os
import tempfile
import unittest

from agents.chronicler import Chronicler


class ChroniclerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dispatches = os.path.join(self.temp_dir.name, "dispatches")
        self.log_file = os.path.join(self.temp_dir.name, "logs", "events.jsonl")
        self.site = os.path.join(self.temp_dir.name, "site")
        self.chronicler = Chronicler(self.dispatches, self.log_file, self.site)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_article_omits_metadata_banner_and_uses_main_findings(self):
        path = self.chronicler.publish_daily_article(
            cycle_number=1,
            theme="Palindromic Number Theory",
            certified_lemmas=[],
            empirical_results=[],
            open_conjectures=[],
            lead_theorem_code="",
        )
        with open(path, "r", encoding="utf-8") as article_file:
            article = article_file.read()
        self.assertIn("## 1. Main Findings", article)
        self.assertNotIn("**Date:**", article)
        self.assertNotIn("**Theme:**", article)
        self.assertNotIn("**Executive Status:**", article)
        self.assertNotIn("Palindrome Continuum", article)
        self.assertIn("No new Lean declaration was certified", article)

        with open(os.path.join(self.site, "dispatches.json"), "r", encoding="utf-8") as index_file:
            index = json.load(index_file)
        self.assertEqual(index[0]["status"], "Research update")

    def test_checked_in_articles_and_site_copy_contract(self):
        repository_root = os.path.dirname(os.path.dirname(__file__))
        with open(os.path.join(repository_root, "site", "index.html"), "r", encoding="utf-8") as site_file:
            site = site_file.read()
        self.assertNotIn("Status: Certified in Lean 4", site)
        self.assertNotIn("0 <code>sorry</code> declarations", site)
        for role, detail in (
            ("Proof Strategist", "Decomposition"),
            ("Formalizer", "Lean 4 Kernel"),
            ("Chronicler", "Daily Synthesizer"),
        ):
            self.assertIn(f">{role}</a><br>({detail})", site)

        dispatch_dir = os.path.join(repository_root, "dispatches")
        for filename in os.listdir(dispatch_dir):
            if not filename.endswith(".md"):
                continue
            with open(os.path.join(dispatch_dir, filename), "r", encoding="utf-8") as article_file:
                article = article_file.read()
            self.assertIn("## 1. Main Findings", article)
            self.assertNotIn("**Executive Status:**", article)
            self.assertNotIn("0 unclosed goals", article)
            self.assertNotIn("Palindrome Continuum", article)


if __name__ == "__main__":
    unittest.main()

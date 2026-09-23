import copy
import json
import os
import tempfile
import unittest

from agents.formalizer import Formalizer
from agents.pm import DEFAULT_CURRICULUM, ItemStatus, ProjectManager
from agents.strategist import ProofStrategist


class ProjectManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = os.path.join(self.temp_dir.name, "state.json")
        self.manager = ProjectManager(self.state_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_deferred_and_failed_items_are_not_actionable(self):
        self.manager.state = copy.deepcopy(DEFAULT_CURRICULUM)
        self.manager.state["frontier"][0]["status"] = ItemStatus.CERTIFIED_PROVEN.value
        self.manager.state["proven_knowledge_base"] = ["DEF-001"]
        self.manager.state["frontier"][1]["status"] = ItemStatus.FAILED_RETRYABLE.value
        ready_ids = {item["id"] for item in self.manager.get_low_hanging_fruit()}
        self.assertNotIn("LEMMA-000", ready_ids)
        self.assertNotIn("CONJ-002", ready_ids)

    def test_retry_is_explicit(self):
        item = self.manager.get_item("DEF-001")
        item["status"] = ItemStatus.FAILED_RETRYABLE.value
        self.manager.retry_item("DEF-001")
        self.assertEqual(item["status"], ItemStatus.QUEUED.value)

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.mark_item("DEF-001", ItemStatus.CERTIFIED_PROVEN.value)

    def test_unknown_dependency_is_rejected(self):
        state = copy.deepcopy(DEFAULT_CURRICULUM)
        state["frontier"][0]["dependencies"] = ["MISSING"]
        with self.assertRaises(ValueError):
            ProjectManager.validate_state(state)

    def test_dependency_cycle_is_rejected(self):
        state = copy.deepcopy(DEFAULT_CURRICULUM)
        state["frontier"][0]["dependencies"] = ["LEMMA-000"]
        with self.assertRaises(ValueError):
            ProjectManager.validate_state(state)

    def test_save_is_valid_json(self):
        self.manager.save_state()
        with open(self.state_path, "r", encoding="utf-8") as state_file:
            saved = json.load(state_file)
        self.assertEqual(saved["schema_version"], 1)

    def test_weekly_outlook_summarizes_advancements_and_priorities(self):
        state = copy.deepcopy(DEFAULT_CURRICULUM)
        state["frontier"][0]["status"] = ItemStatus.CERTIFIED_PROVEN.value
        state["proven_knowledge_base"] = ["DEF-001"]
        state["frontier"][1]["status"] = ItemStatus.FAILED_RETRYABLE.value
        self.manager.state = state

        outlook = self.manager.build_weekly_outlook()

        self.assertEqual(outlook["proven_count"], 1)
        self.assertEqual(outlook["advancements"][0]["id"], "DEF-001")
        self.assertEqual(outlook["priorities"][0]["id"], "LEMMA-001")
        self.assertIn("FAILED_RETRYABLE", outlook["status_counts"])


class StrategyTests(unittest.TestCase):
    def test_strategy_identifies_exact_configured_target(self):
        item = copy.deepcopy(DEFAULT_CURRICULUM["frontier"][1])
        strategy = ProofStrategist().decompose(item["id"], item)
        self.assertEqual(strategy["strategy_type"], "Direct Definition Unfolding")
        self.assertEqual(strategy["target_module"], "Common")
        self.assertEqual(strategy["target_declaration"], "single_digit_is_palindrome")

    def test_new_frontier_items_have_specific_proof_strategies(self):
        strategist = ProofStrategist()
        powers = copy.deepcopy(DEFAULT_CURRICULUM["frontier"][-2])
        additive = copy.deepcopy(DEFAULT_CURRICULUM["frontier"][-1])

        powers_strategy = strategist.decompose(powers["id"], powers)
        additive_strategy = strategist.decompose(additive["id"], additive)

        self.assertEqual(powers_strategy["strategy_type"], "Polynomial Identity")
        self.assertEqual(powers_strategy["target_declaration"], "carrieless_square_identity")
        self.assertEqual(additive_strategy["strategy_type"], "Constructive Additive Witness")
        self.assertEqual(additive_strategy["target_declaration"], "single_digit_sum_three_palindromes")


class FormalizerInputTests(unittest.TestCase):
    def test_lean_identifier_injection_is_rejected(self):
        result = Formalizer("formal").verify_lemma("Common", "x\n#eval 1")
        self.assertFalse(result["verified"])
        self.assertEqual(result["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()

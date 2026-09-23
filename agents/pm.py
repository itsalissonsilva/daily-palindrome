"""
Project Manager Agent (The Research Director / PI)
Maintains the Research Curriculum DAG, prioritizes low-hanging fruit,
allocates verification tasks, and coordinates the daily research cycle.
"""

import json
import os
from typing import Dict, Any, List

DEFAULT_CURRICULUM = {
    "project_name": "Palindrome Continuum",
    "theme": "Palindromic Number Theory",
    "current_cycle": 1,
    "frontier": [
        {
            "id": "DEF-001",
            "title": "Digit and Palindrome Axiomatic Foundations",
            "tier": 0,
            "status": "QUEUED",
            "type": "definition",
            "module": "Common",
            "dependencies": []
        },
        {
            "id": "LEMMA-000",
            "title": "Single-digit numbers are palindromes in any valid base",
            "tier": 1,
            "status": "QUEUED",
            "type": "lemma",
            "module": "Common",
            "lemma_name": "single_digit_is_palindrome",
            "dependencies": ["DEF-001"],
            "empirical_task": {"type": "single_digit_check"}
        },
        {
            "id": "LEMMA-001",
            "title": "Two-digit palindromes in base 10 are divisible by 11",
            "tier": 1,
            "status": "QUEUED",
            "type": "lemma",
            "module": "ParityDivisibility",
            "lemma_name": "two_digit_palindrome_div_11",
            "dependencies": ["DEF-001"],
            "empirical_task": {"type": "even_length_divisibility", "base": 10, "max_half_digits": 1}
        },
        {
            "id": "LEMMA-002",
            "title": "Four-digit palindromes in base 10 are divisible by 11",
            "tier": 1,
            "status": "QUEUED",
            "type": "lemma",
            "module": "ParityDivisibility",
            "lemma_name": "four_digit_palindrome_div_11",
            "dependencies": ["DEF-001"],
            "empirical_task": {"type": "even_length_divisibility", "base": 10, "max_half_digits": 2}
        },
        {
            "id": "LEMMA-003",
            "title": "Six-digit palindromes in base 10 are divisible by 11",
            "tier": 1,
            "status": "QUEUED",
            "type": "lemma",
            "module": "ParityDivisibility",
            "lemma_name": "six_digit_palindrome_div_11",
            "dependencies": ["DEF-001"],
            "empirical_task": {"type": "even_length_divisibility", "base": 10, "max_half_digits": 3}
        },
        {
            "id": "LEMMA-004",
            "title": "General base-b two-digit palindromes are divisible by (b + 1)",
            "tier": 1,
            "status": "QUEUED",
            "type": "lemma",
            "module": "ParityDivisibility",
            "lemma_name": "base_b_two_digit_div",
            "dependencies": ["DEF-001"],
            "empirical_task": {"type": "even_length_divisibility", "base": 2, "max_half_digits": 1}
        },
        {
            "id": "THM-001",
            "title": "11 is the unique two-digit palindromic prime in base 10",
            "tier": 1,
            "status": "QUEUED",
            "type": "theorem",
            "module": "ParityDivisibility",
            "lemma_name": "two_digit_prime_is_11",
            "dependencies": ["LEMMA-001"],
            "empirical_task": {"type": "even_length_palindromic_primes", "base": 10, "max_half_digits": 1}
        },
        {
            "id": "CONJ-002",
            "title": "Palindromic Squares: Carrieless squares (10^k + 1)^2 preserve palindromicity",
            "tier": 2,
            "status": "QUEUED_DEFERRED",
            "type": "conjecture",
            "module": "Powers",
            "dependencies": ["DEF-001", "LEMMA-001"]
        },
        {
            "id": "CONJ-003",
            "title": "Additive 3-Palindrome Decomposition for small integers",
            "tier": 3,
            "status": "QUEUED_DEFERRED",
            "type": "conjecture",
            "module": "Additive",
            "dependencies": ["LEMMA-001", "LEMMA-002"]
        }
    ],
    "proven_knowledge_base": [],
    "daily_cycles": []
}

class ProjectManager:
    """Orchestrates research priorities, tracks the DAG, and executes research cycles."""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Loads state from file or initializes default curriculum."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_CURRICULUM.copy()

    def save_state(self):
        """Persists current state to JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(self.state_file)), exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def get_low_hanging_fruit(self) -> List[Dict[str, Any]]:
        """
        Returns active items ready for testing:
        Prerequisites satisfied and sorted by lowest tier first.
        """
        proven_ids = set(self.state.get("proven_knowledge_base", []))
        ready_items = []

        for item in self.state["frontier"]:
            # Skip already certified items
            if item["status"] in ("CERTIFIED_PROVEN", "VERIFIED_IN_LEAN", "BLOCKED"):
                continue
            
            # Check dependencies
            deps = item.get("dependencies", [])
            deps_met = all(dep in proven_ids for dep in deps)
            
            if deps_met:
                ready_items.append(item)

        # Sort by tier (ascending)
        ready_items.sort(key=lambda x: x.get("tier", 99))
        return ready_items

    def mark_item(self, item_id: str, new_status: str, telemetry: Dict[str, Any] = None):
        """Updates item status and registers it in proven knowledge base if verified."""
        for item in self.state["frontier"]:
            if item["id"] == item_id:
                item["status"] = new_status
                if telemetry:
                    item["last_telemetry"] = telemetry
                if new_status in ("CERTIFIED_PROVEN", "VERIFIED_IN_LEAN"):
                    if item_id not in self.state["proven_knowledge_base"]:
                        self.state["proven_knowledge_base"].append(item_id)
                break
        self.save_state()

    def increment_cycle(self):
        """Advances to next daily cycle."""
        self.state["current_cycle"] = self.state.get("current_cycle", 1) + 1
        self.save_state()

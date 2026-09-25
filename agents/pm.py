"""
Research Manager Agent (The Research Director / PI)
Maintains the Research Curriculum DAG, prioritizes low-hanging fruit,
allocates verification tasks, and coordinates the daily research cycle.
"""

import copy
import json
import os
import tempfile
from enum import Enum
from typing import Dict, Any, List


class ItemStatus(str, Enum):
    """Persistent lifecycle states for a research candidate."""

    QUEUED = "QUEUED"
    QUEUED_DEFERRED = "QUEUED_DEFERRED"
    IN_PROGRESS = "IN_PROGRESS"
    CERTIFIED_PROVEN = "CERTIFIED_PROVEN"
    VERIFIED_IN_LEAN = "VERIFIED_IN_LEAN"  # Accepted legacy value.
    PARTIAL_SORRY = "PARTIAL_SORRY"  # Accepted legacy retryable value.
    COUNTEREXAMPLE_FOUND = "COUNTEREXAMPLE_FOUND"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_PERMANENT = "FAILED_PERMANENT"
    BLOCKED = "BLOCKED"


PROVEN_STATUSES = {ItemStatus.CERTIFIED_PROVEN.value, ItemStatus.VERIFIED_IN_LEAN.value}
ACTIONABLE_STATUSES = {ItemStatus.QUEUED.value}

ALLOWED_TRANSITIONS = {
    ItemStatus.QUEUED.value: {
        ItemStatus.IN_PROGRESS.value,
        ItemStatus.QUEUED_DEFERRED.value,
        ItemStatus.BLOCKED.value,
    },
    ItemStatus.QUEUED_DEFERRED.value: {ItemStatus.QUEUED.value, ItemStatus.BLOCKED.value},
    ItemStatus.IN_PROGRESS.value: {
        ItemStatus.CERTIFIED_PROVEN.value,
        ItemStatus.COUNTEREXAMPLE_FOUND.value,
        ItemStatus.FAILED_RETRYABLE.value,
        ItemStatus.FAILED_PERMANENT.value,
        ItemStatus.PARTIAL_SORRY.value,
        ItemStatus.BLOCKED.value,
    },
    ItemStatus.FAILED_RETRYABLE.value: {ItemStatus.QUEUED.value, ItemStatus.BLOCKED.value},
    ItemStatus.PARTIAL_SORRY.value: {ItemStatus.QUEUED.value, ItemStatus.BLOCKED.value},
    ItemStatus.BLOCKED.value: {ItemStatus.QUEUED.value, ItemStatus.QUEUED_DEFERRED.value},
    ItemStatus.COUNTEREXAMPLE_FOUND.value: {ItemStatus.QUEUED.value},
    ItemStatus.FAILED_PERMANENT.value: {ItemStatus.QUEUED.value},
    ItemStatus.CERTIFIED_PROVEN.value: set(),
    ItemStatus.VERIFIED_IN_LEAN.value: set(),
}


DEFAULT_CURRICULUM = {
    "schema_version": 1,
    "project_name": "Research Collective",
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
            "declaration_name": "IsPalindrome",
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
            "title": "Carrieless square identity for (10^k + 1)^2",
            "tier": 2,
            "status": "QUEUED_DEFERRED",
            "type": "lemma",
            "module": "Powers",
            "lemma_name": "carrieless_square_identity",
            "dependencies": ["DEF-001", "LEMMA-001"],
            "empirical_task": {"type": "carrieless_square_check", "base": 10, "max_exponent": 8}
        },
        {
            "id": "CONJ-003",
            "title": "Single-digit numbers are sums of three base-b palindromes",
            "tier": 3,
            "status": "QUEUED_DEFERRED",
            "type": "lemma",
            "module": "Additive",
            "lemma_name": "single_digit_sum_three_palindromes",
            "dependencies": ["LEMMA-000"],
            "empirical_task": {"type": "single_digit_three_palindrome_sum"}
        },
        {
            "id": "ENUM-001",
            "title": "The two-digit palindrome constructor is injective in every valid base",
            "tier": 4,
            "status": "QUEUED",
            "type": "lemma",
            "module": "Enumeration",
            "lemma_name": "two_digit_palindrome_constructor_injective",
            "dependencies": ["LEMMA-004"],
            "empirical_task": {
                "type": "two_digit_constructor_injective",
                "min_base": 2,
                "max_base": 16
            }
        },
        {
            "id": "ENUM-002",
            "title": "The canonical two-digit palindrome construction yields b - 1 distinct values",
            "tier": 5,
            "status": "QUEUED",
            "type": "lemma",
            "module": "Enumeration",
            "lemma_name": "two_digit_palindrome_count",
            "dependencies": ["ENUM-001"],
            "empirical_task": {
                "type": "two_digit_palindrome_count",
                "min_base": 2,
                "max_base": 16
            }
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
        """Load and validate state without silently discarding corrupt data."""
        if not os.path.exists(self.state_file):
            state = copy.deepcopy(DEFAULT_CURRICULUM)
            self.validate_state(state)
            return state

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unable to load research state {self.state_file}: {exc}") from exc

        self._migrate_state(state)
        self.validate_state(state)
        return state

    @staticmethod
    def _migrate_state(state: Dict[str, Any]) -> None:
        """Apply backward-compatible in-memory defaults for older state files."""
        state.setdefault("schema_version", 1)
        state.setdefault("daily_cycles", [])
        state.setdefault("proven_knowledge_base", [])
        for item in state.get("frontier", []):
            item.setdefault("retry_count", 0)
            if item.get("id") == "DEF-001":
                item.setdefault("declaration_name", "IsPalindrome")

    @staticmethod
    def validate_state(state: Dict[str, Any]) -> None:
        """Validate the state schema and prove that the dependency graph is a DAG."""
        if not isinstance(state, dict) or not isinstance(state.get("frontier"), list):
            raise ValueError("Research state must contain a frontier list")

        frontier = state["frontier"]
        ids = [item.get("id") for item in frontier]
        if any(not isinstance(item_id, str) or not item_id for item_id in ids):
            raise ValueError("Every frontier item must have a non-empty string id")
        if len(ids) != len(set(ids)):
            raise ValueError("Frontier item ids must be unique")

        known_ids = set(ids)
        valid_statuses = {status.value for status in ItemStatus}
        proven_ids = state.get("proven_knowledge_base", [])
        if not isinstance(proven_ids, list) or len(proven_ids) != len(set(proven_ids)):
            raise ValueError("proven_knowledge_base must be a list of unique ids")
        if set(proven_ids) - known_ids:
            raise ValueError("proven_knowledge_base contains unknown frontier ids")
        graph: Dict[str, List[str]] = {}
        for item in frontier:
            status = item.get("status")
            if status not in valid_statuses:
                raise ValueError(f"Unknown status {status!r} for {item['id']}")
            dependencies = item.get("dependencies", [])
            if not isinstance(dependencies, list):
                raise ValueError(f"Dependencies for {item['id']} must be a list")
            missing = set(dependencies) - known_ids
            if missing:
                raise ValueError(f"Unknown dependencies for {item['id']}: {sorted(missing)}")
            if item["id"] in proven_ids and status not in PROVEN_STATUSES:
                raise ValueError(f"Proven item {item['id']} has non-proven status {status}")
            graph[item["id"]] = dependencies

        visiting = set()
        visited = set()

        def visit(item_id: str) -> None:
            if item_id in visiting:
                raise ValueError(f"Dependency cycle detected at {item_id}")
            if item_id in visited:
                return
            visiting.add(item_id)
            for dependency in graph[item_id]:
                visit(dependency)
            visiting.remove(item_id)
            visited.add(item_id)

        for item_id in ids:
            visit(item_id)

    def save_state(self):
        """Persist validated state atomically so interruption cannot truncate it."""
        self.validate_state(self.state)
        state_dir = os.path.dirname(os.path.abspath(self.state_file))
        os.makedirs(state_dir, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=state_dir, delete=False, suffix=".tmp"
            ) as temp_file:
                temp_path = temp_file.name
                json.dump(self.state, temp_file, indent=2)
                temp_file.write("\n")
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, self.state_file)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    def get_low_hanging_fruit(self) -> List[Dict[str, Any]]:
        """
        Returns active items ready for testing:
        Prerequisites satisfied and sorted by lowest tier first.
        """
        proven_ids = set(self.state.get("proven_knowledge_base", []))
        ready_items = []

        for item in self.state["frontier"]:
            # Deferred, failed, and blocked work must be activated explicitly.
            if item["status"] not in ACTIONABLE_STATUSES:
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
        """Apply a validated lifecycle transition and persist its telemetry."""
        if new_status not in {status.value for status in ItemStatus}:
            raise ValueError(f"Unknown item status: {new_status}")

        item = self.get_item(item_id)
        old_status = item["status"]
        if new_status != old_status and new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise ValueError(f"Invalid status transition for {item_id}: {old_status} -> {new_status}")

        item["status"] = new_status
        if telemetry is not None:
            item["last_telemetry"] = telemetry
        if new_status == ItemStatus.FAILED_RETRYABLE.value:
            item["retry_count"] = item.get("retry_count", 0) + 1
        if new_status in PROVEN_STATUSES and item_id not in self.state["proven_knowledge_base"]:
            self.state["proven_knowledge_base"].append(item_id)
        self.save_state()

    def get_item(self, item_id: str) -> Dict[str, Any]:
        for item in self.state["frontier"]:
            if item["id"] == item_id:
                return item
        raise KeyError(f"Unknown frontier item: {item_id}")

    def activate_item(self, item_id: str) -> None:
        """Move deferred or blocked work into the actionable queue."""
        self.mark_item(item_id, ItemStatus.QUEUED.value)

    def retry_item(self, item_id: str) -> None:
        """Explicitly requeue a failed item."""
        self.mark_item(item_id, ItemStatus.QUEUED.value)

    def record_cycle(self, record: Dict[str, Any]) -> None:
        self.state.setdefault("daily_cycles", []).append(record)
        self.save_state()

    def build_weekly_outlook(self) -> Dict[str, Any]:
        """Summarize the frontier for the Research Manager's Sunday review."""
        status_counts: Dict[str, int] = {}
        for item in self.state["frontier"]:
            status = item["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        proven_ids = set(self.state.get("proven_knowledge_base", []))
        advancements = [
            {"id": item["id"], "title": item["title"]}
            for item in self.state["frontier"]
            if item["id"] in proven_ids
        ]

        priorities = []
        action_by_status = {
            ItemStatus.QUEUED.value: "Advance through the empirical gate",
            ItemStatus.IN_PROGRESS.value: "Complete the active proof path",
            ItemStatus.FAILED_RETRYABLE.value: "Review evidence before an explicit retry",
            ItemStatus.PARTIAL_SORRY.value: "Replace the incomplete formal path",
            ItemStatus.FAILED_PERMANENT.value: "Reassess the conjecture and proof target",
            ItemStatus.COUNTEREXAMPLE_FOUND.value: "Study the counterexample and revise scope",
            ItemStatus.BLOCKED.value: "Resolve dependencies before activation",
            ItemStatus.QUEUED_DEFERRED.value: "Evaluate deliberate activation",
        }
        status_order = {
            ItemStatus.QUEUED.value: 0,
            ItemStatus.IN_PROGRESS.value: 1,
            ItemStatus.FAILED_RETRYABLE.value: 2,
            ItemStatus.PARTIAL_SORRY.value: 3,
            ItemStatus.BLOCKED.value: 4,
            ItemStatus.QUEUED_DEFERRED.value: 5,
            ItemStatus.COUNTEREXAMPLE_FOUND.value: 6,
            ItemStatus.FAILED_PERMANENT.value: 7,
        }
        candidates = [
            item for item in self.state["frontier"]
            if item["status"] not in PROVEN_STATUSES
        ]
        candidates.sort(key=lambda item: (
            status_order.get(item["status"], 99),
            item.get("tier", 99),
            item["id"],
        ))
        for item in candidates[:5]:
            priorities.append({
                "id": item["id"],
                "title": item["title"],
                "action": action_by_status.get(item["status"], "Review next action"),
            })

        return {
            "current_cycle": self.state.get("current_cycle", 1),
            "frontier_count": len(self.state["frontier"]),
            "proven_count": len(proven_ids),
            "status_counts": status_counts,
            "advancements": advancements,
            "priorities": priorities,
        }

    def increment_cycle(self):
        """Advances to next daily cycle."""
        self.state["current_cycle"] = self.state.get("current_cycle", 1) + 1
        self.save_state()

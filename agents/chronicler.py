"""
Scientific Chronicler Agent (The Author / Publisher)
Synthesizes research cycles into numbered volumes and weekly outlooks,
logs detailed telemetry to an auditable JSONL ledger, and maintains the blog website index.
"""

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, List

class Chronicler:
    """Compiles daily dispatches, maintains web blog data, and writes telemetry."""

    def __init__(self, dispatches_dir: str, log_file: str, site_dir: str = None):
        self.dispatches_dir = dispatches_dir
        self.log_file = log_file
        self.site_dir = site_dir or os.path.join(os.path.dirname(dispatches_dir), "site")
        self.site_articles_dir = os.path.join(self.site_dir, "articles")

        os.makedirs(self.dispatches_dir, exist_ok=True)
        os.makedirs(self.site_articles_dir, exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)

    @staticmethod
    def _atomic_write_text(path: str, content: str) -> None:
        """Write a UTF-8 file atomically in its destination directory."""
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
            ) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_path, path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    @classmethod
    def _atomic_copy(cls, source: str, destination: str) -> None:
        with open(source, "r", encoding="utf-8") as source_file:
            cls._atomic_write_text(destination, source_file.read())

    def log_event(
        self,
        event_type: str,
        agent_name: str,
        payload: Dict[str, Any],
        run_id: str = None,
    ):
        """Appends an event to the JSONL research log."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "event_type": event_type,
            "agent": agent_name,
            "data": payload
        }
        if run_id:
            record["run_id"] = run_id
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def sync_site_index(self):
        """Build the public index for launch, volume, and weekly-outlook posts."""
        entries = []
        managed_files = set()
        volume_pattern = re.compile(r"volume_(\d+)_(\d{4}-\d{2}-\d{2})\.md")
        launch_pattern = re.compile(r"launch_(\d{4}-\d{2}-\d{2})\.md")
        outlook_pattern = re.compile(r"weekly_outlook_(\d{4}-\d{2}-\d{2})\.md")
        managed_pattern = re.compile(
            r"(?:issue|volume)_\d+_\d{4}-\d{2}-\d{2}\.md|"
            r"launch_\d{4}-\d{2}-\d{2}\.md|"
            r"weekly_outlook_\d{4}-\d{2}-\d{2}\.md"
        )

        if os.path.exists(self.dispatches_dir):
            for fname in sorted(os.listdir(self.dispatches_dir)):
                volume_match = volume_pattern.fullmatch(fname)
                launch_match = launch_pattern.fullmatch(fname)
                outlook_match = outlook_pattern.fullmatch(fname)
                if not (volume_match or launch_match or outlook_match):
                    continue

                src = os.path.join(self.dispatches_dir, fname)
                dst = os.path.join(self.site_articles_dir, fname)
                self._atomic_copy(src, dst)
                managed_files.add(fname)

                with open(src, "r", encoding="utf-8") as article_file:
                    article_text = article_file.read()
                title_match = re.search(r"^#\s+(.+)$", article_text, re.MULTILINE)
                title = title_match.group(1).strip() if title_match else "The Daily Palindrome"
                verified_count = article_text.count("**`CERTIFIED_PROVEN`**")

                if volume_match:
                    volume_num = int(volume_match.group(1))
                    date_val = volume_match.group(2)
                    entry = {
                        "kind": "volume",
                        "cycle": volume_num,
                        "volume": volume_num,
                        "label": f"Vol. {volume_num:02d}",
                        "status": "Certified" if verified_count else "Research update",
                    }
                elif outlook_match:
                    date_val = outlook_match.group(1)
                    entry = {
                        "kind": "weekly_outlook",
                        "cycle": None,
                        "volume": None,
                        "label": "Weekly Outlook",
                        "status": "Planning",
                    }
                else:
                    date_val = launch_match.group(1)
                    entry = {
                        "kind": "launch",
                        "cycle": None,
                        "volume": None,
                        "label": "Launch",
                        "status": "Roadmap",
                    }

                entry.update({
                    "filename": fname,
                    "date": date_val,
                    "title": title,
                    "url": f"articles/{fname}",
                    "verified_lemmas": verified_count,
                })
                entries.append(entry)

        # Remove obsolete generated article copies while preserving unrelated files.
        for fname in os.listdir(self.site_articles_dir):
            if managed_pattern.fullmatch(fname) and fname not in managed_files:
                os.unlink(os.path.join(self.site_articles_dir, fname))

        kind_priority = {"weekly_outlook": 2, "volume": 1, "launch": 0}
        entries.sort(
            key=lambda item: (
                item["date"],
                kind_priority[item["kind"]],
                item.get("volume") or -1,
            ),
            reverse=True,
        )
        index_file = os.path.join(self.site_dir, "dispatches.json")
        self._atomic_write_text(index_file, json.dumps(entries, indent=2) + "\n")

        # Mirror pm_state.json for graph visualization
        state_src = os.path.join(os.path.dirname(self.dispatches_dir), "pm_state.json")
        if os.path.exists(state_src):
            self._atomic_copy(state_src, os.path.join(self.site_dir, "pm_state.json"))

    def _build_abstract(
        self,
        theme: str,
        certified_lemmas: List[Dict[str, Any]],
        empirical_results: List[Dict[str, Any]],
        open_conjectures: List[Dict[str, Any]],
    ) -> str:
        """Generate a concise, data-driven abstract that varies per cycle."""
        parts: List[str] = []

        # Rotate the opening shape so consecutive reports do not read like a template.
        lemma_titles = [l.get("title", "") for l in certified_lemmas]
        if certified_lemmas:
            names = ", ".join(f"**{t}**" for t in lemma_titles[:3])
            parts.append(
                f"Lean 4 closed {len(certified_lemmas)} proof obligation"
                f"{'s' if len(certified_lemmas) != 1 else ''} on the **{theme}** frontier: {names}."
            )
        else:
            parts.append(
                f"Work on the **{theme}** frontier concentrated on empirical reconnaissance "
                f"and proof decomposition; no new declaration reached certification."
            )

        # Empirical summary
        total_tested = sum(r.get("tested_count", 0) for r in empirical_results)
        total_cx = sum(r.get("counterexamples_found", 0) for r in empirical_results)
        if empirical_results:
            hypo_names = [r.get("hypothesis", "unnamed") for r in empirical_results]
            parts.append(
                f"The empirical pass scanned **{total_tested:,}** configurations "
                f"across {len(empirical_results)} hypothesis test{'s' if len(empirical_results) != 1 else ''} "
                f"(*{', '.join(hypo_names[:2])}*"
                + (f", ..." if len(hypo_names) > 2 else "")
                + f"), finding **{total_cx}** counterexample{'s' if total_cx != 1 else ''}."
            )

        # Frontier outlook
        if open_conjectures:
            next_ids = [c.get("id", "?") for c in open_conjectures[:3]]
            parts.append(
                f"The frontier currently tracks {len(open_conjectures)} incomplete conjecture{'s' if len(open_conjectures) != 1 else ''} "
                f"(`{'`, `'.join(next_ids)}`), including deferred and retry-required work."
            )

        return " ".join(parts)

    def publish_daily_article(
        self,
        cycle_number: int,
        theme: str,
        certified_lemmas: List[Dict[str, Any]],
        empirical_results: List[Dict[str, Any]],
        open_conjectures: List[Dict[str, Any]],
        lead_theorem_code: str
    ) -> str:
        """
        Renders a publication-ready research volume in GitHub Flavored Markdown
        ready for publishing to the website / documentation portal.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"volume_{cycle_number:02d}_{date_str}.md"
        filepath = os.path.join(self.dispatches_dir, filename)

        verified_count = len(certified_lemmas)

        # Build dynamic abstract from cycle data
        abstract = self._build_abstract(theme, certified_lemmas, empirical_results, open_conjectures)

        content = f"""# The Daily Palindrome — Vol. {cycle_number:02d}

## 1. Main Findings

{abstract}

---

## 2. Formally Certified Theorems (Lean 4)
"""
        if certified_lemmas:
            content += """
Each declaration below passed an exact-name Lean check and an axiom report containing only the configured trusted axioms.

### Verified Lemma Summary
| Lemma ID | Description | Lean Module | Status |
| :--- | :--- | :--- | :--- |
"""
            for item in certified_lemmas:
                content += f"| `{item.get('id', 'N/A')}` | {item.get('title', 'N/A')} | `{item.get('module', 'N/A')}` | **`CERTIFIED_PROVEN`** |\n"
            if lead_theorem_code.strip():
                content += f"""

```lean
{lead_theorem_code.strip()}
```
"""
        else:
            content += "\nNo new Lean declaration was certified in this cycle.\n"

        content += f"""

---

## 3. Computational Experimentation & Empirical Evidence

The **Computationalist** agent executed exhaustive searches to stress-test candidate conjectures prior to formal proof construction:

"""
        for res in empirical_results:
            hypo = res.get("hypothesis", "")
            tested = res.get("tested_count", 0)
            elapsed = res.get("elapsed_seconds", 0)
            primes = res.get("primes_found", [])
            content += f"### Hypothesis: *\"{hypo}\"*\n"
            noun = "integer" if tested == 1 else "integers"
            content += f"* **Search Space**: {tested:,} {noun} scanned in base {res.get('base', 10)}.\n"
            content += f"* **Counterexamples Discovered**: {res.get('counterexamples_found', 0)}\n"
            content += f"* **Elapsed Compute**: {elapsed}s\n"
            if primes:
                content += f"* **Palindromic Primes Identified**: `{primes}`\n"
            content += "\n"

        content += """---

## 4. Active Research Frontier & Open Conjectures

The **Research Manager** tracks the following incomplete hypotheses and their current lifecycle states:

"""
        for conj in open_conjectures:
            display_status = {
                "PARTIAL_SORRY": "INCOMPLETE",
                "FAILED_RETRYABLE": "RETRY_REQUIRED",
                "FAILED_PERMANENT": "REVIEW_REQUIRED",
            }.get(conj.get("status"), conj.get("status"))
            content += f"* **`{conj.get('id')}`** [Tier {conj.get('tier')}]: {conj.get('title')}\n"
            content += f"  * *Prerequisites*: `{', '.join(conj.get('dependencies', []))}`\n"
            content += f"  * *Status*: `{display_status}`\n"

        content += f"""

---

*Authored autonomously by the research collective.*
*Verification Kernel: Lean 4.34.0 | Language: Lean 4 / Python 3.14*
"""

        self._atomic_write_text(filepath, content)

        # Mirror to site/articles and update site/dispatches.json
        self.sync_site_index()

        self.log_event("RESEARCH_VOLUME_PUBLISHED", "Chronicler", {
            "cycle": cycle_number,
            "file": filename,
            "verified_lemmas": verified_count
        })

        return filepath

    def publish_weekly_outlook(
        self,
        outlook: Dict[str, Any],
        publication_date: str = None,
    ) -> str:
        """Publish the Research Manager's weekly status review and forward plan."""
        date_str = publication_date or datetime.now().strftime("%Y-%m-%d")
        filename = f"weekly_outlook_{date_str}.md"
        filepath = os.path.join(self.dispatches_dir, filename)

        status_names = {
            "CERTIFIED_PROVEN": "Certified",
            "VERIFIED_IN_LEAN": "Certified",
            "QUEUED": "Queued",
            "QUEUED_DEFERRED": "Deferred",
            "IN_PROGRESS": "In progress",
            "PARTIAL_SORRY": "Incomplete",
            "COUNTEREXAMPLE_FOUND": "Counterexample found",
            "FAILED_RETRYABLE": "Retry required",
            "FAILED_PERMANENT": "Review required",
            "BLOCKED": "Blocked",
        }
        status_lines = [
            f"- **{status_names.get(status, status.title())}:** {count}"
            for status, count in sorted(outlook.get("status_counts", {}).items())
            if count
        ]
        advancements = outlook.get("advancements", [])
        advancement_lines = [
            f"- **`{item['id']}`** — {item['title']}"
            for item in advancements
        ] or ["- No declaration entered the proven knowledge base during this review window."]
        priorities = outlook.get("priorities", [])
        priority_lines = [
            f"{index}. **`{item['id']}`** — {item['action']}: {item['title']}"
            for index, item in enumerate(priorities, start=1)
        ] or ["1. Extend the curriculum with the next dependency-backed research question."]

        content = f"""# Weekly Research Outlook

*Research Manager review for Sunday, {date_str}.*

## Status Review

The curriculum contains **{outlook.get('frontier_count', 0)}** tracked items across **{outlook.get('current_cycle', 1) - 1}** completed volume slots. The proven knowledge base currently contains **{outlook.get('proven_count', 0)}** items.

{chr(10).join(status_lines)}

## Advancements

{chr(10).join(advancement_lines)}

## Plan for the Week Ahead

{chr(10).join(priority_lines)}

## Research Manager's Note

The coming week will preserve the evidence gate: computational searches may advance a candidate to proof planning, but only exact-declaration verification can change the proven knowledge base. Deferred and incomplete work will be activated deliberately rather than retried automatically.

---

*Prepared by the Research Manager and published by the research collective.*
"""

        self._atomic_write_text(filepath, content)
        self.sync_site_index()
        self.log_event("WEEKLY_OUTLOOK_PUBLISHED", "ResearchManager", {
            "file": filename,
            "proven_items": outlook.get("proven_count", 0),
            "planned_items": len(priorities),
        })
        return filepath

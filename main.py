"""Research collective orchestrator and CLI driver."""

import os
import sys
import argparse
import uuid
from datetime import datetime, timezone

# Ensure Windows console doesn't crash on UTF-8 characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents.pm import ItemStatus, ProjectManager
from agents.experimenter import Experimenter
from agents.strategist import ProofStrategist
from agents.formalizer import Formalizer
from agents.chronicler import Chronicler

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FORMAL_DIR = os.path.join(PROJECT_ROOT, "formal")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
DISPATCHES_DIR = os.path.join(PROJECT_ROOT, "dispatches")
STATE_FILE = os.path.join(PROJECT_ROOT, "pm_state.json")
LOG_FILE = os.path.join(LOGS_DIR, "research_log.jsonl")


def publish_weekly_outlook_if_due(pm, chronicler, force: bool = False):
    """Publish one date-keyed Research Manager outlook on Sundays."""
    now = datetime.now()
    if not force and now.weekday() != 6:
        return None
    return chronicler.publish_weekly_outlook(
        pm.build_weekly_outlook(),
        publication_date=now.strftime("%Y-%m-%d"),
    )

def run_cycle():
    """Execute one gated research cycle."""
    print("=" * 70)
    print("   AUTONOMOUS NUMBER THEORY RESEARCH COLLECTIVE")
    print("=" * 70)

    # Initialize Agents
    pm = ProjectManager(STATE_FILE)
    experimenter = Experimenter()
    strategist = ProofStrategist()
    formalizer = Formalizer(FORMAL_DIR)
    chronicler = Chronicler(DISPATCHES_DIR, LOG_FILE)

    current_cycle = pm.state.get("current_cycle", 1)
    theme = pm.state.get("theme", "Palindromic Number Theory")
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    def log(event_type, agent_name, payload):
        chronicler.log_event(event_type, agent_name, payload, run_id=run_id)

    print(f"\n[Research Manager Agent] Initializing Cycle #{current_cycle:02d} on theme: '{theme}'")
    log("CYCLE_START", "ResearchManager", {"cycle": current_cycle, "theme": theme})

    # Step 1: Lake integrity build
    print("[Formalizer Agent] Running Lean 4 baseline integrity check...")
    build_res = formalizer.lake_build()
    if not build_res.get("success"):
        print(f"[FAIL] Lean 4 Build Failed:\n{build_res.get('output')}")
        log("BUILD_ERROR", "Formalizer", build_res)
        return False
    print("[OK] [Formalizer Agent] Lean 4 kernel integrity confirmed (0 errors).")

    # Step 2: Research Manager Triages Low-Hanging Fruit
    print("\n[Research Manager Agent] Triaging Research Frontier for low-hanging fruit...")
    candidates = pm.get_low_hanging_fruit()
    if not candidates:
        print("[Research Manager Agent] No actionable work. Deferred and failed items require explicit activation or retry.")
        outlook_path = publish_weekly_outlook_if_due(pm, chronicler)
        if outlook_path:
            print(f"[OK] [Research Manager Agent] Weekly Research Outlook published to:\n    {outlook_path}")
        return "NO_ACTIONABLE_WORK"
    print(f"Found {len(candidates)} actionable candidate tasks ready for exploration.")

    certified_lemmas = []
    empirical_records = []

    for item in candidates:
        item_id = item["id"]
        title = item["title"]
        pm.mark_item(item_id, ItemStatus.IN_PROGRESS.value, {"run_id": run_id, "stage": "selected"})
        print(f"\n---> Examining Candidate {item_id}: '{title}'")
        log("CANDIDATE_SELECTED", "ProjectManager", item)

        # Step 2a: Computational experimentation
        emp_task = item.get("empirical_task")
        if emp_task:
            print(f"  [Computationalist] Running empirical tests ({emp_task.get('type')})...")
            try:
                emp_res = experimenter.analyze_candidate(item_id, emp_task)
            except Exception as exc:
                emp_res = {"candidate_id": item_id, "error": str(exc), "verified_empirically": False}
            empirical_records.append(emp_res)
            print(f"  [OK] [Computationalist] Tested {emp_res.get('tested_count', 0):,} cases. "
                  f"Counterexamples: {emp_res.get('counterexamples_found', 0)} "
                  f"({emp_res.get('elapsed_seconds')}s)")
            log("EMPIRICAL_TEST_COMPLETE", "Experimenter", emp_res)
            if emp_res.get("error"):
                pm.mark_item(item_id, ItemStatus.FAILED_RETRYABLE.value, emp_res)
                print(f"  [!] [Computationalist] Experiment failed: {emp_res['error']}")
                continue
            if not emp_res.get("verified_empirically", False):
                pm.mark_item(item_id, ItemStatus.COUNTEREXAMPLE_FOUND.value, emp_res)
                print("  [!] [Computationalist] Counterexample found; formalization skipped.")
                continue
        
        # Step 2b: Strategic Decomposition
        print("  [Strategist] Decomposing proof structure into modular lemmas...")
        strat_res = strategist.decompose(item_id, item)
        log("DECOMPOSITION_COMPLETE", "ProofStrategist", strat_res)

        target_declaration = strat_res.get("target_declaration")
        target_module = strat_res.get("target_module")
        expected_declaration = item.get("lemma_name") or item.get("declaration_name")
        if not target_declaration or target_declaration != expected_declaration or target_module != item.get("module"):
            failure = {
                "status": "INVALID_PROOF_PLAN",
                "expected_module": item.get("module"),
                "expected_declaration": expected_declaration,
                "proof_plan": strat_res,
            }
            pm.mark_item(item_id, ItemStatus.FAILED_PERMANENT.value, failure)
            log("PROOF_PLAN_REJECTED", "ProjectManager", failure)
            print("  [!] [Strategist] Proof plan did not identify the configured target declaration.")
            continue

        # Step 2c: Formal Verification in Lean 4
        module_name = target_module
        print(f"  [Formalizer] Verifying proofs in Continuum.{module_name}...")
        verif_res = formalizer.verify_lemma(module_name, target_declaration)
        log("FORMALIZATION_CHECK", "Formalizer", verif_res)

        if verif_res.get("verified"):
            print(f"  [OK] [Formalizer] Formally certified in Lean 4! Status: {verif_res.get('status')}")
            pm.mark_item(item_id, ItemStatus.CERTIFIED_PROVEN.value, verif_res)
            certified_lemmas.append(item)
        else:
            print(f"  [!] [Formalizer] Exact declaration verification failed: {verif_res.get('status')}")
            failure_status = (
                ItemStatus.PARTIAL_SORRY.value
                if verif_res.get("uses_sorry_axiom") or verif_res.get("raw_sorry_count", 0)
                else ItemStatus.FAILED_RETRYABLE.value
            )
            pm.mark_item(item_id, failure_status, verif_res)

    # Step 3: Evening Publication & Synthesis
    print("\n[Chronicler Agent] Compiling Daily Research Dispatch and Telemetry...")
    
    # Include only source modules that produced a certificate in this cycle.
    lead_code_parts = []
    certified_modules = dict.fromkeys(item.get("module") for item in certified_lemmas)
    for module_name in certified_modules:
        if not module_name:
            continue
        module_path = os.path.join(FORMAL_DIR, "Continuum", *module_name.split(".")) + ".lean"
        if os.path.exists(module_path):
            with open(module_path, "r", encoding="utf-8") as source_file:
                lead_code_parts.append(source_file.read())
    lead_code = "\n\n".join(lead_code_parts)

    open_conjectures = [
        item for item in pm.state["frontier"]
        if item["status"] not in (ItemStatus.CERTIFIED_PROVEN.value, ItemStatus.VERIFIED_IN_LEAN.value)
    ]

    article_path = chronicler.publish_daily_article(
        cycle_number=current_cycle,
        theme=theme,
        certified_lemmas=certified_lemmas,
        empirical_results=empirical_records,
        open_conjectures=open_conjectures,
        lead_theorem_code=lead_code
    )

    print(f"[OK] [Chronicler Agent] Daily Article published to:\n    {article_path}")
    print(f"[OK] [Chronicler Agent] Telemetry appended to:\n    {LOG_FILE}")

    pm.record_cycle({
        "cycle": current_cycle,
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "certified_items": [item["id"] for item in certified_lemmas],
        "empirical_tests": len(empirical_records),
        "article": os.path.basename(article_path),
    })
    pm.increment_cycle()

    outlook_path = publish_weekly_outlook_if_due(pm, chronicler)
    if outlook_path:
        print(f"[OK] [Research Manager Agent] Weekly Research Outlook published to:\n    {outlook_path}")

    # Sync web blog
    chronicler.sync_site_index()

    print("\n" + "=" * 70)
    print(f"   CYCLE #{current_cycle:02d} COMPLETE: {len(certified_lemmas)} THEOREMS CERTIFIED")
    print("=" * 70)
    return True

def run_continuous(interval_sec: int = 15, max_cycles: int = None):
    """Runs research cycles continuously with interval pauses until stopped or limits reached."""
    print("=" * 70)
    print("   RESEARCH COLLECTIVE : CONTINUOUS HARNESS ACTIVE")
    print(f"   Interval delay: {interval_sec}s | Max cycles: {max_cycles or 'Unlimited'}")
    print("   Press Ctrl+C at any time to gracefully stop.")
    print("=" * 70)

    cycles_completed = 0
    try:
        while True:
            result = run_cycle()
            if result == "NO_ACTIONABLE_WORK":
                print("\n[OK] [Harness] No actionable work remains. Deferred or failed items were not retried automatically.")
                break
            elif not result:
                print("\n[!] Cycle encountered a blocking error or rate limit. Pausing daemon.")
                break

            cycles_completed += 1
            if max_cycles and cycles_completed >= max_cycles:
                print(f"\n[OK] Reached target max cycles ({max_cycles}). Stopping harness.")
                break
            
            print(f"\n[Harness] Cycle complete. Sleeping for {interval_sec}s before next cycle...")
            import time
            time.sleep(interval_sec)
    except KeyboardInterrupt:
        print("\n\n[Harness] User interrupted. State safely persisted. Goodbye!")

def serve_blog(port: int = 8000, host: str = "127.0.0.1"):
    """Starts a local HTTP server to view the research articles blog."""
    import http.server
    import socketserver
    
    # Sync latest dispatches before serving
    chronicler = Chronicler(DISPATCHES_DIR, LOG_FILE)
    chronicler.sync_site_index()

    site_dir = os.path.join(PROJECT_ROOT, "site")
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=site_dir, **kwargs)

    print("=" * 70)
    print("   RESEARCH COLLECTIVE : LOCAL RESEARCH BLOG VIEWER")
    print("=" * 70)
    print(f"\n[OK] Serving research blog at: http://{host}:{port}")
    print(f"[OK] Document root: {site_dir}")
    print("Press Ctrl+C to stop the server.\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((host, port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[OK] Server stopped.")

def print_status():
    """Displays current DAG state."""
    pm = ProjectManager(STATE_FILE)
    print("=" * 60)
    print(f"Research Collective - Project Status (Cycle #{pm.state.get('current_cycle', 1):02d})")
    print("=" * 60)
    proven = pm.state.get("proven_knowledge_base", [])
    print(f"Proven Knowledge Base ({len(proven)} items):")
    for item_id in proven:
        print(f"  [OK] {item_id}")
    
    print("\nFrontier Items:")
    for item in pm.state.get("frontier", []):
        status_icon = "[OK]" if item["status"] == "CERTIFIED_PROVEN" else ("[..]" if item["status"] == "QUEUED" else "[--]")
        print(f"  {status_icon} [{item['id']}] (Tier {item['tier']}) {item['title']} -> {item['status']}")


def audit_certificates() -> bool:
    """Re-verify every declaration recorded in the proven knowledge base."""
    pm = ProjectManager(STATE_FILE)
    formalizer = Formalizer(FORMAL_DIR)
    all_verified = True
    for item_id in pm.state.get("proven_knowledge_base", []):
        item = pm.get_item(item_id)
        declaration = item.get("lemma_name") or item.get("declaration_name")
        if not declaration:
            print(f"[FAIL] {item_id}: no configured Lean declaration")
            all_verified = False
            continue
        result = formalizer.verify_lemma(item["module"], declaration)
        marker = "OK" if result.get("verified") else "FAIL"
        print(f"[{marker}] {item_id}: Continuum.{declaration} -> {result.get('status')}")
        all_verified = all_verified and bool(result.get("verified"))
    return all_verified

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Number Theory Research Collective")
    parser.add_argument("--run-cycle", action="store_true", help="Execute one research cycle")
    parser.add_argument("--continuous", action="store_true", help="Run continuously until interrupted or limits reached")
    parser.add_argument("--interval", type=int, default=15, help="Delay in seconds between continuous cycles (default: 15)")
    parser.add_argument("--max-cycles", type=int, default=None, help="Maximum number of cycles to execute before stopping")
    parser.add_argument("--status", action="store_true", help="Display current curriculum DAG status")
    parser.add_argument("--audit-certificates", action="store_true", help="Re-verify every proven Lean declaration")
    parser.add_argument("--weekly-outlook", action="store_true", help="Publish the Research Manager's weekly outlook now")
    parser.add_argument("--activate", metavar="ITEM_ID", help="Activate a deferred or blocked frontier item")
    parser.add_argument("--retry", metavar="ITEM_ID", help="Explicitly requeue a failed frontier item")
    parser.add_argument("--serve", action="store_true", help="Launch local blog viewer on http://localhost:8000")
    parser.add_argument("--port", type=int, default=8000, help="Port for the blog server (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1", help="Blog bind host (default: 127.0.0.1)")
    args = parser.parse_args()

    if args.activate:
        ProjectManager(STATE_FILE).activate_item(args.activate)
        print(f"Activated {args.activate}.")
    elif args.retry:
        ProjectManager(STATE_FILE).retry_item(args.retry)
        print(f"Requeued {args.retry}.")
    elif args.serve:
        serve_blog(port=args.port, host=args.host)
    elif args.continuous:
        run_continuous(interval_sec=args.interval, max_cycles=args.max_cycles)
    elif args.status:
        print_status()
    elif args.audit_certificates:
        raise SystemExit(0 if audit_certificates() else 1)
    elif args.weekly_outlook:
        manager = ProjectManager(STATE_FILE)
        publisher = Chronicler(DISPATCHES_DIR, LOG_FILE)
        path = publish_weekly_outlook_if_due(manager, publisher, force=True)
        print(f"Weekly Research Outlook published to: {path}")
    elif args.run_cycle:
        run_cycle()
    else:
        parser.print_help()

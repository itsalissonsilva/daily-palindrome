"""
Palindrome Continuum: Autonomous Multi-Agent Number Theory Research Suite
Main Orchestrator and CLI Driver.
"""

import os
import sys
import argparse

# Ensure Windows console doesn't crash on UTF-8 characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents.pm import ProjectManager
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

def run_cycle():
    """Executes a full autonomous research cycle."""
    print("=" * 70)
    print("   PALINDROME CONTINUUM : AUTONOMOUS NUMBER THEORY RESEARCH SUITE")
    print("=" * 70)

    # Initialize Agents
    pm = ProjectManager(STATE_FILE)
    experimenter = Experimenter()
    strategist = ProofStrategist()
    formalizer = Formalizer(FORMAL_DIR)
    chronicler = Chronicler(DISPATCHES_DIR, LOG_FILE)

    current_cycle = pm.state.get("current_cycle", 1)
    theme = pm.state.get("theme", "Palindromic Number Theory")

    print(f"\n[PM Agent] Initializing Cycle #{current_cycle:02d} on theme: '{theme}'")
    chronicler.log_event("CYCLE_START", "ProjectManager", {"cycle": current_cycle, "theme": theme})

    # Step 1: Lake integrity build
    print("[Formalizer Agent] Running Lean 4 baseline integrity check...")
    build_res = formalizer.lake_build()
    if not build_res.get("success"):
        print(f"[FAIL] Lean 4 Build Failed:\n{build_res.get('output')}")
        chronicler.log_event("BUILD_ERROR", "Formalizer", build_res)
        return False
    print("[OK] [Formalizer Agent] Lean 4 kernel integrity confirmed (0 errors).")

    # Step 2: PM Triages Low-Hanging Fruit
    print("\n[PM Agent] Triaging Research Frontier for low-hanging fruit...")
    candidates = pm.get_low_hanging_fruit()
    if not candidates:
        print("[PM Agent] All currently queued frontier candidates are certified or awaiting new hypotheses.")
        return "FRONTIER_EXHAUSTED"
    print(f"Found {len(candidates)} actionable candidate tasks ready for exploration.")

    certified_lemmas = []
    empirical_records = []

    for item in candidates:
        item_id = item["id"]
        title = item["title"]
        print(f"\n---> Examining Candidate {item_id}: '{title}'")
        chronicler.log_event("CANDIDATE_SELECTED", "ProjectManager", item)

        # Step 2a: Computational experimentation
        emp_task = item.get("empirical_task")
        if emp_task:
            print(f"  [Computationalist] Running empirical tests ({emp_task.get('type')})...")
            emp_res = experimenter.analyze_candidate(item_id, emp_task)
            empirical_records.append(emp_res)
            print(f"  [OK] [Computationalist] Tested {emp_res.get('tested_count', 0):,} cases. "
                  f"Counterexamples: {emp_res.get('counterexamples_found', 0)} "
                  f"({emp_res.get('elapsed_seconds')}s)")
            chronicler.log_event("EMPIRICAL_TEST_COMPLETE", "Experimenter", emp_res)
        
        # Step 2b: Strategic Decomposition
        print("  [Strategist] Decomposing proof structure into modular lemmas...")
        strat_res = strategist.decompose(item_id, item)
        chronicler.log_event("DECOMPOSITION_COMPLETE", "ProofStrategist", strat_res)

        # Step 2c: Formal Verification in Lean 4
        module_name = item.get("module", "Common")
        print(f"  [Formalizer] Verifying proofs in Continuum.{module_name}...")
        verif_res = formalizer.check_file(os.path.join("Continuum", f"{module_name}.lean"))
        chronicler.log_event("FORMALIZATION_CHECK", "Formalizer", verif_res)

        if verif_res.get("verified"):
            print(f"  [OK] [Formalizer] Formally certified in Lean 4! Status: {verif_res.get('status')}")
            pm.mark_item(item_id, "CERTIFIED_PROVEN", verif_res)
            certified_lemmas.append(item)
        else:
            print(f"  [!] [Formalizer] Verification incomplete or has sorry: {verif_res.get('status')}")
            pm.mark_item(item_id, "PARTIAL_SORRY", verif_res)

    # Step 3: Evening Publication & Synthesis
    print("\n[Chronicler Agent] Compiling Daily Research Dispatch and Telemetry...")
    
    # Read lead theorem code from ParityDivisibility.lean for snippet
    lead_code_path = os.path.join(FORMAL_DIR, "Continuum", "ParityDivisibility.lean")
    lead_code = ""
    if os.path.exists(lead_code_path):
        with open(lead_code_path, "r", encoding="utf-8") as f:
            lead_code = f.read()

    open_conjectures = [item for item in pm.state["frontier"] if item["status"] not in ("CERTIFIED_PROVEN", "VERIFIED_IN_LEAN")]

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

    # Advance cycle
    pm.increment_cycle()

    # Sync web blog
    chronicler.sync_site_index()

    print("\n" + "=" * 70)
    print(f"   CYCLE #{current_cycle:02d} COMPLETE: {len(certified_lemmas)} THEOREMS CERTIFIED")
    print("=" * 70)
    return True

def run_continuous(interval_sec: int = 15, max_cycles: int = None):
    """Runs research cycles continuously with interval pauses until stopped or limits reached."""
    print("=" * 70)
    print("   PALINDROME CONTINUUM : CONTINUOUS DAEMON HARNESS ACTIVE")
    print(f"   Interval delay: {interval_sec}s | Max cycles: {max_cycles or 'Unlimited'}")
    print("   Press Ctrl+C at any time to gracefully stop.")
    print("=" * 70)

    cycles_completed = 0
    try:
        while True:
            result = run_cycle()
            if result == "FRONTIER_EXHAUSTED":
                print("\n[OK] [Harness] Research frontier completed: all available theorems certified!")
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

def serve_blog(port: int = 8000):
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
    print("   PALINDROME CONTINUUM : LOCAL RESEARCH BLOG VIEWER")
    print("=" * 70)
    print(f"\n[OK] Serving research blog at: http://localhost:{port}")
    print(f"[OK] Document root: {site_dir}")
    print("Press Ctrl+C to stop the server.\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[OK] Server stopped.")

def print_status():
    """Displays current DAG state."""
    pm = ProjectManager(STATE_FILE)
    print("=" * 60)
    print(f"Palindrome Continuum - Project Status (Cycle #{pm.state.get('current_cycle', 1):02d})")
    print("=" * 60)
    proven = pm.state.get("proven_knowledge_base", [])
    print(f"Proven Knowledge Base ({len(proven)} items):")
    for item_id in proven:
        print(f"  [OK] {item_id}")
    
    print("\nFrontier Items:")
    for item in pm.state.get("frontier", []):
        status_icon = "[OK]" if item["status"] == "CERTIFIED_PROVEN" else ("[..]" if item["status"] == "QUEUED" else "[--]")
        print(f"  {status_icon} [{item['id']}] (Tier {item['tier']}) {item['title']} -> {item['status']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Palindrome Continuum Research Suite")
    parser.add_argument("--run-cycle", action="store_true", help="Execute one research cycle")
    parser.add_argument("--continuous", action="store_true", help="Run continuously until interrupted or limits reached")
    parser.add_argument("--interval", type=int, default=15, help="Delay in seconds between continuous cycles (default: 15)")
    parser.add_argument("--max-cycles", type=int, default=None, help="Maximum number of cycles to execute before stopping")
    parser.add_argument("--status", action="store_true", help="Display current curriculum DAG status")
    parser.add_argument("--serve", action="store_true", help="Launch local blog viewer on http://localhost:8000")
    parser.add_argument("--port", type=int, default=8000, help="Port for the blog server (default: 8000)")
    args = parser.parse_args()

    if args.serve:
        serve_blog(port=args.port)
    elif args.continuous:
        run_continuous(interval_sec=args.interval, max_cycles=args.max_cycles)
    elif args.status:
        print_status()
    else:
        run_cycle()

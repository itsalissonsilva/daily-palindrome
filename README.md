# Palindrome Continuum

**Autonomous Multi-Agent Number Theory Research Suite**  
*Formally grounded in Lean 4 • Empirical verification via Python • Curriculum-directed by a Project Manager*

---

## Overview

**Palindrome Continuum** is an open-source autonomous multi-agent research collective dedicated to discovering, analyzing, and formally verifying theorems in palindromic number theory.

Rather than allowing language models to guess or hallucinate mathematical proofs, **Palindrome Continuum** anchors every discovery to the **Lean 4 kernel**. Conjectures are triaged from low-hanging fruit upward, tested computationally across number space, decomposed into modular lemmas, and verified with zero-sorry formal integrity.

```
                      +-----------------------------+
                      |   Project Manager (PI)      |
                      |   Curriculum DAG & Priority |
                      +--------------+--------------+
                                     |
           +-------------------------+-------------------------+
           |                         |                         |
           v                         v                         v
+--------------------+    +--------------------+    +--------------------+
|  Computationalist  |    |  Proof Strategist  |    | Formalizer (Lean4) |
|  Empirical Search  |    |  Lemma Roadmap     |    | Kernel Verifier    |
+--------------------+    +--------------------+    +--------------------+
           |                         |                         |
           +-------------------------+-------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Scientific Chronicler    |
                      |    Daily Articles & Logs    |
                      +-----------------------------+
```

---

## Agent Roster

1. **Project Manager (`agents/pm.py`)**:
   Maintains the Research Curriculum DAG (`pm_state.json`), prioritizes low-hanging fruit, manages compute budgets, and enforces a progressive learning path.
2. **Computationalist / Experimenter (`agents/experimenter.py`)**:
   Tests candidate hypotheses across thousands of integers and multiple bases ($b \in [2, 16]$) to filter out false conjectures before formalization.
3. **Proof Strategist (`agents/strategist.py`)**:
   Decomposes macroscopic conjectures into atomic lemmas (parity invariants, modular digit sums, polynomial expansions).
4. **Formalizer (`agents/formalizer.py`)**:
   Interfaces directly with the Lean 4 compiler via `lake env lean` and `lake build`, verifying type safety and guaranteeing zero unclosed `sorry` goals.
5. **Scientific Chronicler (`agents/chronicler.py`)**:
   Publishes daily Markdown research dispatches in `dispatches/` with $\LaTeX$ math and appends structured telemetry to `logs/research_log.jsonl`.

---

## Directory Structure

```text
palindrome-continuum/
├── agents/                   # Multi-agent Python core
│   ├── pm.py                 # Project Manager & Curriculum DAG
│   ├── experimenter.py       # Empirical scanner & counterexample search
│   ├── strategist.py         # Proof decomposition engine
│   ├── formalizer.py         # Lean 4 compiler bridge
│   └── chronicler.py         # Daily dispatch & telemetry writer
├── formal/                   # Lean 4 verification library
│   ├── lakefile.toml
│   ├── lean-toolchain        # Lean 4.34.0
│   └── Continuum/
│       ├── Common.lean       # Axiomatic definitions (digits, IsPalindrome, IsPrime)
│       └── ParityDivisibility.lean  # Certified theorems (11 | palindrome, prime uniqueness)
├── dispatches/               # Autonomous daily research articles
│   ├── issue_01_*.md
│   └── issue_04_*.md
├── logs/                     # Auditable telemetry ledger
│   └── research_log.jsonl
├── pm_state.json             # Persistent curriculum & DAG state
├── main.py                   # Suite CLI driver
└── README.md
```

---

## Quickstart

### Prerequisites
* **Python 3.10+** (Python 3.14 recommended)
* **Lean 4** (managed via `elan`)

### Running a Research Cycle
To execute an autonomous cycle (Triage $\to$ Experiment $\to$ Decompose $\to$ Formalize $\to$ Publish):

```bash
python main.py --run-cycle
```

### Checking Project Status & DAG
To inspect the current research frontier and proven knowledge base:

```bash
python main.py --status
```

---

## Formally Certified Invariants (POC Highlights)

* **`Continuum.Common.zero_is_palindrome`**: $0$ is a palindrome in any base $b \ge 2$.
* **`Continuum.Common.single_digit_is_palindrome`**: Every single-digit integer $0 < n < b$ is palindromic in base $b$.
* **`Continuum.ParityDivisibility.two_digit_palindrome_div_11`**: $11 \mid (10d + d)$.
* **`Continuum.ParityDivisibility.four_digit_palindrome_div_11`**: $11 \mid (1000a + 100b + 10b + a)$.
* **`Continuum.ParityDivisibility.six_digit_palindrome_div_11`**: $11 \mid (100000a + \dots + a)$.
* **`Continuum.ParityDivisibility.base_b_two_digit_div`**: $(b+1) \mid (bd + d)$ in arbitrary base $b \ge 2$.
* **`Continuum.ParityDivisibility.two_digit_prime_is_11`**: $11$ is the unique 2-digit palindromic prime in base 10.

---

## License
Open source under the Apache 2.0 License.

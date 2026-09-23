"""
Formalization Agent (The Verifier)
Compiles, verifies, and checks Lean 4 proof obligations.
Extracts diagnostic information, verifies zero-sorry integrity,
and provides machine-checked certificates.
"""

import subprocess
import os
import re
import hashlib
import tempfile
from typing import Dict, Any

class Formalizer:
    """Interface to the Lean 4 compiler and Lake build system."""

    def __init__(self, formal_dir: str):
        self.formal_dir = os.path.abspath(formal_dir)
        self.name = "FormalizationAgent"

    def check_file(self, rel_path: str) -> Dict[str, Any]:
        """Runs lean directly on a specific file within the package."""
        full_path = os.path.join(self.formal_dir, rel_path)
        if not os.path.exists(full_path):
            return {
                "status": "ERROR",
                "error": f"File not found: {full_path}"
            }
        
        try:
            # Run lean via lake env to ensure all module dependencies and LEAN_PATH are resolved
            cmd = ["lake", "env", "lean", full_path]
            result = subprocess.run(
                cmd,
                cwd=self.formal_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            stdout = result.stdout
            stderr = result.stderr
            combined = stdout + "\n" + stderr

            has_error = result.returncode != 0 or "error:" in combined

            # Inspect content for sorry declarations
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            raw_sorry_count = len(re.findall(r"\bsorry\b", content))

            if has_error:
                status = "FAILED"
            elif raw_sorry_count > 0:
                status = "PARTIAL_SORRY"
            else:
                status = "CERTIFIED_PROVEN"

            return {
                "file": rel_path,
                "status": status,
                "return_code": result.returncode,
                "raw_sorry_count": raw_sorry_count,
                "compiler_output": combined.strip(),
                "verified": status == "CERTIFIED_PROVEN"
            }
        except subprocess.TimeoutExpired:
            return {
                "file": rel_path,
                "status": "TIMEOUT",
                "error": "Lean compilation timed out after 60 seconds."
            }
        except Exception as e:
            return {
                "file": rel_path,
                "status": "ERROR",
                "error": str(e)
            }

    def lake_build(self) -> Dict[str, Any]:
        """Runs `lake build` to compile and verify the entire Lean 4 library."""
        try:
            cmd = ["lake", "build"]
            result = subprocess.run(
                cmd,
                cwd=self.formal_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            output = (result.stdout + "\n" + result.stderr).strip()
            success = result.returncode == 0 and "error:" not in output

            return {
                "status": "SUCCESS" if success else "BUILD_FAILED",
                "return_code": result.returncode,
                "output": output,
                "success": success
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "output": "lake build timed out after 120s"
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "output": str(e)
            }

    def verify_lemma(self, module_name: str, lemma_name: str) -> Dict[str, Any]:
        """Verify an exact declaration and emit a reproducible proof certificate."""
        identifier = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")
        module = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
        if not module.fullmatch(module_name) or not identifier.fullmatch(lemma_name):
            return {
                "status": "ERROR",
                "verified": False,
                "error": "Invalid Lean module or declaration name",
                "target_module": module_name,
                "target_declaration": lemma_name,
            }

        rel_path = os.path.join("Continuum", *module_name.split(".")) + ".lean"
        source_path = os.path.join(self.formal_dir, rel_path)
        module_result = self.check_file(rel_path)
        if not module_result.get("verified"):
            module_result.update({
                "target_module": module_name,
                "target_declaration": lemma_name,
            })
            return module_result

        with open(source_path, "rb") as source_file:
            source_sha256 = hashlib.sha256(source_file.read()).hexdigest()

        toolchain_path = os.path.join(self.formal_dir, "lean-toolchain")
        with open(toolchain_path, "r", encoding="utf-8") as toolchain_file:
            toolchain = toolchain_file.read().strip()

        qualified_name = f"Continuum.{lemma_name}"
        probe_source = (
            f"import Continuum.{module_name}\n"
            f"#check {qualified_name}\n"
            f"#print axioms {qualified_name}\n"
        )
        probe_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.formal_dir,
                prefix=".continuum_verify_", suffix=".lean", delete=False
            ) as probe_file:
                probe_path = probe_file.name
                probe_file.write(probe_source)

            result = subprocess.run(
                ["lake", "env", "lean", probe_path],
                cwd=self.formal_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = (result.stdout + "\n" + result.stderr).strip()
            uses_sorry = "sorryAx" in output or "declaration uses 'sorry'" in output
            axiom_match = re.search(r"depends on axioms:\s*\[([^\]]*)\]", output)
            axioms = (
                [axiom.strip() for axiom in axiom_match.group(1).split(",") if axiom.strip()]
                if axiom_match else []
            )
            trusted_axioms = {"propext", "Quot.sound", "Classical.choice"}
            unexpected_axioms = sorted(set(axioms) - trusted_axioms)
            verified = (
                result.returncode == 0
                and "error:" not in output
                and not uses_sorry
                and not unexpected_axioms
            )
            certificate_material = "|".join(
                [toolchain, module_name, lemma_name, source_sha256, output]
            ).encode("utf-8")

            return {
                "file": rel_path,
                "status": "CERTIFIED_PROVEN" if verified else "FAILED",
                "return_code": result.returncode,
                "verified": verified,
                "target_module": module_name,
                "target_declaration": lemma_name,
                "qualified_declaration": qualified_name,
                "source_sha256": source_sha256,
                "lean_toolchain": toolchain,
                "axiom_report": output,
                "axioms": axioms,
                "unexpected_axioms": unexpected_axioms,
                "uses_sorry_axiom": uses_sorry,
                "certificate_id": hashlib.sha256(certificate_material).hexdigest(),
            }
        except subprocess.TimeoutExpired:
            return {
                "file": rel_path,
                "status": "TIMEOUT",
                "verified": False,
                "target_module": module_name,
                "target_declaration": lemma_name,
                "error": "Lean declaration verification timed out after 60 seconds.",
            }
        finally:
            if probe_path and os.path.exists(probe_path):
                os.unlink(probe_path)

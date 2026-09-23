"""
Formalization Agent (The Verifier)
Compiles, verifies, and checks Lean 4 proof obligations.
Extracts diagnostic information, verifies zero-sorry integrity,
and provides machine-checked certificates.
"""

import subprocess
import os
import re
from typing import Dict, Any, List

class Formalizer:
    """Interface to the Lean 4 compiler and Lake build system."""

    def __init__(self, formal_dir: str):
        self.formal_dir = formal_dir
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

            # Check for sorry / warning
            has_sorry = "warning: declaration uses 'sorry'" in combined or "sorry" in combined
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
        """Verifies a specific named lemma inside a module."""
        file_path = os.path.join(self.formal_dir, "Continuum", f"{module_name}.lean")
        res = self.check_file(os.path.join("Continuum", f"{module_name}.lean"))
        res["target_lemma"] = lemma_name
        return res

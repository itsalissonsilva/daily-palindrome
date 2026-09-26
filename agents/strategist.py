"""
Proof Strategist Agent (The Architect)
Decomposes mathematical conjectures into modular lemmas,
identifies inductive or algebraic proof patterns,
and maps out proof strategies for the formalization agent.
"""

from typing import Dict, Any

class ProofStrategist:
    """Decomposes conjectures into structured lemmas and proof plans."""

    def __init__(self, name: str = "ProofStrategist"):
        self.name = name

    def decompose(self, hypothesis_id: str, hypothesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a verified empirical hypothesis and constructs a modular proof strategy.
        """
        title = hypothesis_data.get("title", "")
        empirical_type = hypothesis_data.get("empirical_task", {}).get("type")
        target_declaration = hypothesis_data.get("lemma_name") or hypothesis_data.get("declaration_name")
        target_module = hypothesis_data.get("module")

        common = {
            "hypothesis_id": hypothesis_id,
            "target_module": target_module,
            "target_declaration": target_declaration,
        }
        
        if empirical_type == "three_digit_constructor_injective":
            return common | {
                "strategy_type": "Modular Digit Recovery",
                "core_insight": (
                    "Reduce equality of the constructed values modulo b to recover the bounded leading digit. "
                    "After substituting that equality, cancel the common outer factor b and the shared leading "
                    "term to recover the middle digit."
                ),
                "modular_lemmas": [
                    {
                        "id": hypothesis_id,
                        "name": "three_digit_palindrome_constructor_injective",
                        "statement": "equal [a, m, a] values with a < b have equal leading and middle digits",
                        "tactic_hint": "take congrArg (% b), substitute the leading digit, then cancel",
                    }
                ],
                "recommended_module": "Continuum.Enumeration",
            }

        elif empirical_type == "two_digit_palindrome_count":
            return common | {
                "strategy_type": "Finite Enumeration and Injectivity",
                "core_insight": (
                    "Enumerate the nonzero base-b digits with List.range (b - 1), map the repeated-digit "
                    "constructor over that list, and combine preservation of list length with the established "
                    "injectivity theorem to prove the resulting values are distinct."
                ),
                "modular_lemmas": [
                    {
                        "id": hypothesis_id,
                        "name": "two_digit_palindrome_count",
                        "statement": "the canonical list has length b - 1 and contains no duplicates",
                        "tactic_hint": "simp for length; pairwise_map plus constructor injectivity for Nodup",
                    }
                ],
                "recommended_module": "Continuum.Enumeration",
            }

        elif empirical_type == "two_digit_constructor_injective":
            return common | {
                "strategy_type": "Factorization and Cancellation",
                "core_insight": (
                    "Rewrite b*d + d as (b + 1)*d. Since b + 1 is positive, equality of two "
                    "constructed values permits cancellation of the common factor."
                ),
                "modular_lemmas": [
                    {
                        "id": hypothesis_id,
                        "name": "two_digit_palindrome_constructor_injective",
                        "statement": "b*a + a = b*c + c → a = c for b ≥ 2",
                        "tactic_hint": "factor with Nat.add_mul, then apply Nat.mul_left_cancel",
                    }
                ],
                "recommended_module": "Continuum.Enumeration",
            }

        elif empirical_type == "carrieless_square_check":
            return common | {
                "strategy_type": "Polynomial Identity",
                "core_insight": (
                    "Expand (10^k + 1)^2 by the binomial identity. The result is "
                    "10^(2k) + 2*10^k + 1, whose separated coefficients explain the observed palindrome."
                ),
                "modular_lemmas": [
                    {
                        "id": hypothesis_id,
                        "name": "carrieless_square_identity",
                        "statement": "(10^k + 1)^2 = 10^(2*k) + 2*10^k + 1",
                        "tactic_hint": "ring",
                    }
                ],
                "recommended_module": "Continuum.Powers",
            }

        elif empirical_type == "single_digit_three_palindrome_sum":
            return common | {
                "strategy_type": "Constructive Additive Witness",
                "core_insight": (
                    "For a nonzero single digit n, choose the three palindromes n, 0, and 0. "
                    "The existing single-digit and zero lemmas certify the witnesses."
                ),
                "modular_lemmas": [
                    {
                        "id": hypothesis_id,
                        "name": "single_digit_sum_three_palindromes",
                        "statement": "0 < n < b → ∃ x y z, pal x ∧ pal y ∧ pal z ∧ n = x + y + z",
                        "tactic_hint": "refine witnesses n, 0, 0; omega",
                    }
                ],
                "recommended_module": "Continuum.Additive",
            }

        elif empirical_type == "even_length_divisibility" or "divisible by" in title.lower():
            return common | {
                "strategy_type": "Algebraic Parity Invariant",
                "core_insight": (
                    "In base 10, 10 ≡ -1 (mod 11). "
                    "Thus 10^k ≡ (-1)^k (mod 11). "
                    "For any number with digits [d_0, d_1, ..., d_{2m-1}], "
                    "the value modulo 11 is the alternating sum ∑ (-1)^i d_i. "
                    "Since the number is an even-length palindrome, digits pair up with opposite signs: "
                    "(-1)^i d_i + (-1)^{2m-1-i} d_{2m-1-i} = (-1)^i d_i - (-1)^i d_i = 0. "
                    "Hence n ≡ 0 (mod 11)."
                ),
                "modular_lemmas": [
                    {
                        "id": "LEMMA-001",
                        "name": "two_digit_palindrome_div_11",
                        "statement": "11 ∣ (10 * d + d)",
                        "tactic_hint": "omega / ring"
                    },
                    {
                        "id": "LEMMA-002",
                        "name": "four_digit_palindrome_div_11",
                        "statement": "11 ∣ (1000 * a + 100 * b + 10 * b + a)",
                        "tactic_hint": "omega / ring"
                    },
                    {
                        "id": "LEMMA-003",
                        "name": "six_digit_palindrome_div_11",
                        "statement": "11 ∣ (100000*a + 10000*b + 1000*c + 100*c + 10*b + a)",
                        "tactic_hint": "omega / ring"
                    },
                    {
                        "id": "LEMMA-004",
                        "name": "base_b_two_digit_div",
                        "statement": "(b + 1) ∣ (b * d + d)",
                        "tactic_hint": "omega / ring"
                    }
                ],
                "recommended_module": "Continuum.ParityDivisibility"
            }
        
        elif empirical_type == "single_digit_check" or hypothesis_id == "LEMMA-000":
            return common | {
                "strategy_type": "Direct Definition Unfolding",
                "core_insight": "A single digit list [d] has length 1. Its reverse is [d]. By definition, it is a palindrome.",
                "modular_lemmas": [
                    {
                        "id": "LEMMA-000",
                        "name": "single_digit_is_palindrome",
                        "statement": "0 < n < b → IsPalindrome b n",
                        "tactic_hint": "unfold IsPalindrome, simp, decide"
                    }
                ],
                "recommended_module": "Continuum.Common"
            }
        
        elif empirical_type == "even_length_palindromic_primes":
            return common | {
                "strategy_type": "Prime Divisor Elimination",
                "core_insight": (
                    "Use divisibility of even-length palindromes by b + 1. "
                    "Primality forces the palindrome to equal that divisor; in base 10 this is 11."
                ),
                "modular_lemmas": [
                    {
                        "id": "LEMMA-001",
                        "name": "two_digit_palindrome_div_11",
                        "statement": "11 ∣ (10 * d + d)",
                        "tactic_hint": "apply the custom IsPrime divisor characterization",
                    }
                ],
                "recommended_module": "Continuum.ParityDivisibility",
            }

        else:
            return common | {
                "strategy_type": "Generic Scaffolding",
                "core_insight": "Requires empirical observation decomposition.",
                "modular_lemmas": [],
                "recommended_module": f"Continuum.{target_module}" if target_module else None,
            }

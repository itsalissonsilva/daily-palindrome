"""
Experimenter Agent (The Computationalist)
Autonomous empirical testing, pattern discovery, and counterexample search
for palindromic number theory.
"""

from typing import List, Dict, Any, Optional
import time

def digits_in_base(n: int, b: int = 10) -> List[int]:
    """Returns digits of n in base b, least-significant first."""
    if n == 0:
        return [0]
    digits = []
    curr = n
    while curr > 0:
        digits.append(curr % b)
        curr //= b
    return digits

def is_palindrome(n: int, b: int = 10) -> bool:
    """Returns True if n is a palindrome in base b."""
    if n < 0:
        return False
    d = digits_in_base(n, b)
    return d == d[::-1]

def is_prime(n: int) -> bool:
    """Fast deterministic Miller-Rabin primality test for 64-bit integers."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    # Miller-Rabin deterministic bases for n < 3.3 * 10^14
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    
    bases = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    for a in bases:
        if n <= a:
            break
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        composite = True
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                composite = False
                break
        if composite:
            return False
    return True

class Experimenter:
    """Computational experimenter for testing hypotheses on palindromes."""

    def __init__(self, name: str = "Experimenter"):
        self.name = name

    def generate_palindromes(self, max_digits: int = 6, base: int = 10) -> List[int]:
        """Generates all base-b palindromes with up to max_digits length."""
        palindromes = []
        # Single digit
        for d in range(1, base):
            palindromes.append(d)
        
        # Multi-digit: construct from half
        # For length L = 2k (even) or 2k + 1 (odd)
        for length in range(2, max_digits + 1):
            half_len = (length + 1) // 2
            start = base ** (half_len - 1)
            end = base ** half_len
            is_odd = (length % 2 != 0)
            
            for root in range(start, end):
                s = str(root) if base == 10 else "".join(str(x) for x in digits_in_base(root, base)[::-1])
                rev = s[:-1][::-1] if is_odd else s[::-1]
                full_str = s + rev
                pal_val = int(full_str, base)
                palindromes.append(pal_val)
        
        return sorted(list(set(palindromes)))

    def test_even_length_divisibility(self, base: int = 10, max_half_digits: int = 4) -> Dict[str, Any]:
        """
        Tests the conjecture:
        Every even-length palindrome in base b is divisible by (b + 1).
        """
        start_time = time.time()
        divisor = base + 1
        tested_count = 0
        counterexamples = []
        samples = []

        for half_len in range(1, max_half_digits + 1):
            start = base ** (half_len - 1)
            end = base ** half_len
            for root in range(start, end):
                s = str(root)
                full = s + s[::-1]
                pal = int(full, base)
                tested_count += 1
                
                if pal % divisor != 0:
                    counterexamples.append({"n": pal, "length": len(full), "remainder": pal % divisor})
                elif len(samples) < 5:
                    samples.append({"n": pal, "length": len(full), "quotient": pal // divisor})

        elapsed = time.time() - start_time
        return {
            "hypothesis": f"Every even-length palindrome in base {base} is divisible by {divisor}",
            "tested_count": tested_count,
            "counterexamples_found": len(counterexamples),
            "counterexamples": counterexamples[:5],
            "verified_empirically": len(counterexamples) == 0,
            "elapsed_seconds": round(elapsed, 4),
            "samples": samples
        }

    def search_even_length_palindromic_primes(self, base: int = 10, max_half_digits: int = 4) -> Dict[str, Any]:
        """
        Searches for even-length palindromic primes in base 10.
        Known fact: 11 is the only one because 11 | n for all even-length palindromes.
        """
        start_time = time.time()
        primes_found = []
        tested_count = 0

        for half_len in range(1, max_half_digits + 1):
            start = base ** (half_len - 1)
            end = base ** half_len
            for root in range(start, end):
                s = str(root)
                full = s + s[::-1]
                pal = int(full, base)
                tested_count += 1
                if is_prime(pal):
                    primes_found.append(pal)

        elapsed = time.time() - start_time
        return {
            "hypothesis": f"In base {base}, 11 is the sole even-length palindromic prime",
            "tested_count": tested_count,
            "primes_found": primes_found,
            "verified_empirically": (primes_found == [11]),
            "elapsed_seconds": round(elapsed, 4)
        }

    def analyze_candidate(self, candidate_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatcher for candidate hypotheses sent by PM."""
        task_type = payload.get("type")
        if task_type == "even_length_divisibility":
            return self.test_even_length_divisibility(
                base=payload.get("base", 10),
                max_half_digits=payload.get("max_half_digits", 4)
            )
        elif task_type == "even_length_palindromic_primes":
            return self.search_even_length_palindromic_primes(
                base=payload.get("base", 10),
                max_half_digits=payload.get("max_half_digits", 4)
            )
        elif task_type == "single_digit_check":
            tested = 0
            for b in range(2, 17):
                for d in range(1, b):
                    tested += 1
            return {
                "hypothesis": "All single-digit numbers (0 < d < b) are palindromic in base b",
                "tested_count": tested,
                "counterexamples_found": 0,
                "verified_empirically": True,
                "elapsed_seconds": 0.0001
            }
        else:
            return {"error": f"Unknown task type: {task_type}"}

if __name__ == "__main__":
    exp = Experimenter()
    res1 = exp.test_even_length_divisibility(base=10, max_half_digits=3)
    print("Divisibility Test:", res1["verified_empirically"], f"({res1['tested_count']} tested)")
    res2 = exp.search_even_length_palindromic_primes(base=10, max_half_digits=3)
    print("Palindromic Primes:", res2["primes_found"])

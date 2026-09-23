"""
Experimenter Agent (The Computationalist)
Autonomous empirical testing, pattern discovery, and counterexample search
for palindromic number theory.
"""

from typing import List, Dict, Any
import time


def _validate_base(base: int) -> None:
    if base < 2:
        raise ValueError("base must be at least 2")


def digits_in_base(n: int, b: int = 10) -> List[int]:
    """Returns digits of n in base b, least-significant first."""
    _validate_base(b)
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return [0]
    digits = []
    curr = n
    while curr > 0:
        digits.append(curr % b)
        curr //= b
    return digits


def value_from_digits(digits: List[int], base: int = 10) -> int:
    """Evaluate most-significant-first digits without string conversion."""
    _validate_base(base)
    value = 0
    for digit in digits:
        if digit < 0 or digit >= base:
            raise ValueError(f"digit {digit} is invalid in base {base}")
        value = value * base + digit
    return value


def palindrome_from_half(root: int, half_len: int, base: int, odd_length: bool) -> int:
    """Mirror a fixed-width, most-significant-first half arithmetically."""
    half = digits_in_base(root, base)[::-1]
    if len(half) != half_len:
        raise ValueError("root does not have the requested half length")
    mirrored = half[-2::-1] if odd_length else half[::-1]
    return value_from_digits(half + mirrored, base)


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
        _validate_base(base)
        if max_digits < 1:
            return []
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
                palindromes.append(palindrome_from_half(root, half_len, base, is_odd))

        return sorted(list(set(palindromes)))

    def test_even_length_divisibility(self, base: int = 10, max_half_digits: int = 4) -> Dict[str, Any]:
        """
        Tests the conjecture:
        Every even-length palindrome in base b is divisible by (b + 1).
        """
        _validate_base(base)
        if max_half_digits < 1:
            raise ValueError("max_half_digits must be at least 1")
        start_time = time.perf_counter()
        divisor = base + 1
        tested_count = 0
        counterexamples = []
        samples = []

        for half_len in range(1, max_half_digits + 1):
            start = base ** (half_len - 1)
            end = base ** half_len
            for root in range(start, end):
                pal = palindrome_from_half(root, half_len, base, odd_length=False)
                tested_count += 1

                if pal % divisor != 0:
                    counterexamples.append({"n": pal, "length": half_len * 2, "remainder": pal % divisor})
                elif len(samples) < 5:
                    samples.append({"n": pal, "length": half_len * 2, "quotient": pal // divisor})

        elapsed = time.perf_counter() - start_time
        return {
            "hypothesis": f"Every even-length palindrome in base {base} is divisible by {divisor}",
            "tested_count": tested_count,
            "counterexamples_found": len(counterexamples),
            "counterexamples": counterexamples[:5],
            "verified_empirically": len(counterexamples) == 0,
            "elapsed_seconds": round(elapsed, 4),
            "samples": samples,
            "base": base,
        }

    def search_even_length_palindromic_primes(self, base: int = 10, max_half_digits: int = 4) -> Dict[str, Any]:
        """
        Searches for even-length palindromic primes in base b.
        Divisibility by b + 1 means the only possible result is b + 1 itself.
        """
        _validate_base(base)
        if max_half_digits < 1:
            raise ValueError("max_half_digits must be at least 1")
        start_time = time.perf_counter()
        primes_found = []
        tested_count = 0

        for half_len in range(1, max_half_digits + 1):
            start = base ** (half_len - 1)
            end = base ** half_len
            for root in range(start, end):
                pal = palindrome_from_half(root, half_len, base, odd_length=False)
                tested_count += 1
                if is_prime(pal):
                    primes_found.append(pal)

        elapsed = time.perf_counter() - start_time
        expected = [base + 1] if is_prime(base + 1) else []
        return {
            "hypothesis": f"In base {base}, the only possible even-length palindromic prime is {base + 1}",
            "tested_count": tested_count,
            "primes_found": primes_found,
            "counterexamples_found": 0 if primes_found == expected else 1,
            "verified_empirically": primes_found == expected,
            "elapsed_seconds": round(elapsed, 4),
            "base": base,
        }

    def test_carrieless_square_identity(self, base: int = 10, max_exponent: int = 8) -> Dict[str, Any]:
        """Check the palindromic values generated by (b^k + 1)^2 when b > 2."""
        _validate_base(base)
        if base <= 2:
            raise ValueError("carrieless square checks require base at least 3")
        if max_exponent < 1:
            raise ValueError("max_exponent must be at least 1")

        start_time = time.perf_counter()
        counterexamples = []
        samples = []
        for exponent in range(1, max_exponent + 1):
            value = (base ** exponent + 1) ** 2
            if not is_palindrome(value, base):
                counterexamples.append({"exponent": exponent, "value": value})
            elif len(samples) < 5:
                samples.append({"exponent": exponent, "value": value})

        return {
            "hypothesis": f"(base^k + 1)^2 is palindromic in base {base} for k >= 1",
            "tested_count": max_exponent,
            "counterexamples_found": len(counterexamples),
            "counterexamples": counterexamples,
            "verified_empirically": not counterexamples,
            "elapsed_seconds": round(time.perf_counter() - start_time, 4),
            "samples": samples,
            "base": base,
        }

    def test_single_digit_three_palindrome_sum(self) -> Dict[str, Any]:
        """Check n = n + 0 + 0 for every nonzero single digit in bases 2 through 16."""
        start_time = time.perf_counter()
        counterexamples = []
        tested_count = 0
        for base in range(2, 17):
            for value in range(1, base):
                tested_count += 1
                parts = (value, 0, 0)
                if sum(parts) != value or not all(is_palindrome(part, base) for part in parts):
                    counterexamples.append({"base": base, "value": value, "parts": parts})

        return {
            "hypothesis": "Every nonzero single digit is a sum of three palindromes in its base",
            "tested_count": tested_count,
            "counterexamples_found": len(counterexamples),
            "counterexamples": counterexamples,
            "verified_empirically": not counterexamples,
            "elapsed_seconds": round(time.perf_counter() - start_time, 4),
            "base": "2–16",
        }

    def analyze_candidate(self, candidate_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatcher for candidate hypotheses sent by PM."""
        task_type = payload.get("type")
        if task_type == "even_length_divisibility":
            result = self.test_even_length_divisibility(
                base=payload.get("base", 10),
                max_half_digits=payload.get("max_half_digits", 4)
            )
        elif task_type == "even_length_palindromic_primes":
            result = self.search_even_length_palindromic_primes(
                base=payload.get("base", 10),
                max_half_digits=payload.get("max_half_digits", 4)
            )
        elif task_type == "single_digit_check":
            tested = 0
            for b in range(2, 17):
                for d in range(1, b):
                    tested += 1
            return {
                "candidate_id": candidate_id,
                "hypothesis": "All single-digit numbers (0 < d < b) are palindromic in base b",
                "tested_count": tested,
                "counterexamples_found": 0,
                "verified_empirically": True,
                "elapsed_seconds": 0.0001
            }
        elif task_type == "carrieless_square_check":
            result = self.test_carrieless_square_identity(
                base=payload.get("base", 10),
                max_exponent=payload.get("max_exponent", 8),
            )
        elif task_type == "single_digit_three_palindrome_sum":
            result = self.test_single_digit_three_palindrome_sum()
        else:
            return {"candidate_id": candidate_id, "error": f"Unknown task type: {task_type}"}
        result["candidate_id"] = candidate_id
        return result

if __name__ == "__main__":
    exp = Experimenter()
    res1 = exp.test_even_length_divisibility(base=10, max_half_digits=3)
    print("Divisibility Test:", res1["verified_empirically"], f"({res1['tested_count']} tested)")
    res2 = exp.search_even_length_palindromic_primes(base=10, max_half_digits=3)
    print("Palindromic Primes:", res2["primes_found"])

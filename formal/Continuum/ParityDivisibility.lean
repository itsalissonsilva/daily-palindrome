/-
  Continuum.ParityDivisibility
  Theorems establishing divisibility properties of even-length palindromic numbers.
-/

import Continuum.Common

set_option linter.unusedVariables false

namespace Continuum

/-- A two-digit base-10 number with identical digits is divisible by 11. -/
theorem two_digit_palindrome_div_11 (d : Nat) (hd : d > 0) (hd_lt : d < 10) :
    11 ∣ (10 * d + d) := by
  have heq : 10 * d + d = 11 * d := by omega
  rw [heq]
  exact ⟨d, rfl⟩

/-- A four-digit base-10 palindrome `abba` = 1000*a + 100*b + 10*b + a is divisible by 11. -/
theorem four_digit_palindrome_div_11 (a b : Nat) (ha : a > 0) (ha_lt : a < 10) (hb_lt : b < 10) :
    11 ∣ (1000 * a + 100 * b + 10 * b + a) := by
  have heq : 1000 * a + 100 * b + 10 * b + a = 11 * (91 * a + 10 * b) := by omega
  rw [heq]
  exact ⟨91 * a + 10 * b, rfl⟩

/-- A six-digit base-10 palindrome `abccba` is divisible by 11. -/
theorem six_digit_palindrome_div_11 (a b c : Nat) (ha : a > 0) :
    11 ∣ (100000 * a + 10000 * b + 1000 * c + 100 * c + 10 * b + a) := by
  have heq : 100000 * a + 10000 * b + 1000 * c + 100 * c + 10 * b + a =
             11 * (9091 * a + 910 * b + 100 * c) := by omega
  rw [heq]
  exact ⟨9091 * a + 910 * b + 100 * c, rfl⟩

/--
General base-b 2-digit palindrome: d * b + d is divisible by (b + 1).
-/
theorem base_b_two_digit_div (b d : Nat) (hb : b >= 2) (hd : d > 0) :
    (b + 1) ∣ (b * d + d) := by
  have heq : b * d + d = (b + 1) * d := by
    rw [Nat.add_mul]
    simp
  rw [heq]
  exact ⟨d, rfl⟩

/--
If a two-digit base-10 palindrome 10*d + d is prime, then d must equal 1 (hence n = 11).
-/
theorem two_digit_prime_is_11 (d : Nat) (hd_pos : d > 0) (hd_lt : d < 10)
    (hprime : IsPrime (10 * d + d)) : d = 1 := by
  have heq : 10 * d + d = 11 * d := by omega
  have hprime' : IsPrime (11 * d) := by
    have h1 : 10 * d + d = 11 * d := by omega
    rw [← h1]
    exact hprime
  have hdiv11 : 11 ∣ (11 * d) := ⟨d, rfl⟩
  rcases hprime' with ⟨hge2, hdiv⟩
  have hor := hdiv 11 hdiv11
  rcases hor with h11_eq_1 | h11_eq_11d
  · contradiction
  · have h11d : 11 * d = 11 := by rw [← h11_eq_11d]
    omega

end Continuum

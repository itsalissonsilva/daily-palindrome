/-
  Continuum.Common
  Foundational definitions and core properties of palindromic numbers in Lean 4.
-/

namespace Continuum

/-- Fuel-based extraction of digits in base b (least-significant digit first). -/
def digitsFuel (b : Nat) (n : Nat) (fuel : Nat) : List Nat :=
  match fuel with
  | 0 => []
  | fuel + 1 =>
    if n = 0 then []
    else (n % b) :: digitsFuel b (n / b) fuel

/-- For n = 0, digitsFuel is empty regardless of fuel. -/
theorem digitsFuel_zero (b : Nat) (fuel : Nat) : digitsFuel b 0 fuel = [] := by
  cases fuel with
  | zero => rfl
  | succ f =>
    unfold digitsFuel
    rfl

/-- Returns the digits of n in base b. For b < 2 or n = 0, returns [0] or []. -/
def digits (b : Nat) (n : Nat) : List Nat :=
  if b < 2 then []
  else if n = 0 then [0]
  else digitsFuel b n (n + 1)

/-- A natural number `n` is palindromic in base `b` if its digit list equals its reverse. -/
def IsPalindrome (b : Nat) (n : Nat) : Prop :=
  digits b n = (digits b n).reverse

/-- Definition of primality for natural numbers. -/
def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d, d ∣ p → d = 1 ∨ d = p

/-- 0 is palindromic in any base b >= 2. -/
theorem zero_is_palindrome (b : Nat) (hb : b >= 2) : IsPalindrome b 0 := by
  unfold IsPalindrome digits
  have hnot : ¬ (b < 2) := by omega
  simp [hnot]

/-- Single-digit numbers (0 < n < b) are palindromes in base b. -/
theorem single_digit_is_palindrome (b n : Nat) (hb : b >= 2) (hn_pos : n > 0) (hn : n < b) :
    IsPalindrome b n := by
  unfold IsPalindrome digits
  have hnot : ¬ (b < 2) := by omega
  have hn_ne : n ≠ 0 := by omega
  simp [hnot, hn_ne]
  unfold digitsFuel
  simp [hn_ne]
  have hdiv : n / b = 0 := Nat.div_eq_of_lt hn
  have hmod : n % b = n := Nat.mod_eq_of_lt hn
  rw [hdiv, hmod, digitsFuel_zero]
  rfl

end Continuum

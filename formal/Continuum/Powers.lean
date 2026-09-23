/-
  Continuum.Powers
  Algebraic identities behind structured palindromic powers.
-/

import Continuum.Common

namespace Continuum

/-- The algebraic identity behind the decimal palindrome family 10201, 1002001, and so on. -/
theorem carrieless_square_identity (k : Nat) :
    (10 ^ k + 1) ^ 2 = 10 ^ (2 * k) + 2 * 10 ^ k + 1 := by
  have h_exp : 2 * k = k + k := by omega
  rw [h_exp, Nat.pow_add]
  simp [Nat.pow_succ, Nat.mul_add, Nat.mul_comm]
  omega

end Continuum

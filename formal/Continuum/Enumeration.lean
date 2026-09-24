/-
  Continuum.Enumeration
  Injective constructors used to count fixed-length palindromes.
-/

import Continuum.Common

namespace Continuum

/-- Repeating a digit in the two base-b positions never identifies two distinct digits. -/
theorem two_digit_palindrome_constructor_injective (base : Nat) (hbase : base >= 2) :
    Function.Injective (fun digit : Nat => base * digit + digit) := by
  intro a b h
  have hfactor : (base + 1) * a = (base + 1) * b := by
    simpa [Nat.add_mul] using h
  have hpositive : 0 < base + 1 := by omega
  exact Nat.mul_left_cancel hpositive hfactor

end Continuum

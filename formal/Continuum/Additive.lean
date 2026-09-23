/-
  Continuum.Additive
  Constructive base cases for additive palindrome questions.
-/

import Continuum.Common

namespace Continuum

/-- Every nonzero single digit is trivially a sum of three palindromes: n + 0 + 0. -/
theorem single_digit_sum_three_palindromes
    (base n : Nat) (hbase : base >= 2) (hn_pos : n > 0) (hn_lt : n < base) :
    ∃ x y z : Nat,
      IsPalindrome base x ∧ IsPalindrome base y ∧ IsPalindrome base z ∧
      n = x + y + z := by
  refine ⟨n, 0, 0, single_digit_is_palindrome base n hbase hn_pos hn_lt,
    zero_is_palindrome base hbase, zero_is_palindrome base hbase, ?_⟩
  omega

end Continuum

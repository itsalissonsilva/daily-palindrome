import unittest

from agents.experimenter import (
    Experimenter,
    digits_in_base,
    is_palindrome,
    value_from_digits,
)


class ExperimenterTests(unittest.TestCase):
    def test_digit_round_trip_across_supported_bases(self):
        for base in range(2, 17):
            for value in range(0, 250):
                digits_msd_first = digits_in_base(value, base)[::-1]
                self.assertEqual(value_from_digits(digits_msd_first, base), value)

    def test_generated_values_are_palindromes_in_every_supported_base(self):
        experimenter = Experimenter()
        for base in range(2, 17):
            values = experimenter.generate_palindromes(max_digits=4, base=base)
            self.assertTrue(values)
            self.assertTrue(all(is_palindrome(value, base) for value in values))

    def test_even_length_divisibility_does_not_depend_on_decimal_strings(self):
        experimenter = Experimenter()
        for base in range(2, 17):
            result = experimenter.test_even_length_divisibility(base, max_half_digits=3)
            self.assertTrue(result["verified_empirically"], result)
            self.assertEqual(result["counterexamples_found"], 0)

    def test_base_ten_even_length_prime_search(self):
        result = Experimenter().search_even_length_palindromic_primes(10, 3)
        self.assertTrue(result["verified_empirically"])
        self.assertEqual(result["primes_found"], [11])

    def test_carrieless_square_family_in_base_ten(self):
        result = Experimenter().test_carrieless_square_identity(10, 8)
        self.assertTrue(result["verified_empirically"], result)
        self.assertEqual(result["tested_count"], 8)
        self.assertEqual(result["counterexamples_found"], 0)

    def test_single_digits_have_constructive_three_palindrome_decompositions(self):
        result = Experimenter().test_single_digit_three_palindrome_sum()
        self.assertTrue(result["verified_empirically"], result)
        self.assertEqual(result["tested_count"], 120)
        self.assertEqual(result["counterexamples_found"], 0)

    def test_two_digit_constructor_is_injective_across_supported_bases(self):
        result = Experimenter().test_two_digit_constructor_injective(2, 16)
        self.assertTrue(result["verified_empirically"], result)
        self.assertEqual(result["tested_count"], 120)
        self.assertEqual(result["counterexamples_found"], 0)

    def test_two_digit_palindrome_count_across_supported_bases(self):
        result = Experimenter().test_two_digit_palindrome_count(2, 16)
        self.assertTrue(result["verified_empirically"], result)
        self.assertEqual(result["tested_count"], 120)
        self.assertEqual(result["counterexamples_found"], 0)

    def test_invalid_base_is_rejected(self):
        with self.assertRaises(ValueError):
            digits_in_base(12, 1)


if __name__ == "__main__":
    unittest.main()

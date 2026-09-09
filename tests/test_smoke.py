import math
import unittest

from strategy import find_best_one_stop, find_best_two_stop
from traffic import find_best_field_pit


class PortfolioSmokeTests(unittest.TestCase):
    def test_reference_one_stop(self):
        strategy, pit, time_value, _ = find_best_one_stop()
        self.assertEqual(strategy, ("Medium", "Soft"))
        self.assertEqual(pit, 29)
        self.assertTrue(math.isclose(time_value, 4530.065, abs_tol=0.01))

    def test_reference_two_stop(self):
        strategy, pit_1, pit_2, time_value = find_best_two_stop()
        self.assertEqual(strategy, ("Medium", "Soft", "Soft"))
        self.assertEqual((pit_1, pit_2), (19, 34))
        self.assertTrue(math.isclose(time_value, 4502.473, abs_tol=0.01))

    def test_reference_field_result(self):
        pit, result, _ = find_best_field_pit()
        self.assertEqual(pit, 28)
        self.assertEqual(result["final_position"], 2)


if __name__ == "__main__":
    unittest.main()

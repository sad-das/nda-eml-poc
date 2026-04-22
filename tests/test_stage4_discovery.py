import unittest
from nda_eml_poc.stage4_discovery import CurriculumRunner, flat_boundary


class Stage4DiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = CurriculumRunner(seed=0).run()

    def test_stage4_discovers_multiplication_without_manual_registry(self):
        result = self.result
        self.assertEqual(result["manual_registry_dependency"], 0)
        rows = {r["target"]: r for r in result["discoveries"]}
        self.assertTrue(rows["x_times_y"]["found"])
        self.assertIn(rows["x_times_y"]["surface"], {"exp(add(ln(x),ln(y)))", "exp(add(ln(y),ln(x)))"})
        self.assertEqual(rows["x_times_y"]["macro_depth"], 3)

    def test_stage4_taylor_trap_is_fatal_not_reward_shaped(self):
        result = self.result
        trap = result["taylor_trap"]
        self.assertTrue(trap["available"])
        self.assertTrue(trap["is_eml_tree"])
        self.assertFalse(trap["accepted"])
        self.assertIn("asymptotic_stress_failure", trap["reasons"])
        self.assertEqual(result["policy"]["scalar_penalties_used"], 0)
        self.assertGreaterEqual(result["policy"]["fatal_rejection_events"], 1)

    def test_stage4_flat_boundary_records_stage3_limit(self):
        rows = {r["target"]: r for r in flat_boundary(seed=0)}
        self.assertTrue(rows["ln_x"]["found"])
        self.assertFalse(rows["x_times_y"]["found"])
        self.assertFalse(rows["x_plus_y"]["found"])


if __name__ == "__main__":
    unittest.main()

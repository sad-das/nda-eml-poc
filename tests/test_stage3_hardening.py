import unittest

from nda_eml_poc.stage3_hardening import bounded_shallow_discovery, adversarial_hardening


class Stage3HardeningTests(unittest.TestCase):
    def test_stage3_shallow_discovery_recovers_exp_and_log(self):
        rows = bounded_shallow_discovery(seed=0, max_depth=3, threshold=1e-16)
        by_target = {r["target"]: r for r in rows}
        self.assertTrue(by_target["exp_x"]["shallow_found"])
        self.assertTrue(by_target["ln_x"]["shallow_found"])
        self.assertFalse(by_target["x_times_y"]["shallow_found"])

    def test_stage3_gate6_rejects_shortcuts_and_witnesses_hold_adversarially(self):
        rows = adversarial_hardening(seed=0, threshold=1e-16, n_points=64)
        self.assertTrue(all(r["witness_adversarial_pass"] for r in rows))
        self.assertTrue(all(not r["shortcut_gate6_accepted"] for r in rows))
        nontrivial = [r for r in rows if r["target"] not in {"one_const", "e_const", "zero_const"}]
        self.assertTrue(all(r["shortcut_fails_adversarial"] for r in nontrivial))


if __name__ == "__main__":
    unittest.main()

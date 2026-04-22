import unittest
import numpy as np
from nda_eml_poc.constructors import witness_registry
from nda_eml_poc.gate6 import Gate6
from nda_eml_poc.targets import make_targets


class Stage2WitnessTests(unittest.TestCase):
    def test_constructive_witnesses_pass_gate6_for_all_targets(self):
        registry = witness_registry()
        gate = Gate6(threshold=1e-16)
        for target in make_targets(0):
            expr = registry[target.name].expr
            report = gate.check(expr, target, set())
            self.assertTrue(report.accepted, (target.name, report.reasons, report.train_mse, report.holdout_mse, report.complex_mse))
            self.assertTrue(expr.is_eml_tree)

    def test_gate6_rejects_shortcut(self):
        from nda_eml_poc.eml import Expr
        target = make_targets(0)[0]
        shortcut = Expr.shortcut(target.name, target.train_x, target.train_y(), arity=target.arity)
        report = Gate6().check(shortcut, target, set())
        self.assertFalse(report.accepted)
        self.assertIn("non_constructive_shortcut_or_non_eml_tree", report.reasons)

    def test_arithmetic_witness_values(self):
        reg = witness_registry()
        x = np.array([0.5, 1.2, 2.0], dtype=np.complex128)
        y = np.array([0.7, 1.5, 3.0], dtype=np.complex128)
        checks = {
            "x_minus_y": x - y,
            "x_plus_y": x + y,
            "x_times_y": x * y,
            "x_div_y": x / y,
            "x_square": x * x,
            "neg_x": -x,
        }
        for name, expected in checks.items():
            got = reg[name].expr.eval(x, y)
            self.assertLess(np.max(np.abs(got - expected)), 1e-12, name)


if __name__ == "__main__":
    unittest.main()

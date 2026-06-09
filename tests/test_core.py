"""
Tests for OpenSeeFace pure-logic modules.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openseeface.remedian import remedian, median


class TestRemedian(unittest.TestCase):
    """Test the incremental median estimator."""

    def test_median_odd(self):
        self.assertEqual(median([1, 2, 3]), 2)

    def test_median_even(self):
        self.assertEqual(median([1, 2, 3, 4]), 2.5)

    def test_median_single(self):
        self.assertEqual(median([42]), 42)

    def test_median_two(self):
        self.assertEqual(median([10, 20]), 15)

    def test_median_empty_raises(self):
        with self.assertRaises(AssertionError):
            median([])

    def test_remedian_basic(self):
        r = remedian()
        for i in range(1000):
            r + i
        m = r.median()
        # Should be close to 500
        self.assertTrue(450 < m < 550, f"Expected ~500, got {m}")

    def test_remedian_inits(self):
        r = remedian(inits=[10, 20, 30])
        m = r.median()
        self.assertTrue(10 <= m <= 30)


class TestConfigManager(unittest.TestCase):
    """Test config default values and conversions."""

    def test_default_config_structure(self):
        from openseeface.config_manager import DEFAULT_CONFIG
        self.assertIn("general", DEFAULT_CONFIG)
        self.assertIn("camera", DEFAULT_CONFIG)
        self.assertIn("tracking", DEFAULT_CONFIG)
        self.assertIn("network", DEFAULT_CONFIG)
        self.assertIn("logging", DEFAULT_CONFIG)

    def test_default_tracking_config(self):
        from openseeface.config_manager import DEFAULT_CONFIG
        t = DEFAULT_CONFIG["tracking"]
        self.assertEqual(t["model"], 3)
        self.assertEqual(t["quality_preset"], 3)
        self.assertGreater(t["detection_threshold"], 0)

    def test_config_manager_loads_defaults(self):
        from openseeface.config_manager import ConfigManager
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cm = ConfigManager(config_dir=td)
            data = cm.load()
            self.assertEqual(data["general"]["mode"], "camera")

    def test_cli_args_conversion(self):
        from openseeface.config_manager import ConfigManager
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cm = ConfigManager(config_dir=td)
            cm.load()
            args = cm.to_cli_args()
            self.assertIn("-c", args)
            self.assertIn("--model", args)

    def test_no_3d_adapt_summary_display(self):
        """Regression test: no_3d_adapt=True means adaptation is CLOSED."""
        from openseeface.config_manager import ConfigManager
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cm = ConfigManager(config_dir=td)
            cm.load()
            summary = cm.to_summary()
            # Default no_3d_adapt=False, so 3D adaptation should show as ON (开启)
            self.assertIn("3D自适应 : 开启", summary)


class TestDefaultConfigImmutability(unittest.TestCase):
    """Regression: modifying loaded config must not mutate DEFAULT_CONFIG."""

    def test_deepcopy_isolation(self):
        import copy
        from openseeface.config_manager import DEFAULT_CONFIG, ConfigManager
        import tempfile
        original_model = DEFAULT_CONFIG['tracking']['model']
        with tempfile.TemporaryDirectory() as td:
            cm = ConfigManager(config_dir=td)
            data = cm.load()
            data['tracking']['model'] = 999
            cm.save()
        self.assertEqual(DEFAULT_CONFIG['tracking']['model'], original_model,
                         "DEFAULT_CONFIG was mutated by shallow copy!")


class TestSimilarityTransform(unittest.TestCase):
    """Test geometry utilities."""

    def test_safe_as_int(self):
        from openseeface.similaritytransform import safe_as_int
        self.assertEqual(safe_as_int(7.0), 7)
        import numpy as np
        arr = safe_as_int([9, 4, 2.9999999999])
        np.testing.assert_array_equal(arr, [9, 4, 3])

    def test_safe_as_int_rejects_float(self):
        from openseeface.similaritytransform import safe_as_int
        with self.assertRaises(ValueError):
            safe_as_int(53.1)


if __name__ == '__main__':
    unittest.main()

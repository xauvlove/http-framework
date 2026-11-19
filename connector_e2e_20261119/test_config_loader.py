"""Unit tests for the pure standard-library configuration loader.

Run them with::

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s connector_e2e_20261119 -v
"""

import json
import os
import pathlib
import sys
import tempfile
import unittest

# Allow the test module to be executed directly as well as through discovery.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from config_loader import (  # noqa: E402  (import after the sys.path tweak)
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    load_config,
    normalize_config,
)


class NormalizeConfigTest(unittest.TestCase):
    """Covers defaults, a valid configuration, invalid timeout and retries."""

    def test_defaults_are_applied_for_missing_values(self):
        """An empty mapping yields the documented default timeout/retries."""
        self.assertEqual(DEFAULT_TIMEOUT, 7)
        self.assertEqual(DEFAULT_RETRIES, 0)
        self.assertEqual(normalize_config({}), {"timeout": 7, "retries": 0})

    def test_valid_configuration_is_preserved_and_loadable_from_json(self):
        """Valid values survive normalisation and a JSON file round trip."""
        raw = {"timeout": 30, "retries": 3, "endpoint": "https://example.com"}

        normalized = normalize_config(raw)

        self.assertEqual(normalized["timeout"], 30)
        self.assertEqual(normalized["retries"], 3)
        self.assertEqual(normalized["endpoint"], "https://example.com")
        # The caller-owned mapping must not be mutated.
        self.assertEqual(
            raw, {"timeout": 30, "retries": 3, "endpoint": "https://example.com"}
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "config.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"timeout": 30, "retries": 3}, handle)

            self.assertEqual(
                load_config(config_path), {"timeout": 30, "retries": 3}
            )
            # os.PathLike paths are supported as well.
            self.assertEqual(
                load_config(pathlib.Path(config_path)),
                {"timeout": 30, "retries": 3},
            )

    def test_invalid_timeout_raises_value_error(self):
        """Non-positive, non-integer and boolean timeouts are rejected."""
        invalid_timeouts = (0, -1, -30, 1.5, "10", None, True, False)

        for timeout in invalid_timeouts:
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    normalize_config({"timeout": timeout})

        # The same rule applies when the configuration comes from a file.
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "invalid.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"timeout": 0}, handle)

            with self.assertRaises(ValueError):
                load_config(config_path)

    def test_invalid_retries(self):
        """Negative, boolean and string retries are rejected."""
        invalid_retries = (-1, -5, True, False, "3", "abc")

        for retries in invalid_retries:
            with self.subTest(retries=retries):
                with self.assertRaises(ValueError):
                    normalize_config({"retries": retries})

        # The same rule applies when the configuration comes from a file.
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "invalid_retries.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"retries": -1}, handle)

            with self.assertRaises(ValueError):
                load_config(config_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

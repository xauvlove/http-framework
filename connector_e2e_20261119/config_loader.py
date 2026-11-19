"""Pure standard-library configuration loader.

This module intentionally depends on nothing but the Python standard library
(``json`` and ``os``), so it can be dropped into any environment without
installing extra packages.

Public API
----------
normalize_config(config) -> dict
    Validate and normalise a raw configuration mapping.
load_config(path) -> dict
    Read a JSON file and return its normalised configuration.

Both functions raise ``ValueError`` when the input is invalid, which also
covers malformed JSON because ``json.JSONDecodeError`` is a subclass of
``ValueError``.
"""

import json
import os

__all__ = [
    "DEFAULT_TIMEOUT",
    "DEFAULT_RETRIES",
    "normalize_config",
    "load_config",
]

#: Default value used when the ``timeout`` key is absent.
DEFAULT_TIMEOUT = 5

#: Default value used when the ``retries`` key is absent.
DEFAULT_RETRIES = 0


def _require_int(value, name, minimum, requirement):
    """Return ``value`` as an int or raise ``ValueError``.

    ``bool`` is rejected explicitly: ``isinstance(True, int)`` is ``True`` in
    Python, but a boolean is never a meaningful timeout/retries value.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            "{0} must be {1}, got {2!r} of type {3}".format(
                name, requirement, value, type(value).__name__
            )
        )
    if value < minimum:
        raise ValueError(
            "{0} must be {1}, got {2!r}".format(name, requirement, value)
        )
    return value


def normalize_config(config):
    """Validate a raw configuration mapping and return a normalised copy.

    Rules:

    * ``timeout`` defaults to :data:`DEFAULT_TIMEOUT` (5) and must be a
      positive integer. Booleans are rejected.
    * ``retries`` defaults to :data:`DEFAULT_RETRIES` (0) and must be a
      non-negative integer. Booleans are rejected.
    * Any other key is preserved untouched.
    * The input mapping is never mutated; a new dictionary is returned.

    Raises:
        ValueError: if ``config`` is not a dict, or if ``timeout``/``retries``
            hold an invalid value.
    """
    if not isinstance(config, dict):
        raise ValueError(
            "config must be a dict, got {0}".format(type(config).__name__)
        )

    normalized = dict(config)

    timeout = normalized.get("timeout", DEFAULT_TIMEOUT)
    retries = normalized.get("retries", DEFAULT_RETRIES)

    normalized["timeout"] = _require_int(
        timeout, "timeout", 1, "a positive integer"
    )
    normalized["retries"] = _require_int(
        retries, "retries", 0, "a non-negative integer"
    )
    return normalized


def load_config(path):
    """Read a JSON configuration file and return its normalised form.

    Args:
        path: path to the JSON file, as a ``str`` or ``os.PathLike``.

    Returns:
        dict: the normalised configuration.

    Raises:
        ValueError: if the path is not a string/path-like object, if the file
            does not contain a JSON object, or if a value is invalid.
        OSError: if the file cannot be read (for example it does not exist).
    """
    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    elif not isinstance(path, str):
        raise ValueError(
            "path must be a str or os.PathLike, got {0}".format(
                type(path).__name__
            )
        )

    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    return normalize_config(raw)

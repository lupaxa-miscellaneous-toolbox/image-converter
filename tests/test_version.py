"""Smoke tests for lupaxa.image_converter version."""

from __future__ import annotations

from lupaxa.image_converter.version import __version__, get_version


def test_version_is_semver_like() -> None:
    """The package version is a dotted string with numeric major and minor parts."""
    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) >= 2
    assert all(part.isdigit() for part in parts[:2])


def test_get_version_matches_dunder() -> None:
    """``get_version()`` returns the module's ``__version__``."""
    assert get_version() == __version__

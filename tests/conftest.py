"""Shared image fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def png_source(tmp_path: Path) -> Path:
    """Return a small RGBA PNG with one opaque red pixel."""
    path = tmp_path / "photo.png"
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    image.putpixel((0, 0), (200, 10, 10, 255))
    image.save(path)
    return path


@pytest.fixture
def svg_source(tmp_path: Path) -> Path:
    """Return a tiny SVG circle."""
    path = tmp_path / "logo.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">'
        '<circle cx="8" cy="8" r="6" fill="#336699"/></svg>',
        encoding="utf-8",
    )
    return path

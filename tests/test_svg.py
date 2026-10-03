"""SVG input tests. Skipped when native Cairo is unavailable."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from lupaxa.image_converter.cli import main
from lupaxa.image_converter.convert import convert_image


def _cairo_works() -> bool:
    try:
        import cairosvg

        png = cairosvg.svg2png(
            bytestring=(
                b'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8">'
                b'<rect width="8" height="8" fill="red"/></svg>'
            )
        )
    except Exception:
        return False
    return bool(png)


pytestmark = pytest.mark.cairo


@pytest.mark.skipif(not _cairo_works(), reason="native Cairo / cairosvg unavailable")
def test_svg_to_png(svg_source: Path, tmp_path: Path) -> None:
    """SVG input is rasterised to a PNG."""
    destination = tmp_path / "logo.png"
    convert_image(svg_source, destination, 90)
    with Image.open(destination) as image:
        assert image.format == "PNG"
        assert image.size == (16, 16)


@pytest.mark.skipif(not _cairo_works(), reason="native Cairo / cairosvg unavailable")
def test_cli_svg_to_jpeg(
    svg_source: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI rasterises SVG to JPEG."""
    destination = tmp_path / "logo.jpeg"
    assert main([str(svg_source), str(destination)]) == 0
    assert "Converted:" in capsys.readouterr().out
    with Image.open(destination) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"

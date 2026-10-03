"""Conversion behaviour for raster formats and embedded SVG."""

from __future__ import annotations

import io
import sys
import types
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PIL import Image

from lupaxa.image_converter.convert import (
    CAIRO_DEPENDENCY_ERROR,
    _convert_raster_to_svg,
    _save_raster,
    convert_image,
)
from lupaxa.image_converter.exceptions import InputError


def test_png_to_jpeg_flattens_transparency(tmp_path: Path) -> None:
    """A fully transparent PNG becomes a white JPEG."""
    source = tmp_path / "clear.png"
    Image.new("RGBA", (16, 16), (0, 0, 0, 0)).save(source)
    destination = tmp_path / "clear.jpg"
    convert_image(source, destination, 95)

    with Image.open(destination) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"
        pixel = image.getpixel((8, 8))
    assert pixel == (255, 255, 255)


def test_png_to_webp_and_gif(png_source: Path, tmp_path: Path) -> None:
    """PNG converts to WebP and GIF."""
    webp = tmp_path / "photo.webp"
    gif = tmp_path / "photo.gif"
    convert_image(png_source, webp, 90)
    convert_image(png_source, gif, 90)

    with Image.open(webp) as image:
        assert image.format == "WEBP"
        assert image.size == (4, 4)
    with Image.open(gif) as image:
        assert image.format == "GIF"
        assert image.size == (4, 4)


def test_png_to_svg_embeds_pixels(png_source: Path, tmp_path: Path) -> None:
    """Raster to SVG wraps the original bytes and does not trace vectors."""
    destination = tmp_path / "photo.svg"
    convert_image(png_source, destination, 90)
    svg = destination.read_text(encoding="utf-8")
    assert 'width="4"' in svg
    assert 'height="4"' in svg
    assert "data:image/png;base64," in svg
    assert "<image" in svg


def test_rejects_same_format(png_source: Path, tmp_path: Path) -> None:
    """Identical suffixes are refused."""
    with pytest.raises(InputError, match="same"):
        convert_image(png_source, tmp_path / "other.png", 90)


def test_rejects_unsupported_suffixes(png_source: Path, tmp_path: Path) -> None:
    """Unknown suffixes are refused before any write."""
    bmp = tmp_path / "scan.bmp"
    bmp.write_bytes(b"not-an-image")
    with pytest.raises(InputError, match="unsupported input format"):
        convert_image(bmp, tmp_path / "scan.png", 90)
    with pytest.raises(InputError, match="unsupported output format"):
        convert_image(png_source, tmp_path / "photo.tiff", 90)


def test_rejects_quality_out_of_range(png_source: Path, tmp_path: Path) -> None:
    """Quality must stay inside 1 to 100."""
    with pytest.raises(InputError, match="quality"):
        convert_image(png_source, tmp_path / "photo.jpg", 0)


def test_rejects_unreadable_raster(tmp_path: Path) -> None:
    """A supported suffix with invalid bytes is an input error."""
    source = tmp_path / "broken.png"
    source.write_bytes(b"not a png")
    with pytest.raises(InputError, match="cannot read image"):
        convert_image(source, tmp_path / "broken.jpg", 90)


def test_rejects_missing_suffix_and_high_quality(png_source: Path, tmp_path: Path) -> None:
    """A file with no suffix, and quality above 100, are input errors."""
    plain = tmp_path / "noext"
    plain.write_bytes(b"x")
    with pytest.raises(InputError, match=r"\(none\)"):
        convert_image(plain, tmp_path / "noext.png", 90)
    with pytest.raises(InputError, match="quality"):
        convert_image(png_source, tmp_path / "photo.jpg", 101)


def test_other_raster_modes_and_png_output(tmp_path: Path) -> None:
    """Greyscale, RGB, and LA sources convert, including JPEG to PNG."""
    grey = tmp_path / "grey.png"
    Image.new("L", (8, 8), 40).save(grey)
    convert_image(grey, tmp_path / "grey.jpg", 90)
    convert_image(grey, tmp_path / "grey.gif", 90)

    rgb = tmp_path / "rgb.png"
    Image.new("RGB", (8, 8), (20, 30, 40)).save(rgb)
    convert_image(rgb, tmp_path / "rgb.jpeg", 90)

    alpha = tmp_path / "alpha.png"
    Image.new("LA", (8, 8), (12, 0)).save(alpha)
    convert_image(alpha, tmp_path / "alpha.jpg", 90)

    with Image.open(tmp_path / "grey.jpg") as image:
        assert image.format == "JPEG"
    with Image.open(tmp_path / "grey.gif") as image:
        assert image.format == "GIF"
    convert_image(tmp_path / "grey.jpg", tmp_path / "grey-out.png", 90)
    with Image.open(tmp_path / "grey-out.png") as image:
        assert image.format == "PNG"


def test_svg_rasterise_is_wrapped(
    svg_source: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SVG conversion uses cairosvg output and reports rasteriser failures."""
    buffer = io.BytesIO()
    Image.new("RGBA", (16, 16), (10, 20, 30, 128)).save(buffer, format="PNG")
    payload = buffer.getvalue()
    fake = types.ModuleType("cairosvg")

    def svg2png(*, bytestring: bytes) -> bytes:
        assert b"<svg" in bytestring
        return payload

    fake.svg2png = svg2png  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "cairosvg", fake)

    destination = tmp_path / "logo.png"
    convert_image(svg_source, destination, 90)
    with Image.open(destination) as image:
        assert image.format == "PNG"
        assert image.size == (16, 16)

    def fail_os(*, bytestring: bytes) -> bytes:
        raise OSError("cairo missing")

    fake.svg2png = fail_os  # type: ignore[attr-defined]
    with pytest.raises(InputError, match="Cairo"):
        convert_image(svg_source, tmp_path / "logo.jpg", 90)

    def fail_parse(*, bytestring: bytes) -> bytes:
        raise ValueError("bad svg")

    fake.svg2png = fail_parse  # type: ignore[attr-defined]
    with pytest.raises(InputError, match="failed to rasterise"):
        convert_image(svg_source, tmp_path / "logo.webp", 90)

    def empty(*, bytestring: bytes) -> bytes:
        return b""

    fake.svg2png = empty  # type: ignore[attr-defined]
    with pytest.raises(InputError, match="failed to rasterise"):
        convert_image(svg_source, tmp_path / "logo.gif", 90)

    def fail_xml(*, bytestring: bytes) -> bytes:
        raise ElementTree.ParseError("bad svg")

    fake.svg2png = fail_xml  # type: ignore[attr-defined]
    with pytest.raises(InputError, match="failed to rasterise"):
        convert_image(svg_source, tmp_path / "logo.gif", 90)


def test_missing_cairosvg_is_an_input_error(
    svg_source: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing cairosvg install is reported as an input error."""
    monkeypatch.delitem(sys.modules, "cairosvg", raising=False)
    real_import = __import__

    def blocked(name: str, *args: object, **kwargs: object) -> object:
        if name == "cairosvg":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked)
    with pytest.raises(InputError, match=CAIRO_DEPENDENCY_ERROR):
        convert_image(svg_source, tmp_path / "logo.png", 90)


def test_internal_format_guards(tmp_path: Path) -> None:
    """Private savers reject suffixes the public API already filters."""
    with pytest.raises(InputError, match="unsupported raster output format"):
        _save_raster(Image.new("RGB", (2, 2), "red"), tmp_path / "photo.bmp", 90)
    with pytest.raises(InputError, match="cannot embed"):
        _convert_raster_to_svg(tmp_path / "logo.svg", tmp_path / "logo-out.svg")

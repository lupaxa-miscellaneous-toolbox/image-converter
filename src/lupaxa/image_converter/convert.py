"""Convert images between raster formats and SVG."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Final
from xml.etree import ElementTree

from PIL import Image, UnidentifiedImageError

from .exceptions import InputError

SUPPORTED_FORMATS: Final[frozenset[str]] = frozenset({"jpg", "jpeg", "png", "gif", "webp", "svg"})
SUPPORTED_SUFFIXES: Final[frozenset[str]] = frozenset(
    f".{format_name}" for format_name in SUPPORTED_FORMATS
)
JPEG_SUFFIXES: Final[frozenset[str]] = frozenset({".jpg", ".jpeg"})
_MIME_TYPES: Final[dict[str, str]] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
CAIRO_DEPENDENCY_ERROR: Final[str] = (
    "SVG input requires cairosvg and the native Cairo library. "
    "Install with: python -m pip install cairosvg; "
    "macOS: brew install cairo; Debian/Ubuntu: apt install libcairo2"
)


def convert_image(source: Path, destination: Path, quality: int) -> None:
    """Convert an image to another supported format.

    Parameters
    ----------
    source
        Existing image file.
    destination
        Output path. The suffix selects the format.
    quality
        JPEG and WebP quality, from 1 to 100.

    Raises
    ------
    InputError
        The path, format, or quality is not valid for conversion.
    """
    if not 1 <= quality <= 100:
        raise InputError("quality must be between 1 and 100.")

    source_suffix = source.suffix.lower()
    destination_suffix = destination.suffix.lower()
    _require_supported_suffix(source_suffix, "input")
    _require_supported_suffix(destination_suffix, "output")

    if source_suffix == destination_suffix:
        raise InputError("input and output formats are the same.")

    if source_suffix == ".svg":
        _convert_svg_to_raster(source, destination, quality)
    elif destination_suffix == ".svg":
        _convert_raster_to_svg(source, destination)
    else:
        _convert_raster_to_raster(source, destination, quality)


def _require_supported_suffix(suffix: str, role: str) -> None:
    if suffix not in SUPPORTED_SUFFIXES:
        shown = suffix or "(none)"
        raise InputError(f"unsupported {role} format: {shown}")


def _flatten_for_jpeg(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"}:
        background = Image.new("RGB", image.size, "white")
        background.paste(image, mask=image.getchannel("A"))
        return background
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def _save_raster(image: Image.Image, destination: Path, quality: int) -> None:
    suffix = destination.suffix.lower()
    if suffix in JPEG_SUFFIXES:
        _flatten_for_jpeg(image).save(
            destination,
            format="JPEG",
            quality=quality,
            optimize=True,
        )
        return
    if suffix == ".png":
        image.save(destination, format="PNG", optimize=True)
        return
    if suffix == ".webp":
        image.save(destination, format="WEBP", quality=quality, method=6)
        return
    if suffix == ".gif":
        prepared = image if image.mode in {"P", "L"} else image.convert("RGBA")
        prepared.save(destination, format="GIF")
        return
    raise InputError(f"unsupported raster output format: {suffix}")


def _read_image(source: Path) -> Image.Image:
    try:
        with Image.open(source) as image:
            image.load()
            return image.copy()
    except UnidentifiedImageError as exc:
        raise InputError(f"cannot read image: {source}") from exc


def _convert_raster_to_raster(source: Path, destination: Path, quality: int) -> None:
    _save_raster(_read_image(source), destination, quality)


def _rasterise_svg(source: Path) -> bytes:
    try:
        import cairosvg
    except ImportError as exc:
        raise InputError(CAIRO_DEPENDENCY_ERROR) from exc

    try:
        png_data = cairosvg.svg2png(bytestring=source.read_bytes())
    except OSError as exc:
        raise InputError(CAIRO_DEPENDENCY_ERROR) from exc
    except (ValueError, ElementTree.ParseError) as exc:
        raise InputError(f"failed to rasterise SVG: {source}") from exc

    if not isinstance(png_data, bytes) or not png_data:
        raise InputError(f"failed to rasterise SVG: {source}")
    return png_data


def _convert_svg_to_raster(source: Path, destination: Path, quality: int) -> None:
    with Image.open(io.BytesIO(_rasterise_svg(source))) as image:
        image.load()
        _save_raster(image, destination, quality)


def _convert_raster_to_svg(source: Path, destination: Path) -> None:
    """Embed a raster image inside an SVG document.

    This does not vectorise the raster image.
    """
    suffix = source.suffix.lower()
    mime_type = _MIME_TYPES.get(suffix)
    if mime_type is None:
        raise InputError(f"cannot embed unsupported format in SVG: {suffix}")

    image = _read_image(source)
    width, height = image.size
    encoded = base64.b64encode(source.read_bytes()).decode("ascii")
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<svg\n"
        '  xmlns="http://www.w3.org/2000/svg"\n'
        f'  width="{width}"\n'
        f'  height="{height}"\n'
        f'  viewBox="0 0 {width} {height}">\n'
        "  <image\n"
        f'    width="{width}"\n'
        f'    height="{height}"\n'
        f'    href="data:{mime_type};base64,{encoded}" />\n'
        "</svg>\n"
    )
    destination.write_text(svg, encoding="utf-8")

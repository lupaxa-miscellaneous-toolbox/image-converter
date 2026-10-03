"""Command-line interface for lupaxa.image_converter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .convert import SUPPORTED_FORMATS, convert_image
from .exceptions import ImageConverterError, InputError


def build_destination(
    source: Path,
    output: Path | None,
    output_format: str | None,
) -> Path:
    """Resolve the output path from an explicit path or ``--format``."""
    if output is not None:
        return output.expanduser().resolve()
    if output_format is None:
        raise InputError("specify either an output filename or --format.")
    return source.with_suffix(f".{output_format.lower()}")


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert images between JPG, JPEG, PNG, GIF, WebP, and SVG.",
        epilog=(
            "examples:\n"
            "  image-converter photo.png photo.webp\n"
            "  image-converter photo.png --format webp\n"
            "  image-converter logo.svg --format png\n"
            "\n"
            "Raster images converted to SVG are embedded. "
            "This does not vectorise the image."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Input image.")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output image. Optional when --format is used.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=sorted(SUPPORTED_FORMATS),
        help="Output format. The output name is the input name with this suffix.",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=90,
        metavar="1-100",
        help="JPEG and WebP quality from 1 to 100. Default: 90.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Convert one image and return a process exit code."""
    try:
        args = parse_arguments(argv)
        source = args.input.expanduser().resolve()
        if not source.exists():
            raise InputError(f"input file does not exist: {source}")
        if not source.is_file():
            raise InputError(f"input path is not a file: {source}")

        destination = build_destination(source, args.output, args.format)
        if args.output is not None and args.format is not None:
            requested_suffix = f".{args.format.lower()}"
            if destination.suffix.lower() != requested_suffix:
                raise InputError(
                    f"the output filename extension does not match --format {args.format}."
                )

        destination.parent.mkdir(parents=True, exist_ok=True)
        convert_image(source, destination, args.quality)
    except (ImageConverterError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Converted: {source}")
    print(f"Output:    {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

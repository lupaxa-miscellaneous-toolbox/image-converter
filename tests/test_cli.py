"""CLI exit codes and output paths."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

from lupaxa.image_converter.cli import main


def test_format_flag_writes_beside_input(
    png_source: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--format`` replaces the input suffix."""
    assert main([str(png_source), "--format", "webp"]) == 0
    destination = png_source.with_suffix(".webp")
    assert destination.is_file()
    captured = capsys.readouterr()
    assert "Converted:" in captured.out
    assert str(destination) in captured.out


def test_output_and_format_can_agree(png_source: Path, tmp_path: Path) -> None:
    """An output path is accepted when its suffix matches ``--format``."""
    destination = tmp_path / "photo.webp"
    assert main([str(png_source), str(destination), "--format", "webp"]) == 0
    assert destination.is_file()


def test_explicit_output_creates_parents(png_source: Path, tmp_path: Path) -> None:
    """An explicit output path is created, including missing parents."""
    destination = tmp_path / "nested" / "out" / "photo.jpg"
    assert main([str(png_source), str(destination)]) == 0
    with Image.open(destination) as image:
        assert image.format == "JPEG"


def test_format_must_match_output_suffix(
    png_source: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--format`` and the output suffix have to agree."""
    destination = tmp_path / "photo.jpg"
    assert main([str(png_source), str(destination), "--format", "png"]) == 1
    assert "does not match" in capsys.readouterr().err
    assert not destination.exists()


def test_missing_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing input file exits 1."""
    missing = tmp_path / "missing.png"
    assert main([str(missing), "--format", "webp"]) == 1
    assert "does not exist" in capsys.readouterr().err


def test_directory_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A directory is not a valid input image."""
    assert main([str(tmp_path), "--format", "png"]) == 1
    assert "not a file" in capsys.readouterr().err


def test_requires_output_or_format(
    png_source: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command needs an output path or ``--format``."""
    assert main([str(png_source)]) == 1
    assert "--format" in capsys.readouterr().err


def test_bad_quality_is_an_error(
    png_source: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Quality outside 1-100 is reported on stderr."""
    assert main([str(png_source), "--format", "jpg", "--quality", "0"]) == 1
    assert "quality" in capsys.readouterr().err


def test_argparse_rejects_unknown_format(png_source: Path) -> None:
    """An unknown ``--format`` choice exits through argparse."""
    with pytest.raises(SystemExit) as caught:
        main([str(png_source), "--format", "bmp"])
    assert caught.value.code == 2


def test_module_entrypoint(png_source: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``python -m lupaxa.image_converter`` runs the CLI."""
    import runpy

    monkeypatch.setattr(
        sys,
        "argv",
        ["image-converter", str(png_source), "--format", "gif"],
    )
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("lupaxa.image_converter", run_name="__main__")
    assert caught.value.code == 0
    assert png_source.with_suffix(".gif").is_file()

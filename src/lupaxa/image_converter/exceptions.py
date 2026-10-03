"""Exceptions for lupaxa.image_converter."""

from __future__ import annotations


class ImageConverterError(Exception):
    """Base error for image conversion failures."""


class InputError(ImageConverterError):
    """Invalid path, format, or conversion request."""

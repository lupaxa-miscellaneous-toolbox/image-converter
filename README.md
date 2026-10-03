<p align="center">
    <a href="https://github.com/lupaxa-miscellaneous-toolbox">
        <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/miscellaneous-toolbox/readme-logo.png" alt="Organisation Logo" />
    </a>
</p>

<h1 align="center">Image Converter</h1>

Convert an image from one format to another: JPG, JPEG, PNG, GIF, WebP, and SVG.

Raster formats are converted with Pillow. SVG input is rasterised with CairoSVG.
A raster image converted to SVG is embedded in an SVG document.

> **Note:** Embedding a raster image in SVG does not vectorise it.

## Install

Python 3.10 or newer. The PyPI package name is `lupaxa-image-converter`.
The console command is `image-converter`.

SVG input also needs the system Cairo library (`brew install cairo` on macOS,
or `apt install libcairo2` on Debian/Ubuntu).

```bash
python -m pip install lupaxa-image-converter
```

From a clone, for development:

```bash
python -m pip install -e ".[dev]"
```

## Use

```bash
image-converter photo.png photo.webp
image-converter photo.png --format webp
image-converter logo.svg --format png
```

The same commands work as a module:

```bash
python -m lupaxa.image_converter photo.png --format webp
```

`--format` writes the result next to the input, using the input name and the
new suffix. Pass an output path when the file should live somewhere else.
If you pass both, the output suffix must match `--format`.

JPEG output flattens transparency onto white. `--quality` applies to JPEG
and WebP (default 90).

## CLI Options

Run `image-converter --help` for the authoritative list from your installed
version.

| Option             | Default      | Description                                      |
| :----------------- | :----------- | :----------------------------------------------- |
| `input`            | *(required)* | Input image.                                     |
| `output`           |              | Output image. Optional when `--format` is used.  |
| `-f` / `--format`  |              | `jpg`, `jpeg`, `png`, `gif`, `webp`, or `svg`.   |
| `-q` / `--quality` | `90`         | JPEG and WebP quality from 1 to 100.             |

## Testing

```bash
make init
make python-install-dev
make python-check
```

Or without Make:

```bash
python -m pip install -e ".[test]"
pytest
```

Coverage for `lupaxa.image_converter` is reported by default. SVG tests run
when native Cairo is available and skip otherwise:

```bash
pytest -m cairo
```

<a href="https://github.com/the-lupaxa-project">
    <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>

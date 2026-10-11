"""Create a multi-page PDF from local image files with Pillow and PyMuPDF."""

from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
import tempfile

import fitz
from PIL import Image, ImageOps

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path

DEFAULT_DPI = 150
MIN_DPI = 36
MAX_DPI = 600


def images_to_pdf(
    input_paths: list[str | os.PathLike[str]],
    output_path: str | os.PathLike[str],
    *,
    dpi: int = DEFAULT_DPI,
    overwrite: bool = False,
) -> Path:
    """Create one PDF page per image, preserving supplied order and aspect ratio."""
    if not input_paths:
        raise PDFOperationError("Select at least one image to convert.")
    if type(dpi) is not int or not MIN_DPI <= dpi <= MAX_DPI:
        raise PDFOperationError(f"Image resolution must be between {MIN_DPI} and {MAX_DPI} DPI.")
    sources = [Path(path).expanduser() for path in input_paths]
    for source in sources:
        if not source.exists():
            raise PDFOperationError(f"The selected image was not found: {source}")
        if not source.is_file():
            raise PDFOperationError(f"The selected path is not a file: {source}")
    output = validate_pdf_output_path(output_path, sources, overwrite=overwrite)

    document = fitz.open()
    temporary_path: Path | None = None
    try:
        for source in sources:
            try:
                with Image.open(source) as opened:
                    image = ImageOps.exif_transpose(opened)
                    image.seek(0)
                    # Flatten transparency consistently on white and normalize
                    # palette, grayscale, and CMYK sources to PDF-friendly RGB.
                    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                        rgba = image.convert("RGBA")
                        background = Image.new("RGBA", rgba.size, "white")
                        background.alpha_composite(rgba)
                        normalized = background.convert("RGB")
                    else:
                        normalized = image.convert("RGB")
                    width, height = normalized.size
                    if width < 1 or height < 1:
                        raise ValueError("image has no pixels")
                    page_width, page_height = width * 72 / dpi, height * 72 / dpi
                    if page_width > 14_000 or page_height > 14_000:
                        raise ValueError("image dimensions exceed PDF page limits at the selected resolution")
                    image_bytes = BytesIO()
                    normalized.save(image_bytes, format="PNG", optimize=True)
                    page = document.new_page(width=page_width, height=page_height)
                    page.insert_image(page.rect, stream=image_bytes.getvalue())
                    normalized.close()
            except Exception as exc:
                if isinstance(exc, PDFOperationError):
                    raise
                raise PDFOperationError(f"Could not read image '{source}': {exc}") from exc

        try:
            with tempfile.NamedTemporaryFile(
                prefix=f".{output.stem}_", suffix=".pdf", dir=output.parent, delete=False,
            ) as temp_file:
                temporary_path = Path(temp_file.name)
            temporary_path.unlink()
            document.save(str(temporary_path), garbage=3, deflate=True)
            document.close()
            document = None
        except Exception as exc:
            raise PDFOperationError(f"Could not create the PDF: {exc}") from exc

        try:
            if overwrite:
                os.replace(temporary_path, output)
            else:
                try:
                    os.link(temporary_path, output)
                except FileExistsError as exc:
                    raise PDFOperationError(
                        "The output file already exists. Confirm replacement to continue."
                    ) from exc
                temporary_path.unlink()
            temporary_path = None
        except PDFOperationError:
            raise
        except Exception as exc:
            raise PDFOperationError(f"Could not save the PDF to '{output}': {exc}") from exc
    finally:
        if document is not None:
            document.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return output

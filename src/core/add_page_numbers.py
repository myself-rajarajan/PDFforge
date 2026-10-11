"""Add locally rendered page numbers to PDF documents with PyMuPDF."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

import pymupdf as fitz

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path


PAGE_NUMBER_POSITIONS = {
    "Top-left": "top-left",
    "Top-center": "top-center",
    "Top-right": "top-right",
    "Bottom-left": "bottom-left",
    "Bottom-center": "bottom-center",
    "Bottom-right": "bottom-right",
}
MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 72
MAX_STARTING_NUMBER = 1_000_000_000


def _validate_settings(starting_number: int, font_size: int, position: str) -> None:
    if type(starting_number) is not int or not 1 <= starting_number <= MAX_STARTING_NUMBER:
        raise PDFOperationError(
            f"Starting page number must be between 1 and {MAX_STARTING_NUMBER}."
        )
    if type(font_size) is not int or not MIN_FONT_SIZE <= font_size <= MAX_FONT_SIZE:
        raise PDFOperationError(
            f"Font size must be between {MIN_FONT_SIZE} and {MAX_FONT_SIZE} points."
        )
    if position not in PAGE_NUMBER_POSITIONS.values():
        raise PDFOperationError("Choose one of the six supported page number positions.")


def add_page_numbers(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    *,
    position: str = "bottom-center",
    starting_number: int = 1,
    font_size: int = 12,
    overwrite: bool = False,
) -> Path:
    """Add sequential page numbers, preserving page order/content and writing atomically."""
    _validate_settings(starting_number, font_size, position)
    source = Path(input_path).expanduser()
    if not source.exists():
        raise PDFOperationError(f"The selected PDF was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected path is not a file: {source}")
    output = validate_pdf_output_path(output_path, [source], overwrite=overwrite)

    temporary_path: Path | None = None
    document: fitz.Document | None = None
    try:
        try:
            document = fitz.open(source)
            if document.needs_pass:
                raise PDFOperationError(
                    f"'{source.name}' is password-protected. PDFForge will not bypass its password."
                )
            if document.page_count < 1:
                raise PDFOperationError("The selected PDF does not contain any pages.")
        except PDFOperationError:
            raise
        except Exception as exc:
            raise PDFOperationError(f"Could not read '{source}': {exc}") from exc

        font = fitz.Font("helv")
        margin = max(12.0, float(font_size))
        for page_index, page in enumerate(document):
            label = str(starting_number + page_index)
            page_rect = page.rect
            text_width = font.text_length(label, fontsize=font_size)
            ascender = font.ascender * font_size
            descender = abs(font.descender * font_size)
            if (page_rect.width < text_width + margin * 2 or
                    page_rect.height < ascender + descender + margin * 2):
                raise PDFOperationError(
                    f"Page {page_index + 1} is too small for the selected font size and margins."
                )

            vertical, horizontal = position.split("-")
            if horizontal == "left":
                x = page_rect.x0 + margin
            elif horizontal == "right":
                x = page_rect.x1 - margin - text_width
            else:
                x = page_rect.x0 + (page_rect.width - text_width) / 2

            if vertical == "top":
                y = page_rect.y0 + margin + ascender
            else:
                y = page_rect.y1 - margin - descender

            # PyMuPDF insertion coordinates are unrotated; map the visible
            # position back so labels stay inside rotated pages too.
            point = fitz.Point(x, y) * page.derotation_matrix
            try:
                page.insert_text(point, label, fontname="helv", fontsize=font_size)
            except Exception as exc:
                raise PDFOperationError(
                    f"Could not add a page number to page {page_index + 1}: {exc}"
                ) from exc

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
            raise PDFOperationError(f"Could not create the numbered PDF: {exc}") from exc

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
            raise PDFOperationError(f"Could not save the numbered PDF to '{output}': {exc}") from exc
    finally:
        if document is not None:
            document.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    return output

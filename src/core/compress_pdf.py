"""Best-effort local PDF cleanup and image compression using PyMuPDF."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import tempfile

import pymupdf

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path


IMAGE_DPI_THRESHOLD = 200
MIN_IMAGE_QUALITY = 20
MAX_IMAGE_QUALITY = 95
DEFAULT_IMAGE_QUALITY = 75


def target_dpi_for_quality(quality: int) -> int:
    """Map the visible image-quality slider to a gentle downsampling target."""
    if type(quality) is not int or not MIN_IMAGE_QUALITY <= quality <= MAX_IMAGE_QUALITY:
        raise PDFOperationError(
            f"Image quality must be between {MIN_IMAGE_QUALITY} and {MAX_IMAGE_QUALITY}."
        )
    return 100 + (quality * 2 // 3)


def compression_savings_percent(original_size: int, output_size: int) -> float | None:
    """Return percentage saved, or None when the original size is zero."""
    if original_size < 0 or output_size < 0:
        raise PDFOperationError("File sizes cannot be negative.")
    if original_size == 0:
        return None
    return (original_size - output_size) * 100.0 / original_size


def format_file_size(size: int) -> str:
    """Format a byte count for user-facing size summaries."""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GB"


def compression_result_text(original_size: int, output_size: int) -> str:
    """Describe reductions, unchanged size, or growth accurately."""
    savings = compression_savings_percent(original_size, output_size)
    if savings is None:
        return "Size change could not be calculated because the original file is empty."
    if savings > 0:
        return f"Saved {savings:.1f}% of the original size."
    if savings == 0:
        return "No size reduction (0.0%)."
    return f"The output is {abs(savings):.1f}% larger than the original."


def compress_pdf(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    *,
    quality: int = DEFAULT_IMAGE_QUALITY,
    overwrite: bool = False,
) -> Path:
    """Optimize high-resolution images and rewrite a PDF with cleanup/deflation.

    Lower image quality values trade image detail for smaller image streams.
    Output size remains content-dependent and cannot be guaranteed.
    """
    target_dpi = target_dpi_for_quality(quality)
    source = Path(input_path).expanduser()
    if not source.exists():
        raise PDFOperationError(f"The selected PDF was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected path is not a file: {source}")
    output = validate_pdf_output_path(output_path, [source], overwrite=overwrite)

    temporary_path: Path | None = None
    document: pymupdf.Document | None = None
    try:
        try:
            document = pymupdf.open(source)
            if document.needs_pass:
                raise PDFOperationError(
                    f"'{source.name}' is password-protected. Unlock it with its authorized password before compressing."
                )
            if document.page_count < 1:
                raise PDFOperationError("The selected PDF does not contain any pages.")
        except PDFOperationError:
            raise
        except Exception as exc:
            raise PDFOperationError(f"Could not read '{source}': {exc}") from exc

        try:
            # Recompress/downsample only images over the threshold. Page text and
            # vector content stay as PDF objects; image fidelity may be reduced.
            document.rewrite_images(
                dpi_threshold=IMAGE_DPI_THRESHOLD,
                dpi_target=target_dpi,
                quality=quality,
                lossy=True,
                lossless=True,
                bitonal=True,
            )
            with tempfile.NamedTemporaryFile(
                prefix=f".{output.stem}_", suffix=".pdf", dir=output.parent, delete=False,
            ) as temp_file:
                temporary_path = Path(temp_file.name)
            temporary_path.unlink()
            document.save(
                str(temporary_path),
                garbage=4,
                clean=True,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
            )
            document.close()
            document = None
        except Exception as exc:
            raise PDFOperationError(
                "Could not compress the PDF. Check that it is a supported PDF and the destination has enough free space."
            ) from exc

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
        raise PDFOperationError(
            "Could not save the compressed PDF. Check that the destination is writable and has enough free space."
        ) from exc
    finally:
        if document is not None:
            document.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    return output


def estimate_compressed_size(
    input_path: str | os.PathLike[str],
    *,
    quality: int = DEFAULT_IMAGE_QUALITY,
) -> int:
    """Measure a temporary compression pass without creating a user output."""
    with tempfile.TemporaryDirectory(prefix="pdfforge_compression_estimate_") as folder:
        estimate_path = Path(folder) / "estimate.pdf"
        compress_pdf(input_path, estimate_path, quality=quality)
        return estimate_path.stat().st_size

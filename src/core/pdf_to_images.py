"""Export PDF pages as local raster image files."""

from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
import tempfile
from typing import Callable

import fitz
from PIL import Image

from src.core.pdf_output import PDFOperationError

SUPPORTED_FORMATS = {"PNG": ".png", "JPEG": ".jpg", "TIFF": ".tiff", "WEBP": ".webp"}
DEFAULT_DPI = 150
MIN_DPI = 36
MAX_DPI = 600


def expected_image_paths(output_folder: str | os.PathLike[str], page_count: int, image_format: str) -> list[Path]:
    """Return predictable one-based image paths for the selected export format."""
    if type(page_count) is not int or page_count < 1:
        raise PDFOperationError("The PDF must contain at least one page.")
    normalized = image_format.upper()
    extension = SUPPORTED_FORMATS.get(normalized)
    if extension is None:
        raise PDFOperationError("Choose PNG, JPEG, TIFF, or WebP as the output format.")
    return [Path(output_folder) / f"page_{index:03d}{extension}" for index in range(1, page_count + 1)]


def pdf_to_images(
    input_path: str | os.PathLike[str],
    output_folder: str | os.PathLike[str],
    *,
    image_format: str = "PNG",
    dpi: int = DEFAULT_DPI,
    overwrite: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[Path]:
    """Render pages in order and install a complete image set in the destination folder."""
    source = Path(input_path).expanduser()
    folder = Path(output_folder).expanduser().absolute()
    normalized = image_format.upper()
    if normalized not in SUPPORTED_FORMATS:
        raise PDFOperationError("Choose PNG, JPEG, TIFF, or WebP as the output format.")
    if type(dpi) is not int or not MIN_DPI <= dpi <= MAX_DPI:
        raise PDFOperationError(f"Resolution must be between {MIN_DPI} and {MAX_DPI} DPI.")
    if not source.exists():
        raise PDFOperationError(f"The selected PDF was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected path is not a file: {source}")
    if not folder.exists() or not folder.is_dir():
        raise PDFOperationError("Choose an existing output folder.")

    document: fitz.Document | None = None
    installed: list[Path] = []
    backups: dict[Path, Path] = {}
    try:
        try:
            document = fitz.open(source)
            if document.needs_pass:
                raise PDFOperationError(
                    f"'{source.name}' is password-protected. PDFForge will not bypass its password."
                )
            page_count = document.page_count
            if page_count < 1:
                raise PDFOperationError("The selected PDF does not contain any pages.")
        except PDFOperationError:
            raise
        except Exception as exc:
            raise PDFOperationError(f"Could not read '{source}': {exc}") from exc

        outputs = expected_image_paths(folder, page_count, normalized)
        existing = [path for path in outputs if path.exists()]
        if any(path.is_dir() for path in existing):
            raise PDFOperationError("An output image path conflicts with a folder. Choose a different output folder.")
        if existing and not overwrite:
            names = ", ".join(path.name for path in existing[:5])
            extra = f" and {len(existing) - 5} more" if len(existing) > 5 else ""
            raise PDFOperationError(
                f"Output images already exist: {names}{extra}. Confirm replacement to continue."
            )

        with tempfile.TemporaryDirectory(prefix=".pdfforge_export_", dir=folder) as staging_dir:
            staging = Path(staging_dir)
            scale = dpi / 72
            for index, page in enumerate(document, 1):
                try:
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                    png_data = pixmap.tobytes("png")
                    with Image.open(BytesIO(png_data)) as rendered:
                        image = rendered.convert("RGB") if normalized == "JPEG" else rendered
                        image.save(
                            staging / outputs[index - 1].name,
                            format=normalized,
                            quality=92,
                            dpi=(dpi, dpi),
                        )
                        if image is not rendered:
                            image.close()
                except Exception as exc:
                    raise PDFOperationError(
                        f"Could not render PDF page {index} as {normalized}: {exc}"
                    ) from exc
                if progress_callback is not None:
                    progress_callback(index, page_count)
            document.close()
            document = None

            # Protect against races after the initial collision check. For an
            # approved replacement, move previous files aside until commit ends.
            new_collisions = [path for path in outputs if path.exists() and path not in existing]
            if new_collisions:
                raise PDFOperationError(
                    f"Output image already exists: {new_collisions[0].name}. Choose another folder or confirm replacement."
                )
            try:
                if existing:
                    backup_folder = staging / "previous"
                    backup_folder.mkdir()
                    for path in existing:
                        backup_path = backup_folder / path.name
                        os.replace(path, backup_path)
                        backups[path] = backup_path
                for path in outputs:
                    staged_path = staging / path.name
                    if path in backups:
                        os.replace(staged_path, path)
                    else:
                        try:
                            os.link(staged_path, path)
                        except FileExistsError as exc:
                            raise PDFOperationError(
                                f"Output image already exists: {path.name}. Choose another folder or confirm replacement."
                            ) from exc
                    installed.append(path)
            except Exception:
                for path in installed:
                    path.unlink(missing_ok=True)
                for path, backup_path in backups.items():
                    if backup_path.exists():
                        os.replace(backup_path, path)
                installed.clear()
                backups.clear()
                raise

        return outputs
    except PDFOperationError:
        raise
    except Exception as exc:
        raise PDFOperationError(f"Could not export PDF pages to '{folder}': {exc}") from exc
    finally:
        if document is not None:
            document.close()
        # TemporaryDirectory removes staging and any backup files after success.

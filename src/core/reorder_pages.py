"""Local PDF page reordering operations using the existing pypdf dependency."""

import os
from pathlib import Path
import tempfile

from pypdf import PdfReader, PdfWriter

from src.core.pdf_output import PDFOperationError, install_output_file, validate_pdf_output_path


def reorder_pdf_pages(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    page_order: list[int],
    *,
    overwrite: bool = False,
) -> Path:
    """Save a copy of a PDF in the supplied one-based page order."""
    source = Path(input_path).expanduser()
    if not source.exists():
        raise PDFOperationError(f"The selected PDF was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected path is not a file: {source}")
    output = validate_pdf_output_path(output_path, [source], overwrite=overwrite)
    temporary_path: Path | None = None
    writer = PdfWriter()
    try:
        with source.open("rb") as stream:
            try:
                reader = PdfReader(stream, strict=True)
                if reader.is_encrypted:
                    raise PDFOperationError(
                        f"'{source.name}' is password-protected. PDFForge will not bypass its password."
                    )
                page_count = len(reader.pages)
                if page_count < 1:
                    raise PDFOperationError("The selected PDF does not contain any pages.")
                if (len(page_order) != page_count or
                        any(type(page) is not int for page in page_order) or
                        set(page_order) != set(range(1, page_count + 1))):
                    raise PDFOperationError(
                        f"Page order must contain each page number from 1 to {page_count} exactly once."
                    )
                for page_number in page_order:
                    writer.add_page(reader.pages[page_number - 1])
            except PDFOperationError:
                raise
            except Exception as exc:
                raise PDFOperationError(f"Could not read '{source}': {exc}") from exc

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix=f".{output.stem}_", suffix=".tmp",
                    dir=output.parent, delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    writer.write(temporary_file)
            except Exception as exc:
                raise PDFOperationError(f"Could not create the reordered PDF: {exc}") from exc

        try:
            try:
                install_output_file(temporary_path, output, overwrite)
            except FileExistsError as exc:
                raise PDFOperationError(
                    "The output file already exists. Confirm replacement to continue."
                ) from exc
            temporary_path = None
        except PDFOperationError:
            raise
        except Exception as exc:
            raise PDFOperationError(f"Could not save the reordered PDF to '{output}': {exc}") from exc
    finally:
        writer.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return output

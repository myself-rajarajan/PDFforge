"""Local PDF page-selection validation and removal operations."""

import os
from pathlib import Path
import re
import tempfile

from pypdf import PdfReader, PdfWriter

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path


def read_pdf_page_count(input_path: str | os.PathLike[str]) -> int:
    """Return the page count after validating that a PDF can be read locally."""
    source = Path(input_path).expanduser()
    if not source.exists():
        raise PDFOperationError(f"The selected PDF was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected path is not a file: {source}")
    try:
        with source.open("rb") as stream:
            reader = PdfReader(stream, strict=True)
            if reader.is_encrypted:
                raise PDFOperationError(
                    f"'{source.name}' is password-protected. PDFForge will not bypass its password."
                )
            page_count = len(reader.pages)
    except PDFOperationError:
        raise
    except Exception as exc:
        raise PDFOperationError(f"Could not read '{source}': {exc}") from exc
    if page_count < 1:
        raise PDFOperationError("The selected PDF does not contain any pages.")
    return page_count


def parse_page_selection(
    selection: str, page_count: int, *, allow_all: bool = False,
) -> list[int]:
    """Parse one-based pages; dedupe repeats and reject deleting all unless previewing."""
    if page_count < 1:
        raise PDFOperationError("The PDF must contain at least one page.")
    if not selection or not selection.strip():
        raise PDFOperationError("Enter the page numbers to remove, for example 2,4,7-9.")

    selected: set[int] = set()

    def page_number(value: str) -> int:
        try:
            return int(value)
        except ValueError as exc:
            raise PDFOperationError("A page number is too large to process.") from exc

    terms = selection.split(",")
    for raw_term in terms:
        term = raw_term.strip()
        if not term:
            raise PDFOperationError("Page selection contains an empty item. Use numbers separated by commas.")
        if "-" in term:
            bounds = term.split("-")
            if len(bounds) != 2 or not all(re.fullmatch(r"\d+", part.strip()) for part in bounds):
                raise PDFOperationError(f"'{term}' is not a valid page range. Use a range like 7-9.")
            start, end = (page_number(part.strip()) for part in bounds)
            if start > end:
                raise PDFOperationError(f"The range '{term}' is reversed. Start with the smaller page number.")
            numbers = range(start, end + 1)
        else:
            if not re.fullmatch(r"\d+", term):
                raise PDFOperationError(f"'{term}' is not a valid page number.")
            numbers = (page_number(term),)

        for number in numbers:
            if number < 1 or number > page_count:
                raise PDFOperationError(
                    f"Page {number} is outside this document. Enter page numbers from 1 to {page_count}."
                )
            selected.add(number)

    if len(selected) == page_count and not allow_all:
        raise PDFOperationError("You cannot remove every page. Leave at least one page in the PDF.")
    return sorted(selected)


def format_page_numbers(page_numbers: list[int]) -> str:
    """Format sorted one-based page numbers into compact comma-separated ranges."""
    if not page_numbers:
        return "None"
    values = sorted(set(page_numbers))
    ranges: list[str] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = value
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return ", ".join(ranges)


def remove_pdf_pages(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    selection: str,
    *,
    overwrite: bool = False,
) -> tuple[Path, list[int], int]:
    """Save a copy without selected one-based pages, returning path, removed pages, and kept count."""
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
                removed = parse_page_selection(selection, page_count)
                removed_set = set(removed)
                kept = [index for index in range(page_count) if index + 1 not in removed_set]
                writer.append(reader, pages=kept)
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
                raise PDFOperationError(f"Could not create the output PDF: {exc}") from exc

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
            raise PDFOperationError(f"Could not save the modified PDF to '{output}': {exc}") from exc
    finally:
        writer.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    return output, removed, len(kept)

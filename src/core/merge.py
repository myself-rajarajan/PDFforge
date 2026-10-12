"""Offline PDF merge operations built on the project's existing pypdf dependency."""

from contextlib import ExitStack
import os
from pathlib import Path
import tempfile

from pypdf import PdfReader, PdfWriter
from src.core.pdf_output import PDFOperationError, install_output_file, validate_pdf_output_path


# Keep the earlier names as aliases for existing Merge PDF callers.
MergeError = PDFOperationError
validate_output_path = validate_pdf_output_path


def merge_pdfs(
    input_paths: list[str | os.PathLike[str]],
    output_path: str | os.PathLike[str],
    *,
    overwrite: bool = False,
) -> Path:
    """Merge PDFs in the supplied order, writing atomically to a local destination."""
    if not input_paths:
        raise MergeError("Select at least one PDF to merge.")

    output = validate_pdf_output_path(output_path, input_paths, overwrite=overwrite)
    sources = [Path(path).expanduser() for path in input_paths]
    for source in sources:
        if not source.exists():
            raise MergeError(f"The selected input file was not found: {source}")
        if not source.is_file():
            raise MergeError(f"The selected input is not a file: {source}")

    temporary_path: Path | None = None
    writer = PdfWriter()
    try:
        # Keep every reader and source stream alive until the writer has finished.
        with ExitStack() as stack:
            for source in sources:
                try:
                    stream = stack.enter_context(source.open("rb"))
                    reader = PdfReader(stream, strict=True)
                    if reader.is_encrypted:
                        raise MergeError(f"'{source.name}' is password-protected and cannot be merged.")
                    writer.append(reader)
                except MergeError:
                    raise
                except Exception as exc:
                    raise MergeError(f"Could not read '{source}': {exc}") from exc

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb", prefix=f".{output.stem}_", suffix=".tmp",
                    dir=output.parent, delete=False,
                ) as temporary_file:
                    temporary_path = Path(temporary_file.name)
                    writer.write(temporary_file)
                try:
                    install_output_file(temporary_path, output, overwrite)
                except FileExistsError as exc:
                    raise MergeError(
                        "The output file already exists. Confirm replacement to continue."
                    ) from exc
                temporary_path = None
            except MergeError:
                raise
            except Exception as exc:
                raise MergeError(f"Could not save the merged PDF to '{output}': {exc}") from exc
    finally:
        writer.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    return output

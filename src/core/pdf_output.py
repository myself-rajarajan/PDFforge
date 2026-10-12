"""Shared output-path validation for local PDF operations."""

import os
from pathlib import Path


class PDFOperationError(Exception):
    """An expected, user-correctable error in a local PDF operation."""


def install_output_file(temporary_path: Path, output_path: Path, overwrite: bool) -> None:
    """Atomically install a same-folder temporary file without accidental clobbering."""
    if overwrite:
        os.replace(temporary_path, output_path)
    elif os.name == "nt":
        # Windows rename is atomic on the same volume and fails if the destination exists.
        os.rename(temporary_path, output_path)
    else:
        # A POSIX hard link is an atomic create-if-absent operation.
        os.link(temporary_path, output_path)
        temporary_path.unlink()


def _same_path(first: Path, second: Path) -> bool:
    """Compare paths including case normalization and existing file identities."""
    try:
        if first.exists() and second.exists() and os.path.samefile(first, second):
            return True
    except OSError:
        pass
    return os.path.normcase(str(first.resolve(strict=False))) == os.path.normcase(
        str(second.resolve(strict=False))
    )


def validate_pdf_output_path(
    output_path: str | os.PathLike[str],
    input_paths: list[str | os.PathLike[str]],
    *,
    overwrite: bool = False,
) -> Path:
    """Validate a PDF destination and prevent it from aliasing a source file."""
    output = Path(output_path).expanduser()
    if not str(output).strip() or not output.name:
        raise PDFOperationError("Choose a valid output filename and destination.")
    output = output.absolute()
    if output.suffix.casefold() != ".pdf":
        raise PDFOperationError("The output filename must end in .pdf.")
    if not output.parent.exists() or not output.parent.is_dir():
        raise PDFOperationError("The output folder does not exist or is not a folder.")
    if output.exists() and output.is_dir():
        raise PDFOperationError("The output path points to a folder. Choose a PDF filename.")
    for input_path in input_paths:
        source = Path(input_path).expanduser().absolute()
        if _same_path(source, output):
            raise PDFOperationError("The output file cannot be one of the selected input PDFs.")
    if output.exists() and not overwrite:
        raise PDFOperationError("The output file already exists. Confirm replacement to continue.")
    return output

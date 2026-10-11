"""Offline PDF merge operations built on the project's existing pypdf dependency."""

from contextlib import ExitStack
import os
from pathlib import Path
import tempfile

from pypdf import PdfReader, PdfWriter


class MergeError(Exception):
    """An expected, user-correctable error while merging PDF documents."""


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


def validate_output_path(
    output_path: str | os.PathLike[str],
    input_paths: list[str | os.PathLike[str]],
    *,
    overwrite: bool = False,
) -> Path:
    """Validate destination shape and protect all source files from replacement."""
    output = Path(output_path).expanduser()
    if not str(output).strip() or not output.name:
        raise MergeError("Choose a valid output filename and destination.")
    output = output.absolute()
    if output.suffix.casefold() != ".pdf":
        raise MergeError("The output filename must end in .pdf.")
    if not output.parent.exists() or not output.parent.is_dir():
        raise MergeError("The output folder does not exist or is not a folder.")
    if output.exists() and output.is_dir():
        raise MergeError("The output path points to a folder. Choose a PDF filename.")
    for input_path in input_paths:
        source = Path(input_path).expanduser().absolute()
        if _same_path(source, output):
            raise MergeError("The output file cannot be one of the selected input PDFs.")
    if output.exists() and not overwrite:
        raise MergeError("The output file already exists. Confirm replacement to continue.")
    return output


def merge_pdfs(
    input_paths: list[str | os.PathLike[str]],
    output_path: str | os.PathLike[str],
    *,
    overwrite: bool = False,
) -> Path:
    """Merge PDFs in the supplied order, writing atomically to a local destination."""
    if not input_paths:
        raise MergeError("Select at least one PDF to merge.")

    output = validate_output_path(output_path, input_paths, overwrite=overwrite)
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
                if overwrite:
                    os.replace(temporary_path, output)
                else:
                    # A same-directory hard link creates the destination atomically
                    # and fails if another process created it during the merge.
                    try:
                        os.link(temporary_path, output)
                    except FileExistsError as exc:
                        raise MergeError(
                            "The output file already exists. Confirm replacement to continue."
                        ) from exc
                    temporary_path.unlink()
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

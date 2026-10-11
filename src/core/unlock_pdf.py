"""Unlock local PDFs when the user supplies an authorized password."""

import os
from pathlib import Path
import tempfile

import pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.errors import DependencyError

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path


def _write_unencrypted_with_pymupdf(source: Path, temporary_path: Path, password: str) -> None:
    """Use the installed MuPDF backend when pypdf lacks an encryption primitive."""
    try:
        with pymupdf.open(source) as document:
            if not document.is_encrypted:
                raise PDFOperationError("This PDF is not password-protected.")
            if not document.authenticate(password):
                raise PDFOperationError("The password is incorrect.")
            document.save(temporary_path, encryption=pymupdf.PDF_ENCRYPT_NONE)
    except PDFOperationError:
        raise
    except Exception as exc:
        raise PDFOperationError(
            "This PDF uses encryption that PDFForge could not unlock, or the file is damaged."
        ) from exc


def _install_output(temporary_path: Path, output: Path, overwrite: bool) -> None:
    if overwrite:
        os.replace(temporary_path, output)
        return
    try:
        os.link(temporary_path, output)
    except FileExistsError as exc:
        raise PDFOperationError(
            "The output file already exists. Confirm replacement to continue."
        ) from exc
    temporary_path.unlink()


def unlock_pdf(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    password: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Verify the supplied password and write a new unencrypted PDF atomically."""
    if not password:
        raise PDFOperationError("Enter the PDF password to continue.")

    source = Path(input_path).expanduser()
    if not source.exists():
        raise PDFOperationError(f"The selected input file was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected input is not a file: {source}")
    output = validate_pdf_output_path(output_path, [source], overwrite=overwrite)

    temporary_path: Path | None = None
    writer = PdfWriter()
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{output.stem}_", suffix=".tmp",
            dir=output.parent, delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

        try:
            with source.open("rb") as stream:
                reader = PdfReader(stream, strict=True)
                if not reader.is_encrypted:
                    raise PDFOperationError("This PDF is not password-protected.")
                if not reader.decrypt(password):
                    raise PDFOperationError("The password is incorrect.")
                writer.append(reader)
                with temporary_path.open("wb") as temporary_file:
                    writer.write(temporary_file)
        except DependencyError:
            # Some pypdf AES handlers require its optional cryptography package.
            # This app already includes PyMuPDF, which authenticates AES PDFs locally.
            _write_unencrypted_with_pymupdf(source, temporary_path, password)
        except PDFOperationError:
            raise
        except NotImplementedError as exc:
            raise PDFOperationError(
                "This PDF uses an encryption method that is not supported by the installed PDF libraries."
            ) from exc
        except Exception as exc:
            raise PDFOperationError(
                "Could not read or decrypt this PDF. Check the password and that the file is valid."
            ) from exc

        _install_output(temporary_path, output, overwrite)
        temporary_path = None
    except PDFOperationError:
        raise
    except Exception as exc:
        raise PDFOperationError(
            "Could not save the unlocked PDF. Check that the destination is writable and has enough free space."
        ) from exc
    finally:
        writer.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    return output

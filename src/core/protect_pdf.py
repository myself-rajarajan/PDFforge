"""Password protection for local PDF documents."""

import os
from pathlib import Path
import tempfile

import pymupdf
from pypdf import PdfReader, PdfWriter
from pypdf.errors import DependencyError

from src.core.pdf_output import PDFOperationError, validate_pdf_output_path


def validate_passwords(password: str, confirmation: str) -> None:
    """Reject empty or mismatched credentials without exposing their values."""
    if not password:
        raise PDFOperationError("Enter a password to protect the PDF.")
    if password != confirmation:
        raise PDFOperationError("The password and confirmation do not match.")


def protect_pdf(
    input_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    password: str,
    *,
    overwrite: bool = False,
) -> Path:
    """Encrypt a PDF using AES-256 and save it atomically to a new destination."""
    if not password:
        raise PDFOperationError("Enter a password to protect the PDF.")

    source = Path(input_path).expanduser()
    if not source.exists():
        raise PDFOperationError(f"The selected input file was not found: {source}")
    if not source.is_file():
        raise PDFOperationError(f"The selected input is not a file: {source}")
    output = validate_pdf_output_path(output_path, [source], overwrite=overwrite)

    writer = PdfWriter()
    temporary_path: Path | None = None
    try:
        try:
            with source.open("rb") as stream:
                reader = PdfReader(stream, strict=True)
                if reader.is_encrypted:
                    raise PDFOperationError(
                        "This PDF is already password-protected. Remove its protection first, then try again."
                    )
                writer.append(reader)
        except PDFOperationError:
            raise
        except Exception as exc:
            raise PDFOperationError(f"Could not read the selected PDF: {exc}") from exc

        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=f".{output.stem}_", suffix=".tmp",
                dir=output.parent, delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)

            try:
                writer.encrypt(user_password=password, algorithm="AES-256")
                with temporary_path.open("wb") as temporary_file:
                    writer.write(temporary_file)
            except DependencyError:
                # pypdf exposes AES-256 but delegates AES primitives to its optional
                # cryptography backend. PyMuPDF already ships with PDFForge and can
                # provide the same AES-256 protection when that backend is absent.
                with pymupdf.open(source) as document:
                    if document.needs_pass:
                        raise PDFOperationError(
                            "This PDF is already password-protected. Remove its protection first, then try again."
                        )
                    document.save(
                        temporary_path,
                        encryption=pymupdf.PDF_ENCRYPT_AES_256,
                        user_pw=password,
                    )

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
                "Could not protect or save the PDF. Check that the destination is writable and has enough free space."
            ) from exc
    finally:
        writer.close()
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

    return output

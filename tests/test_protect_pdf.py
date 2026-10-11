"""Tests for local AES-256 PDF protection."""

import fitz
import pytest
from pypdf import PdfReader, PdfWriter

from src.core.pdf_output import PDFOperationError
from src.core.protect_pdf import protect_pdf, validate_passwords


def make_pdf(path, labels=("first", "second")):
    document = fitz.open()
    for index, label in enumerate(labels):
        page = document.new_page(width=200 + index * 50, height=300)
        page.insert_text((30, 50), label)
    document.save(path)
    document.close()


def read_text(path, password=None):
    with fitz.open(path) as document:
        if password is not None:
            assert document.authenticate(password)
        return len(document), [page.get_text().strip() for page in document]


def test_protect_pdf_encrypts_with_aes256_and_preserves_content_order(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "protected.pdf"
    make_pdf(source, ("alpha page", "beta page", "gamma page"))

    assert protect_pdf(source, output, "correct horse") == output
    with fitz.open(output) as document:
        assert document.is_encrypted
        assert document.authenticate("correct horse")
        assert len(document) == 3
        assert [page.get_text().strip() for page in document] == [
            "alpha page", "beta page", "gamma page",
        ]
    assert read_text(source) == (3, ["alpha page", "beta page", "gamma page"])


def test_wrong_password_cannot_read_protected_pages(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "protected.pdf"
    make_pdf(source, ("private",))
    protect_pdf(source, output, "right password")

    with fitz.open(output) as document:
        assert not document.authenticate("wrong password")


def test_empty_or_mismatched_passwords_are_rejected_without_echoing_values():
    with pytest.raises(PDFOperationError, match="Enter a password"):
        validate_passwords("", "")
    with pytest.raises(PDFOperationError, match="do not match") as error:
        validate_passwords("secret-one", "secret-two")
    assert "secret" not in str(error.value)


def test_missing_invalid_and_encrypted_inputs_fail_safely(tmp_path):
    output = tmp_path / "protected.pdf"
    with pytest.raises(PDFOperationError, match="not found"):
        protect_pdf(tmp_path / "missing.pdf", output, "password")

    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a pdf", encoding="utf-8")
    with pytest.raises(PDFOperationError, match="Could not read"):
        protect_pdf(invalid, output, "password")
    assert not output.exists()

    encrypted = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("existing password")
    with encrypted.open("wb") as stream:
        writer.write(stream)
    writer.close()
    with pytest.raises(PDFOperationError, match="already password-protected"):
        protect_pdf(encrypted, output, "new password")
    assert not output.exists()


def test_output_cannot_replace_source_even_when_overwrite_is_requested(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source, ("keep original",))
    original = source.read_bytes()
    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        protect_pdf(source, source, "password", overwrite=True)
    assert source.read_bytes() == original
    assert read_text(source)[1] == ["keep original"]


def test_existing_output_requires_confirmation_and_can_be_replaced(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "output.pdf"
    make_pdf(source, ("source",))
    make_pdf(output, ("existing",))
    original_output = output.read_bytes()

    with pytest.raises(PDFOperationError, match="already exists"):
        protect_pdf(source, output, "password")
    assert output.read_bytes() == original_output

    protect_pdf(source, output, "password", overwrite=True)
    with fitz.open(output) as document:
        assert document.is_encrypted
        assert document.authenticate("password")
        assert document[0].get_text().strip() == "source"



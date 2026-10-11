"""Temporary-file tests for authorized PDF unlocking."""

import fitz
import pytest
from pypdf import PdfReader, PdfWriter

from src.core.pdf_output import PDFOperationError
from src.core.unlock_pdf import unlock_pdf


PASSWORD = "authorized test password"


def make_encrypted_pdf(path, labels=("first page", "second page")):
    document = fitz.open()
    for index, label in enumerate(labels):
        page = document.new_page(width=220 + index * 40, height=320)
        page.insert_text((30, 50), label)
    document.save(
        path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=PASSWORD,
    )
    document.close()


def test_unlocks_with_correct_password_and_preserves_page_content_order(tmp_path):
    source = tmp_path / "locked.pdf"
    output = tmp_path / "unlocked.pdf"
    make_encrypted_pdf(source, ("alpha text", "beta text", "gamma text"))

    assert unlock_pdf(source, output, PASSWORD) == output
    with output.open("rb") as stream:
        reader = PdfReader(stream, strict=True)
        assert not reader.is_encrypted
        assert len(reader.pages) == 3
        assert [page.extract_text().strip() for page in reader.pages] == [
            "alpha text", "beta text", "gamma text",
        ]


def test_wrong_password_does_not_create_output_or_change_source(tmp_path):
    source = tmp_path / "locked.pdf"
    output = tmp_path / "unlocked.pdf"
    make_encrypted_pdf(source, ("keep locked",))
    original = source.read_bytes()

    with pytest.raises(PDFOperationError, match="incorrect"):
        unlock_pdf(source, output, "wrong password")
    assert not output.exists()
    assert source.read_bytes() == original


def test_pypdf_encrypted_input_can_be_unlocked_using_its_password(tmp_path):
    source = tmp_path / "pypdf-locked.pdf"
    output = tmp_path / "pypdf-unlocked.pdf"
    writer = PdfWriter()
    first = writer.add_blank_page(width=111, height=200)
    second = writer.add_blank_page(width=222, height=200)
    first.rotate(90)
    second.rotate(180)
    writer.encrypt(PASSWORD)
    with source.open("wb") as stream:
        writer.write(stream)
    writer.close()

    unlock_pdf(source, output, PASSWORD)
    with output.open("rb") as stream:
        reader = PdfReader(stream, strict=True)
        assert not reader.is_encrypted
        assert [float(page.mediabox.width) for page in reader.pages] == [111, 222]
        assert [page.get("/Rotate", 0) for page in reader.pages] == [90, 180]


def test_unencrypted_missing_and_corrupt_inputs_are_rejected(tmp_path):
    output = tmp_path / "unlocked.pdf"
    with pytest.raises(PDFOperationError, match="not found"):
        unlock_pdf(tmp_path / "missing.pdf", output, PASSWORD)

    unencrypted = tmp_path / "plain.pdf"
    with unencrypted.open("wb") as stream:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(stream)
        writer.close()
    with pytest.raises(PDFOperationError, match="not password-protected"):
        unlock_pdf(unencrypted, output, PASSWORD)

    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(PDFOperationError, match="Could not read or decrypt"):
        unlock_pdf(corrupt, output, PASSWORD)
    assert not output.exists()


def test_empty_password_and_unsafe_output_are_rejected(tmp_path):
    source = tmp_path / "locked.pdf"
    make_encrypted_pdf(source, ("original",))
    original = source.read_bytes()
    with pytest.raises(PDFOperationError, match="Enter the PDF password"):
        unlock_pdf(source, tmp_path / "unlocked.pdf", "")
    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        unlock_pdf(source, source, PASSWORD, overwrite=True)
    assert source.read_bytes() == original


def test_existing_destination_requires_confirmation_before_replacement(tmp_path):
    source = tmp_path / "locked.pdf"
    output = tmp_path / "existing.pdf"
    make_encrypted_pdf(source, ("source page",))
    output.write_bytes(b"keep this existing destination")
    original = output.read_bytes()

    with pytest.raises(PDFOperationError, match="already exists"):
        unlock_pdf(source, output, PASSWORD)
    assert output.read_bytes() == original

    unlock_pdf(source, output, PASSWORD, overwrite=True)
    with output.open("rb") as stream:
        reader = PdfReader(stream)
        assert not reader.is_encrypted
        assert reader.pages[0].extract_text().strip() == "source page"

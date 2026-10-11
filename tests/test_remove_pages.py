"""Temporary-file tests for removing selected PDF pages."""

import pytest
from pypdf import PdfReader, PdfWriter

from src.core.pdf_output import PDFOperationError
from src.core.remove_pages import (
    format_page_numbers, parse_page_selection, remove_pdf_pages,
)


def make_pdf(path, page_widths):
    writer = PdfWriter()
    for width in page_widths:
        writer.add_blank_page(width=width, height=100)
    with path.open("wb") as stream:
        writer.write(stream)
    writer.close()


def page_widths(path):
    with path.open("rb") as stream:
        reader = PdfReader(stream)
        return [float(page.mediabox.width) for page in reader.pages]


def test_remove_one_page_preserves_other_pages_in_order(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "without-page-two.pdf"
    make_pdf(source, [101, 202, 303, 404])

    saved, removed, remaining_count = remove_pdf_pages(source, output, "2")

    assert saved == output
    assert removed == [2]
    assert remaining_count == 3
    assert page_widths(output) == [101, 303, 404]
    assert page_widths(source) == [101, 202, 303, 404]


def test_remove_multiple_selected_pages(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "multiple-removed.pdf"
    make_pdf(source, [100, 200, 300, 400, 500])

    remove_pdf_pages(source, output, "2,4")

    assert page_widths(output) == [100, 300, 500]


def test_remove_page_range_and_preserve_remaining_order(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "range-removed.pdf"
    make_pdf(source, [110, 220, 330, 440, 550, 660])

    remove_pdf_pages(source, output, "2-4")

    assert page_widths(output) == [110, 550, 660]


def test_page_syntax_normalizes_duplicates_and_formats_ranges():
    assert parse_page_selection("2, 4, 2, 7-9", 10) == [2, 4, 7, 8, 9]
    assert format_page_numbers([2, 4, 7, 8, 9]) == "2, 4, 7-9"


@pytest.mark.parametrize(
    "selection",
    ["", "   ", "0", "-1", "1,,2", "abc", "2-", "3-1", "1-2-3", "2.5"],
)
def test_malformed_page_selection_is_rejected(selection):
    with pytest.raises(PDFOperationError):
        parse_page_selection(selection, 5)


@pytest.mark.parametrize("selection", ["6", "1-6"])
def test_page_numbers_outside_document_are_rejected(selection):
    with pytest.raises(PDFOperationError, match="outside this document"):
        parse_page_selection(selection, 5)


def test_cannot_remove_every_page(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "empty.pdf"
    make_pdf(source, [100, 200, 300])

    with pytest.raises(PDFOperationError, match="cannot remove every page"):
        remove_pdf_pages(source, output, "1-3")
    assert not output.exists()


def test_missing_and_invalid_pdfs_are_reported(tmp_path):
    output = tmp_path / "result.pdf"
    with pytest.raises(PDFOperationError, match="not found"):
        remove_pdf_pages(tmp_path / "missing.pdf", output, "1")

    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(PDFOperationError, match="Could not read"):
        remove_pdf_pages(invalid, output, "1")


def test_password_protected_pdf_is_rejected_without_decryption(tmp_path):
    source = tmp_path / "protected.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("test-password")
    with source.open("wb") as stream:
        writer.write(stream)
    writer.close()

    with pytest.raises(PDFOperationError, match="password-protected"):
        remove_pdf_pages(source, tmp_path / "output.pdf", "1")


def test_output_cannot_overwrite_original_even_when_overwrite_enabled(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source, [111, 222, 333])

    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        remove_pdf_pages(source, source, "2", overwrite=True)
    assert page_widths(source) == [111, 222, 333]

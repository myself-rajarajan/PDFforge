"""Generated-PDF tests for local page reordering."""

import pytest
from pypdf import PdfReader, PdfWriter

from src.core.pdf_output import PDFOperationError
from src.core.reorder_pages import reorder_pdf_pages


def make_pdf(path, widths):
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=100)
    with path.open("wb") as stream:
        writer.write(stream)
    writer.close()


def widths(path):
    with path.open("rb") as stream:
        reader = PdfReader(stream)
        return [float(page.mediabox.width) for page in reader.pages]


def test_reorders_multiple_pages_and_preserves_page_count_and_rotation(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "reordered.pdf"
    make_pdf(source, [101, 202, 303, 404])
    writer = PdfWriter(clone_from=source)
    writer.pages[1].rotate(90)
    with source.open("wb") as stream:
        writer.write(stream)
    writer.close()

    saved = reorder_pdf_pages(source, output, [3, 1, 4, 2])

    assert saved == output
    assert widths(output) == [303, 101, 404, 202]
    with output.open("rb") as stream:
        reader = PdfReader(stream)
        assert len(reader.pages) == 4
        assert reader.pages[3].rotation == 90
    assert widths(source) == [101, 202, 303, 404]


def test_reorders_single_page_document(tmp_path):
    source = tmp_path / "one.pdf"
    output = tmp_path / "one-reordered.pdf"
    make_pdf(source, [123])
    reorder_pdf_pages(source, output, [1])
    assert widths(output) == [123]


@pytest.mark.parametrize("order", [[], [1, 1, 3], [1, 2], [0, 1, 2], [1, 2, 4], [True, 2, 3]])
def test_rejects_invalid_page_orders(tmp_path, order):
    source = tmp_path / "source.pdf"
    output = tmp_path / "output.pdf"
    make_pdf(source, [100, 200, 300])
    with pytest.raises(PDFOperationError, match="each page number"):
        reorder_pdf_pages(source, output, order)
    assert not output.exists()


def test_missing_and_invalid_pdfs_are_reported(tmp_path):
    output = tmp_path / "output.pdf"
    with pytest.raises(PDFOperationError, match="not found"):
        reorder_pdf_pages(tmp_path / "missing.pdf", output, [1])
    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(PDFOperationError, match="Could not read"):
        reorder_pdf_pages(invalid, output, [1])


def test_rejects_password_protected_pdf(tmp_path):
    source = tmp_path / "protected.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    with source.open("wb") as stream:
        writer.write(stream)
    writer.close()
    with pytest.raises(PDFOperationError, match="password-protected"):
        reorder_pdf_pages(source, tmp_path / "output.pdf", [1])


def test_input_cannot_be_overwritten(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source, [111, 222, 333])
    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        reorder_pdf_pages(source, source, [3, 2, 1], overwrite=True)
    assert widths(source) == [111, 222, 333]


def test_existing_output_requires_explicit_overwrite(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "output.pdf"
    make_pdf(source, [111, 222])
    make_pdf(output, [999])
    with pytest.raises(PDFOperationError, match="already exists"):
        reorder_pdf_pages(source, output, [2, 1])
    assert widths(output) == [999]


"""Temporary-PDF tests for page numbering, placement, and output safety."""

import fitz
import pytest

from src.core.add_page_numbers import add_page_numbers
from src.core.pdf_output import PDFOperationError


def make_pdf(path, dimensions=((300, 400), (400, 300))):
    document = fitz.open()
    for index, (width, height) in enumerate(dimensions, 1):
        page = document.new_page(width=width, height=height)
        page.insert_text((30, 40), f"Original page {index}", fontsize=11)
    document.save(path)
    document.close()


@pytest.mark.parametrize(
    "position, expected_x, expected_y",
    [
        ("top-left", "left", "top"),
        ("top-center", "center", "top"),
        ("top-right", "right", "top"),
        ("bottom-left", "left", "bottom"),
        ("bottom-center", "center", "bottom"),
        ("bottom-right", "right", "bottom"),
    ],
)
def test_all_six_positions_are_inside_expected_page_regions(
    tmp_path, position, expected_x, expected_y
):
    source = tmp_path / "input.pdf"
    output = tmp_path / f"{position}.pdf"
    make_pdf(source, ((300, 400),))

    add_page_numbers(source, output, position=position, starting_number=987, font_size=12)

    document = fitz.open(output)
    page = document[0]
    words = page.get_text("words")
    number = next(word for word in words if word[4] == "987")
    x0, y0, x1, y1 = number[:4]
    assert page.rect.contains(fitz.Rect(x0, y0, x1, y1))
    if expected_x == "left":
        assert x0 < page.rect.width * 0.25
    elif expected_x == "center":
        assert abs((x0 + x1) / 2 - page.rect.width / 2) < 2
    else:
        assert x1 > page.rect.width * 0.75
    if expected_y == "top":
        assert y1 < page.rect.height * 0.25
    else:
        assert y0 > page.rect.height * 0.75
    document.close()


def test_custom_starting_number_applies_sequentially_across_pages(tmp_path):
    source = tmp_path / "input.pdf"
    output = tmp_path / "numbered.pdf"
    make_pdf(source)

    add_page_numbers(source, output, position="bottom-center", starting_number=42)

    document = fitz.open(output)
    assert [page.get_text().splitlines()[-1] for page in document] == ["42", "43"]
    assert [page.get_text().splitlines()[0] for page in document] == [
        "Original page 1", "Original page 2",
    ]
    document.close()
    original = fitz.open(source)
    assert all(not any(line in {"42", "43"} for line in page.get_text().splitlines()) for page in original)
    original.close()


def test_rotated_page_keeps_rotation_and_contains_number(tmp_path):
    source = tmp_path / "rotated.pdf"
    output = tmp_path / "rotated-numbered.pdf"
    make_pdf(source, ((300, 400),))
    document = fitz.open(source)
    document[0].set_rotation(90)
    document.save(source.with_name("rotated-source.pdf"))
    document.close()
    source = source.with_name("rotated-source.pdf")

    add_page_numbers(source, output, position="top-right")

    result = fitz.open(output)
    assert result[0].rotation == 90
    assert any(word[4] == "1" for word in result[0].get_text("words"))
    result.close()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"starting_number": 0},
        {"starting_number": 1.5},
        {"font_size": 0},
        {"font_size": 100},
        {"position": "center"},
    ],
)
def test_invalid_numbering_settings_are_rejected(tmp_path, kwargs):
    source = tmp_path / "input.pdf"
    make_pdf(source, ((300, 400),))
    with pytest.raises(PDFOperationError):
        add_page_numbers(source, tmp_path / "output.pdf", **kwargs)


def test_missing_and_invalid_pdfs_are_reported(tmp_path):
    output = tmp_path / "output.pdf"
    with pytest.raises(PDFOperationError, match="not found"):
        add_page_numbers(tmp_path / "missing.pdf", output)
    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(PDFOperationError, match="Could not read"):
        add_page_numbers(invalid, output)


def test_encrypted_pdf_is_rejected(tmp_path):
    source = tmp_path / "encrypted.pdf"
    document = fitz.open()
    document.new_page()
    document.save(source, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user")
    document.close()
    with pytest.raises(PDFOperationError, match="password-protected"):
        add_page_numbers(source, tmp_path / "output.pdf")


def test_source_cannot_be_overwritten_even_with_confirmation(tmp_path):
    source = tmp_path / "input.pdf"
    make_pdf(source, ((300, 400),))
    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        add_page_numbers(source, source, overwrite=True)
    document = fitz.open(source)
    assert "1" not in document[0].get_text().splitlines()
    document.close()


def test_existing_destination_requires_overwrite_confirmation(tmp_path):
    source = tmp_path / "input.pdf"
    output = tmp_path / "existing.pdf"
    make_pdf(source, ((300, 400),))
    output.write_bytes(b"keep existing output")
    with pytest.raises(PDFOperationError, match="already exists"):
        add_page_numbers(source, output)
    assert output.read_bytes() == b"keep existing output"


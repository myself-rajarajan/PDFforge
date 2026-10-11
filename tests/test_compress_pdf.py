"""Tests for local best-effort PDF compression and result reporting."""

from io import BytesIO

import pymupdf as fitz
import pytest
from pypdf import PdfReader
from PIL import Image

from src.core.compress_pdf import (
    compress_pdf, compression_result_text, compression_savings_percent,
    estimate_compressed_size,
    target_dpi_for_quality,
)
from src.core.pdf_output import PDFOperationError


def make_pdf(path, labels=("alpha", "beta")):
    document = fitz.open()
    for label in labels:
        page = document.new_page(width=300, height=400)
        page.insert_text((36, 48), label)
    document.save(path)
    document.close()


def test_compression_produces_valid_pdf_with_pages_and_text_in_order(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "compressed.pdf"
    make_pdf(source, ("page one text", "page two text", "page three text"))

    assert compress_pdf(source, output) == output
    with output.open("rb") as stream:
        reader = PdfReader(stream, strict=True)
        assert not reader.is_encrypted
        assert len(reader.pages) == 3
        assert [page.extract_text().strip() for page in reader.pages] == [
            "page one text", "page two text", "page three text",
        ]
    assert source.exists()
    assert output.stat().st_size > 0


def test_compression_handles_high_resolution_images_without_size_assumption(tmp_path):
    source = tmp_path / "image-source.pdf"
    output = tmp_path / "image-compressed.pdf"
    image = Image.effect_noise((1200, 1600), 90).convert("RGB")
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG", quality=95)
    image.close()
    image_bytes.seek(0)
    document = fitz.open()
    page = document.new_page(width=300, height=400)
    page.insert_image(page.rect, stream=image_bytes.getvalue())
    page.insert_text((20, 30), "image document")
    document.save(source)
    document.close()

    compress_pdf(source, output, quality=20)

    with fitz.open(output) as result:
        assert len(result) == 1
        assert "image document" in result[0].get_text()
        assert len(result[0].get_images()) == 1
    assert output.stat().st_size > 0


def test_estimated_size_measures_temporary_compression_pass(tmp_path):
    source = tmp_path / "estimate-source.pdf"
    make_pdf(source, ("estimate page",))
    estimated = estimate_compressed_size(source, quality=65)
    assert estimated > 0
    assert sorted(path.name for path in tmp_path.iterdir()) == ["estimate-source.pdf"]


def test_missing_invalid_and_password_protected_inputs_are_reported(tmp_path):
    output = tmp_path / "compressed.pdf"
    with pytest.raises(PDFOperationError, match="not found"):
        compress_pdf(tmp_path / "missing.pdf", output)

    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(PDFOperationError, match="Could not read"):
        compress_pdf(invalid, output)

    protected = tmp_path / "protected.pdf"
    document = fitz.open()
    document.new_page()
    document.save(protected, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="secret")
    document.close()
    with pytest.raises(PDFOperationError, match="password-protected"):
        compress_pdf(protected, output)
    assert not output.exists()


def test_output_safety_prevents_input_overwrite_and_requires_confirmation(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source, ("preserve original",))
    original = source.read_bytes()
    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        compress_pdf(source, source, overwrite=True)
    assert source.read_bytes() == original

    output = tmp_path / "existing.pdf"
    output.write_bytes(b"existing output")
    previous = output.read_bytes()
    with pytest.raises(PDFOperationError, match="already exists"):
        compress_pdf(source, output)
    assert output.read_bytes() == previous

    compress_pdf(source, output, overwrite=True)
    with output.open("rb") as stream:
        assert len(PdfReader(stream).pages) == 1


@pytest.mark.parametrize(
    ("original_size", "output_size", "expected_percent", "expected_text"),
    [
        (1000, 700, 30.0, "Saved 30.0%"),
        (1000, 1000, 0.0, "No size reduction"),
        (1000, 1200, -20.0, "20.0% larger"),
        (0, 120, None, "original file is empty"),
    ],
)
def test_size_reporting_handles_savings_no_change_growth_and_zero(
    original_size, output_size, expected_percent, expected_text,
):
    assert compression_savings_percent(original_size, output_size) == expected_percent
    assert expected_text in compression_result_text(original_size, output_size)


def test_size_reporting_rejects_negative_sizes():
    with pytest.raises(PDFOperationError, match="cannot be negative"):
        compression_savings_percent(-1, 2)


def test_quality_setting_controls_target_resolution_and_validation():
    assert target_dpi_for_quality(20) == 113
    assert target_dpi_for_quality(75) == 150
    assert target_dpi_for_quality(95) == 163
    with pytest.raises(PDFOperationError, match="Image quality must be between"):
        target_dpi_for_quality(0)

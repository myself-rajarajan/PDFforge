"""Tests for local best-effort PDF compression and result reporting."""

from io import BytesIO

import pymupdf as fitz
import pytest
from pypdf import PdfReader
from PIL import Image

from src.core.compress_pdf import (
    COMPRESSION_PRESETS, compress_pdf, compression_preset_for_quality,
    compression_preset_settings, compression_result_text, compression_savings_percent,
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


def test_compression_handles_high_resolution_images_without_size_assumption(tmp_path, monkeypatch):
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

    rewrite_images = fitz.Document.rewrite_images
    rewrite_settings = {}

    def record_rewrite_settings(document, **settings):
        rewrite_settings.update(settings)
        return rewrite_images(document, **settings)

    monkeypatch.setattr(fitz.Document, "rewrite_images", record_rewrite_settings)
    compress_pdf(source, output, preset="Maximum")

    with fitz.open(output) as result:
        assert len(result) == 1
        assert "image document" in result[0].get_text()
        assert len(result[0].get_images()) == 1
    assert output.stat().st_size > 0
    assert rewrite_settings["dpi_threshold"] == 200
    assert rewrite_settings["dpi_target"] == 116
    assert rewrite_settings["quality"] == 25
    assert rewrite_settings["lossy"] is True
    assert rewrite_settings["lossless"] is False
    assert rewrite_settings["bitonal"] is False


def test_larger_rewrite_keeps_original_bytes_as_output(tmp_path, monkeypatch):
    source = tmp_path / "small.pdf"
    output = tmp_path / "small-compressed.pdf"
    make_pdf(source, ("retain original if optimization grows it",))
    original = source.read_bytes()
    save = fitz.Document.save

    def save_with_growth(document, filename, *args, **kwargs):
        save(document, filename, *args, **kwargs)
        with open(filename, "ab") as stream:
            stream.write(b"padding" * 2048)

    monkeypatch.setattr(fitz.Document, "save", save_with_growth)
    compress_pdf(source, output)

    assert output.read_bytes() == original
    with fitz.open(output) as result:
        assert len(result) == 1
        assert "retain original" in result[0].get_text()


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


def test_named_presets_use_verified_quality_and_resolution_settings():
    assert compression_preset_settings("Recommended").quality == 75
    assert compression_preset_settings("Recommended").target_dpi == target_dpi_for_quality(75)
    assert compression_preset_settings("Strong").quality == 50
    assert compression_preset_settings("Strong").target_dpi == target_dpi_for_quality(50)
    assert compression_preset_settings("Maximum").quality == 25
    assert compression_preset_settings("Maximum").target_dpi == target_dpi_for_quality(25)
    assert compression_preset_for_quality(75) == "Recommended"
    assert compression_preset_for_quality(50) == "Strong"
    assert compression_preset_for_quality(25) == "Maximum"
    assert compression_preset_for_quality(47) == "Custom (47% quality)"
    assert list(COMPRESSION_PRESETS) == ["Recommended", "Strong", "Maximum"]
    with pytest.raises(PDFOperationError, match="Choose Recommended"):
        compression_preset_settings("unrecognized")

"""Temporary-file tests for image/PDF conversion services."""

from pathlib import Path

import pymupdf as fitz
from PIL import Image
import pytest

from src.core.images_to_pdf import images_to_pdf
from src.core.pdf_output import PDFOperationError
from src.core.pdf_to_images import pdf_to_images


def make_image(path: Path, color: tuple[int, int, int], size: tuple[int, int]) -> None:
    image_format = {".jpg": "JPEG", ".jpeg": "JPEG", ".pdf": "PNG"}.get(path.suffix.lower())
    Image.new("RGB", size, color).save(path, format=image_format)


def make_pdf(path: Path, pages=((120, 80, (255, 0, 0)), (80, 120, (0, 0, 255)))) -> None:
    document = fitz.open()
    for width, height, color in pages:
        page = document.new_page(width=width, height=height)
        normalized = tuple(component / 255 for component in color)
        page.draw_rect(page.rect, color=normalized, fill=normalized)
    document.save(path)
    document.close()


def test_images_to_pdf_preserves_order_and_aspect_ratio(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.jpg"
    output = tmp_path / "images.pdf"
    make_image(first, (255, 0, 0), (30, 15))
    make_image(second, (0, 0, 255), (15, 30))

    images_to_pdf([first, second], output)

    document = fitz.open(output)
    assert document.page_count == 2
    assert document[0].rect.width / document[0].rect.height == pytest.approx(2)
    assert document[1].rect.width / document[1].rect.height == pytest.approx(0.5)
    for page, expected in zip(document, ((255, 0, 0), (0, 0, 255))):
        image = page.get_pixmap().pil_image()
        pixels = image.convert("RGB")
        actual = pixels.getpixel((pixels.width // 2, pixels.height // 2))
        assert actual[0] == pytest.approx(expected[0], abs=4)
        assert actual[2] == pytest.approx(expected[2], abs=4)
    document.close()


def test_images_to_pdf_supports_jpeg_png_and_transparency(tmp_path):
    jpeg = tmp_path / "photo.jpeg"
    png = tmp_path / "transparent.png"
    output = tmp_path / "result.pdf"
    make_image(jpeg, (20, 180, 50), (12, 16))
    Image.new("RGBA", (20, 10), (255, 0, 0, 128)).save(png)

    images_to_pdf([jpeg, png], output)

    document = fitz.open(output)
    assert document.page_count == 2
    assert document[0].rect.height > document[0].rect.width
    assert document[1].rect.width > document[1].rect.height
    assert document[1].get_pixmap().pil_image().convert("RGB").getpixel((5, 2)) == (255, 127, 127)
    document.close()


def test_images_to_pdf_rejects_empty_missing_invalid_and_source_overwrite(tmp_path):
    with pytest.raises(PDFOperationError, match="at least one image"):
        images_to_pdf([], tmp_path / "empty.pdf")
    with pytest.raises(PDFOperationError, match="not found"):
        images_to_pdf([tmp_path / "missing.png"], tmp_path / "out.pdf")
    invalid = tmp_path / "invalid.png"
    invalid.write_bytes(b"not an image")
    with pytest.raises(PDFOperationError, match="Could not read image"):
        images_to_pdf([invalid], tmp_path / "out.pdf")
    image = tmp_path / "source.pdf"
    make_image(image, (20, 30, 40), (10, 10))
    with pytest.raises(PDFOperationError, match="cannot be one of the selected input"):
        images_to_pdf([image], image, overwrite=True)


def test_images_to_pdf_never_silently_replaces_existing_output(tmp_path):
    image = tmp_path / "source.png"
    output = tmp_path / "existing.pdf"
    make_image(image, (0, 0, 0), (10, 10))
    output.write_bytes(b"keep me")
    with pytest.raises(PDFOperationError, match="already exists"):
        images_to_pdf([image], output)
    assert output.read_bytes() == b"keep me"


@pytest.mark.parametrize("image_format, suffix", [("PNG", ".png"), ("JPEG", ".jpg"), ("TIFF", ".tiff"), ("WEBP", ".webp")])
def test_pdf_to_images_exports_ordered_pages_with_expected_names(tmp_path, image_format, suffix):
    source = tmp_path / "source.pdf"
    folder = tmp_path / "exported"
    folder.mkdir()
    make_pdf(source)
    progress = []

    outputs = pdf_to_images(
        source, folder, image_format=image_format, dpi=72,
        progress_callback=lambda current, total: progress.append((current, total)),
    )

    assert [path.name for path in outputs] == [f"page_001{suffix}", f"page_002{suffix}"]
    assert [path.exists() for path in outputs] == [True, True]
    assert progress == [(1, 2), (2, 2)]
    with Image.open(outputs[0]) as first, Image.open(outputs[1]) as second:
        assert first.size == (120, 80)
        assert second.size == (80, 120)
        assert first.convert("RGB").getpixel((first.width // 2, first.height // 2))[0] > 245
        assert second.convert("RGB").getpixel((second.width // 2, second.height // 2))[2] > 245


def test_pdf_to_images_rejects_invalid_pdf_and_password_protected_pdf(tmp_path):
    folder = tmp_path / "exported"
    folder.mkdir()
    with pytest.raises(PDFOperationError, match="not found"):
        pdf_to_images(tmp_path / "missing.pdf", folder)
    invalid = tmp_path / "invalid.pdf"
    invalid.write_bytes(b"not a PDF")
    with pytest.raises(PDFOperationError, match="Could not read"):
        pdf_to_images(invalid, folder)
    encrypted = tmp_path / "encrypted.pdf"
    document = fitz.open()
    document.new_page()
    document.save(encrypted, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="user")
    document.close()
    with pytest.raises(PDFOperationError, match="password-protected"):
        pdf_to_images(encrypted, folder)


def test_pdf_to_images_requires_confirmation_and_can_replace_existing_set(tmp_path):
    source = tmp_path / "source.pdf"
    folder = tmp_path / "exported"
    folder.mkdir()
    make_pdf(source, pages=((60, 40, (0, 255, 0)),))
    existing = folder / "page_001.png"
    existing.write_bytes(b"keep me")
    with pytest.raises(PDFOperationError, match="already exist"):
        pdf_to_images(source, folder)
    assert existing.read_bytes() == b"keep me"

    outputs = pdf_to_images(source, folder, overwrite=True)
    assert outputs == [existing]
    with Image.open(existing) as image:
        assert image.size == (125, 84)  # 60×40 points rendered at the default 150 DPI.


def test_pdf_to_images_validates_format_dpi_and_output_folder(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source, pages=((60, 40, (0, 255, 0)),))
    with pytest.raises(PDFOperationError, match="output format"):
        pdf_to_images(source, tmp_path, image_format="GIF")
    with pytest.raises(PDFOperationError, match="between 36 and 600"):
        pdf_to_images(source, tmp_path, dpi=0)
    with pytest.raises(PDFOperationError, match="existing output folder"):
        pdf_to_images(source, tmp_path / "missing")

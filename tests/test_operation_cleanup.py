"""Cross-feature regression tests for temporary output cleanup."""

import os

import pymupdf as fitz
import pytest
from PIL import Image

from src.core.add_page_numbers import add_page_numbers
from src.core.compress_pdf import compress_pdf
from src.core.images_to_pdf import images_to_pdf
from src.core.merge import merge_pdfs
from src.core.pdf_output import PDFOperationError
from src.core.pdf_to_images import pdf_to_images
from src.core.protect_pdf import protect_pdf
from src.core.remove_pages import remove_pdf_pages
from src.core.reorder_pages import reorder_pdf_pages
from src.core.unlock_pdf import unlock_pdf


def _make_pdf(path, *, encrypted=False):
    document = fitz.open()
    for label in ("first page", "second page"):
        page = document.new_page(width=200, height=200)
        page.insert_text((30, 50), label)
    options = {"encryption": fitz.PDF_ENCRYPT_AES_256, "user_pw": "test-password"} if encrypted else {}
    document.save(path, **options)
    document.close()


@pytest.mark.parametrize(
    "operation",
    ["merge", "remove", "reorder", "number", "images", "protect", "unlock", "compress"],
)
def test_failed_atomic_install_removes_temporary_pdf(tmp_path, monkeypatch, operation):
    """A failed final install must leave neither partial output nor temp PDFs."""
    plain = tmp_path / "source.pdf"
    encrypted = tmp_path / "encrypted.pdf"
    image_path = tmp_path / "image.png"
    output = tmp_path / f"{operation}.pdf"
    _make_pdf(plain)
    _make_pdf(encrypted, encrypted=True)
    Image.new("RGB", (20, 30), "blue").save(image_path)

    calls = {
        "merge": lambda: merge_pdfs([plain], output),
        "remove": lambda: remove_pdf_pages(plain, output, "1"),
        "reorder": lambda: reorder_pdf_pages(plain, output, [2, 1]),
        "number": lambda: add_page_numbers(plain, output),
        "images": lambda: images_to_pdf([image_path], output),
        "protect": lambda: protect_pdf(plain, output, "new-password"),
        "unlock": lambda: unlock_pdf(encrypted, output, "test-password"),
        "compress": lambda: compress_pdf(plain, output),
    }

    def fail_install(_temporary, _destination):
        raise OSError("simulated destination installation failure")

    monkeypatch.setattr(os, "link", fail_install)
    with pytest.raises(PDFOperationError):
        calls[operation]()

    assert not output.exists()
    assert list(tmp_path.glob(f".{operation}_*.pdf")) == []
    assert list(tmp_path.glob(f".{operation}_*.tmp")) == []


def test_failed_image_export_removes_staging_and_keeps_existing_outputs(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    output_folder = tmp_path / "images"
    output_folder.mkdir()
    _make_pdf(source)
    existing = output_folder / "page_001.png"
    existing.write_bytes(b"preserve this existing output")

    def fail_image_save(*_args, **_kwargs):
        raise OSError("simulated image encoding failure")

    monkeypatch.setattr(Image.Image, "save", fail_image_save)
    with pytest.raises(PDFOperationError, match="Could not render PDF page"):
        pdf_to_images(source, output_folder, overwrite=True)

    assert existing.read_bytes() == b"preserve this existing output"
    assert list(output_folder.glob(".pdfforge_export_*")) == []
    assert sorted(path.name for path in output_folder.iterdir()) == ["page_001.png"]


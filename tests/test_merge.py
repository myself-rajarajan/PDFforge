"""Temporary-file tests for the local PDF merge service."""

import pytest
from pypdf import PdfReader, PdfWriter

from src.core.merge import MergeError, merge_pdfs


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


def test_merge_two_pdfs_preserves_page_order(tmp_path):
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    output = tmp_path / "merged.pdf"
    make_pdf(first, [101, 102])
    make_pdf(second, [201])

    assert merge_pdfs([first, second], output) == output
    assert page_widths(output) == [101, 102, 201]


def test_merge_multiple_pdfs_preserves_displayed_order(tmp_path):
    inputs = [tmp_path / f"part-{index}.pdf" for index in range(3)]
    for path, width in zip(inputs, [310, 120, 230]):
        make_pdf(path, [width])
    output = tmp_path / "all-parts.pdf"

    merge_pdfs(inputs, output)

    assert page_widths(output) == [310, 120, 230]


def test_empty_input_selection_is_rejected(tmp_path):
    with pytest.raises(MergeError, match="Select at least one"):
        merge_pdfs([], tmp_path / "empty.pdf")


def test_missing_and_invalid_inputs_are_reported(tmp_path):
    output = tmp_path / "merged.pdf"
    with pytest.raises(MergeError, match="not found"):
        merge_pdfs([tmp_path / "missing.pdf"], output)

    invalid = tmp_path / "invalid.pdf"
    invalid.write_text("not a PDF", encoding="utf-8")
    with pytest.raises(MergeError, match="Could not read"):
        merge_pdfs([invalid], output)


def test_output_conflicts_and_input_overwrite_are_protected(tmp_path):
    source = tmp_path / "source.pdf"
    other = tmp_path / "other.pdf"
    make_pdf(source, [111])
    make_pdf(other, [222])

    with pytest.raises(MergeError, match="cannot be one of the selected input"):
        merge_pdfs([source, other], source, overwrite=True)
    assert page_widths(source) == [111]

    existing_output = tmp_path / "existing.pdf"
    make_pdf(existing_output, [333])
    with pytest.raises(MergeError, match="already exists"):
        merge_pdfs([source, other], existing_output)
    assert page_widths(existing_output) == [333]

    merge_pdfs([source, other], existing_output, overwrite=True)
    assert page_widths(existing_output) == [111, 222]


def test_invalid_output_folder_and_extension_are_rejected(tmp_path):
    source = tmp_path / "source.pdf"
    make_pdf(source, [100])
    with pytest.raises(MergeError, match="output folder"):
        merge_pdfs([source], tmp_path / "missing-folder" / "merged.pdf")
    with pytest.raises(MergeError, match="must end in .pdf"):
        merge_pdfs([source], tmp_path / "merged.txt")

"""Add visible signatures to the two PDFs beside this script.

Dependency: python -m pip install pymupdf
Run: python sign_documents.py
Originals are preserved. These are not certificate-based digital signatures.
"""

import html
import math
import os
from pathlib import Path

import fitz


SIGNATURE = "Nadira Bajraktarevi\u0107"
DOCUMENTS = (
    (
        "[CONTRACT]_TRAINING & TEST PERIOD_NADIRA BAJRAKTAREVIC.docx.pdf",
        "Contract_signed.pdf",
        "Freelancer\u2019s Signature",
    ),
    (
        "[POL] _ NDA _ Nadira Bajraktarevic .docx.pdf",
        "NDA_signed.pdf",
        "Receiving Party:",
    ),
)


def create_signature(name, style="handwritten", color="black"):
    if not isinstance(name, str) or not name.strip() or len(name) > 120:
        raise ValueError("Enter a name between 1 and 120 characters.")
    name = " ".join(name.split())
    fonts = {
        "handwritten": ("segoesc.ttf", "cursive"),
        "classic": ("georgiai.ttf", "serif"),
        "plain": ("segoeui.ttf", "sans-serif"),
    }
    colors = {"black": "#18181b", "blue": "#2458a6"}
    if style not in fonts or color not in colors:
        raise ValueError("Choose an available signature style and ink color.")

    filename, fallback = fonts[style]
    font_folder = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    font_face = (
        f"@font-face {{ font-family: signature; src: url('{filename}'); }}"
        if (font_folder / filename).is_file()
        else ""
    )
    css = (
        font_face
        + f"body {{ margin: 0; font-family: signature, {fallback}; "
        + f"font-size: 48pt; line-height: 1.5; color: {colors[color]}; }}"
    )
    signature = fitz.open()
    page = signature.new_page(width=8000, height=180)
    font_path = font_folder / filename
    font = fitz.Font(fontfile=str(font_path)) if font_path.is_file() else None
    if font and all(ord(character) < 0x590 and font.has_glyph(ord(character)) for character in name):
        page.insert_text(
            (8, 105),
            name,
            fontname="Signature",
            fontfile=str(font_path),
            fontsize=48,
            color=fitz.sRGB_to_pdf(int(colors[color][1:], 16)),
        )
    else:
        page.insert_htmlbox(
            page.rect,
            html.escape(name),
            css=css,
            archive=fitz.Archive(str(font_folder)) if font_folder.is_dir() else None,
            scale_low=1,
        )
    ink_bounds = [fitz.Rect(entry[1]) for entry in page.get_bboxlog()]
    if not ink_bounds:
        signature.close()
        raise ValueError("This name could not be rendered.")
    bounds = ink_bounds[0]
    for rectangle in ink_bounds[1:]:
        bounds |= rectangle
    page.set_cropbox((bounds + (-3, -3, 3, 3)) & page.rect)
    signature.subset_fonts()
    return signature


def sign_pdf(pdf_bytes, name, placements, style="handwritten", color="black"):
    if not isinstance(placements, list) or not 1 <= len(placements) <= 50:
        raise ValueError("Place between 1 and 50 signatures on the document.")
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        if document.needs_pass:
            raise ValueError("Unlock the password-protected PDF before uploading it.")
        with create_signature(name, style, color) as signature:
            aspect_ratio = signature[0].rect.height / signature[0].rect.width
            for placement in placements:
                if not isinstance(placement, dict):
                    raise ValueError("Invalid signature position.")
                page_number = placement.get("page")
                if type(page_number) is not int or not 0 <= page_number < len(document):
                    raise ValueError("Choose a valid document page.")
                coordinates = [placement.get(key) for key in ("x", "y", "width")]
                if any(
                    type(value) not in (int, float) or not math.isfinite(value)
                    for value in coordinates
                ):
                    raise ValueError("Invalid signature position or size.")
                left, top, width = coordinates
                if not 0.01 <= width <= 1:
                    raise ValueError("Choose a signature width between 1% and 100%.")
                page = document[page_number]
                rectangle = fitz.Rect(
                    left * page.rect.width,
                    top * page.rect.height,
                    (left + width) * page.rect.width,
                    top * page.rect.height + width * page.rect.width * aspect_ratio,
                )
                if not page.rect.contains(rectangle):
                    raise ValueError("Move the entire signature inside the page.")
                page.show_pdf_page(
                    rectangle * page.derotation_matrix,
                    signature,
                    0,
                    rotate=page.rotation,
                    overlay=True,
                )
        return document.tobytes(garbage=3, deflate=True)


def find_signature_line(page, label):
    labels = page.search_for(label)
    if len(labels) != 1:
        raise ValueError(f"Expected exactly one signing field labeled {label!r}.")

    label_rect = labels[0]
    lines = [
        fitz.Rect(word[:4])
        for word in page.get_text("words")
        if len(word[4]) >= 5
        and set(word[4]) == {"_"}
        and word[0] >= label_rect.x1 - 1
        and abs(word[1] - label_rect.y0) < 2
    ]
    if len(lines) != 1:
        raise ValueError(f"Could not identify the blank line after {label!r}.")

    signature_line = lines[0]
    printed_names = page.search_for("Nadira Bajraktarevic")
    if not any(0 <= name.y0 - signature_line.y1 < 30 for name in printed_names):
        raise ValueError("The signing field is not above Nadira's printed name.")
    return signature_line


def sign_document(source, destination, label, font_path, font):
    with fitz.open(source) as document:
        page_count = len(document)
        page = document[-1]
        signature_line = find_signature_line(page, label)
        font_size = min(
            16, (signature_line.width - 8) / font.text_length(SIGNATURE, fontsize=1)
        )
        if font_size < 8:
            raise ValueError(f"The signing field in {source.name} is too narrow.")

        baseline = signature_line.y1 - 1 + font.descender * font_size
        page.insert_text(
            (signature_line.x0 + 4, baseline),
            SIGNATURE,
            fontname="NadiraSignature",
            fontfile=str(font_path),
            fontsize=font_size,
            color=(0, 0, 0),
            overlay=True,
        )
        document.subset_fonts()
        document.save(destination, garbage=3, deflate=True)

    with fitz.open(destination) as signed:
        if len(signed) != page_count or signed[-1].get_text().count(SIGNATURE) != 1:
            raise RuntimeError(f"Signature verification failed for {destination.name}.")
    print(f"Saved: {destination}")


def main():
    folder = Path(__file__).resolve().parent
    font_path = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "segoesc.ttf"
    for required in [font_path, *(folder / entry[0] for entry in DOCUMENTS)]:
        if not required.is_file():
            raise FileNotFoundError(f"Required file not found: {required}")

    font = fitz.Font(fontfile=str(font_path))
    if any(not font.has_glyph(ord(character)) for character in SIGNATURE):
        raise ValueError("The signature font does not support the complete name.")

    for source_name, destination_name, label in DOCUMENTS:
        sign_document(
            folder / source_name, folder / destination_name, label, font_path, font
        )


if __name__ == "__main__":
    main()
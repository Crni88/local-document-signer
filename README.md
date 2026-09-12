# Local Document Signer

Upload a document, enter a name, place a transparent signature, and download a signed PDF. Originals are not modified, and processing stays on your computer.

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5050. For a different port, run `python app.py --port 5051`. Stop the server with Ctrl+C in its terminal.

## Sign

1. Choose a document or drag one into the app.
2. Enter the full name and select a style and ink color.
3. Choose a page, then click the signing location. The pen tool adds further signatures.
4. Drag signatures to move them. Select a signature to change its width or delete it. Undo restores placement changes.
5. Download the signed PDF.

The name, style, and ink color apply to all signatures in the current document. Width can be adjusted individually. Tab focuses controls; Enter on a focused page places a signature in its center; arrow keys move a focused signature; Delete removes the selected signature.

## Supported Files

- PDF, including scanned and rotated pages.
- DOCX, converted using Microsoft Word on Windows with `pywin32` installed.
- PNG, JPG/JPEG, TIFF, BMP, and WEBP images, converted to PDF.
- Other formats, including legacy DOC files, must be exported to PDF first.
- Maximum upload and converted PDF size: 25 MB. Maximum signatures per document: 50.

Unlock password-protected PDFs before uploading. Macro-enabled Word documents are not supported. Without Microsoft Word, export DOCX files to PDF first. Review any Word-to-PDF layout changes before downloading.

Accented names are supported. Windows fonts provide the signature styles; other scripts use fallback fonts and text shaping where needed. The preview shows the appearance embedded in the output.

## Privacy and Limitations

The server listens only on `127.0.0.1`. PDFs and images are processed in memory. DOCX conversion uses temporary files and a separate Word instance with macros and automatic link updates disabled. Temporary files are cleaned up after conversion. Only the theme preference is stored in the browser.

These are visible, typed electronic signatures, not certificate-based digital signatures or proof of identity. Adding content can invalidate an existing digital signature; the app asks for confirmation when one is detected.

## Python API

[sign_documents.py](sign_documents.py) exposes a reusable function:

```python
from pathlib import Path
from sign_documents import sign_pdf

source = Path("document.pdf")
signed = sign_pdf(
    source.read_bytes(),
    name="Amira Had\u017ei\u0107",
    placements=[{"page": 0, "x": 0.2, "y": 0.7, "width": 0.3}],
    style="handwritten",
    color="black",
)
source.with_name(source.stem + "_signed.pdf").write_bytes(signed)
```

Pages are zero-based. `x` and `y` are the signature's top-left position as fractions of the displayed page; `width` is a fraction of page width. Signatures must fit inside the page. Rotated pages use visible-page coordinates.

The original `python sign_documents.py` command still signs the two original Nadira documents.

## Tests

```powershell
python -m unittest discover -v
```

Tests cover signatures, Unicode, transparency, rotated pages, original-content preservation, upload and download validation, and Word conversion. The real Word conversion test is skipped when Word is unavailable.
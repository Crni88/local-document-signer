"""Create release package for Local Document Signer distribution."""

from pathlib import Path
import zipfile

README_CONTENT = """================================================================================
  LOCAL DOCUMENT SIGNER (Windows Standalone Release)
================================================================================

A fast, private, offline document signing application.
Upload documents, craft stylish electronic signatures, position them visually,
and download the signed PDF - without any data ever leaving your machine.

--------------------------------------------------------------------------------
1. QUICK START
--------------------------------------------------------------------------------
1. Double-click "LocalDocumentSigner.exe".
2. The companion control window will appear and automatically open your
   default web browser to http://127.0.0.1:5050 (or next free port).
3. Choose or drag-and-drop a document (PDF, Word DOCX, or images).
4. Enter your name, select your preferred signature style & ink color.
5. Click on any page to place your signature. Drag or resize as needed.
6. Click "Download signed PDF" to save your signed document.
7. When finished, click "Stop & Exit" on the companion window.

--------------------------------------------------------------------------------
2. KEY FEATURES
--------------------------------------------------------------------------------
* 100% Private & Local: All file processing and signature generation occurs
  strictly in-memory on your computer. Zero cloud uploads, zero telemetry.
* Broad Format Support:
  - PDF (including rotated and multi-page documents)
  - Word DOCX (converted via local Microsoft Word instance)
  - Images: PNG, JPG/JPEG, TIFF, BMP, WEBP (converted to PDF automatically)
* Vector & High-Res Signatures:
  - Styles: Script / Classic / Plain
  - Colors: Midnight Black / Royal Blue
* Interactive Visual Editor:
  - Free drag-and-drop placement
  - Adjustable signature scaling (1% to 95% of page width)
  - Multi-page navigation, zoom in/out, fit to width
  - Undo/redo support and keyboard shortcuts
  - Dark / Light / System theme switching

--------------------------------------------------------------------------------
3. COMMAND LINE OPTIONS (ADVANCED)
--------------------------------------------------------------------------------
You can also launch Local Document Signer from Command Prompt or PowerShell:

  LocalDocumentSigner.exe --cli
      Runs headlessly in your terminal without the companion GUI window.

  LocalDocumentSigner.exe --port 5055
      Binds the local server to a custom port number.

  LocalDocumentSigner.exe --no-browser
      Starts the local server without auto-opening the web browser.

--------------------------------------------------------------------------------
4. REQUIREMENTS & COMPATIBILITY
--------------------------------------------------------------------------------
* Operating System: Windows 10 or Windows 11 (64-bit).
* Dependencies: None! Standalone single executable (Python is not required).
* DOCX Support: Microsoft Word installed on Windows is required for automatic
  DOCX conversion. If Word is not installed, export DOCX to PDF first.

================================================================================
"""


def package():
    dist_dir = Path(__file__).resolve().parent / "dist"
    exe_path = dist_dir / "LocalDocumentSigner.exe"
    readme_path = dist_dir / "README.txt"
    zip_path = dist_dir / "LocalDocumentSigner-Windows.zip"

    assert exe_path.is_file(), f"Executable not found at {exe_path}"

    readme_path.write_text(README_CONTENT, encoding="utf-8")
    print(f"Created {readme_path}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(exe_path, arcname="LocalDocumentSigner.exe")
        zipf.write(readme_path, arcname="README.txt")

    print(f"Created release zip archive: {zip_path} ({zip_path.stat().st_size / (1024 * 1024):.1f} MB)")


if __name__ == "__main__":
    package()

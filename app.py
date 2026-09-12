"""Local document signing interface. Run with: python app.py"""

import argparse
import base64
import io
import json
from pathlib import Path
import sys

import fitz
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.utils import secure_filename

from sign_documents import create_signature, sign_pdf
from word_conversion import convert_docx, word_available


def get_bundle_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


bundle_dir = get_bundle_dir()
app = Flask(
    __name__,
    template_folder=str(bundle_dir / "templates"),
    static_folder=str(bundle_dir / "static"),
)
app.config.update(
    MAX_CONTENT_LENGTH=26 * 1024 * 1024,
    TRUSTED_HOSTS=["localhost", "127.0.0.1", "[::1]"],
)
MAX_FILE_SIZE = 25 * 1024 * 1024
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


@app.before_request
def protect_local_requests():
    if request.path.startswith("/api/") and request.method == "POST":
        if request.headers.get("X-Requested-With") != "LocalSigner":
            return jsonify(error="Open the local signing app to upload documents."), 403
        origin = request.headers.get("Origin")
        if origin and origin != request.host_url.rstrip("/"):
            return jsonify(error="Cross-origin uploads are not allowed."), 403


@app.after_request
def response_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' blob: data:; font-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    )
    return response


@app.errorhandler(ValueError)
@app.errorhandler(fitz.FileDataError)
def invalid_document(error):
    message = str(error) if not isinstance(error, fitz.FileDataError) else "This file could not be opened. Upload a valid, unlocked document."
    return jsonify(error=message), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error="Choose a document smaller than 25 MB."), 413


@app.errorhandler(HTTPException)
def request_error(error):
    return jsonify(error=error.description), error.code


def uploaded_file(pdf_only=False):
    upload = request.files.get("document")
    if upload is None or not upload.filename:
        raise ValueError("Choose a document first.")
    filename = secure_filename(upload.filename) or "document.pdf"
    contents = upload.read(MAX_FILE_SIZE + 1)
    if not contents or len(contents) > MAX_FILE_SIZE:
        raise ValueError("Choose a non-empty document smaller than 25 MB.")
    if pdf_only and Path(filename).suffix.lower() != ".pdf":
        raise ValueError("This action requires a PDF document.")
    return contents, filename


def check_pdf(document):
    if not document.is_pdf:
        raise ValueError("Upload a valid PDF document.")
    if document.needs_pass:
        raise ValueError("Unlock the password-protected PDF before uploading it.")
    if not len(document):
        raise ValueError("This document has no pages.")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/capabilities")
def capabilities():
    return jsonify(docx=word_available(), maxFileSize=MAX_FILE_SIZE)


@app.post("/api/document")
def inspect_document():
    contents, filename = uploaded_file()
    extension = Path(filename).suffix.lower()
    converted = extension != ".pdf"
    if extension == ".docx":
        contents = convert_docx(contents)
    elif extension in IMAGE_TYPES:
        with fitz.open(stream=contents, filetype=extension.lstrip(".")) as image:
            contents = image.convert_to_pdf()
    elif extension != ".pdf":
        raise ValueError("Supported files: PDF, DOCX, PNG, JPG, TIFF, BMP, and WEBP. Export other formats to PDF first.")
    if len(contents) > MAX_FILE_SIZE:
        raise ValueError("The converted PDF exceeds 25 MB. Export a smaller PDF first.")
    with fitz.open(stream=contents, filetype="pdf") as document:
        check_pdf(document)
        pages = [{"width": page.rect.width, "height": page.rect.height} for page in document]
        signed = bool(document.get_sigflags() > 0)
    return jsonify(
        filename=f"{Path(filename).stem}.pdf",
        pages=pages,
        pdf=base64.b64encode(contents).decode("ascii") if converted else None,
        digitallySigned=signed,
    )


@app.post("/api/page")
def preview_page():
    contents, filename = uploaded_file(pdf_only=True)
    page_number = int(request.form.get("page", "0"))
    with fitz.open(stream=contents, filetype="pdf") as document:
        check_pdf(document)
        if not 0 <= page_number < len(document):
            raise ValueError("Choose a valid page.")
        page = document[page_number]
        scale = min(2, 1500 / page.rect.width, 2100 / page.rect.height)
        preview = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png")
    return send_file(io.BytesIO(preview), mimetype="image/png")


@app.post("/api/signature")
def preview_signature():
    settings = request.get_json()
    if not isinstance(settings, dict):
        raise ValueError("Enter a signature name.")
    with create_signature(settings.get("name"), settings.get("style", "handwritten"), settings.get("color", "black")) as signature:
        page = signature[0]
        scale = min(3, 1800 / page.rect.width, 400 / page.rect.height)
        image = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True).tobytes("png")
        return jsonify(
            image=base64.b64encode(image).decode("ascii"),
            width=page.rect.width,
            height=page.rect.height,
        )


@app.post("/api/sign")
def download_signed():
    contents, filename = uploaded_file(pdf_only=True)
    try:
        placements = json.loads(request.form.get("placements", "[]"))
    except json.JSONDecodeError as error:
        raise ValueError("Invalid signature positions.") from error
    signed = sign_pdf(
        contents,
        request.form.get("name"),
        placements,
        request.form.get("style", "handwritten"),
        request.form.get("color", "black"),
    )
    return send_file(
        io.BytesIO(signed),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{Path(filename).stem}_signed.pdf",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5050)
    arguments = parser.parse_args()
    app.run(host="127.0.0.1", port=arguments.port, debug=False, use_reloader=False)
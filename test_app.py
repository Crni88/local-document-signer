import base64
import io
import json
import unittest
from unittest.mock import patch

import fitz

from app import app


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.headers = {"X-Requested-With": "LocalSigner"}
        with fitz.open() as document:
            document.new_page().insert_text((50, 50), "Original document")
            self.pdf = document.tobytes()

    def post_document(self, endpoint, contents=None, filename="example.pdf", **fields):
        fields["document"] = (io.BytesIO(self.pdf if contents is None else contents), filename)
        return self.client.post(endpoint, data=fields, headers=self.headers)

    def test_pdf_upload_and_preview(self):
        response = self.post_document("/api/document")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["pages"]), 1)
        self.assertIsNone(response.json["pdf"])
        response = self.post_document("/api/page", page="0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "image/png")

    def test_image_upload_converts_to_pdf(self):
        with fitz.open(stream=self.pdf) as document:
            image = document[0].get_pixmap().tobytes("png")
        response = self.post_document("/api/document", image, "scan.png")
        self.assertEqual(response.status_code, 200)
        with fitz.open(stream=base64.b64decode(response.json["pdf"])) as converted:
            self.assertEqual(len(converted), 1)

    def test_signature_preview_and_download(self):
        name = "Lejla O'Connor"
        response = self.client.post("/api/signature", json={"name": name}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fitz.Pixmap(base64.b64decode(response.json["image"])).alpha, 1)
        response = self.post_document(
            "/api/sign",
            name=name,
            placements=json.dumps([{"page": 0, "x": 0.1, "y": 0.5, "width": 0.4}]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("example_signed.pdf", response.headers["Content-Disposition"])
        with fitz.open(stream=response.data) as signed:
            self.assertIn(name, signed[0].get_text())
            self.assertIn("Original document", signed[0].get_text())

    def test_signed_word_download_converts_signed_pdf(self):
        name = "Lejla O'Connor"
        with patch("app.convert_pdf_to_docx", return_value=b"Word document") as convert:
            response = self.post_document(
                "/api/sign",
                name=name,
                format="docx",
                placements=json.dumps([{"page": 0, "x": 0.1, "y": 0.5, "width": 0.4}]),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assertIn("example_signed.docx", response.headers["Content-Disposition"])
        self.assertEqual(response.data, b"Word document")
        with fitz.open(stream=convert.call_args.args[0], filetype="pdf") as signed:
            self.assertIn(name, signed[0].get_text())

    def test_unsupported_download_format_is_rejected(self):
        response = self.post_document(
            "/api/sign",
            format="txt",
            name="Test Signer",
            placements=json.dumps([{"page": 0, "x": 0.1, "y": 0.5, "width": 0.4}]),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("PDF or Word", response.json["error"])

    def test_word_download_option_requires_word(self):
        with patch("app.word_available", return_value=True):
            response = self.client.get("/")
        self.assertIn(b'id="download-word"', response.data)

        with patch("app.word_available", return_value=False):
            response = self.client.get("/")
        self.assertNotIn(b'id="download-word"', response.data)

    def test_invalid_uploads_and_cross_origin_are_rejected(self):
        self.assertEqual(self.post_document("/api/document", b"bad PDF").status_code, 400)
        self.assertEqual(self.post_document("/api/document", b"text", "note.txt").status_code, 400)
        self.assertEqual(self.post_document("/api/page", page="99").status_code, 400)
        self.assertEqual(self.client.post("/api/document").status_code, 403)
        response = self.client.post(
            "/api/document", headers={**self.headers, "Origin": "https://example.com"}
        )
        self.assertEqual(response.status_code, 403)

    def test_password_protected_pdf_is_rejected(self):
        with fitz.open(stream=self.pdf) as document:
            protected = document.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="test-password", owner_pw="owner-password")
        response = self.post_document("/api/document", protected)
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json["error"])

    def test_upload_limit_has_a_useful_error(self):
        with patch.dict(app.config, {"MAX_CONTENT_LENGTH": 100}):
            response = self.post_document("/api/document")
        self.assertEqual(response.status_code, 413)
        self.assertIn("25 MB", response.json["error"])


if __name__ == "__main__":
    unittest.main()
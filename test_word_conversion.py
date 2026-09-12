import io
import unittest
from unittest.mock import patch
import zipfile

import fitz

from word_conversion import convert_docx, word_available


def make_docx():
    contents = io.BytesIO()
    with zipfile.ZipFile(contents, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>',
        )
        archive.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>',
        )
        archive.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>Word upload test</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>Signature: ____________________</w:t></w:r></w:p>'
            '</w:body></w:document>',
        )
    return contents.getvalue()


class WordConversionTests(unittest.TestCase):
    @unittest.skipUnless(word_available(), "Requires Microsoft Word and pywin32 on Windows.")
    def test_actual_word_conversion(self):
        result = convert_docx(make_docx())
        with fitz.open(stream=result, filetype="pdf") as document:
            self.assertEqual(len(document), 1)
            self.assertIn("Word upload test", document[0].get_text())

    def test_invalid_docx_is_rejected(self):
        with patch("word_conversion.word_available", return_value=True):
            with self.assertRaisesRegex(ValueError, "valid DOCX"):
                convert_docx(b"Not a Word document")

    def test_missing_word_explains_pdf_alternative(self):
        with patch("word_conversion.word_available", return_value=False):
            with self.assertRaisesRegex(ValueError, "Export the document to PDF"):
                convert_docx(make_docx())


if __name__ == "__main__":
    unittest.main()
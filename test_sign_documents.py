import unittest

import fitz

from sign_documents import create_signature, sign_pdf


class SigningTests(unittest.TestCase):
    def make_pdf(self, rotation=0):
        with fitz.open() as document:
            for text in ("Original first page", "Original second page"):
                page = document.new_page(width=500, height=700)
                page.insert_text((40, 40), text)
                page.set_rotation(rotation)
            return document.tobytes()

    def test_arbitrary_name_and_page_preserve_original(self):
        source = self.make_pdf()
        name = "Amira Had\u017ei\u0107"
        result = sign_pdf(source, name, [{"page": 0, "x": 0.2, "y": 0.4, "width": 0.4}])
        with fitz.open(stream=source) as original, fitz.open(stream=result) as signed:
            self.assertEqual(len(signed), 2)
            self.assertIn(name, signed[0].get_text())
            self.assertIn("Original first page", signed[0].get_text())
            self.assertEqual(original[1].get_pixmap().samples, signed[1].get_pixmap().samples)

    def test_signature_has_transparent_background_and_unicode(self):
        for name in ("Nadira Bajraktarevi\u0107", "\u0410\u043d\u0430", "\u674e\u660e", "\u0646\u0627\u062f\u0631\u0629"):
            with self.subTest(name=name), create_signature(name) as signature:
                pixmap = signature[0].get_pixmap(alpha=True)
                alpha_values = pixmap.samples[3::4]
                self.assertIn(0, alpha_values)
                self.assertIn(255, alpha_values)

    def test_html_characters_are_literal(self):
        with create_signature("A <B> & C") as signature:
            self.assertIn("A <B> & C", signature[0].get_text())

    def test_multiple_signatures_and_rotated_pages(self):
        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                source = self.make_pdf(rotation)
                placements = [
                    {"page": 0, "x": 0.2, "y": 0.4, "width": 0.4},
                    {"page": 1, "x": 0.1, "y": 0.7, "width": 0.3},
                ]
                result = sign_pdf(source, "Test Signer", placements)
                with fitz.open(stream=result) as signed:
                    for page, placement in zip(signed, placements):
                        self.assertEqual(page.rotation, rotation)
                        self.assertIn("Test Signer", page.get_text())
                        bounds = page.search_for("Test Signer")[0] * page.rotation_matrix
                        expected_left = placement["x"] * page.rect.width
                        expected_top = placement["y"] * page.rect.height
                        self.assertLess(abs(bounds.x0 - expected_left), 8)
                        self.assertLess(abs(bounds.y0 - expected_top), 25)

    def test_invalid_placements_are_rejected(self):
        for placement in (
            {"page": 3, "x": 0, "y": 0, "width": 0.3},
            {"page": 0, "x": 0.9, "y": 0, "width": 0.3},
            {"page": 0, "x": 0, "y": 0.99, "width": 0.3},
            {"page": 0, "x": float("nan"), "y": 0, "width": 0.3},
            {"page": 0, "x": 0, "y": 0, "width": -0.3},
        ):
            with self.subTest(placement=placement), self.assertRaises(ValueError):
                sign_pdf(self.make_pdf(), "Test Signer", [placement])

    def test_empty_name_and_empty_placements_are_rejected(self):
        with self.assertRaises(ValueError):
            create_signature("   ")
        with self.assertRaises(ValueError):
            sign_pdf(self.make_pdf(), "Test Signer", [])


if __name__ == "__main__":
    unittest.main()
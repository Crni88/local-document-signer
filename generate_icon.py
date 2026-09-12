"""Generate an application icon (.ico and .png) for Local Document Signer."""

from pathlib import Path
from PIL import Image, ImageDraw


def create_app_icon(output_ico_path="app_icon.ico", output_png_path="app_icon.png"):
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Document card background with rounded corners
    doc_x0, doc_y0 = 36, 20
    doc_x1, doc_y1 = 200, 236
    radius = 16

    # Shadow
    draw.rounded_rectangle(
        [doc_x0 + 4, doc_y0 + 6, doc_x1 + 4, doc_y1 + 6],
        radius=radius,
        fill=(15, 23, 42, 40),
    )

    # Document background (clean white/slate)
    draw.rounded_rectangle(
        [doc_x0, doc_y0, doc_x1, doc_y1],
        radius=radius,
        fill=(255, 255, 255, 255),
        outline=(203, 213, 225, 255),
        width=4,
    )

    # Header bar on document (primary blue accent)
    draw.rounded_rectangle(
        [doc_x0 + 16, doc_y0 + 20, doc_x1 - 16, doc_y0 + 44],
        radius=6,
        fill=(37, 99, 235, 240),
    )

    # Document text lines (skeleton lines)
    line_color = (226, 232, 240, 255)
    for y in (80, 104, 128, 152):
        draw.rounded_rectangle(
            [doc_x0 + 20, y, doc_x1 - 20, y + 8],
            radius=4,
            fill=line_color,
        )

    # Signature line
    draw.line(
        [(doc_x0 + 20, doc_y1 - 44), (doc_x1 - 40, doc_y1 - 44)],
        fill=(148, 163, 184, 255),
        width=3,
    )

    # Signature flourish (smooth ink curve in deep navy/blue)
    points = [
        (doc_x0 + 26, doc_y1 - 50),
        (doc_x0 + 40, doc_y1 - 70),
        (doc_x0 + 55, doc_y1 - 42),
        (doc_x0 + 72, doc_y1 - 65),
        (doc_x0 + 90, doc_y1 - 46),
        (doc_x0 + 115, doc_y1 - 62),
        (doc_x0 + 140, doc_y1 - 48),
    ]
    # Draw curved signature stroke
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=(30, 58, 138, 255), width=5)

    # Verified seal badge in bottom-right
    badge_cx, badge_cy = 188, 196
    badge_r = 30
    draw.ellipse(
        [badge_cx - badge_r - 2, badge_cy - badge_r - 2, badge_cx + badge_r + 2, badge_cy + badge_r + 2],
        fill=(255, 255, 255, 255),
    )
    draw.ellipse(
        [badge_cx - badge_r, badge_cy - badge_r, badge_cx + badge_r, badge_cy + badge_r],
        fill=(16, 185, 129, 255),
        outline=(5, 150, 105, 255),
        width=3,
    )

    # Checkmark inside badge
    check_coords = [
        (badge_cx - 12, badge_cy + 1),
        (badge_cx - 4, badge_cy + 9),
        (badge_cx + 13, badge_cy - 8),
    ]
    draw.line(check_coords, fill=(255, 255, 255, 255), width=5, joint="curve")

    # Save PNG
    img.save(output_png_path, "PNG")

    # Save multi-size ICO
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(output_ico_path, format="ICO", sizes=sizes)
    print(f"Generated {output_ico_path} and {output_png_path}")


if __name__ == "__main__":
    create_app_icon()

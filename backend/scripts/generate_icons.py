"""
Generate simple PNG icons for the Chrome extension using standard library zlib and struct.
Creates 16, 32, 48, 128 px PNG icons with a calm teal circle and an emblem.
"""

import zlib
import struct
from pathlib import Path


def create_png(width: int, height: int, pixels: list[list[tuple[int, int, int, int]]]) -> bytes:
    # 8-byte PNG header
    header = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk: width, height, bit depth 8, color type 6 (RGBA), compression 0, filter 0, interlace 0
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + ihdr_crc

    # Raw scanlines
    raw_lines = bytearray()
    for row in pixels:
        raw_lines.append(0)  # filter type 0 (None)
        for r, g, b, a in row:
            raw_lines.extend((r, g, b, a))

    idat_data = zlib.compress(bytes(raw_lines), 9)
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + idat_data) & 0xFFFFFFFF)
    idat_chunk = struct.pack(">I", len(idat_data)) + b"IDAT" + idat_data + idat_crc

    # IEND chunk
    iend_crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    iend_chunk = struct.pack(">I", 0) + b"IEND" + iend_crc

    return header + ihdr_chunk + idat_chunk + iend_chunk


def draw_icon(size: int) -> bytes:
    # Background: teal circle (#0d9488) on transparent background
    # Foreground: white book/symbol in center
    pixels = []
    center = (size - 1) / 2.0
    radius = size * 0.46
    inner_radius = size * 0.28

    teal = (13, 148, 136, 255)
    white = (255, 255, 255, 255)
    transparent = (0, 0, 0, 0)

    for y in range(size):
        row = []
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = (dx * dx + dy * dy) ** 0.5

            if dist <= radius:
                # Inside outer circle
                # Draw white central book/symbol
                # Normalized coordinates in [-1, 1]
                nx = dx / radius
                ny = dy / radius

                # Simple book glyph or emblem
                is_glyph = False
                # Book shape: left page and right page
                if -0.55 <= ny <= 0.45:
                    if (-0.6 <= nx <= -0.08 or 0.08 <= nx <= 0.6) and abs(ny) < 0.45:
                        # horizontal pages
                        if abs(ny) < 0.38:
                            is_glyph = True
                    # Book spine curve
                    if -0.08 < nx < 0.08 and -0.45 <= ny <= 0.45:
                        is_glyph = False

                if is_glyph:
                    row.append(white)
                else:
                    # Anti-alias boundary
                    if dist > radius - 1.0:
                        alpha = int(255 * (radius - dist))
                        row.append((teal[0], teal[1], teal[2], max(0, min(255, alpha))))
                    else:
                        row.append(teal)
            else:
                row.append(transparent)
        pixels.append(row)

    return create_png(size, size, pixels)


def main():
    icons_dir = Path(__file__).resolve().parent.parent.parent / "extension" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    for sz in [16, 32, 48, 128]:
        png_bytes = draw_icon(sz)
        out_file = icons_dir / f"icon{sz}.png"
        out_file.write_bytes(png_bytes)
        print(f"Generated {out_file.name} ({sz}x{sz}, {len(png_bytes)} bytes)")


if __name__ == "__main__":
    main()

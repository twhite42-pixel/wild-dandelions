"""Cut a single earring out of a white studio photo, for the hanging hero.

You should not need to run this again unless you swap the hero photos.
It needs Pillow and numpy, which the site itself does not:

    ./.venv/bin/pip install pillow numpy
    ./.venv/bin/python tools/make_hero_cutouts.py

How it works: the background is flood-filled inward from the edges, so white
highlights *inside* a bead stay white. Whatever solid shape is left gets split
into separate earrings, and the biggest single one is kept and trimmed.
"""

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent.parent
SOURCE = HERE / "public" / "static" / "img" / "products"
TARGET = HERE / "public" / "static" / "img" / "hero"

# Which pieces hang in the hero, and how wide each should end up.
HERO_PIECES = [
    ("sunset-marble.jpg", 150),
    ("beach-day-bar.jpg", 110),
    ("coral-swirl.jpg", 140),
    ("forget-me-not.jpg", 155),
]

WHITE_CUTOFF = 234  # any channel above this, at the edges, counts as backdrop


def background_mask(pixels: np.ndarray) -> np.ndarray:
    """True wherever a pixel is backdrop reachable from the image border."""
    near_white = pixels.min(axis=2) >= WHITE_CUTOFF
    height, width = near_white.shape

    seen = np.zeros_like(near_white)
    queue = deque()

    for y in range(height):
        for x in (0, width - 1):
            if near_white[y, x] and not seen[y, x]:
                seen[y, x] = True
                queue.append((y, x))
    for x in range(width):
        for y in (0, height - 1):
            if near_white[y, x] and not seen[y, x]:
                seen[y, x] = True
                queue.append((y, x))

    while queue:
        y, x = queue.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width:
                if near_white[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
    return seen


def largest_piece(solid: np.ndarray) -> np.ndarray:
    """Keep only the biggest connected blob - one earring out of the pair."""
    height, width = solid.shape
    labels = np.zeros((height, width), dtype=np.int32)
    best_label, best_size = 0, 0
    label = 0

    for start_y in range(height):
        row = solid[start_y]
        for start_x in np.flatnonzero(row):
            if labels[start_y, start_x]:
                continue
            label += 1
            size = 0
            stack = [(start_y, int(start_x))]
            labels[start_y, start_x] = label
            while stack:
                y, x = stack.pop()
                size += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if solid[ny, nx] and not labels[ny, nx]:
                            labels[ny, nx] = label
                            stack.append((ny, nx))
            if size > best_size:
                best_label, best_size = label, size

    return labels == best_label


def cut_out(filename: str, target_width: int) -> None:
    image = Image.open(SOURCE / filename).convert("RGB")
    pixels = np.asarray(image)

    solid = ~background_mask(pixels)
    solid = largest_piece(solid)

    alpha = Image.fromarray((solid * 255).astype(np.uint8), mode="L")
    # A touch of blur stops the edge looking cut out with scissors.
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))

    cut = image.convert("RGBA")
    cut.putalpha(alpha)
    cut = cut.crop(cut.getbbox())

    scale = target_width / cut.width
    cut = cut.resize(
        (target_width, max(1, round(cut.height * scale))), Image.LANCZOS
    )

    TARGET.mkdir(parents=True, exist_ok=True)
    out = TARGET / (Path(filename).stem + ".png")
    cut.save(out, optimize=True)
    print(f"  {filename:24} -> {out.name:24} {cut.width}x{cut.height}")


# The logo is drawn in exactly one colour: Mulled Wine from the brand deck.
LOGO_INK = (75, 75, 103)


def make_logo_transparent() -> None:
    """Turn the logo's white page into transparency.

    Flood filling would eat the dandelion, whose seed head is drawn in strokes
    barely a pixel wide. Instead, every pixel is read as 'how much ink is on
    the page here' - full ink is opaque, bare paper is clear, and the soft
    edges in between come out correctly anti-aliased.
    """
    source = HERE / "public" / "static" / "img" / "logo.png"
    pixels = np.asarray(Image.open(source).convert("RGB")).astype(np.float32)

    paper = 255.0
    ink_level = float(max(LOGO_INK))
    coverage = (paper - pixels.max(axis=2)) / (paper - ink_level)
    alpha = np.clip(coverage, 0.0, 1.0)

    logo = Image.new("RGBA", (pixels.shape[1], pixels.shape[0]), LOGO_INK + (0,))
    logo.putalpha(Image.fromarray((alpha * 255).astype(np.uint8), mode="L"))
    logo = logo.crop(logo.getbbox())

    scale = 900 / logo.width
    logo = logo.resize((900, round(logo.height * scale)), Image.LANCZOS)

    out = HERE / "public" / "static" / "img" / "logo-transparent.png"
    logo.save(out, optimize=True)
    print(f"  logo.png                 -> {out.name:24} {logo.width}x{logo.height}")


if __name__ == "__main__":
    print("Cutting hero pieces out of their backgrounds:")
    for filename, width in HERO_PIECES:
        cut_out(filename, width)
    make_logo_transparent()
    print("Done.")

"""Generate animated dark.svg and light.svg for the GitHub profile.

If assets/profile-photo.jpg, .jpeg, .png or .webp exists, the portrait area is
generated from that image with Pillow and NumPy. Without a photo, the script
keeps a neutral point map. It never invents a face.
"""

from __future__ import annotations

import argparse
import html
import math
import random
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps
    import numpy as np
except Exception:  # pragma: no cover - optional until a photo is present
    Image = None
    ImageChops = None
    ImageDraw = None
    ImageEnhance = None
    ImageFilter = None
    ImageOps = None
    np = None


ROOT = Path(__file__).resolve().parents[1]
PHOTO_CANDIDATES = [
    ROOT / "assets" / "profile-photo.jpg",
    ROOT / "assets" / "profile-photo.jpeg",
    ROOT / "assets" / "profile-photo.png",
    ROOT / "assets" / "profile-photo.webp",
]

WIDTH = 1180
HEIGHT = 610

THEMES = {
    "dark": {
        "bg": "#06110D",
        "window": "#0A1712",
        "panel": "#0D2118",
        "panel2": "#0F2A1E",
        "line": "#1E3A2D",
        "text": "#F8FAFC",
        "muted": "#9CA3AF",
        "soft": "#D1D5DB",
        "accent": "#10B981",
        "accent2": "#34D399",
        "green": "#047857",
        "white": "#FFFFFF",
        "shadow": "#020604",
        "red": "#EF4444",
    },
    "light": {
        "bg": "#F8FAFC",
        "window": "#FFFFFF",
        "panel": "#ECFDF5",
        "panel2": "#D1FAE5",
        "line": "#A7F3D0",
        "text": "#0B1F16",
        "muted": "#4B5563",
        "soft": "#374151",
        "accent": "#047857",
        "accent2": "#059669",
        "green": "#065F46",
        "white": "#FFFFFF",
        "shadow": "#CBD5E1",
        "red": "#DC2626",
    },
}


def find_photo() -> Path | None:
    for path in PHOTO_CANDIDATES:
        if path.exists():
            return path
    return None


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def leaders(label: str, value: str, width: int = 50) -> str:
    base = f"{label.upper()} "
    dots = "." * max(3, width - len(base) - len(value))
    return f"{base}{dots} {value}"


def dot_path(points: list[tuple[float, float, float]], size: float) -> str:
    commands = []
    for x, y, _opacity in points:
        commands.append(f"M{x:.1f},{y:.1f}h{size:.1f}v{size:.1f}h-{size:.1f}z")
    return "".join(commands)


def placeholder_points() -> list[tuple[float, float, float]]:
    random.seed(42)
    points: list[tuple[float, float, float]] = []
    cols, rows = 64, 42
    left, top = 80, 152
    dx, dy = 4.45, 5.85

    def in_letter_f(c: int, r: int) -> bool:
        return (8 <= c <= 12 and 8 <= r <= 31) or (12 <= c <= 27 and 8 <= r <= 11) or (
            12 <= c <= 24 and 19 <= r <= 22
        )

    def in_letter_p(c: int, r: int) -> bool:
        return (35 <= c <= 39 and 8 <= r <= 31) or (39 <= c <= 52 and 8 <= r <= 11) or (
            39 <= c <= 52 and 19 <= r <= 22
        ) or (50 <= c <= 54 and 11 <= r <= 19)

    for r in range(rows):
        for c in range(cols):
            wave = math.sin(c * 0.34) + math.cos(r * 0.39)
            border = c in (0, cols - 1) or r in (0, rows - 1)
            letter = in_letter_f(c, r) or in_letter_p(c, r)
            diagonal = (c + r) % 9 == 0
            density = 0.08 + (0.10 if wave > 1.1 else 0) + (0.45 if diagonal else 0)
            if border or letter or random.random() < density:
                opacity = 0.35 + random.random() * 0.55
                if letter:
                    opacity = 0.9
                points.append((left + c * dx, top + r * dy, opacity))
    return points


def photo_points(photo: Path, mode: str) -> list[tuple[float, float, float]]:
    if Image is None or np is None:
        return placeholder_points()

    img = Image.open(photo).convert("RGB")
    w, h = img.size
    side = min(w, h)
    # Head and shoulders friendly crop: center square, slightly high.
    left = max(0, (w - side) // 2)
    top = max(0, int((h - side) * 0.34))
    img = img.crop((left, top, left + side, top + side))
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    gray = ImageOps.grayscale(img).resize((84, 96), Image.Resampling.LANCZOS)
    arr = np.asarray(gray).astype(float) / 255.0

    if mode == "dark":
        # Lightweight background suppression: keep pixels that differ from the
        # border median, enough to avoid drawing a full photo rectangle.
        rgb_small = np.asarray(img.resize((84, 96), Image.Resampling.LANCZOS)).astype(float)
        border = np.concatenate([rgb_small[0], rgb_small[-1], rgb_small[:, 0], rgb_small[:, -1]])
        bg = np.median(border, axis=0)
        dist = np.linalg.norm(rgb_small - bg, axis=2)
        mask = dist > np.percentile(dist, 58)
        ink = (1.0 - arr) * mask
    else:
        ink = 1.0 - arr

    random.seed(73)
    points: list[tuple[float, float, float]] = []
    left_px, top_px = 70, 126
    dx, dy = 3.42, 3.72
    for r in range(96):
        for c in range(84):
            value = ink[r, c]
            threshold = 0.25 + random.random() * 0.42
            if value > threshold:
                opacity = min(0.98, 0.28 + value * 0.9)
                points.append((left_px + c * dx, top_px + r * dy, opacity))
    return points


def render_svg(theme_name: str, photo: Path | None) -> str:
    theme = THEMES[theme_name]
    points = photo_points(photo, theme_name) if photo else placeholder_points()
    groups: list[list[tuple[float, float, float]]] = [[] for _ in range(18)]
    for point in points:
        band = int((point[0] * 0.13 + point[1] * 0.19) % len(groups))
        groups[band].append(point)

    rows = [
        ("Subject", "Fabricio Prado"),
        ("Handle", "@DaikiLevrone"),
        ("Role", "Full-stack / automation"),
        ("Origin", "Lima, Peru"),
        ("Education", "UPC Systems Engineering"),
        ("Status", "Final cycle / shipping"),
        ("Core.Lang", "TypeScript, JS, Python, SQL"),
        ("Frontend", "React, Vite, Tailwind"),
        ("Motion", "Framer Motion, GSAP"),
        ("Backend", "Node.js, Firebase"),
        ("Database", "PostgreSQL, SQL"),
        ("Data", "Power BI, analysis"),
        ("Ops", "Git, Linux, Windows, TI"),
    ]

    row_svg = []
    y = 166
    for label, value in rows:
        row = leaders(label, value)
        row_svg.append(
            f'<text x="500" y="{y}" class="row" textLength="565" '
            f'lengthAdjust="spacingAndGlyphs">{esc(row)}</text>'
        )
        y += 24

    dot_svg = []
    for i, group in enumerate(groups):
        if not group:
            continue
        avg_opacity = sum(p[2] for p in group) / len(group)
        begin = i * 0.035
        drift_x = ((i % 6) - 2.5) * 1.5
        drift_y = ((i // 3) - 2.5) * 0.9
        dot_svg.append(
            f'<path d="{dot_path(group, 2.0)}" fill="{theme["accent2"]}" '
            f'opacity="{avg_opacity:.2f}" shape-rendering="crispEdges">'
            f'<animate attributeName="opacity" values="0;{avg_opacity:.2f};{avg_opacity:.2f};0.55;{avg_opacity:.2f}" '
            f'dur="14.2s" begin="{begin:.2f}s" repeatCount="indefinite" />'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 0; {drift_x:.1f} {drift_y:.1f}; 0 0" dur="14.2s" '
            f'begin="{begin:.2f}s" repeatCount="indefinite" />'
            f'</path>'
        )

    photo_label = "POINT PORTRAIT" if photo else "SIGNAL MAP"
    photo_hint = "DAIKILEVRONE // AVATAR FIELD" if photo else "DAIKILEVRONE // VISUAL FIELD"

    return f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Fabricio Prado - GitHub profile terminal banner</title>
  <desc id="desc">Animated terminal style banner for Fabricio Prado, GitHub user DaikiLevrone, using a dark green, emerald, white and gray identity.</desc>
  <style>
    .mono {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; }}
    .row {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 14px; fill: {theme["soft"]}; }}
    .label {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme["accent2"]}; letter-spacing: 0; }}
    .title {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 18px; font-weight: 700; fill: {theme["text"]}; }}
    .small {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; fill: {theme["muted"]}; }}
  </style>
  <rect width="{WIDTH}" height="{HEIGHT}" rx="0" fill="{theme["bg"]}" />
  <rect x="32" y="36" width="1116" height="538" rx="18" fill="{theme["shadow"]}" opacity="0.32" />
  <rect x="28" y="30" width="1116" height="538" rx="18" fill="{theme["window"]}" stroke="{theme["line"]}" stroke-width="2" />
  <rect x="28" y="30" width="1116" height="58" rx="18" fill="{theme["panel"]}" />
  <rect x="28" y="70" width="1116" height="18" fill="{theme["panel"]}" />
  <circle cx="61" cy="59" r="7" fill="{theme["red"]}" opacity="0.9" />
  <circle cx="85" cy="59" r="7" fill="{theme["accent"]}" opacity="0.9" />
  <circle cx="109" cy="59" r="7" fill="{theme["muted"]}" opacity="0.8" />
  <text x="144" y="64" class="title">profile.sh --live</text>
  <rect x="936" y="45" width="78" height="26" rx="13" fill="{theme["red"]}" opacity="0.16" stroke="{theme["red"]}" />
  <circle cx="953" cy="58" r="4" fill="{theme["red"]}">
    <animate attributeName="opacity" values="1;0.25;1" dur="1.25s" repeatCount="indefinite" />
  </circle>
  <text x="965" y="63" class="small" fill="{theme["red"]}">LIVE</text>
  <rect x="1028" y="43" width="88" height="30" rx="15" fill="{theme["accent"]}" opacity="0.18" stroke="{theme["accent"]}" />
  <text x="1044" y="63" class="small" fill="{theme["accent2"]}">@Daiki</text>

  <rect x="58" y="116" width="364" height="382" rx="10" fill="{theme["panel"]}" stroke="{theme["line"]}" />
  <text x="78" y="142" class="label">VISUAL.MAP / {photo_label}</text>
  <text x="78" y="480" class="small">{esc(photo_hint)}</text>
  <g opacity="0.18" stroke="{theme["line"]}">
    <path d="M78 164H402" />
    <path d="M78 450H402" />
    <path d="M78 164V450" />
    <path d="M402 164V450" />
  </g>
  <g>{''.join(dot_svg)}</g>

  <rect x="462" y="116" width="626" height="382" rx="10" fill="{theme["panel"]}" stroke="{theme["line"]}" />
  <text x="492" y="142" class="label">SYSTEM.INFO</text>
  <text x="500" y="464" class="small">$ focus --stack --automation --data</text>
  <rect x="770" y="125" width="276" height="26" rx="13" fill="{theme["panel2"]}" stroke="{theme["line"]}" />
  <text x="788" y="143" class="small">green terminal identity online</text>
  {''.join(row_svg)}
  <text x="500" y="526" class="small">fabricio@github:~$ ship useful systems</text>
  <rect x="772" y="513" width="9" height="18" fill="{theme["accent2"]}">
    <animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" repeatCount="indefinite" />
  </rect>
</svg>
'''


def draw_png_preview(theme_name: str, photo: Path | None, out: Path) -> None:
    if Image is None:
        return
    theme = THEMES[theme_name]
    img = Image.new("RGB", (WIDTH, HEIGHT), theme["bg"])
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((28, 30, 1144, 568), radius=18, fill=theme["window"], outline=theme["line"], width=2)
    draw.rounded_rectangle((58, 116, 422, 498), radius=10, fill=theme["panel"], outline=theme["line"], width=1)
    draw.rounded_rectangle((462, 116, 1088, 498), radius=10, fill=theme["panel"], outline=theme["line"], width=1)
    draw.text((144, 48), "profile.sh --live", fill=theme["text"])
    draw.text((78, 126), "VISUAL.MAP / " + ("POINT PORTRAIT" if photo else "SIGNAL MAP"), fill=theme["accent2"])
    for x, y, opacity in (photo_points(photo, theme_name) if photo else placeholder_points()):
        color = theme["accent2"] if opacity > 0.65 else theme["accent"]
        draw.rectangle((x, y, x + 2, y + 2), fill=color)
    y = 156
    for label, value in [
        ("Subject", "Fabricio Prado"),
        ("Handle", "@DaikiLevrone"),
        ("Role", "Full-stack / automation"),
        ("Origin", "Lima, Peru"),
        ("Education", "UPC Systems Engineering"),
        ("Core.Lang", "TypeScript, JS, Python, SQL"),
        ("Frontend", "React, Vite, Tailwind"),
        ("Data", "Power BI, SQL, analytics"),
    ]:
        draw.text((500, y), leaders(label, value, 48), fill=theme["soft"])
        y += 28
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-preview", action="store_true", help="Skip PNG preview generation.")
    args = parser.parse_args()

    photo = find_photo()
    for theme_name in ("dark", "light"):
        (ROOT / f"{theme_name}.svg").write_text(render_svg(theme_name, photo), encoding="utf-8", newline="\n")
        if not args.no_preview:
            draw_png_preview(theme_name, photo, ROOT / "previews" / f"banner-{theme_name}.png")

    if photo:
        print(f"Generated banners from {photo}")
    else:
        print("Generated banners without portrait.")


if __name__ == "__main__":
    main()

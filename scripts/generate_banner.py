"""Generate animated responsive banner SVGs for the GitHub profile.

If assets/profile-photo.jpg, .jpeg, .png or .webp exists, the portrait field is
generated from that image with Pillow and NumPy. Without a photo, the script
keeps an abstract point mark. It never invents a face.
"""

from __future__ import annotations

import argparse
import html
import math
import random
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
    import numpy as np
except Exception:  # pragma: no cover - optional until a photo is present
    Image = None
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

PALETTE = {
    "mist": "#E7DFF7",
    "soft": "#C6B4EE",
    "mid": "#A48AE0",
    "violet": "#7B5FD1",
    "deep": "#4E2FB0",
    "ink": "#110927",
    "ink2": "#1A0F36",
    "white": "#FFFFFF",
}

THEMES = {
    "dark": {
        "bg": PALETTE["ink"],
        "panel": PALETTE["ink2"],
        "panel2": "#241449",
        "line": PALETTE["violet"],
        "text": PALETTE["mist"],
        "muted": PALETTE["soft"],
        "accent": PALETTE["mid"],
        "accent2": PALETTE["soft"],
        "deep": PALETTE["deep"],
        "glow": PALETTE["mid"],
    },
    "light": {
        "bg": PALETTE["mist"],
        "panel": PALETTE["white"],
        "panel2": "#F4F0FC",
        "line": PALETTE["soft"],
        "text": PALETTE["deep"],
        "muted": "#5A438F",
        "accent": PALETTE["violet"],
        "accent2": PALETTE["mid"],
        "deep": PALETTE["deep"],
        "glow": PALETTE["violet"],
    },
}


def find_photo() -> Path | None:
    for path in PHOTO_CANDIDATES:
        if path.exists():
            return path
    return None


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def clean_svg(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"


def wrap_text(value: str, width: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        draft = " ".join(current + [word])
        if len(draft) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def placeholder_points(size: int) -> list[tuple[float, float, float]]:
    random.seed(42)
    points: list[tuple[float, float, float]] = []
    cols = 56
    rows = 56
    for r in range(rows):
        for c in range(cols):
            dx = c - cols / 2
            dy = r - rows / 2
            radius = math.sqrt(dx * dx + dy * dy)
            mark = (
                (abs(dx) < 4 and -18 < dy < 20)
                or (-18 < dx < -2 and -18 < dy < -11)
                or (2 < dx < 18 and -18 < dy < -11)
                or (-22 < dx < -10 and 2 < dy < 14)
                or (10 < dx < 22 and 2 < dy < 14)
            )
            ring = 22 < radius < 25 and (c + r) % 3 == 0
            noise = random.random() < 0.035
            if mark or ring or noise:
                points.append((c / cols * size, r / rows * size, 0.45 + random.random() * 0.5))
    return points


def photo_points(photo: Path, size: int, mode: str) -> list[tuple[float, float, float]]:
    if Image is None or np is None:
        return placeholder_points(size)

    img = Image.open(photo).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = max(0, (w - side) // 2)
    top = max(0, (h - side) // 2)
    img = img.crop((left, top, left + side, top + side))
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.45)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

    cells = 74
    gray = ImageOps.grayscale(img).resize((cells, cells), Image.Resampling.LANCZOS)
    arr = np.asarray(gray).astype(float) / 255.0
    rgb = np.asarray(img.resize((cells, cells), Image.Resampling.LANCZOS)).astype(float)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(rgb - bg, axis=2)
    contrast = np.maximum(1.0 - arr, dist / max(1.0, dist.max()))

    random.seed(91 if mode == "dark" else 97)
    points: list[tuple[float, float, float]] = []
    center = (cells - 1) / 2
    for r in range(cells):
        for c in range(cells):
            dx = c - center
            dy = r - center
            if math.sqrt(dx * dx + dy * dy) > center * 0.96:
                continue
            value = contrast[r, c]
            threshold = 0.19 + random.random() * 0.48
            if value > threshold:
                points.append((c / cells * size, r / cells * size, min(0.98, 0.32 + value * 0.75)))
    return points or placeholder_points(size)


def dot_groups(points: list[tuple[float, float, float]], x: int, y: int, dot: float) -> str:
    groups: list[list[tuple[float, float, float]]] = [[] for _ in range(20)]
    for point in points:
        band = int((point[0] * 0.11 + point[1] * 0.17) % len(groups))
        groups[band].append(point)

    svg = []
    colors = [PALETTE["mist"], PALETTE["soft"], PALETTE["mid"], PALETTE["violet"]]
    for index, group in enumerate(groups):
        if not group:
            continue
        path = "".join(
            f"M{x + px:.1f},{y + py:.1f}h{dot:.1f}v{dot:.1f}h-{dot:.1f}z" for px, py, _opacity in group
        )
        opacity = sum(p[2] for p in group) / len(group)
        drift = ((index % 5) - 2) * 1.2
        color = colors[index % len(colors)]
        svg.append(
            f'<path d="{path}" fill="{color}" opacity="{opacity:.2f}" shape-rendering="crispEdges">'
            f'<animate attributeName="opacity" values="0.28;{opacity:.2f};0.64;{opacity:.2f}" '
            f'dur="{8.8 + index * 0.13:.2f}s" begin="{index * 0.04:.2f}s" repeatCount="indefinite" />'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{drift:.1f} {-drift:.1f};0 0" '
            f'dur="{10.5 + index * 0.11:.2f}s" repeatCount="indefinite" />'
            "</path>"
        )
    return "".join(svg)


def defs(theme: dict, uid: str) -> str:
    return f"""
  <defs>
    <linearGradient id="{uid}-wash" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['mist']}" stop-opacity="0.12">
        <animate attributeName="stop-opacity" values="0.10;0.24;0.10" dur="7s" repeatCount="indefinite" />
      </stop>
      <stop offset="45%" stop-color="{PALETTE['mid']}" stop-opacity="0.20" />
      <stop offset="100%" stop-color="{PALETTE['deep']}" stop-opacity="0.30">
        <animate attributeName="stop-opacity" values="0.22;0.38;0.22" dur="8s" repeatCount="indefinite" />
      </stop>
    </linearGradient>
    <linearGradient id="{uid}-line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{PALETTE['deep']}" />
      <stop offset="52%" stop-color="{PALETTE['soft']}" />
      <stop offset="100%" stop-color="{PALETTE['violet']}" />
    </linearGradient>
    <filter id="{uid}-soft-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="{theme['deep']}" flood-opacity="0.28" />
    </filter>
  </defs>"""


def render_desktop(theme_name: str, photo: Path | None) -> str:
    theme = THEMES[theme_name]
    uid = f"banner-{theme_name}"
    points = photo_points(photo, 248, theme_name) if photo else placeholder_points(248)
    skills = ["React", "TypeScript", "Python", "SQL", "Power BI", "C#/.NET", "PHP"]
    chips = []
    chip_x = 58
    chip_y = 470
    for skill in skills:
        width = 44 + len(skill) * 11
        chips.append(
            f'<rect x="{chip_x}" y="{chip_y}" width="{width}" height="34" rx="17" fill="{theme["panel2"]}" '
            f'stroke="{theme["line"]}" stroke-opacity="0.72">'
            f'<animate attributeName="stroke-opacity" values="0.38;0.95;0.38" dur="6s" begin="{len(chips) * 0.12:.2f}s" repeatCount="indefinite" />'
            f'</rect><text x="{chip_x + 22}" y="{chip_y + 23}" class="chip">{esc(skill)}</text>'
        )
        chip_x += width + 12

    rows = [
        ("Frontend", "React, Vite, TypeScript and motion systems"),
        ("Automation", "Python scripts, workflow design and process tooling"),
        ("Systems", "C#/.NET, PHP, SQL and operational applications"),
        ("Data", "Power BI, PostgreSQL and analytics"),
    ]
    row_svg = []
    y = 264
    for label, text in rows:
        row_svg.append(f'<text x="64" y="{y}" class="row-label">{esc(label)}</text>')
        for line in wrap_text(text, 36)[:2]:
            row_svg.append(f'<text x="192" y="{y}" class="row-text">{esc(line)}</text>')
            y += 26
        y += 12

    return f'''<svg width="980" height="560" viewBox="0 0 980 560" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Fabricio Prado - animated GitHub profile banner</title>
  <desc id="desc">Responsive animated terminal banner for Fabricio Prado, GitHub user DaikiLevrone, using lavender and violet colors.</desc>
  <style>
    .mono {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; }}
    .name {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 52px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .handle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 22px; fill: {theme['muted']}; }}
    .kicker {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 19px; fill: {theme['accent2']}; }}
    .row-label {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 21px; font-weight: 700; fill: {theme['accent']}; }}
    .row-text {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 19px; fill: {theme['text']}; }}
    .chip {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 16px; fill: {theme['text']}; }}
    .tiny {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 15px; fill: {theme['muted']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="980" height="560" rx="0" fill="{theme['bg']}" />
  <rect x="18" y="18" width="944" height="524" rx="28" fill="url(#{uid}-wash)" filter="url(#{uid}-soft-shadow)" />
  <rect x="26" y="28" width="928" height="504" rx="24" fill="{theme['panel']}" stroke="{theme['line']}" stroke-width="2" />
  <rect x="26" y="28" width="928" height="62" rx="24" fill="{theme['panel2']}" />
  <rect x="26" y="70" width="928" height="20" fill="{theme['panel2']}" />
  <circle cx="62" cy="59" r="8" fill="{PALETTE['deep']}" />
  <circle cx="91" cy="59" r="8" fill="{PALETTE['violet']}" />
  <circle cx="120" cy="59" r="8" fill="{PALETTE['soft']}" />
  <text x="154" y="66" class="kicker">daikilevrone/profile --visual-system</text>
  <rect x="770" y="43" width="148" height="32" rx="16" fill="{theme['bg']}" stroke="{theme['line']}" />
  <circle cx="794" cy="59" r="5" fill="{theme['accent2']}">
    <animate attributeName="opacity" values="1;0.25;1" dur="1.4s" repeatCount="indefinite" />
  </circle>
  <text x="810" y="65" class="tiny">available</text>

  <text x="58" y="157" class="kicker">FULL-STACK / AUTOMATION / DATA SYSTEMS</text>
  <text x="58" y="216" class="name">Fabricio Prado</text>
  <text x="60" y="248" class="handle">@DaikiLevrone - Lima, Peru - UPC</text>
  {''.join(row_svg)}
  {''.join(chips)}

  <g>
    <circle cx="800" cy="302" r="150" fill="{theme['bg']}" opacity="0.42" stroke="url(#{uid}-line)" stroke-width="3">
      <animate attributeName="stroke-width" values="2;5;2" dur="6s" repeatCount="indefinite" />
    </circle>
    <circle cx="800" cy="302" r="123" fill="{theme['panel2']}" opacity="0.72" />
    <path d="M650 302a150 150 0 1 0 300 0a150 150 0 1 0 -300 0" stroke="{theme['accent2']}" stroke-width="2" stroke-dasharray="16 18" opacity="0.72">
      <animateTransform attributeName="transform" type="rotate" from="0 800 302" to="360 800 302" dur="24s" repeatCount="indefinite" />
    </path>
    {dot_groups(points, 676, 178, 3.1)}
    <text x="704" y="476" class="tiny">animated point portrait</text>
  </g>
  <rect x="58" y="520" width="304" height="4" rx="2" fill="url(#{uid}-line)">
    <animate attributeName="width" values="160;304;228;304" dur="7s" repeatCount="indefinite" />
  </rect>
</svg>
'''


def render_mobile(theme_name: str, photo: Path | None) -> str:
    theme = THEMES[theme_name]
    uid = f"banner-mobile-{theme_name}"
    points = photo_points(photo, 178, theme_name) if photo else placeholder_points(178)
    chips = ["React", "Python", "SQL", "Power BI", "C#/.NET", "PHP"]
    chip_svg = []
    x, y = 30, 534
    for skill in chips:
        width = min(170, 38 + len(skill) * 10)
        if x + width > 398:
            x = 30
            y += 42
        chip_svg.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="34" rx="17" fill="{theme["panel2"]}" stroke="{theme["line"]}" />'
            f'<text x="{x + 18}" y="{y + 23}" class="chip">{esc(skill)}</text>'
        )
        x += width + 10

    return f'''<svg width="430" height="730" viewBox="0 0 430 730" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Fabricio Prado - mobile GitHub profile banner</title>
  <desc id="desc">Mobile animated terminal banner for Fabricio Prado, GitHub user DaikiLevrone.</desc>
  <style>
    .name {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 38px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .handle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 17px; fill: {theme['muted']}; }}
    .kicker {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 15px; fill: {theme['accent2']}; }}
    .row {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 17px; fill: {theme['text']}; }}
    .chip {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 14px; fill: {theme['text']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="430" height="730" fill="{theme['bg']}" />
  <rect x="16" y="18" width="398" height="688" rx="24" fill="{theme['panel']}" stroke="{theme['line']}" stroke-width="2" />
  <rect x="16" y="18" width="398" height="58" rx="24" fill="{theme['panel2']}" />
  <circle cx="48" cy="47" r="7" fill="{PALETTE['deep']}" />
  <circle cx="74" cy="47" r="7" fill="{PALETTE['violet']}" />
  <circle cx="100" cy="47" r="7" fill="{PALETTE['soft']}" />
  <text x="126" y="53" class="kicker">profile.sh</text>
  <text x="30" y="122" class="kicker">FULL-STACK / DATA SYSTEMS</text>
  <text x="28" y="168" class="name">Fabricio</text>
  <text x="28" y="211" class="name">Prado</text>
  <text x="30" y="244" class="handle">@DaikiLevrone - Lima, Peru</text>
  <g>
    <circle cx="216" cy="368" r="110" fill="{theme['bg']}" opacity="0.46" stroke="url(#{uid}-line)" stroke-width="3" />
    <path d="M106 368a110 110 0 1 0 220 0a110 110 0 1 0 -220 0" stroke="{theme['accent2']}" stroke-width="2" stroke-dasharray="12 14" opacity="0.82">
      <animateTransform attributeName="transform" type="rotate" from="0 216 368" to="360 216 368" dur="22s" repeatCount="indefinite" />
    </path>
    {dot_groups(points, 127, 279, 2.6)}
  </g>
  <text x="30" y="506" class="row">React - Python - SQL - Power BI</text>
  {''.join(chip_svg)}
</svg>
'''


def draw_preview(theme_name: str, photo: Path | None, out: Path, mobile: bool = False) -> None:
    if Image is None:
        return
    theme = THEMES[theme_name]
    w, h = (430, 730) if mobile else (980, 560)
    img = Image.new("RGB", (w, h), theme["bg"])
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((18, 18, w - 18, h - 22), radius=24, fill=theme["panel"], outline=theme["line"], width=2)
    title = "Fabricio Prado" if not mobile else "Fabricio\nPrado"
    draw.multiline_text((30, 120 if mobile else 150), title, fill=theme["text"], spacing=8)
    dot_size = 178 if mobile else 248
    px, py = (127, 279) if mobile else (676, 178)
    for x, y, opacity in (photo_points(photo, dot_size, theme_name) if photo else placeholder_points(dot_size)):
        color = theme["accent2"] if opacity > 0.64 else theme["accent"]
        draw.rectangle((px + x, py + y, px + x + (2 if mobile else 3), py + y + (2 if mobile else 3)), fill=color)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-preview", action="store_true", help="Skip PNG preview generation.")
    args = parser.parse_args()

    photo = find_photo()
    outputs = {
        ROOT / "dark.svg": render_desktop("dark", photo),
        ROOT / "light.svg": render_desktop("light", photo),
        ROOT / "assets" / "banner-dark-mobile.svg": render_mobile("dark", photo),
        ROOT / "assets" / "banner-light-mobile.svg": render_mobile("light", photo),
    }
    for path, content in outputs.items():
        path.write_text(clean_svg(content), encoding="utf-8", newline="\n")

    if not args.no_preview:
        draw_preview("dark", photo, ROOT / "previews" / "banner-dark.png")
        draw_preview("light", photo, ROOT / "previews" / "banner-light.png")
        draw_preview("dark", photo, ROOT / "previews" / "banner-dark-mobile.png", mobile=True)
        draw_preview("light", photo, ROOT / "previews" / "banner-light-mobile.png", mobile=True)

    print(f"Generated banners from {photo}" if photo else "Generated banners without portrait.")


if __name__ == "__main__":
    main()

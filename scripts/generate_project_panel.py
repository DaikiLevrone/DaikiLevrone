"""Generate responsive animated project panel SVGs from projects.json."""

from __future__ import annotations

import argparse
import html
import json
import textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


ROOT = Path(__file__).resolve().parents[1]

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
        "card": "#201144",
        "card2": "#281753",
        "line": PALETTE["violet"],
        "text": PALETTE["mist"],
        "muted": PALETTE["soft"],
        "accent": PALETTE["mid"],
        "accent2": PALETTE["soft"],
        "chip": "#2C1A5E",
    },
    "light": {
        "bg": PALETTE["mist"],
        "panel": "#F8F5FE",
        "card": PALETTE["white"],
        "card2": "#F1EBFB",
        "line": PALETTE["soft"],
        "text": PALETTE["deep"],
        "muted": "#5B478E",
        "accent": PALETTE["violet"],
        "accent2": PALETTE["deep"],
        "chip": "#ECE5FA",
    },
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def clean_svg(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"


def wrap(value: str, width: int, limit: int) -> list[str]:
    return textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)[:limit]


def defs(theme: dict, uid: str) -> str:
    return f"""
  <defs>
    <linearGradient id="{uid}-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['mist']}" stop-opacity="0.13" />
      <stop offset="52%" stop-color="{PALETTE['mid']}" stop-opacity="0.18">
        <animate attributeName="stop-opacity" values="0.10;0.28;0.10" dur="8s" repeatCount="indefinite" />
      </stop>
      <stop offset="100%" stop-color="{PALETTE['deep']}" stop-opacity="0.26" />
    </linearGradient>
    <linearGradient id="{uid}-stroke" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{PALETTE['deep']}" />
      <stop offset="50%" stop-color="{PALETTE['soft']}" />
      <stop offset="100%" stop-color="{PALETTE['violet']}" />
    </linearGradient>
    <filter id="{uid}-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="{theme['accent2']}" flood-opacity="0.16" />
    </filter>
  </defs>"""


def chip_row(stack: list[str], x: int, y: int, max_x: int, theme: dict, class_name: str = "chip") -> str:
    svg = []
    chip_x = x
    for tech in stack:
        width = max(72, min(150, 35 + len(tech) * 10))
        if chip_x + width > max_x:
            break
        svg.append(
            f'<rect x="{chip_x}" y="{y}" width="{width}" height="32" rx="16" fill="{theme["chip"]}" stroke="{theme["line"]}" stroke-opacity="0.62" />'
            f'<text x="{chip_x + 17}" y="{y + 21}" class="{class_name}">{esc(tech)}</text>'
        )
        chip_x += width + 9
    return "".join(svg)


def desktop_card(project: dict, idx: int, theme: dict, uid: str) -> str:
    col = idx % 2
    row = idx // 2
    x = 38 + col * 482
    y = 136 + row * 300
    width = 444
    height = 260
    name = project["name"]
    category = project["category"]
    summary = project["summary"]
    repo = project["repoUrl"].replace("https://github.com/", "github.com/")
    body = []
    text_y = y + 104
    for line in wrap(summary, 48, 4):
        body.append(f'<text x="{x + 26}" y="{text_y}" class="body">{esc(line)}</text>')
        text_y += 22
    return f'''
  <g filter="url(#{uid}-shadow)">
    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="{theme["card"]}" stroke="url(#{uid}-stroke)" stroke-width="1.4" stroke-opacity="0.74">
      <animate attributeName="stroke-opacity" values="0.42;0.95;0.42" dur="{7.5 + idx * 0.4:.1f}s" repeatCount="indefinite" />
    </rect>
    <rect x="{x}" y="{y}" width="{width}" height="72" rx="18" fill="{theme["card2"]}" />
    <rect x="{x}" y="{y + 54}" width="{width}" height="18" fill="{theme["card2"]}" />
    <circle cx="{x + 27}" cy="{y + 36}" r="7" fill="{theme["accent2"]}">
      <animate attributeName="opacity" values="0.45;1;0.45" dur="{4.8 + idx * 0.2:.1f}s" repeatCount="indefinite" />
    </circle>
    <text x="{x + 48}" y="{y + 44}" class="name">{esc(name)}</text>
    <text x="{x + 26}" y="{y + 79}" class="category">{esc(category)}</text>
    {''.join(body)}
    {chip_row(project["stack"][:5], x + 26, y + 196, x + width - 24, theme)}
    <text x="{x + 26}" y="{y + 242}" class="link">{esc(repo)}</text>
    <rect x="{x + 26}" y="{y + height - 8}" width="72" height="3" rx="1.5" fill="{theme["accent2"]}">
      <animate attributeName="x" values="{x + 26};{x + width - 98};{x + 26}" dur="{8.2 + idx * 0.5:.1f}s" repeatCount="indefinite" />
    </rect>
  </g>'''


def mobile_card(project: dict, idx: int, theme: dict, uid: str) -> str:
    x = 22
    y = 118 + idx * 324
    width = 386
    height = 292
    body = []
    text_y = y + 102
    for line in wrap(project["summary"], 38, 5):
        body.append(f'<text x="{x + 22}" y="{text_y}" class="body">{esc(line)}</text>')
        text_y += 21

    return f'''
  <g filter="url(#{uid}-shadow)">
    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="{theme["card"]}" stroke="url(#{uid}-stroke)" stroke-width="1.3" stroke-opacity="0.76">
      <animate attributeName="stroke-opacity" values="0.46;1;0.46" dur="{7.5 + idx * 0.4:.1f}s" repeatCount="indefinite" />
    </rect>
    <rect x="{x}" y="{y}" width="{width}" height="70" rx="18" fill="{theme["card2"]}" />
    <rect x="{x}" y="{y + 52}" width="{width}" height="18" fill="{theme["card2"]}" />
    <text x="{x + 22}" y="{y + 42}" class="name">{esc(project["name"])}</text>
    <text x="{x + 22}" y="{y + 80}" class="category">{esc(project["category"])}</text>
    {''.join(body)}
    {chip_row(project["stack"][:4], x + 22, y + 216, x + width - 20, theme, "chip-mobile")}
    <text x="{x + 22}" y="{y + 274}" class="link">{esc(project["repoUrl"].replace("https://github.com/", "github.com/"))}</text>
  </g>'''


def render_desktop(theme_name: str, projects: list[dict]) -> str:
    theme = THEMES[theme_name]
    uid = f"projects-{theme_name}"
    cards = "".join(desktop_card(project, idx, theme, uid) for idx, project in enumerate(projects[:4]))
    return f'''<svg width="980" height="770" viewBox="0 0 980 770" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Featured projects by Fabricio Prado</title>
  <desc id="desc">Four selected public repositories with readable cards, verified repository links and a purple visual system.</desc>
  <style>
    .title {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 44px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .subtitle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 17px; fill: {theme['muted']}; }}
    .name {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 24px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .category {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 15px; fill: {theme['accent2']}; }}
    .body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 17px; fill: {theme['muted']}; }}
    .chip {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['text']}; }}
    .link {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['accent2']}; }}
    .note {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['muted']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="980" height="770" fill="{theme['bg']}" />
  <rect x="18" y="18" width="944" height="734" rx="28" fill="url(#{uid}-bg)" stroke="{theme['line']}" stroke-opacity="0.58" />
  <text x="38" y="72" class="title">selected.systems</text>
  <text x="40" y="106" class="subtitle">Curated public implementation work. Generated language noise removed.</text>
  <rect x="736" y="44" width="194" height="38" rx="19" fill="{theme['chip']}" stroke="{theme['line']}">
    <animate attributeName="stroke-opacity" values="0.45;1;0.45" dur="6s" repeatCount="indefinite" />
  </rect>
  <text x="760" y="68" class="subtitle">DaikiLevrone/repo</text>
  {cards}
</svg>
'''


def render_mobile(theme_name: str, projects: list[dict]) -> str:
    theme = THEMES[theme_name]
    uid = f"projects-mobile-{theme_name}"
    cards = "".join(mobile_card(project, idx, theme, uid) for idx, project in enumerate(projects[:4]))
    return f'''<svg width="430" height="1450" viewBox="0 0 430 1450" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Featured mobile projects by Fabricio Prado</title>
  <desc id="desc">Mobile stacked cards for four selected public repositories by Fabricio Prado.</desc>
  <style>
    .title {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 31px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .subtitle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['muted']}; }}
    .name {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 20px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .category {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['accent2']}; }}
    .body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 15px; fill: {theme['muted']}; }}
    .chip-mobile {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; fill: {theme['text']}; }}
    .link {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; fill: {theme['accent2']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="430" height="1450" fill="{theme['bg']}" />
  <rect x="14" y="16" width="402" height="1418" rx="24" fill="url(#{uid}-bg)" stroke="{theme['line']}" stroke-opacity="0.58" />
  <text x="22" y="62" class="title">selected.systems</text>
  <text x="24" y="92" class="subtitle">Real public repositories, readable on mobile.</text>
  {cards}
</svg>
'''


def draw_png(theme_name: str, projects: list[dict], out: Path, mobile: bool = False) -> None:
    if Image is None:
        return
    theme = THEMES[theme_name]
    w, h = (430, 1450) if mobile else (980, 770)
    img = Image.new("RGB", (w, h), theme["bg"])
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((18, 18, w - 18, h - 18), radius=24, fill=theme["panel"], outline=theme["line"], width=2)
    draw.text((28, 36), "selected.systems", fill=theme["text"])
    for idx, project in enumerate(projects[:4]):
        if mobile:
            x, y, cw, ch = 22, 118 + idx * 324, 386, 292
        else:
            x, y, cw, ch = 38 + (idx % 2) * 482, 136 + (idx // 2) * 300, 444, 260
        draw.rounded_rectangle((x, y, x + cw, y + ch), radius=18, fill=theme["card"], outline=theme["line"], width=2)
        draw.text((x + 22, y + 24), project["name"], fill=theme["text"])
        yy = y + 92
        for line in wrap(project["summary"], 40 if mobile else 48, 4):
            draw.text((x + 22, yy), line, fill=theme["muted"])
            yy += 20
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    projects = data["projects"]
    for theme in ("dark", "light"):
        (ROOT / "assets" / f"projects-{theme}.svg").write_text(
            clean_svg(render_desktop(theme, projects)), encoding="utf-8", newline="\n"
        )
        (ROOT / "assets" / f"projects-{theme}-mobile.svg").write_text(
            clean_svg(render_mobile(theme, projects)), encoding="utf-8", newline="\n"
        )
        if not args.no_preview:
            draw_png(theme, projects, ROOT / "previews" / f"projects-{theme}.png")
            draw_png(theme, projects, ROOT / "previews" / f"projects-{theme}-mobile.png", mobile=True)
    print(f"Generated project panels for {len(projects)} projects.")


if __name__ == "__main__":
    main()

"""Generate responsive project panel SVGs from projects.json."""

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
WIDTH = 1180
HEIGHT = 650

THEMES = {
    "dark": {
        "bg": "#06110D",
        "card": "#0A1712",
        "card2": "#0D2118",
        "line": "#1E3A2D",
        "text": "#F8FAFC",
        "muted": "#9CA3AF",
        "accent": "#10B981",
        "accent2": "#34D399",
        "chip": "#0F2A1E",
    },
    "light": {
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "card2": "#ECFDF5",
        "line": "#A7F3D0",
        "text": "#0B1F16",
        "muted": "#4B5563",
        "accent": "#047857",
        "accent2": "#059669",
        "chip": "#D1FAE5",
    },
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def wrap(value: str, width: int) -> list[str]:
    return textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)


def project_card(project: dict, idx: int, theme: dict) -> str:
    col = idx % 2
    row = idx // 2
    x = 54 + col * 548
    y = 122 + row * 236
    name = project["name"]
    category = project["category"]
    summary = project["summary"]
    stack = project["stack"][:5]
    repo = project["repoUrl"].replace("https://github.com/", "github.com/")
    demo = "Demo: not public" if not project.get("demoVerified") else f'Demo: {project["demoUrl"]}'

    lines = []
    text_y = y + 82
    for line in wrap(summary, 64)[:4]:
        lines.append(f'<text x="{x + 24}" y="{text_y}" class="body">{esc(line)}</text>')
        text_y += 19

    chip_svg = []
    chip_x = x + 24
    chip_y = y + 154
    for tech in stack:
        chip_w = max(54, min(124, 11 * len(tech) + 22))
        chip_svg.append(
            f'<rect x="{chip_x}" y="{chip_y}" width="{chip_w}" height="25" rx="12" fill="{theme["chip"]}" stroke="{theme["line"]}" />'
            f'<text x="{chip_x + 11}" y="{chip_y + 17}" class="chip">{esc(tech)}</text>'
        )
        chip_x += chip_w + 8
        if chip_x > x + 488:
            break

    return f'''
  <g>
    <rect x="{x}" y="{y}" width="514" height="206" rx="8" fill="{theme["card"]}" stroke="{theme["line"]}" />
    <rect x="{x}" y="{y}" width="514" height="54" rx="8" fill="{theme["card2"]}" />
    <text x="{x + 24}" y="{y + 33}" class="name">{esc(name)}</text>
    <text x="{x + 344}" y="{y + 33}" class="category">{esc(category)}</text>
    {''.join(lines)}
    {''.join(chip_svg)}
    <text x="{x + 24}" y="{y + 194}" class="link">{esc(repo)}</text>
    <text x="{x + 308}" y="{y + 194}" class="note">{esc(demo)}</text>
  </g>'''


def render_svg(theme_name: str, projects: list[dict]) -> str:
    theme = THEMES[theme_name]
    cards = "".join(project_card(project, idx, theme) for idx, project in enumerate(projects[:4]))
    return f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Featured projects by Fabricio Prado</title>
  <desc id="desc">Four selected public repositories with real technical scope and no unverified demo links.</desc>
  <style>
    .title {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 30px; font-weight: 700; fill: {theme["text"]}; }}
    .subtitle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 14px; fill: {theme["muted"]}; }}
    .name {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 19px; font-weight: 700; fill: {theme["text"]}; }}
    .category {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; fill: {theme["accent"]}; }}
    .body {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme["muted"]}; }}
    .chip {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 11px; fill: {theme["accent2"]}; }}
    .link {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 11px; fill: {theme["accent2"]}; }}
    .note {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 11px; fill: {theme["muted"]}; }}
  </style>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{theme["bg"]}" />
  <text x="54" y="64" class="title">selected.systems</text>
  <text x="54" y="93" class="subtitle">Real public repositories filtered with GitHub CLI. No empty repos, no forks, no invented demos.</text>
  <rect x="930" y="44" width="196" height="34" rx="17" fill="{theme["chip"]}" stroke="{theme["line"]}" />
  <text x="952" y="66" class="subtitle">DaikiLevrone/projects</text>
  {cards}
</svg>
'''


def draw_png(theme_name: str, projects: list[dict], out: Path) -> None:
    if Image is None:
        return
    theme = THEMES[theme_name]
    img = Image.new("RGB", (WIDTH, HEIGHT), theme["bg"])
    draw = ImageDraw.Draw(img)
    draw.text((54, 42), "selected.systems", fill=theme["text"])
    draw.text((54, 78), "Real public repositories filtered with GitHub CLI.", fill=theme["muted"])
    for idx, project in enumerate(projects[:4]):
        col = idx % 2
        row = idx // 2
        x = 54 + col * 548
        y = 122 + row * 236
        draw.rounded_rectangle((x, y, x + 514, y + 206), radius=8, fill=theme["card"], outline=theme["line"], width=1)
        draw.rectangle((x, y, x + 514, y + 54), fill=theme["card2"])
        draw.text((x + 24, y + 18), project["name"], fill=theme["text"])
        yy = y + 74
        for line in wrap(project["summary"], 58)[:4]:
            draw.text((x + 24, yy), line, fill=theme["muted"])
            yy += 18
        draw.text((x + 24, y + 176), project["repoUrl"].replace("https://github.com/", "github.com/"), fill=theme["accent2"])
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    projects = data["projects"]
    for theme in ("dark", "light"):
        (ROOT / "assets" / f"projects-{theme}.svg").write_text(render_svg(theme, projects), encoding="utf-8", newline="\n")
        if not args.no_preview:
            draw_png(theme, projects, ROOT / "previews" / f"projects-{theme}.png")
    print(f"Generated project panels for {len(projects)} projects.")


if __name__ == "__main__":
    main()

"""Generate profile stats, technology, streak and social badge SVG assets."""

from __future__ import annotations

import argparse
import html
import json
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
        "card": "#211347",
        "card2": "#2B195A",
        "line": PALETTE["violet"],
        "text": PALETTE["mist"],
        "muted": PALETTE["soft"],
        "accent": PALETTE["mid"],
        "accent2": PALETTE["soft"],
        "chip": "#301D66",
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

TECH_GROUPS = [
    ("Frontend", ["React", "Vite", "TypeScript", "JavaScript", "Tailwind", "Framer Motion", "GSAP"]),
    ("Data", ["Python", "SQL", "Power BI", "PostgreSQL"]),
    ("Backend", ["Firebase", "Node.js", "C#", ".NET", "PHP"]),
    ("Web Core", ["HTML", "CSS", "Git", "GitHub"]),
]


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def clean_svg(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"


def load_data() -> dict:
    return json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))


def stats_from_data(data: dict) -> dict:
    stats = data.get("profile", {}).get("stats", {})
    return {
        "repos": int(stats.get("publicRepositories", 11)),
        "contributions": int(stats.get("contributions", 25)),
        "commits": int(stats.get("commits", 19)),
        "created": int(stats.get("createdRepositories", 6)),
        "featured": len(data.get("projects", [])),
    }


def defs(theme: dict, uid: str) -> str:
    return f"""
  <defs>
    <linearGradient id="{uid}-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['mist']}" stop-opacity="0.12" />
      <stop offset="48%" stop-color="{PALETTE['mid']}" stop-opacity="0.22">
        <animate attributeName="stop-opacity" values="0.12;0.31;0.12" dur="7.5s" repeatCount="indefinite" />
      </stop>
      <stop offset="100%" stop-color="{PALETTE['deep']}" stop-opacity="0.28" />
    </linearGradient>
    <linearGradient id="{uid}-bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{PALETTE['deep']}" />
      <stop offset="45%" stop-color="{PALETTE['soft']}" />
      <stop offset="100%" stop-color="{PALETTE['violet']}" />
    </linearGradient>
    <filter id="{uid}-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="{theme['accent2']}" flood-opacity="0.15" />
    </filter>
  </defs>"""


def metric_card(x: int, y: int, width: int, label: str, value: str, note: str, theme: dict, uid: str, idx: int) -> str:
    bar_width = min(width - 40, 66 + len(value) * 11)
    return f'''
    <g filter="url(#{uid}-shadow)">
      <rect x="{x}" y="{y}" width="{width}" height="122" rx="18" fill="{theme["card"]}" stroke="{theme["line"]}" stroke-opacity="0.64" />
      <text x="{x + 22}" y="{y + 36}" class="metric-label">{esc(label)}</text>
      <text x="{x + 22}" y="{y + 82}" class="metric-value">{esc(value)}</text>
      <text x="{x + 118}" y="{y + 82}" class="metric-note">{esc(note)}</text>
      <rect x="{x + 22}" y="{y + 99}" width="{bar_width}" height="5" rx="2.5" fill="url(#{uid}-bar)">
        <animate attributeName="width" values="{max(36, bar_width - 54)};{bar_width};{max(48, bar_width - 20)};{bar_width}" dur="{6.5 + idx * 0.3:.1f}s" repeatCount="indefinite" />
      </rect>
    </g>'''


def tech_chip(x: int, y: int, label: str, theme: dict, idx: int, small: bool = False) -> tuple[str, int]:
    width = max(78 if small else 94, min(190, (34 if small else 42) + len(label) * (8 if small else 10)))
    klass = "tech-small" if small else "tech"
    svg = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{30 if small else 36}" rx="{15 if small else 18}" '
        f'fill="{theme["chip"]}" stroke="{theme["line"]}" stroke-opacity="0.68">'
        f'<animate attributeName="stroke-opacity" values="0.38;0.95;0.38" dur="{5.5 + idx * 0.11:.2f}s" repeatCount="indefinite" />'
        f'</rect><text x="{x + (15 if small else 19)}" y="{y + (20 if small else 24)}" class="{klass}">{esc(label)}</text>'
    )
    return svg, width


def render_metrics_desktop(theme_name: str, data: dict) -> str:
    theme = THEMES[theme_name]
    uid = f"metrics-{theme_name}"
    stats = stats_from_data(data)
    metric_svg = [
        metric_card(42, 138, 202, "Public repos", str(stats["repos"]), "active", theme, uid, 0),
        metric_card(264, 138, 202, "Contributions", str(stats["contributions"]), "calendar", theme, uid, 1),
        metric_card(42, 282, 202, "Commits", str(stats["commits"]), "tracked", theme, uid, 2),
        metric_card(264, 282, 202, "Featured", str(stats["featured"]), "systems", theme, uid, 3),
    ]
    tech_svg = []
    y = 166
    chip_index = 0
    for title, chips in TECH_GROUPS:
        tech_svg.append(f'<text x="536" y="{y}" class="group">{esc(title)}</text>')
        x = 536
        y += 24
        for tech in chips:
            chip, width = tech_chip(x, y, tech, theme, chip_index)
            if x + width > 936:
                x = 536
                y += 44
                chip, width = tech_chip(x, y, tech, theme, chip_index)
            tech_svg.append(chip)
            x += width + 9
            chip_index += 1
        y += 54

    return f'''<svg width="980" height="700" viewBox="0 0 980 700" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">GitHub stats and professional technology stack for Fabricio Prado</title>
  <desc id="desc">A two column visual panel with public GitHub metrics and technologies used by Fabricio Prado, excluding auxiliary generated languages.</desc>
  <style>
    .title {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 38px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .subtitle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 16px; fill: {theme['muted']}; }}
    .section {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 24px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .metric-label {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 15px; fill: {theme['muted']}; }}
    .metric-value {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 42px; font-weight: 900; fill: {theme['text']}; letter-spacing: 0; }}
    .metric-note {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 14px; fill: {theme['accent2']}; }}
    .group {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 17px; font-weight: 700; fill: {theme['accent2']}; }}
    .tech {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 15px; fill: {theme['text']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="980" height="700" fill="{theme['bg']}" />
  <rect x="18" y="18" width="944" height="664" rx="28" fill="url(#{uid}-bg)" stroke="{theme['line']}" stroke-opacity="0.58" />
  <text x="42" y="68" class="title">operating.stack</text>
  <text x="42" y="101" class="subtitle">Stats and real technologies, with auxiliary language noise removed.</text>
  <text x="42" y="130" class="section">GitHub pulse</text>
  <text x="536" y="130" class="section">Technologies</text>
  {''.join(metric_svg)}
  {''.join(tech_svg)}
</svg>
'''


def render_metrics_mobile(theme_name: str, data: dict) -> str:
    theme = THEMES[theme_name]
    uid = f"metrics-mobile-{theme_name}"
    stats = stats_from_data(data)
    metric_svg = [
        metric_card(28, 132, 174, "Repos", str(stats["repos"]), "public", theme, uid, 0),
        metric_card(228, 132, 174, "Contribs", str(stats["contributions"]), "year", theme, uid, 1),
        metric_card(28, 274, 174, "Commits", str(stats["commits"]), "tracked", theme, uid, 2),
        metric_card(228, 274, 174, "Featured", str(stats["featured"]), "systems", theme, uid, 3),
    ]
    tech_svg = []
    y = 496
    chip_index = 0
    for title, chips in TECH_GROUPS:
        tech_svg.append(f'<text x="28" y="{y}" class="group">{esc(title)}</text>')
        x = 28
        y += 24
        for tech in chips:
            chip, width = tech_chip(x, y, tech, theme, chip_index, small=True)
            if x + width > 402:
                x = 28
                y += 38
                chip, width = tech_chip(x, y, tech, theme, chip_index, small=True)
            tech_svg.append(chip)
            x += width + 8
            chip_index += 1
        y += 48

    return f'''<svg width="430" height="1060" viewBox="0 0 430 1060" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Mobile GitHub stats and technology stack for Fabricio Prado</title>
  <desc id="desc">Mobile visual panel with GitHub metrics and technologies used by Fabricio Prado.</desc>
  <style>
    .title {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 30px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .subtitle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['muted']}; }}
    .section {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 22px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .metric-label {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; fill: {theme['muted']}; }}
    .metric-value {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: 34px; font-weight: 900; fill: {theme['text']}; letter-spacing: 0; }}
    .metric-note {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; fill: {theme['accent2']}; }}
    .group {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 15px; font-weight: 700; fill: {theme['accent2']}; }}
    .tech-small {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: 12px; fill: {theme['text']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="430" height="1060" fill="{theme['bg']}" />
  <rect x="14" y="16" width="402" height="1028" rx="24" fill="url(#{uid}-bg)" stroke="{theme['line']}" stroke-opacity="0.58" />
  <text x="28" y="62" class="title">operating.stack</text>
  <text x="28" y="91" class="subtitle">Readable stats + real technologies.</text>
  <text x="28" y="122" class="section">GitHub pulse</text>
  {''.join(metric_svg)}
  <text x="28" y="438" class="section">Technologies</text>
  {''.join(tech_svg)}
</svg>
'''


def render_streak(theme_name: str, data: dict, mobile: bool = False) -> str:
    theme = THEMES[theme_name]
    uid = f"streak-{'mobile-' if mobile else ''}{theme_name}"
    stats = stats_from_data(data)
    width, height = (430, 280) if mobile else (980, 220)
    cards = []
    values = [
        ("current streak", "1", "day"),
        ("contribs", str(stats["contributions"]), "calendar"),
        ("created repos", str(stats["created"]), "total"),
    ]
    for idx, (label, value, note) in enumerate(values):
        if mobile:
            x, y, w = 28, 92 + idx * 58, 374
        else:
            x, y, w = 42 + idx * 300, 102, 268
        cards.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{44 if mobile else 70}" rx="16" fill="{theme["card"]}" stroke="{theme["line"]}" stroke-opacity="0.62" />'
            f'<text x="{x + 18}" y="{y + (27 if mobile else 30)}" class="streak-label">{esc(label)}</text>'
            f'<text x="{x + w - 116}" y="{y + (31 if mobile else 47)}" class="streak-value">{esc(value)}</text>'
            f'<text x="{x + w - 58}" y="{y + (31 if mobile else 47)}" class="streak-note">{esc(note)}</text>'
        )
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">GitHub contribution streak for DaikiLevrone</title>
  <desc id="desc">Contribution pulse summary for DaikiLevrone using a lavender and violet visual identity.</desc>
  <style>
    .title {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: {28 if mobile else 34}px; font-weight: 800; fill: {theme['text']}; letter-spacing: 0; }}
    .subtitle {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: {12 if mobile else 15}px; fill: {theme['muted']}; }}
    .streak-label {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: {12 if mobile else 14}px; fill: {theme['muted']}; }}
    .streak-value {{ font-family: Inter, Segoe UI, Arial, sans-serif; font-size: {25 if mobile else 37}px; font-weight: 900; fill: {theme['text']}; letter-spacing: 0; }}
    .streak-note {{ font-family: Consolas, "Liberation Mono", Menlo, monospace; font-size: {11 if mobile else 13}px; fill: {theme['accent2']}; }}
  </style>
  {defs(theme, uid)}
  <rect width="{width}" height="{height}" fill="{theme['bg']}" />
  <rect x="{14 if mobile else 18}" y="{16 if mobile else 18}" width="{402 if mobile else 944}" height="{248 if mobile else 184}" rx="24" fill="url(#{uid}-bg)" stroke="{theme['line']}" stroke-opacity="0.58" />
  <text x="{28 if mobile else 42}" y="{57 if mobile else 66}" class="title">contribution.pulse</text>
  <text x="{28 if mobile else 44}" y="{80 if mobile else 91}" class="subtitle">Public GitHub activity, refreshed by workflow.</text>
  {''.join(cards)}
  <rect x="{28 if mobile else 42}" y="{246 if mobile else 188}" width="{160 if mobile else 250}" height="4" rx="2" fill="url(#{uid}-bar)">
    <animate attributeName="width" values="{70 if mobile else 130};{160 if mobile else 250};{110 if mobile else 190};{160 if mobile else 250}" dur="7s" repeatCount="indefinite" />
  </rect>
</svg>
'''


def render_badge(theme_name: str, label: str, icon: str) -> str:
    theme = THEMES[theme_name]
    uid = f"badge-{theme_name}-{label.lower().replace(' ', '-')}"
    return f'''<svg width="210" height="54" viewBox="0 0 210 54" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{esc(label)} badge</title>
  <desc id="desc">Animated profile badge linking to {esc(label)}.</desc>
  {defs(theme, uid)}
  <rect x="2" y="2" width="206" height="50" rx="18" fill="{theme['card']}" stroke="url(#{uid}-bar)" stroke-width="1.5">
    <animate attributeName="stroke-opacity" values="0.45;1;0.45" dur="5.8s" repeatCount="indefinite" />
  </rect>
  <circle cx="31" cy="27" r="9" fill="{theme['accent2']}">
    <animate attributeName="r" values="8;10;8" dur="4.5s" repeatCount="indefinite" />
  </circle>
  <text x="50" y="33" font-family="Consolas, Liberation Mono, Menlo, monospace" font-size="15" font-weight="700" fill="{theme['text']}">{esc(icon)} {esc(label)}</text>
</svg>
'''


def draw_preview(theme_name: str, out: Path, mobile: bool = False) -> None:
    if Image is None:
        return
    theme = THEMES[theme_name]
    w, h = (430, 1060) if mobile else (980, 700)
    img = Image.new("RGB", (w, h), theme["bg"])
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((18, 18, w - 18, h - 18), radius=24, fill=theme["panel"], outline=theme["line"], width=2)
    draw.text((32, 42), "operating.stack", fill=theme["text"])
    draw.text((32, 82), "Stats and technologies", fill=theme["muted"])
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()
    data = load_data()
    assets = ROOT / "assets"

    for theme in ("dark", "light"):
        (assets / f"metrics-tech-{theme}.svg").write_text(
            clean_svg(render_metrics_desktop(theme, data)), encoding="utf-8", newline="\n"
        )
        (assets / f"metrics-tech-{theme}-mobile.svg").write_text(
            clean_svg(render_metrics_mobile(theme, data)), encoding="utf-8", newline="\n"
        )
        (assets / f"streak-{theme}.svg").write_text(clean_svg(render_streak(theme, data)), encoding="utf-8", newline="\n")
        (assets / f"streak-{theme}-mobile.svg").write_text(
            clean_svg(render_streak(theme, data, mobile=True)), encoding="utf-8", newline="\n"
        )
        (assets / f"badge-github-{theme}.svg").write_text(
            clean_svg(render_badge(theme, "GitHub", "GH")), encoding="utf-8", newline="\n"
        )
        (assets / f"badge-repositories-{theme}.svg").write_text(
            clean_svg(render_badge(theme, "Repositories", "RP")), encoding="utf-8", newline="\n"
        )
        (assets / f"badge-profile-repo-{theme}.svg").write_text(
            clean_svg(render_badge(theme, "Profile Repo", "PR")), encoding="utf-8", newline="\n"
        )
        if not args.no_preview:
            draw_preview(theme, ROOT / "previews" / f"metrics-tech-{theme}.png")
            draw_preview(theme, ROOT / "previews" / f"metrics-tech-{theme}-mobile.png", mobile=True)
    print("Generated profile metric, streak and badge assets.")


if __name__ == "__main__":
    main()

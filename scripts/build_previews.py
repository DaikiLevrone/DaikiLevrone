"""Build local HTML and PNG previews for review."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / "previews"


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Fabricio Prado GitHub Profile Preview</title>
  <style>
    :root { color-scheme: dark light; --bg: #06110d; --text: #f8fafc; --muted: #9ca3af; --line: #1e3a2d; }
    @media (prefers-color-scheme: light) { :root { --bg: #f8fafc; --text: #0b1f16; --muted: #4b5563; --line: #a7f3d0; } }
    body { margin: 0; background: var(--bg); color: var(--text); font: 16px/1.55 system-ui, sans-serif; }
    main { max-width: 980px; margin: 0 auto; padding: 24px 16px 56px; }
    img { max-width: 100%; height: auto; display: block; }
    section { border-top: 1px solid var(--line); margin-top: 28px; padding-top: 22px; }
    p { color: var(--muted); }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
    @media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="../dark.svg" />
      <source media="(prefers-color-scheme: light)" srcset="../light.svg" />
      <img src="../light.svg" alt="Fabricio Prado terminal banner" />
    </picture>
    <section>
      <h1>Fabricio Prado</h1>
      <p>Full-stack development, process automation, IT support and data/systems analysis.</p>
    </section>
    <section>
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="../assets/projects-dark.svg" />
        <source media="(prefers-color-scheme: light)" srcset="../assets/projects-light.svg" />
        <img src="../assets/projects-light.svg" alt="Selected professional repositories" />
      </picture>
    </section>
    <section class="grid">
      <img src="https://github-profile-summary-cards.vercel.app/api/cards/stats?username=DaikiLevrone&theme=github" alt="GitHub stats preview" />
      <img src="https://github-profile-summary-cards.vercel.app/api/cards/repos-per-language?username=DaikiLevrone&theme=github" alt="Repository languages preview" />
    </section>
  </main>
</body>
</html>
"""


def compose() -> None:
    if Image is None:
        return
    dark = Image.open(PREVIEWS / "banner-dark.png").convert("RGB")
    projects = Image.open(PREVIEWS / "projects-dark.png").convert("RGB")
    desktop = Image.new("RGB", (1280, 1700), "#06110D")
    mobile = Image.new("RGB", (430, 1400), "#06110D")

    draw = ImageDraw.Draw(desktop)
    draw.text((80, 44), "Desktop preview / README flow", fill="#F8FAFC")
    desktop.paste(dark.resize((1080, 559)), (100, 88))
    desktop.paste(projects.resize((1080, 595)), (100, 700))
    draw.rectangle((100, 1340, 1180, 1600), outline="#1E3A2D", width=2)
    draw.text((132, 1380), "Stats, languages and contribution snake render from GitHub-hosted endpoints.", fill="#9CA3AF")
    desktop.save(PREVIEWS / "profile-desktop.png")

    draw_m = ImageDraw.Draw(mobile)
    draw_m.text((18, 24), "Mobile preview", fill="#F8FAFC")
    mobile.paste(dark.resize((398, 206)), (16, 64))
    mobile.paste(projects.resize((398, 219)), (16, 304))
    draw_m.rectangle((16, 560, 414, 760), outline="#1E3A2D", width=2)
    draw_m.text((32, 596), "Text sections stay readable below the images.", fill="#9CA3AF")
    draw_m.text((32, 632), "External cards scale to 100% width on mobile.", fill="#9CA3AF")
    mobile.save(PREVIEWS / "profile-mobile.png")


def main() -> None:
    PREVIEWS.mkdir(exist_ok=True)
    (PREVIEWS / "README_PREVIEW.html").write_text(HTML, encoding="utf-8", newline="\n")
    compose()
    print("Generated previews in previews/.")


if __name__ == "__main__":
    main()

# Profile Setup And Maintenance

This repository is the public special GitHub profile repository for `DaikiLevrone/DaikiLevrone`.

## Current State

- Local branch: `main`
- Remote: `https://github.com/DaikiLevrone/DaikiLevrone.git`
- Repository visibility: public
- Visual palette: `#E7DFF7`, `#C6B4EE`, `#A48AE0`, `#7B5FD1`, `#4E2FB0`
- Source avatar/photo path: `E:\UPC\TB\github\assets\profile-photo.jpg`

The source avatar/photo is ignored by `.gitignore`; only the generated point portrait in the banner SVGs is published.

## Project Selection

Projects were inspected with GitHub CLI. The selected repositories are public, non-empty and not forks:

- `DaikiLevrone/SistemaGuiasBoletas`
- `DaikiLevrone/Enkarga`
- `DaikiLevrone/TRABAJO-FINAL-BPA`
- `DaikiLevrone/Fitfat-Site-Web`

The visual technology panel removes auxiliary language noise from generated or vendored files, such as Hack, Gherkin, Less and package/vendor internals.

## Local Regeneration

Install local dependencies only if Pillow or NumPy are missing:

```powershell
python -m pip install -r requirements.txt
```

Generate all visual assets:

```powershell
python scripts/generate_banner.py
python scripts/generate_project_panel.py
python scripts/generate_profile_sections.py
python scripts/build_previews.py
```

Refresh project metadata:

```powershell
python scripts/update_projects.py --write
python scripts/generate_project_panel.py
python scripts/generate_profile_sections.py
```

Validate locally and remotely:

```powershell
python scripts/validate_profile.py
python scripts/validate_profile.py --check-remote
```

## Actions

Two workflows are included:

- `.github/workflows/update-projects.yml`: refreshes project metadata and regenerated profile panels weekly and on manual dispatch.
- `.github/workflows/snake.yml`: regenerates the contribution snake every 12 hours, on manual dispatch and after pushes to `main`.

Minimum permissions are used:

```yaml
permissions:
  contents: write
```

External actions are pinned to full commit SHAs:

- `actions/checkout@11d5960a326750d5838078e36cf38b85af677262`
- `Platane/snk/svg-only@d8f6715049803e982ee5ff501b6b9b7d5deeb09b`
- `crazy-max/ghaction-github-pages@c0d7ff0487ee0415efb7f32dab10ea880330b1dd`

## Security Notes

- Do not commit `.env`, tokens, private keys, real databases, private PDFs or logs.
- Do not add demo URLs unless they return a real public page.
- Keep the source photo private unless you explicitly decide to publish it.
- Review generated SVGs before publishing because the banner can reveal a derived point portrait.

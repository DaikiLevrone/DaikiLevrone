# Profile Setup And Maintenance

This repository is the public special GitHub profile repository for `DaikiLevrone/DaikiLevrone`.

## Current State

- Local branch: `feat/github-profile`
- Remote: `https://github.com/DaikiLevrone/DaikiLevrone.git`
- Repository visibility: public
- Push status: not pushed by Codex
- Personal photo: not found in the original folder

Pending photo path:

```text
E:\UPC\TB\github\assets\profile-photo.jpg
```

Use that exact filename when you want the banner to generate a real point portrait. The source photo is ignored by `.gitignore` to avoid publishing a private image by accident.

## Project Selection

Projects were inspected with GitHub CLI. The selected repositories are public, non-empty and not forks:

- `DaikiLevrone/SistemaGuiasBoletas`
- `DaikiLevrone/Enkarga`
- `DaikiLevrone/TRABAJO-FINAL-BPA`
- `DaikiLevrone/Fitfat-Site-Web`

Repositories excluded from the featured section were too small, empty-looking, duplicate/older iterations, or mainly academic acceptance-criteria exercises. No demo link was added unless a public deployment or GitHub Pages site could be verified.

## Local Regeneration

Install local dependencies only if Pillow or NumPy are missing:

```powershell
python -m pip install -r requirements.txt
```

Generate banners:

```powershell
python scripts/generate_banner.py
```

Generate project panels:

```powershell
python scripts/generate_project_panel.py
```

Refresh project metadata and README project text:

```powershell
python scripts/update_projects.py --write
python scripts/generate_project_panel.py
```

Build review previews:

```powershell
python scripts/build_previews.py
```

Validate locally:

```powershell
python scripts/validate_profile.py
```

Validate remote links:

```powershell
python scripts/validate_profile.py --check-remote
```

The contribution snake URLs are allowed as pending until the first successful workflow creates the `output` branch.

## GitHub Stats

The README currently uses public `github-profile-summary-cards` URLs because they were reachable during validation and do not require secrets. For a more custom green theme, self-host `github-readme-stats` on Vercel:

1. Create a GitHub classic token with only the scope required by your deployment plan.
2. Never commit the token and never paste it into README files, scripts, issues or chats.
3. Fork `anuraghazra/github-readme-stats`.
4. Import the fork in Vercel.
5. Add `PAT_1` as a Vercel environment variable.
6. Replace the stats card URLs in `README.md` with your Vercel instance URL.

## Actions

Two workflows are included:

- `.github/workflows/update-projects.yml`: refreshes project metadata weekly and on manual dispatch.
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

To verify or update a pin later:

```powershell
git ls-remote https://github.com/actions/checkout.git refs/tags/v4
git ls-remote https://github.com/Platane/snk.git refs/tags/v3
git ls-remote https://github.com/crazy-max/ghaction-github-pages.git refs/tags/v3.1.0
```

## First Deployment Checklist

1. Review `README.md`, `dark.svg`, `light.svg` and `previews/README_PREVIEW.html`.
2. Commit locally if the diff looks correct.
3. Push `feat/github-profile`.
4. Open a PR or merge into `main`.
5. In the repository settings, go to Actions, General, Workflow permissions, and enable Read and write permissions for this repository.
6. Run `Generate Snake Animation` manually once.
7. After the run is green, verify that the `output` branch contains `github-snake.svg` and `github-snake-dark.svg`.

## Security Notes

- Do not commit `.env`, tokens, private keys, real databases, private PDFs or logs.
- Do not add demo URLs unless they return a real public page.
- Keep the source photo private unless you explicitly decide to publish it.
- The generated SVG can reveal a derived portrait, so review it before publishing.

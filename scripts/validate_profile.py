"""Validate profile assets, links and obvious secret leaks."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".md", ".json", ".py", ".svg", ".yml", ".yaml", ".txt", ".html", ".css"}
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(password|passwd|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]"),
]


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate_svg(path: Path, errors: list[str]) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        fail(f"{path}: invalid SVG XML: {exc}", errors)
        return
    if not root.tag.endswith("svg"):
        fail(f"{path}: root is not svg", errors)
    text = path.read_text(encoding="utf-8")
    if "<title" not in text or "<desc" not in text:
        fail(f"{path}: missing title or desc for accessibility", errors)
    if "role=\"img\"" not in text:
        fail(f"{path}: missing role=\"img\"", errors)


def scan_secrets(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or path.is_dir() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"{rel}: possible secret matched {pattern.pattern}", errors)


def extract_links() -> set[str]:
    links: set[str] = set()
    for path in [ROOT / "README.md", ROOT / "docs" / "PROFILE_SETUP.md"]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        links.update(re.findall(r"https?://[^\s)\"<>`]+", text))
    data = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    for project in data["projects"]:
        links.add(project["repoUrl"])
        if project.get("demoUrl"):
            links.add(project["demoUrl"])
    return links


def remote_ok(url: str) -> tuple[bool, str]:
    if "raw.githubusercontent.com/DaikiLevrone/DaikiLevrone/output/github-snake" in url:
        return True, "pending snake output branch"
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DaikiLevrone-profile-validator"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return 200 <= res.status < 400, f"HTTP {res.status}"
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            req = urllib.request.Request(url, headers={"User-Agent": "DaikiLevrone-profile-validator"})
            try:
                with urllib.request.urlopen(req, timeout=15) as res:
                    return 200 <= res.status < 400, f"HTTP {res.status}"
            except Exception as inner:
                return False, str(inner)
        return False, f"HTTP {exc.code}"
    except Exception as exc:
        return False, str(exc)


def validate_files(errors: list[str]) -> None:
    required = [
        ROOT / "README.md",
        ROOT / "dark.svg",
        ROOT / "light.svg",
        ROOT / "projects.json",
        ROOT / "assets" / "projects-dark.svg",
        ROOT / "assets" / "projects-light.svg",
        ROOT / ".github" / "workflows" / "snake.yml",
        ROOT / ".github" / "workflows" / "update-projects.yml",
        ROOT / "docs" / "PROFILE_SETUP.md",
    ]
    for path in required:
        if not path.exists():
            fail(f"missing required file: {path.relative_to(ROOT)}", errors)
    for path in [p for p in required if p.suffix == ".svg" and p.exists()]:
        validate_svg(path, errors)

    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    if 'alt="' not in readme and "alt=" not in readme:
        fail("README: no image alt text detected", errors)
    if "<!-- PROJECTS:START -->" not in readme or "<!-- PROJECTS:END -->" not in readme:
        fail("README: project markers missing", errors)


def validate_action_pins(errors: list[str]) -> None:
    action_ref = re.compile(r"uses:\s+[^@\s]+@([^\s#]+)")
    sha = re.compile(r"^[a-f0-9]{40}$")
    for workflow in (ROOT / ".github" / "workflows").glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        for ref in action_ref.findall(text):
            if not sha.match(ref):
                fail(f"{workflow.relative_to(ROOT)}: action ref is not pinned to full SHA: {ref}", errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-remote", action="store_true", help="Check remote HTTP links.")
    args = parser.parse_args()

    errors: list[str] = []
    validate_files(errors)
    validate_action_pins(errors)
    scan_secrets(errors)

    if args.check_remote:
        for url in sorted(extract_links()):
            ok, status = remote_ok(url)
            print(f"{status:>28}  {url}")
            if not ok:
                fail(f"remote link failed: {url} ({status})", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Profile validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Refresh project metadata and the README project block.

The script uses only the Python standard library so it can run in GitHub
Actions without installing dependencies. GITHUB_TOKEN is optional but recommended
for higher rate limits.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_FILE = ROOT / "projects.json"
README_FILE = ROOT / "README.md"
API = "https://api.github.com"
GRAPHQL_API = "https://api.github.com/graphql"


def request_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "DaikiLevrone-profile-refresh",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read().decode("utf-8"))


def request_graphql(query: str, variables: dict) -> dict | None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "DaikiLevrone-profile-refresh",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = urllib.request.Request(GRAPHQL_API, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=20) as res:
        data = json.loads(res.read().decode("utf-8"))
    if data.get("errors"):
        print(f"warning: GraphQL stats refresh failed: {data['errors']}", file=sys.stderr)
        return None
    return data.get("data")


def check_url(url: str | None) -> bool:
    if not url:
        return False
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "DaikiLevrone-profile-refresh"})
    try:
        with urllib.request.urlopen(req, timeout=12) as res:
            return 200 <= res.status < 400
    except Exception:
        return False


def refresh_project(project: dict) -> dict:
    owner_repo = project["repo"]
    meta = request_json(f"{API}/repos/{owner_repo}")
    project["repoUrl"] = meta["html_url"]
    project["lastPushedAt"] = meta.get("pushed_at")
    project["stars"] = meta.get("stargazers_count", 0)
    project["forks"] = meta.get("forks_count", 0)
    project["primaryLanguage"] = meta.get("language")

    homepage = meta.get("homepage")
    has_pages = bool(meta.get("has_pages"))
    demo = homepage if homepage and check_url(homepage) else None
    project["demoUrl"] = demo
    project["demoVerified"] = bool(demo)
    if demo:
        project["demoNote"] = "Public demo verified from repository homepage."
    elif has_pages:
        project["demoNote"] = "GitHub Pages is enabled but no public demo URL was verified by this script."
    else:
        project["demoNote"] = "No public deployment or GitHub Pages site was verified."
    return project


def refresh_profile_stats(data: dict) -> None:
    owner = data.get("profile", {}).get("owner", "DaikiLevrone")
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          totalCount
        }
        contributionsCollection {
          contributionCalendar { totalContributions }
          totalCommitContributions
          totalRepositoryContributions
        }
      }
    }
    """
    result = request_graphql(query, {"login": owner})
    user = result.get("user") if result else None
    if not user:
        return
    data.setdefault("profile", {}).setdefault("stats", {})
    stats = data["profile"]["stats"]
    stats["publicRepositories"] = user["repositories"]["totalCount"]
    stats["contributions"] = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    stats["commits"] = user["contributionsCollection"]["totalCommitContributions"]
    stats["createdRepositories"] = user["contributionsCollection"]["totalRepositoryContributions"]


def project_markdown(projects: list[dict]) -> str:
    blocks = []
    for project in projects:
        stack = ", ".join(project["stack"][:7])
        demo = f"[Demo]({project['demoUrl']})" if project.get("demoVerified") else "Demo: not public"
        blocks.append(
            "\n".join(
                [
                    f"### [{project['name']}]({project['repoUrl']})",
                    f"**{project['category']}** - {project['summary']}",
                    "",
                    f"- Impact: {project['impact']}",
                    f"- Stack: {stack}",
                    f"- Links: [Repository]({project['repoUrl']}) - {demo}",
                ]
            )
        )
    return "\n\n".join(blocks)


def replace_block(readme: str, marker: str, body: str) -> str:
    start = f"<!-- {marker}:START -->"
    end = f"<!-- {marker}:END -->"
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.S)
    replacement = f"{start}\n{body}\n{end}"
    if not pattern.search(readme):
        return readme
    return pattern.sub(replacement, readme)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write refreshed metadata and README block.")
    parser.add_argument("--skip-network", action="store_true", help="Only regenerate README from local projects.json.")
    args = parser.parse_args()

    data = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
    projects = data["projects"]

    if not args.skip_network:
        refreshed = []
        for project in projects:
            try:
                refreshed.append(refresh_project(project))
            except urllib.error.HTTPError as exc:
                print(f"warning: could not refresh {project['repo']}: HTTP {exc.code}", file=sys.stderr)
                refreshed.append(project)
        data["projects"] = refreshed
        refresh_profile_stats(data)
        data["profile"]["updatedAt"] = dt.datetime.now(dt.UTC).date().isoformat()

    readme = README_FILE.read_text(encoding="utf-8")
    readme = replace_block(readme, "PROJECTS", project_markdown(data["projects"]))

    if args.write:
        PROJECTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        README_FILE.write_text(readme, encoding="utf-8", newline="\n")
    else:
        print(project_markdown(data["projects"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

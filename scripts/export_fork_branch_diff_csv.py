#!/usr/bin/env python3
"""
Export Lakr233/vphone-cli forks to CSV: repo id, default-branch vs upstream main,
and branch-name symmetric diff (fork branches vs upstream branch names).

Requires: GITHUB_TOKEN or GH_TOKEN (e.g. `export GITHUB_TOKEN="$(gh auth token)"`).

Usage:
  export GITHUB_TOKEN="$(gh auth token)"
  python3 scripts/export_fork_branch_diff_csv.py [--out path/to.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

UPSTREAM = "Lakr233/vphone-cli"
UPSTREAM_MAIN = "main"
API = "https://api.github.com"


def _request(path: str, token: str) -> tuple[Any, dict[str, str]]:
    url = API + path if path.startswith("/") else path
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode()), {k.lower(): v for k, v in resp.headers.items()}


def _paged_branches(owner_repo: str, token: str) -> list[str]:
    names: list[str] = []
    page = 1
    while True:
        path = f"/repos/{owner_repo}/branches?per_page=100&page={page}"
        data, _ = _request(path, token)
        if not data:
            break
        for b in data:
            names.append(b["name"])
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.02)
    return names


def _paged_forks(token: str) -> list[dict[str, Any]]:
    forks: list[dict[str, Any]] = []
    page = 1
    while True:
        path = f"/repos/{UPSTREAM}/forks?per_page=100&page={page}&sort=newest"
        data, _ = _request(path, token)
        if not data:
            break
        forks.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.02)
    return forks


def _compare_default(
    token: str, fork_owner: str, default_branch: str
) -> tuple[str | None, int | None, int | None, str | None]:
    path = f"/repos/{UPSTREAM}/compare/{UPSTREAM_MAIN}...{fork_owner}:{default_branch}"
    try:
        cmp, _ = _request(path, token)
    except urllib.error.HTTPError as e:
        if e.code == 404 and default_branch != UPSTREAM_MAIN:
            path = f"/repos/{UPSTREAM}/compare/{UPSTREAM_MAIN}...{fork_owner}:{UPSTREAM_MAIN}"
            try:
                cmp, _ = _request(path, token)
            except urllib.error.HTTPError as e2:
                return None, None, None, e2.read().decode(errors="replace")[:300]
        else:
            return None, None, None, e.read().decode(errors="replace")[:300]
    return (
        cmp.get("status"),
        cmp.get("ahead_by"),
        cmp.get("behind_by"),
        None,
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        default="docs/vphone_upstream_forks_branch_diff.csv",
        help="Output CSV path (default: docs/vphone_upstream_forks_branch_diff.csv)",
    )
    args = p.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("Set GITHUB_TOKEN or GH_TOKEN (e.g. export GITHUB_TOKEN=\"$(gh auth token)\")", file=sys.stderr)
        return 1

    print("Fetching upstream branch list...", flush=True)
    upstream_branches = set(_paged_branches(UPSTREAM, token))
    print(f"  upstream branches: {len(upstream_branches)}", flush=True)

    print("Fetching forks...", flush=True)
    forks = _paged_forks(token)
    print(f"  forks: {len(forks)}", flush=True)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        w = csv.writer(fp)
        w.writerow(
            [
                "repo",
                "fork_default_branch",
                "vs_upstream_main_status",
                "commits_ahead_of_upstream_main",
                "commits_behind_upstream_main",
                "branches_on_fork_not_on_upstream",
                "branches_on_upstream_not_on_fork",
                "compare_error",
                "fork_pushed_at",
                "fork_stars",
            ]
        )

        for i, f in enumerate(forks):
            full = f["full_name"]
            owner = f["owner"]["login"]
            db = f.get("default_branch") or UPSTREAM_MAIN

            st, ahead, behind, err = _compare_default(token, owner, db)
            time.sleep(0.02)

            try:
                fb = set(_paged_branches(full, token))
            except urllib.error.HTTPError as e:
                fb = set()
                err = (err or "") + f" | branches_fetch:{e.code}"

            only_fork = sorted(fb - upstream_branches)
            only_up = sorted(upstream_branches - fb)

            w.writerow(
                [
                    full,
                    db,
                    st or "",
                    ahead if ahead is not None else "",
                    behind if behind is not None else "",
                    ";".join(only_fork),
                    ";".join(only_up),
                    err or "",
                    f.get("pushed_at") or "",
                    f.get("stargazers_count", 0),
                ]
            )

            if (i + 1) % 100 == 0:
                print(f"  processed {i + 1}/{len(forks)}...", flush=True)
            time.sleep(0.02)

    print(f"Wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

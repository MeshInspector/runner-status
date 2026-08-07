"""Builds _site/ from allowlist.json + the org's self-hosted runner list.

Only two fields per runner ever come from the GitHub API: `status` and `busy`.
Every human-readable string on the published page comes from allowlist.json, so a
runner that is not listed there cannot leak its name, labels or hostname.
"""

import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

token = os.environ.get("GH_TOKEN")
if not token:
    sys.exit("GH_TOKEN is not set")

root = Path(__file__).resolve().parent.parent
allowlist = json.loads((root / "allowlist.json").read_text(encoding="utf-8"))
org = allowlist.get("org", "MeshInspector")


def fetch_runners():
    live, page = {}, 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/orgs/{org}/actions/runners?per_page=100&page={page}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(req) as res:
            body = json.load(res)
        for runner in body["runners"]:
            live[runner["name"].lower()] = runner
        if not body["runners"] or len(live) >= body["total_count"]:
            return live
        page += 1


def state_of(runner):
    if runner is None:
        return "unregistered"
    if runner["status"] != "online":
        return "offline"
    return "busy" if runner["busy"] else "idle"


live = fetch_runners()

runners = [
    {
        "display": entry.get("display") or entry["name"],
        "os": entry["os"],
        "spec": entry.get("spec", ""),
        "state": state_of(live.get(entry["name"].lower())),
    }
    for entry in allowlist["runners"]
]

listed = {entry["name"].lower() for entry in allowlist["runners"]}
unlisted = sum(1 for name in live if name not in listed)

counts = {
    "total": len(runners),
    "idle": sum(1 for r in runners if r["state"] == "idle"),
    "busy": sum(1 for r in runners if r["state"] == "busy"),
    "down": sum(1 for r in runners if r["state"] in ("offline", "unregistered")),
}
if allowlist.get("showUnlistedCount"):
    counts["unlisted"] = unlisted

data = {
    "title": allowlist.get("title", f"{org} CI runners"),
    "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "counts": counts,
    "runners": runners,
}

site = root / "_site"
shutil.rmtree(site, ignore_errors=True)
shutil.copytree(root / "site", site)
(site / "runners.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print(f"{len(runners)} published, {unlisted} unlisted runner(s) suppressed")
print(json.dumps(counts))

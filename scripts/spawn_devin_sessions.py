#!/usr/bin/env python3
"""Fan out one Devin session per SonarCloud finding.

Reads the open issues and security hotspots SonarCloud reported for a pull
request (or a branch), and creates one Devin session per finding. Each session
triages the finding first (real vulnerability vs false positive) and only then
remediates, pushing its fix to a shared remediation branch.

Environment:
  SONAR_TOKEN        SonarCloud token with "Browse" on the project
  SONAR_HOST_URL     defaults to https://sonarcloud.io
  SONAR_PROJECT_KEY  e.g. HoltzTomas_sonarcloud-repsol-demo
  DEVIN_API_KEY      Devin API key of the org that owns the repo
  DEVIN_API_BASE     defaults to https://api.devin.ai
  GITHUB_REPOSITORY  owner/repo, provided by GitHub Actions
  PR_NUMBER          pull request number (omit to scan the branch)
  REMEDIATION_BRANCH branch every session targets, defaults to sonar/remediation
  MAX_SESSIONS       safety cap on the fan-out, defaults to 10
"""

import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

SONAR_HOST = os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io").rstrip("/")
SONAR_TOKEN = os.environ["SONAR_TOKEN"]
PROJECT_KEY = os.environ["SONAR_PROJECT_KEY"]
DEVIN_API_BASE = os.environ.get("DEVIN_API_BASE", "https://api.devin.ai").rstrip("/")
DEVIN_API_KEY = os.environ["DEVIN_API_KEY"]
REPO = os.environ["GITHUB_REPOSITORY"]
PR_NUMBER = os.environ.get("PR_NUMBER", "").strip()
REMEDIATION_BRANCH = os.environ.get("REMEDIATION_BRANCH", "sonar/remediation")
MAX_SESSIONS = int(os.environ.get("MAX_SESSIONS", "10"))

PLAYBOOK = pathlib.Path(__file__).resolve().parents[1] / "playbooks" / "sonar-triage-remediation.md"


def sonar_get(path, **params):
    if PR_NUMBER:
        params["pullRequest"] = PR_NUMBER
    url = f"{SONAR_HOST}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {SONAR_TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def findings():
    issues = sonar_get(
        "/api/issues/search",
        componentKeys=PROJECT_KEY,
        resolved="false",
        types="VULNERABILITY,BUG",
        ps=100,
    )["issues"]

    out = []
    for issue in issues:
        out.append(
            {
                "key": issue["key"],
                "kind": issue["type"],
                "severity": issue.get("severity", "UNKNOWN"),
                "rule": issue["rule"],
                "message": issue["message"],
                "component": issue["component"].split(":", 1)[-1],
                "line": issue.get("line"),
                "url": f"{SONAR_HOST}/project/issues?id={PROJECT_KEY}&open={issue['key']}",
            }
        )

    hotspots = sonar_get(
        "/api/hotspots/search",
        projectKey=PROJECT_KEY,
        status="TO_REVIEW",
        ps=100,
    ).get("hotspots", [])
    for hs in hotspots:
        out.append(
            {
                "key": hs["key"],
                "kind": "SECURITY_HOTSPOT",
                "severity": hs.get("vulnerabilityProbability", "UNKNOWN"),
                "rule": hs["ruleKey"],
                "message": hs["message"],
                "component": hs["component"].split(":", 1)[-1],
                "line": hs.get("line"),
                "url": f"{SONAR_HOST}/security_hotspots?id={PROJECT_KEY}&hotspots={hs['key']}",
            }
        )
    return out


def prompt_for(finding):
    playbook = PLAYBOOK.read_text()
    return (
        f"{playbook}\n\n"
        "## Finding to work\n"
        f"- Repository: {REPO}\n"
        f"- Pull request: {PR_NUMBER or '(branch scan)'}\n"
        f"- Remediation branch (base your PR on this branch): {REMEDIATION_BRANCH}\n"
        f"- Sonar key: {finding['key']}\n"
        f"- Type / severity: {finding['kind']} / {finding['severity']}\n"
        f"- Rule: {finding['rule']}\n"
        f"- Location: {finding['component']}:{finding['line']}\n"
        f"- Message: {finding['message']}\n"
        f"- Sonar link: {finding['url']}\n"
    )


def create_session(finding):
    payload = {
        "prompt": prompt_for(finding),
        "title": f"Sonar {finding['rule']} — {finding['component']}:{finding['line']}",
        "tags": ["sonar-remediation", finding["kind"].lower()],
        "idempotent": True,
    }
    req = urllib.request.Request(
        f"{DEVIN_API_BASE}/v1/sessions",
        data=json.dumps(payload).encode(),
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {DEVIN_API_KEY}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main():
    found = findings()
    if not found:
        print("No open Sonar findings; nothing to remediate.")
        return

    print(f"{len(found)} finding(s) reported by SonarCloud")
    lines = ["| Finding | Location | Devin session |", "| --- | --- | --- |"]
    for finding in found[:MAX_SESSIONS]:
        session = create_session(finding)
        url = session.get("url", session.get("session_id", "created"))
        print(f"  {finding['rule']} {finding['component']}:{finding['line']} -> {url}")
        lines.append(
            f"| `{finding['rule']}` {finding['message']} "
            f"| `{finding['component']}:{finding['line']}` | {url} |"
        )

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write("\n".join(lines) + "\n")

    skipped = len(found) - MAX_SESSIONS
    if skipped > 0:
        print(f"{skipped} finding(s) skipped by MAX_SESSIONS={MAX_SESSIONS}")


if __name__ == "__main__":
    sys.exit(main())

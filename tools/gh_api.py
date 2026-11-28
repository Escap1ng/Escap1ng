#!/usr/bin/env python3
"""Small GitHub client for the generators: a token from the environment in CI,
the logged-in gh CLI locally. Import only; nothing runs on import."""
import json
import os
import subprocess
import urllib.request

USER = "Escap1ng"


def graphql(query, variables):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/graphql",
            data=json.dumps({"query": query, "variables": variables}).encode(),
            headers={"Authorization": f"Bearer {token}",
                     "User-Agent": "profile-assets",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.load(r)
    else:
        args = ["gh", "api", "graphql", "-f", f"query={query}"]
        for key, value in variables.items():
            args += ["-f", f"{key}={value}"]
        payload = json.loads(subprocess.check_output(args))
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def rest(path):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            f"https://api.github.com/{path}",
            headers={"Authorization": f"Bearer {token}",
                     "User-Agent": "profile-assets",
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    return json.loads(subprocess.check_output(["gh", "api", path]))


def repositories(login=USER):
    return rest(f"users/{login}/repos?per_page=100")


def profile(login=USER):
    return rest(f"users/{login}")

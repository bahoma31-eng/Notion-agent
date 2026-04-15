#!/usr/bin/env python3

import os
import re
import json
import textwrap
import urllib.request


def gh_api(url: str, token: str):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_openai(api_key: str, model: str, prompt: str) -> str:
    # Minimal OpenAI-compatible Chat Completions request.
    # If you are using another provider with an OpenAI-compatible endpoint,
    # set OPENAI_BASE_URL accordingly.
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a senior software engineer. Produce a clean, actionable strategic implementation plan."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req) as resp:
        out = json.loads(resp.read().decode("utf-8"))

    return out["choices"][0]["message"]["content"]


def sanitize_filename(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_.-]", "_", s)
    return s


def main():
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    issue_number = os.environ["ISSUE_NUMBER"]

    issue = gh_api(f"https://api.github.com/repos/{repo}/issues/{issue_number}", token)
    title = issue.get("title", "")
    body = issue.get("body", "") or ""
    url = issue.get("html_url", "")

    # One-time config (copied from your current preferences)
    config = {
        "audience": "Mixed (maintainers + contributors)",
        "detail_level": "Detailed (step-by-step)",
        "phase_structure": "By area (CI/CD, security, dependencies, docs/quality)",
        "priorities": {
            "P0": "security issues, broken CI, production-impacting bugs",
            "P1": "important improvements and reliability/performance work",
            "P2": "nice-to-have refactors and cleanup",
        },
        "outputs": "Both PRs and a short report summary per phase",
        "constraints": "Do not expose secrets. Prefer pinned versions. Suggest dependency updates only when low-risk.",
    }

    prompt = textwrap.dedent(
        f"""
        Analyze the GitHub issue below, then produce a strategic plan file in Markdown.

        Requirements:
        - Output MUST be valid Markdown only.
        - Use this exact structure and headings:
          # Goal
          # Assumptions
          # Phases
          # Risks / Notes
        - Under # Phases, create a numbered list of phases. Each phase MUST include:
          - Description
          - Tasks (as a checklist)
          - Expected Output
        - Keep phases sequential and executable.
        - Use priorities P0/P1/P2 where relevant.
        - Do NOT include secrets. If the issue contains secrets, replace with [REDACTED] and mention it.

        Plan settings (fixed):
        {json.dumps(config, ensure_ascii=False, indent=2)}

        Issue:
        - Number: #{issue_number}
        - Title: {title}
        - URL: {url}
        - Body:\n{body}
        """
    ).strip()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing OPENAI_API_KEY secret")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    md = call_openai(api_key, model, prompt)

    # Ensure file is written
    filename = sanitize_filename(f"plan_strategy_{issue_number}.md")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md.strip() + "\n")


if __name__ == "__main__":
    main()

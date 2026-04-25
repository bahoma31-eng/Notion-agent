# Notion-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

An AI-powered GitHub automation agent that analyses newly opened issues and automatically generates structured, actionable strategic plan files using the OpenAI API. Every time a new issue is created in the repository, a `plan_strategy_<issue_number>.md` file is committed, giving contributors an instant, prioritised implementation roadmap.

---

## Features

- **Automatic plan generation** — a GitHub Actions workflow triggers on every new issue and produces a Markdown strategic plan without any manual steps.
- **AI-powered analysis** — uses OpenAI's Chat Completions API (configurable model) to create detailed, phased implementation plans.
- **Structured output** — every generated plan follows a consistent format: Goal, Assumptions, Phases (with tasks checklist and expected outputs), and Risks / Notes.
- **Configurable model** — supports any OpenAI-compatible endpoint and model via environment variables.
- **Zero external dependencies** — the Python script relies only on the standard library (`urllib`, `json`, `os`, `re`, `textwrap`).
- **Idempotent runs** — the workflow skips file generation if a plan file for that issue already exists.

---

## Requirements

- **Python** 3.11 or higher
- No third-party Python packages are required (standard library only)
- A GitHub repository with Actions enabled
- An **OpenAI API key** (or a compatible provider key)

---

## Installation

1. **Fork / clone** this repository:

   ```bash
   git clone https://github.com/bahoma31-eng/Notion-agent.git
   cd Notion-agent
   ```

2. **Add required secrets** to your GitHub repository (Settings → Secrets and variables → Actions):

   | Secret | Required | Description |
   |--------|----------|-------------|
   | `OPENAI_API_KEY` | ✅ | Your OpenAI (or compatible) API key |

3. **Add optional variables** (Settings → Secrets and variables → Actions → Variables):

   | Variable | Default | Description |
   |----------|---------|-------------|
   | `OPENAI_MODEL` | `gpt-4o-mini` | Model name to use for generation |
   | `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Base URL for the OpenAI-compatible endpoint |

4. The GitHub Actions workflow (`.github/workflows/auto_plan_strategy.yml`) is already configured and will activate automatically once secrets are set.

---

## Usage

### Automatic (recommended)

Simply **open a new issue** in your repository. The `Auto-create plan_strategy file` workflow will:

1. Check out the repository.
2. Fetch the issue title and body from the GitHub API.
3. Call the OpenAI API to generate a structured plan.
4. Commit and push `plan_strategy_<issue_number>.md` to the repository.

### Manual (local)

You can also run the script locally by exporting the required environment variables:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_REPOSITORY="bahoma31-eng/Notion-agent"
export ISSUE_NUMBER="7"
export OPENAI_API_KEY="sk-your-key-here"
# Optional overrides:
export OPENAI_MODEL="gpt-4o"
export OPENAI_BASE_URL="https://api.openai.com/v1"

python scripts/generate_plan_strategy.py
```

The script writes the resulting plan to `plan_strategy_<ISSUE_NUMBER>.md` in the current working directory.

---

## Project Structure

```
Notion-agent/
├── .github/
│   └── workflows/
│       └── auto_plan_strategy.yml  # GitHub Actions workflow that triggers on new issues
├── scripts/
│   └── generate_plan_strategy.py   # Core Python script: fetches issue data and calls OpenAI
├── input/                          # Input data files (images, JSON tasks, Markdown notes)
├── intput/                         # Alternate input folder (legacy; contains initial plan stub)
├── plans/                          # Additional strategy and planning Markdown files
├── plan_strategy_<N>.md            # Auto-generated plan files (one per issue number)
└── README.md                       # This file
```

---

## Configuration

All runtime configuration is done through **environment variables** (injected as GitHub Actions secrets/variables in CI, or exported in your shell for local runs):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | ✅ | — | GitHub token used to fetch issue details via the API. Automatically available in Actions. |
| `GITHUB_REPOSITORY` | ✅ | — | `owner/repo` string (e.g. `bahoma31-eng/Notion-agent`). Automatically available in Actions. |
| `ISSUE_NUMBER` | ✅ | — | The issue number to generate a plan for. Automatically set in Actions. |
| `OPENAI_API_KEY` | ✅ | — | API key for the OpenAI (or compatible) service. |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | Model name passed to the chat completions endpoint. |
| `OPENAI_BASE_URL` | ❌ | `https://api.openai.com/v1` | Base URL for the API endpoint. Override to use Azure OpenAI, Ollama, or other compatible providers. |

### Using an alternative OpenAI-compatible provider

Set `OPENAI_BASE_URL` to point at any OpenAI-compatible endpoint, for example:

```bash
export OPENAI_BASE_URL="https://my-azure-instance.openai.azure.com/openai/deployments/my-deployment"
export OPENAI_MODEL="gpt-4o"
```

---

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

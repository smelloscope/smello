# AI Agent Skills

Smello ships with two [Agent Skills](https://agentskills.io) that work with Claude Code, Cursor, GitHub Copilot, and [20+ other AI coding tools](https://skills.sh/).

## Install

Install both skills at once:

```bash
npx skills add smelloscope/smello
```

Or install them individually:

```bash
npx skills add smelloscope/smello --skill smello-setup
npx skills add smelloscope/smello --skill smello-debugger
```

Skills are placed in your project's `.claude/skills/` directory (or equivalent for other agents) and are available immediately.

## Available skills

### `/smello-setup` — Project integration

Explores your codebase and proposes a plan to integrate Smello. The skill:

1. Detects your package manager (pip, uv, poetry, pipenv)
2. Finds HTTP, gRPC, and logging library usage (`requests`, `httpx`, `aiohttp`, `grpc`, `botocore`, Google Cloud libraries, `logging`)
3. Locates the application entrypoint (Django, Flask, FastAPI, CLI, etc.)
4. Checks for Docker Compose files
5. Presents a step-by-step integration plan (including log and exception capture options)

The skill does **not** make any changes — it only proposes. You approve each step before anything is modified.

**Usage** (in Claude Code or any compatible agent):

```
/smello-setup
```

### `/smello-debugger` — Event inspection

Helps you debug events captured by a running Smello instance — HTTP requests, Python log records, and unhandled exceptions. The skill queries the Smello API to:

- List recent events with filtering (event type, host, method, status code, full-text search)
- Fetch full event details (headers/bodies for HTTP, tracebacks/frames for exceptions, message/extra for logs)
- Identify failed API calls (4xx/5xx), unhandled exceptions, error-level logs, and slow requests
- Cross-reference captured events with your source code

This skill is also invoked automatically when you ask your AI agent about HTTP debugging, exception analysis, log inspection, or API troubleshooting.

**Usage:**

```
/smello-debugger
```

Or just ask naturally:

```
Why is my Stripe API call returning 401?
Show me the recent exceptions
What errors are in the logs?
What HTTP calls is my app making to OpenAI?
```

## How skills work

Skills follow the [Agent Skills](https://agentskills.io) open standard. They are Markdown files (`SKILL.md`) that give your AI agent specialized knowledge and workflows. Unlike plugins or extensions, skills require no runtime dependencies — they are pure instructions.

After installing with `npx skills add`, the skill files are placed in your project's `.claude/skills/` directory (or equivalent for other agents). They are picked up automatically.

## Compatibility

Skills work with any AI coding tool that supports the Agent Skills standard:

- [Claude Code](https://claude.ai/code)
- [Cursor](https://cursor.com)
- [GitHub Copilot](https://github.com/features/copilot)
- [Cline](https://github.com/cline/cline)
- And [many more](https://skills.sh/)

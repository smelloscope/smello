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
npx skills add smelloscope/smello --skill smello
```

The command places skills in your project's `.claude/skills/` directory (or equivalent for other agents). They're available immediately.

## Available skills

### `/smello-setup`: Project integration

Explores your codebase and sets up `smello run` as part of your development workflow. The skill:

1. Detects your package manager (pip, uv, poetry, pipenv)
2. Finds HTTP, gRPC, and logging library usage (`requests`, `httpx`, `aiohttp`, `grpc`, `botocore`, Google Cloud libraries, `logging`)
3. Locates how you run your app (Django, Flask, FastAPI, CLI scripts, etc.)
4. Checks for Docker Compose files and run scripts
5. Proposes wiring `smello run` into your dev commands, adding FastAPI/Django middleware if applicable, and enabling log capture

The skill does **not** make any changes: it only proposes. You approve each step before anything is modified.

**Usage** (in Claude Code or any compatible agent):

```
/smello-setup
```

### `/smello`: Debug with captured events

Helps you debug issues using events captured by a running Smello instance. The skill queries the Smello API to:

- List recent events with filtering (event type, host, method, status code, full-text search)
- Fetch full event details (headers/bodies for HTTP, tracebacks/frames for exceptions, message/extra for logs)
- Diagnose failures: API errors (4xx/5xx), unhandled exceptions, error-level log patterns, slow requests
- Cross-reference captured events with your source code to pinpoint root causes

This skill is also invoked automatically when you ask your AI agent about debugging: whether it's an API error, a crash, a log message, or unexpected behavior.

**Usage:**

```
/smello
```

Or just ask naturally:

```
Why is my Stripe API call returning 401?
Show me the recent exceptions
What errors are in the logs?
What HTTP calls is my app making to OpenAI?
```

## How skills work

Skills follow the [Agent Skills](https://agentskills.io) open standard. They are Markdown files (`SKILL.md`) that give your AI agent specialized knowledge and workflows. Unlike plugins or extensions, skills require no runtime dependencies: they are pure instructions.

After installing with `npx skills add`, the skill files are placed in your project's `.claude/skills/` directory (or equivalent for other agents). Your AI agent loads them automatically.

## Compatibility

Skills work with any AI coding tool that supports the Agent Skills standard:

- [Claude Code](https://claude.ai/code)
- [Cursor](https://cursor.com)
- [GitHub Copilot](https://github.com/features/copilot)
- [Cline](https://github.com/cline/cline)
- And [many more](https://skills.sh/)

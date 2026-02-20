# AI Agent Skills

Smello ships with two [Agent Skills](https://agentskills.io) that work with Claude Code, Cursor, GitHub Copilot, and [20+ other AI coding tools](https://skills.sh/).

## Install

Install both skills at once:

```bash
npx skills add smelloscope/smello
```

Or install them individually:

```bash
npx skills add smelloscope/smello --skill setup-smello
npx skills add smelloscope/smello --skill http-debugger
```

Skills are placed in your project's `.claude/skills/` directory (or equivalent for other agents) and are available immediately.

## Available skills

### `/setup-smello` — Project integration

Explores your codebase and proposes a plan to integrate Smello. The skill:

1. Detects your package manager (pip, uv, poetry, pipenv)
2. Finds HTTP and gRPC library usage (`requests`, `httpx`, `grpc`, Google Cloud libraries)
3. Locates the application entrypoint (Django, Flask, FastAPI, CLI, etc.)
4. Checks for Docker Compose files
5. Presents a step-by-step integration plan

The skill does **not** make any changes — it only proposes. You approve each step before anything is modified.

**Usage** (in Claude Code or any compatible agent):

```
/setup-smello
```

### `/http-debugger` — Traffic inspection

Helps you debug traffic captured by a running Smello instance (HTTP and gRPC). The skill queries the Smello API to:

- List recent requests with filtering (host, method, status code, URL search)
- Fetch full request/response details (headers, bodies, timing)
- Identify failed API calls (4xx/5xx), slow requests, and malformed payloads
- Cross-reference captured traffic with your source code

This skill is also invoked automatically when you ask your AI agent about HTTP debugging, API troubleshooting, or inspecting captured traffic.

**Usage:**

```
/http-debugger
```

Or just ask naturally:

```
Why is my Stripe API call returning 401?
Show me the recent failed requests
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

# pinboard-mcp

AI-powered Pinboard.in tooling — tag monitoring, MCP server integration, and tag management via Claude.

Built and maintained by [jonesybot1984](https://github.com/jonesybot1984) for [@darrellodonnell](https://github.com/darrellodonnell).

---

## What This Is

A set of tools for connecting [Pinboard.in](https://pinboard.in) with Claude and other AI assistants:

1. **Tag Watcher** — detects new tags in a private Pinboard account since the last known baseline, and reports them automatically
2. **MCP Server** *(planned)* — exposes Pinboard bookmark and tag operations as MCP tools for use with Claude Desktop or Claude Code

---

## Status

Early planning / build phase. See [PLAN.md](./PLAN.md) for full details.

---

## Prior Art

| Repo | What it does |
|------|-------------|
| [rossshannon/pinboard-bookmarks-mcp-server](https://github.com/rossshannon/pinboard-bookmarks-mcp-server) | Read-only MCP: search, list, tags |
| [vicgarcia/pinboard-mcp](https://github.com/vicgarcia/pinboard-mcp) | Docker MCP: read + write bookmarks, tag management |
| [kevinmcmahon/smartpin](https://github.com/kevinmcmahon/smartpin) | AI-powered bookmark adding (auto-tag via Claude/GPT) |

None of these detect new tags against a stored baseline. That's the gap this project fills.

---

## Setup

*Coming soon — see PLAN.md for the build roadmap.*

Requirements:
- Python 3.10+
- Pinboard API token (`https://pinboard.in/settings/password`)
- Anthropic API key (optional, for tag consolidation features)

---

## License

MIT

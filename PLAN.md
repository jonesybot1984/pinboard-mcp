# Pinboard Tag Watcher — Build Plan

## Problem
Darrell has a large private Pinboard account with many tags. He wants to know when new tags appear — so he can review, consolidate, or act on them. Nothing off-the-shelf does this.

## Existing Art (Don't Rebuild)

| Repo | What it does | Gap |
|------|-------------|-----|
| [rossshannon/pinboard-bookmarks-mcp-server](https://github.com/rossshannon/pinboard-bookmarks-mcp-server) | Read-only MCP for Claude Desktop: search, list, tags | No baseline diff, no write |
| [vicgarcia/pinboard-mcp](https://github.com/vicgarcia/pinboard-mcp) | Docker MCP: read + write bookmarks, rename/list tags, suggest tags | No new-tag detection |
| [kevinmcmahon/smartpin](https://github.com/kevinmcmahon/smartpin) | AI-powered bookmark *adding* (auto-tag via Claude/GPT) | Wrong direction — adds, doesn't audit |

**Key insight:** The Pinboard API has `GET /tags/get` which returns all tags + counts. Everything we need is one API call away. The "new tag detection" layer just doesn't exist yet.

---

## What We're Building

### Option A — Standalone Script (simplest, fastest to ship)

A Python script that:
1. Calls Pinboard API for full tag list
2. Loads a local `tags_baseline.json` (last known state)
3. Diffs: finds net-new tags since last run
4. Reports them (stdout / Slack message)
5. Optionally updates the baseline

**File layout:**
```
projects/pinboard-tag-watcher/
  tag_watcher.py          # core logic
  tags_baseline.json      # snapshot of known tags (updated after each run)
  .env                    # PINBOARD_TOKEN=username:token
  requirements.txt        # requests, python-dotenv
  README.md
```

**Run modes:**
- `python tag_watcher.py --report` — show new tags since last baseline, don't update
- `python tag_watcher.py --update` — report + update baseline
- `python tag_watcher.py --full` — dump full tag list with counts

**Cron/heartbeat integration:**
- Jones runs this periodically (daily or on heartbeat)
- If new tags found → Slack DM to Darrell
- If nothing new → silent

---

### Option B — MCP Tool Extension (more powerful, for Claude Desktop)

Fork `rossshannon/pinboard-bookmarks-mcp-server` and add:

- `detectNewTags` — compares current tags against a stored baseline, returns diff
- `consolidateTags` — takes two tag names, renames one to the other via API
- `suggestTagMerges` — finds near-duplicate tags (e.g. `SSI` and `self-sovereign-identity`) and suggests consolidations using Claude

This turns Claude Desktop into a tag management console: "show me new tags" → "those two look like duplicates, merge them" → done.

---

### Option C — Both (recommended flow)

1. Build Option A first (30 min) — get the detection working, prove it out
2. Wire it into Jones heartbeat/cron — automatic monitoring starts
3. Build Option B on top when Darrell wants interactive tag management in Claude Desktop

---

## Pinboard API Details

```
Base: https://api.pinboard.in/v1/
Auth: HTTP Basic (username:password) or token param (?auth_token=user:TOKEN)
Rate: 3 seconds between calls (enforced)

Tags endpoint:
  GET /tags/get?format=json
  Returns: { "tag-name": "count", ... }

Token location: https://pinboard.in/settings/password
```

---

## Claude Integration Options

Once we have the tag list, Claude can:
- **Cluster** tags by theme (AI, SSI, Bitcoin, etc.)
- **Detect near-duplicates** (edit distance, semantic similarity)
- **Suggest a canonical taxonomy** from existing tags
- **Auto-rename** via the `tags/rename` API endpoint

This is where it gets genuinely useful — not just "new tag appeared" but "here are 8 tags that probably mean the same thing."

---

## Tailnet Deployment (Required)

The MCP server must be accessible across the full Tailscale network (`quagga-chicken.ts.net`), not just localhost. This means running as a **remote MCP server** over HTTPS — not the local stdio mode used by most example repos.

### Architecture

```
Any device on tailnet
  → https://jones.quagga-chicken.ts.net/pinboard-mcp
    → nginx (reverse proxy, SSL termination)
      → MCP server (Python, Streamable HTTP transport, localhost:PORT)
```

### What This Requires

- **HTTP transport** (not stdio) — use FastMCP 2.0's `StreamableHTTP` mode
- **systemd service** — runs persistently, restarts on failure, same pattern as mission-control
- **nginx proxy** — add `/pinboard-mcp` location block to existing nginx config on jones
- **Tailscale-only exposure** — bind to `jones.quagga-chicken.ts.net`, not public internet
- **Auth** — MCP clients connect with a shared secret or the Pinboard token serves as implicit auth

### MCP Client Config (for any device on tailnet)

```json
{
  "mcpServers": {
    "pinboard": {
      "type": "streamable",
      "url": "https://jones.quagga-chicken.ts.net/pinboard-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <shared-secret>"
      }
    }
  }
}
```

This config works in Claude Desktop, Claude Code, Cursor, or any MCP-compatible client connected to the tailnet.

### Deployment Script

Follow the same pattern as mission-control:
- `deploy.sh` — build + restart service in one step
- `systemd` unit file in repo
- nginx location block as a config snippet

---

## Build Order

- [ ] **Step 1:** Get Pinboard API token from Darrell, store in `.env`
- [ ] **Step 2:** Build `tag_watcher.py` — fetch tags, diff, report
- [ ] **Step 3:** Run first time to establish baseline (`tags_baseline.json`)
- [ ] **Step 4:** Wire into Jones heartbeat or cron — auto-notify on new tags
- [ ] **Step 5:** Build MCP server with HTTP transport (FastMCP 2.0, StreamableHTTP)
- [ ] **Step 6:** Deploy as systemd service on jones
- [ ] **Step 7:** Add nginx proxy block → expose on tailnet at `/pinboard-mcp`
- [ ] **Step 8:** Test from another tailnet device
- [ ] **Step 9:** (Optional) Claude tag consolidation analysis tools

---

## Notes / Decisions Pending

- Does Darrell want baseline auto-updated after each report, or manual control?
- Report threshold: report every new tag, or batch weekly?
- Tag consolidation: read-only suggestions, or actually rename via API?
- Auth for MCP endpoint: **Tailscale ACLs** (decided 2026-03-14) — no shared secret needed for now. Review if/when access needs finer control.
- Does Darrell want baseline auto-updated after each report, or manual control?
- Report threshold: report every new tag, or batch weekly?
- Tag consolidation: read-only suggestions, or actually rename via API?

---

## Mission Control Module (Planned)

A widget/page in MC (`/tools/pinboard` or similar) showing basic Pinboard status:

- Total bookmark count
- Total tag count
- New tags since last baseline (with counts)
- Last checked timestamp
- Link to full tag list

**Data source:** MC calls the tag_watcher logic (or reads `tags_baseline.json` + calls the API directly). Could be a simple read-only panel to start, with more interactivity (rename/merge tags) added later.

**Build approach:** Same Next.js pattern as other MC tools. API route hits the Pinboard API server-side, renders in a client component.

---

*Written: 2026-03-14. Updated: 2026-03-14 (tailnet deployment, auth decision, MC module added).*

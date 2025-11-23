# E2B + TweekIT + Groq – Hackathon Demo (Stage Deployment)

**Stage Demo UI:** https://stage-958133016924.us-west1.run.app  
**Stage MCP Endpoint:** https://tweekit-mcp-stage-958133016924.us-west1.run.app/mcp  
**Repository:** https://github.com/equilibrium-eq/tweekit-mcp-docker-groq-e2b

---

## 1. Architecture Overview

```
Browser (Cloud Run UI or localhost)
      ↓
FastAPI demo backend (demo/api.py)
      ↓
E2B Sandbox (creates session, runs MCP calls)
      ↓
TweekIT MCP (Cloud Run – streamable HTTP)
      ↓
Groq API (analysis, summaries)
```

Key characteristics:
- MCP handshake uses SSE + `initialize` + `notifications/initialized`.
- Text-first files fall back to local Markdown extraction to avoid upstream 500s.
- Unsupported conversions are logged to `demo/logs/unsupported_formats.log`.

---

## 2. Stage Environment (Current Status)

| Component | Cloud Run Service | Revision | Notes |
|-----------|------------------|----------|-------|
| Demo UI | `stage` | `stage-00002-qlr` | Shared styling with homepage and press release; progress rail shows Groq model. |
| TweekIT MCP | `tweekit-mcp-stage` | `tweekit-mcp-stage-00022-8kw` | Exposes 5 MCP tools (`convert`, `convert_url`, `doctype`, `fetch`, `search`). |
| Discord Webhook | n/a | disabled | Enable by setting `DISCORD_WEBHOOK_URL` and `ERROR_REPORTING_ENABLED=true` before redeploying. |

Prod deployment is pending credential confirmation.

---

## 3. Running Locally (Optional)

Stage is already live. Use these steps only if you need to iterate locally:

```bash
# 1. Load environment variables and virtualenv
direnv allow          # only required once
direnv exec . uv run python demo/api.py

# 2. Open browser
#    Local preview: http://localhost:8081
#    Stage:         https://stage-958133016924.us-west1.run.app
```

Local mode still calls the stage MCP endpoint by default (see `TUNNEL_URL` env var). Update `.envrc` if you want to point to a different MCP instance.

---

## 4. API Endpoints (FastAPI)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves the demo frontend. |
| GET | `/health` | Reports env-var readiness and MCP reachability. |
| POST | `/api/process` | Full pipeline: upload → E2B sandbox → TweekIT MCP → Groq. |

Example request:
```json
{
  "file_base64": "<base64_data>",
  "filename": "document.doc",
  "output_format": "pdf",
  "use_vision": false
}
```

---

## 5. MCP Usage (Stage Endpoint)

```python
from fastmcp import Client

async def convert_doc(blob_b64: str):
    async with Client("https://tweekit-mcp-stage-958133016924.us-west1.run.app/mcp") as client:
        return await client.call_tool("convert", {
            "apiKey": "<TWEEKIT_API_KEY>",
            "apiSecret": "<TWEEKIT_API_SECRET>",
            "inext": "doc",
            "outfmt": "pdf",
            "blob": blob_b64
        })
```

Tools available:
- `convert`, `convert_url`
- `doctype`
- `fetch`
- `search`

---

## 6. Deployment Commands

Deploy demo UI (stage):
```bash
direnv exec . bash demo/deploy.sh stage --version 1.6.01
```

Deploy MCP service (stage):
```bash
direnv exec . bash scripts/deploy_cloud_run.sh stage --version 1.6.01
```

Remember to set `DISCORD_WEBHOOK_URL` and `ERROR_REPORTING_ENABLED=true` in `.envrc` if you want Stage to push error notifications to Discord.

---

## 7. Logs & Monitoring

- Demo UI logs:
  ```bash
  gcloud run services logs tail stage --region us-west1
  ```
- MCP logs:
  ```bash
  gcloud run services logs tail tweekit-mcp-stage --region us-west1
  ```
- Unsupported format tracker: `demo/logs/unsupported_formats.log`

---

## 8. File Layout

```
demo/
├── api.py                # FastAPI backend (E2B + MCP orchestration)
├── static/
│   ├── index.html        # Demo UI
│   ├── app.js            # Frontend logic
│   └── styles            # Shared CSS (loaded from /static/styles/main.css)
└── README.md             # This document
```

---

## 9. Next Steps

1. Promote both services to production once secrets are signed off.  
2. Enable Discord webhook notifications.  
3. Continue expanding Markdown fallback coverage as new unsupported formats are logged.  
4. Finalize documentation bundle + letter to community (see project root).

Stage environment is fully operational; no tunnel or local Docker MCP is required.***

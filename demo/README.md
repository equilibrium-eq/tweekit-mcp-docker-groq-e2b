# E2B + TweekIT + Groq Hackathon Demo

**Universal AI File Ingestion Demo** showcasing E2B sandboxes, TweekIT MCP conversion, and Groq AI analysis in a single seamless workflow.

---

## Quick Start

### 1. Ensure tunnel and MCP server are running

```bash
# Check if they're running
ps aux | grep -E "server.py|cloudflared" | grep -v grep

# If not, start them (from project root)
python server.py --host 127.0.0.1 --port 8080 &
cloudflared tunnel --url http://localhost:8080 &
```

### 2. Set environment variables

```bash
# From project root
source .envrc
source .venv/bin/activate
```

### 3. Install demo dependencies

```bash
# Should already have these from pyproject.toml:
# - fastapi
# - uvicorn
# - e2b-code-interpreter
# - groq
```

### 4. Start the demo

```bash
cd demo
python api.py
```

### 5. Open in browser

```
http://localhost:8081
```

---

## Demo Workflow

1. **Upload File** → Click "Select File" or drag & drop
2. **Watch Progress** → See E2B sandbox → TweekIT conversion → Groq analysis
3. **View Results** → See conversion details + AI insights
4. **Process Another** → Repeat with different file types

---

## Architecture

```
Browser (localhost:8081)
    ↓
FastAPI Backend (demo/api.py)
    ↓
E2B Sandbox (remote)
    ↓
TweekIT MCP (via Cloudflared tunnel)
    ↓
Groq AI (analysis)
```

---

## Testing Different File Types

### Documents
- `test.doc` → PDF conversion
- `test.docx` → PDF conversion
- `test.txt` → PDF conversion

### Images
- `test.png` → PDF conversion
- `test.jpg` → PDF conversion
- `test.tiff` → PDF conversion

### Design Files (impressive!)
- `test.psd` → PNG conversion
- `test.ai` → PNG conversion

---

## API Endpoints

### GET `/`
Serves the demo frontend

### GET `/health`
Health check - shows API key status

### POST `/api/process`
Process a file through the full pipeline

**Request**:
```json
{
  "file_base64": "base64_encoded_file",
  "filename": "document.doc",
  "output_format": "pdf",
  "use_vision": false
}
```

**Response**:
```json
{
  "success": true,
  "conversion": {
    "input_format": "DOC",
    "output_format": "PDF",
    "size": "2.3 KB",
    "time": "1.8s"
  },
  "analysis": {
    "model": "llama-3.3-70b-versatile",
    "summary": "This DOC file typically contains...",
    "time": "0.9s"
  },
  "total_time": 2.7
}
```

---

## Troubleshooting

### API keys not found
```bash
# Make sure .envrc is loaded
source .envrc

# Check variables
echo $TWEEKIT_API_KEY
echo $E2B_API_KEY
echo $GROQ_API_KEY
```

### Tunnel not working
```bash
# Check if tunnel is running
ps aux | grep cloudflared

# If not, start it
cloudflared tunnel --url http://localhost:8080 &

# Get the new URL
grep "trycloudflare.com" /tmp/tunnel.log
```

### E2B timeout
- Default timeout is 60 seconds
- For large files, may need to increase
- Or use smaller test files

### Port 8081 already in use
```bash
# Kill process on port 8081
lsof -ti:8081 | xargs kill -9

# Or use a different port
python api.py  # (edit api.py to change port)
```

---

## Demo Tips

### For Video Recording
1. Use small test files (<1MB) for fast demos
2. Pre-load the page so it's ready
3. Show 2-3 different file types (DOC, PNG, PSD)
4. Emphasize the speed (2-3 seconds total)

### For Live Demo
1. Have test files ready in a folder
2. Test connection first with `/health` endpoint
3. Show different output formats
4. Mention enterprise on-prem option in footer

---

## Files

```
demo/
├── api.py              # FastAPI backend
├── static/
│   ├── index.html      # Demo UI
│   └── app.js          # Frontend logic
└── README.md           # This file
```

---

## Next Steps

1. **Test with real files** → Verify all file types work
2. **Record demo video** → Show the workflow in action
3. **Deploy publicly** → Use Railway/Fly.io for judges to test
4. **Add vision model demo** → Show image analysis (optional)

---

**Status**: ✅ Ready for testing and demo recording!

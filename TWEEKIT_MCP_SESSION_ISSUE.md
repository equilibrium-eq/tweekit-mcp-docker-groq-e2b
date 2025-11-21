# TweekIT MCP Session Handshake Issue - Root Cause Analysis

**Date**: November 21, 2025
**Status**: ✅ **DIAGNOSED** - Solution Identified
**Priority**: HIGH (Blocking E2B hackathon demo)

---

## Executive Summary

The TweekIT MCP server integration works perfectly when hosted locally, but fails when accessed via the Cloud Run deployment at `https://mcp.tweekit.io/mcp/` due to an **HTTPS redirect loop**.

**Key Finding**: This is a deployment configuration issue, NOT a problem with:
- E2B integration code ✅
- FastMCP Client session handshake ✅
- TweekIT MCP server implementation ✅

---

## Root Cause

### The Redirect Loop

```
https://mcp.tweekit.io/mcp/
  ↓ (307 Temporary Redirect)
http://mcp.tweekit.io/mcp
  ↓ (302 Found)
https://mcp.tweekit.io/mcp
  ↓ (LOOP)
```

### Impact

1. **Session Establishment Fails**: FastMCP Client cannot establish an MCP session because it gets caught in the redirect loop
2. **All Requests Return 400**: Server responds with `"Bad Request: Missing session ID"` because no session was ever established
3. **Both E2B and Direct Calls Fail**: Any client attempting to connect encounters the same issue

---

## Proof of Concept

### ✅ Local Server Works Perfectly

```bash
# Start local server
python server.py --transport streamable-http --host 127.0.0.1 --port 8080

# Test with FastMCP Client
async with Client('http://127.0.0.1:8080/mcp') as client:
    tools = await client.list_tools()  # ✓ Works!
    result = await client.call_tool('convert', {...})  # ✓ Works!
```

**Result**: ✅ **PASSED** - 5 tools discovered, conversion successful

### ❌ Cloud Run Deployment Fails

```bash
# Test cloud endpoint
async with Client('https://mcp.tweekit.io/mcp/') as client:
    # Error: 400 Bad Request - Missing session ID
```

**Result**: ❌ **FAILED** - Cannot establish session due to redirect loop

---

## Technical Details

### What FastMCP Client Does (Correct Behavior)

1. **Initial Connection**: Sends GET to `/mcp` with `Accept: text/event-stream`
2. **Server Response**: Returns session ID in SSE stream or header `mcp-session-id`
3. **Subsequent Requests**: Includes session ID in `mcp-session-id` header
4. **Tool Calls**: POST with both `Accept: text/event-stream` and session header

### What Cloud Run Does (Broken)

1. **Client**: GET https://mcp.tweekit.io/mcp/ with `Accept: text/event-stream`
2. **Server**: 307 → http://mcp.tweekit.io/mcp (downgrades to HTTP)
3. **Client**: GET http://mcp.tweekit.io/mcp (follows redirect)
4. **Server**: 302 → https://mcp.tweekit.io/mcp (upgrades back to HTTPS)
5. **Client**: 💥 **Redirect loop detected or timeout**

---

## Solutions

### Option 1: Fix Cloud Run HTTPS Handling ⭐ RECOMMENDED

**Problem**: Cloud Run is misconfigured for HTTPS/HTTP handling

**Solution**: Update Cloud Run configuration to handle HTTPS properly:

```yaml
# Cloud Run service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
spec:
  template:
    metadata:
      annotations:
        # Force HTTPS, don't redirect to HTTP
        run.googleapis.com/ingress: "all"
    spec:
      containers:
        - name: mcp-server
          env:
            # FastMCP should trust X-Forwarded-Proto header
            - name: FORWARDED_ALLOW_IPS
              value: "*"
```

**Steps**:
1. Check Cloud Run service configuration
2. Ensure `X-Forwarded-Proto` header is being respected
3. Remove any manual HTTPS → HTTP redirects
4. Test with `curl -L -v https://mcp.tweekit.io/mcp/`

**Timeline**: 30-60 minutes

---

### Option 2: Deploy to Alternative Platform

**Platforms without HTTPS issues**:

- **Railway.app** ⚡ (Easiest, auto-HTTPS)
- **Fly.io** (Good for global deployment)
- **Render.com** (Free tier available)
- **Heroku** (Classic option)

**Steps**:
1. Choose platform
2. Deploy MCP server
3. Update E2B code with new endpoint
4. Test integration

**Timeline**: 1-2 hours

---

### Option 3: Expose Local Server for Demo 🚀 FASTEST

Use tunneling service to expose local server:

**Using Cloudflare Tunnel (cloudflared)**:
```bash
# Install cloudflared
brew install cloudflared

# Start local MCP server
python server.py --transport streamable-http --host 127.0.0.1 --port 8080

# Create tunnel
cloudflared tunnel --url http://localhost:8080
# Returns: https://random-name.trycloudflare.com
```

**Using ngrok**:
```bash
# Start local server
python server.py --host 127.0.0.1 --port 8080

# Create tunnel
ngrok http 8080
# Returns: https://xxxx.ngrok.io
```

**Update E2B code**:
```python
# Use tunnel URL
client = Client('https://random-name.trycloudflare.com/mcp')
```

**Timeline**: 10-15 minutes ⚡

---

### Option 4: Use HTTP-Only Endpoint (Not Recommended)

**Workaround**: Deploy an HTTP-only endpoint (no HTTPS redirect)

**Pros**: Would work immediately
**Cons**:
- Insecure (API keys transmitted in plain text)
- Not suitable for production
- Bad security practice for hackathon demo

**Status**: ❌ NOT RECOMMENDED

---

## Recommended Path Forward

### For Immediate Testing (Next 30 minutes)

✅ **Use Cloudflare Tunnel** (Option 3)
- Start local server
- Create cloudflared tunnel
- Update E2B demo code with tunnel URL
- Complete integration testing

### For Hackathon Demo (By Saturday)

✅ **Fix Cloud Run** (Option 1)
OR
✅ **Deploy to Railway** (Option 2)

Both provide production-ready HTTPS endpoints suitable for:
- Live demo
- Video recording
- Submission materials

---

## Files Updated

### Working Code (Local)
- ✅ `scripts/e2b_test_with_local_mcp.py` - Demonstrates working integration
- ✅ `scripts/tweekit_mcp_client.py` - Custom client (not needed with FastMCP)
- ✅ `server.py` - Works correctly when deployed properly

### Test Results
- ✅ Local MCP server: **WORKING**
- ✅ FastMCP Client: **WORKING**
- ✅ E2B Sandbox: **WORKING**
- ✅ Groq API: **WORKING**
- ❌ Cloud Run endpoint: **REDIRECT LOOP**

---

## Next Steps

1. **Immediate** (15 min):
   - [ ] Set up cloudflared tunnel
   - [ ] Update E2B demo with tunnel URL
   - [ ] Run full integration test
   - [ ] Verify all components working

2. **Short-term** (1-2 hours):
   - [ ] Fix Cloud Run HTTPS configuration, OR
   - [ ] Deploy to Railway/Fly.io
   - [ ] Update documentation with new endpoint

3. **Documentation**:
   - [ ] Add troubleshooting section to README
   - [ ] Document Cloud Run HTTPS configuration
   - [ ] Update E2B integration guide

---

## Test Commands

### Verify Local Server
```bash
python server.py --host 127.0.0.1 --port 8080
python scripts/e2b_test_with_local_mcp.py
```

### Test Cloud Run Diagnosis
```bash
curl -L -v https://mcp.tweekit.io/mcp/ 2>&1 | grep -E "(HTTP|Location)"
```

### Test with Tunnel
```bash
cloudflared tunnel --url http://localhost:8080
# Update script with tunnel URL
python scripts/e2b_demo_agent.py
```

---

## Summary

| Component | Status | Notes |
|-----------|--------|-------|
| TweekIT MCP Server | ✅ | Works perfectly locally |
| FastMCP Client | ✅ | Handles sessions correctly |
| E2B Sandbox | ✅ | Can make HTTP requests |
| Groq API | ✅ | Working |
| Cloud Run Deployment | ❌ | HTTPS redirect loop |

**Conclusion**: The integration code is correct. The deployment needs fixing. Use Option 3 (tunnel) for immediate testing, then fix Cloud Run (Option 1) or redeploy (Option 2) for production demo.

---

## Contact

**Issue Identified By**: E2B Hackathon Team
**Date Diagnosed**: November 21, 2025
**Estimated Fix Time**: 15 minutes (tunnel) to 2 hours (redeploy)

**Status**: Ready to proceed with hackathon demo once deployment is fixed.

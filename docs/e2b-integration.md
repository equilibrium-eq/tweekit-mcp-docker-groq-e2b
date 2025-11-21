# E2B Integration Guide

## Overview

This guide covers the integration of E2B (E2B Code Interpreter) with the TweekIT MCP Server for the E2B Hackathon. E2B provides secure, sandboxed cloud environments for executing code safely.

## What E2B Provides

- **Secure Sandboxes**: Isolated environments for untrusted code execution
- **Pre-configured Runtimes**: Python, Node.js, and more out-of-the-box
- **File System Access**: Upload/download files within sandbox
- **Automatic Cleanup**: Sandboxes destroyed after use
- **Timeout Controls**: Prevent runaway processes
- **Multi-language Support**: Python, JavaScript, Bash, etc.

## Architecture

```
User Request
    ↓
E2B Sandbox (safe execution environment)
    ↓
[Parallel MCP Calls]
    ├─→ TweekIT MCP (convert 400+ formats)
    └─→ Groq API (LLM analysis)
    ↓
Aggregated Results
```

## Prerequisites

1. **E2B Account**
   - Sign up at https://e2b.dev/dashboard
   - Create API key

2. **Groq Account**
   - Sign up at https://console.groq.com
   - Create API key

3. **TweekIT Credentials**
   - Sign up at https://www.tweekit.io
   - Get API key and secret from account dashboard

## Installation

### 1. Install E2B SDK

```bash
# Using uv (recommended for this project)
uv pip install e2b-code-interpreter

# Or using pip
pip install e2b-code-interpreter
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# TweekIT Credentials
TWEEKIT_API_KEY=your-tweekit-api-key
TWEEKIT_API_SECRET=your-tweekit-api-secret

# E2B Credentials
E2B_API_KEY=your-e2b-api-key

# Groq Credentials
GROQ_API_KEY=your-groq-api-key
```

### 3. Verify Installation

```bash
# Test basic E2B connection
python -c "from e2b_code_interpreter import Sandbox; print('E2B SDK installed successfully!')"
```

## Usage

### Basic E2B Sandbox

```python
from e2b_code_interpreter import Sandbox

# Create and use sandbox
with Sandbox(api_key="your-e2b-key") as sandbox:
    result = sandbox.run_code("print('Hello from E2B!')")
    print(result.logs.stdout)
```

### E2B + TweekIT Integration

```python
from e2b_integration import E2BSandboxManager

# Initialize manager
manager = E2BSandboxManager()

# Execute code in sandbox
code = """
import httpx
response = httpx.post(
    'https://mcp.tweekit.io/mcp/',
    json={'jsonrpc': '2.0', 'method': 'tools/list', 'id': 1}
)
print(response.json())
"""

result = manager.execute_code(code)
print(result['stdout'])
```

### E2B + TweekIT + Groq Full Stack

See `scripts/e2b_demo_agent.py` for complete integration example.

## Testing

### Run Full Integration Test

```bash
# Ensure .env is configured with all API keys
python scripts/e2b_demo_agent.py
```

This will test:
1. ✓ E2B sandbox creation
2. ✓ TweekIT MCP connection
3. ✓ TweekIT file conversion
4. ✓ Groq API analysis

### Run POC Examples

```bash
# Run basic POC examples
python e2b_integration.py
```

This demonstrates:
- Basic code execution in E2B
- Image processing with PIL
- Integration workflow concept

## API Reference

### E2BSandboxManager

Main class for managing E2B sandboxes.

#### `__init__(api_key: Optional[str] = None)`

Initialize sandbox manager.

- **api_key**: E2B API key (defaults to `E2B_API_KEY` env var)

#### `execute_code(code: str, timeout: int = 30) -> Dict[str, Any]`

Execute Python code in E2B sandbox.

**Parameters:**
- `code`: Python code string to execute
- `timeout`: Execution timeout in seconds (default: 30)

**Returns:**
```python
{
    "success": bool,      # Execution succeeded
    "stdout": str,        # Standard output
    "stderr": str,        # Standard error
    "error": str | None,  # Error message if failed
    "results": list       # Execution results
}
```

#### `execute_with_files(code: str, files: Dict[str, bytes], timeout: int = 60) -> Dict[str, Any]`

Execute code with uploaded files.

**Parameters:**
- `code`: Python code to execute
- `files`: Dict mapping filename → file content (bytes)
- `timeout`: Execution timeout in seconds (default: 60)

**Returns:** Same format as `execute_code()`

## Use Cases

### 1. Safe File Conversion

Convert untrusted user files in isolated sandbox:

```python
manager = E2BSandboxManager()

# Upload and convert file safely
files = {"input.doc": doc_file_bytes}

code = """
import httpx
import base64

with open('input.doc', 'rb') as f:
    blob = base64.b64encode(f.read()).decode()

# Call TweekIT to convert
response = httpx.post(
    'https://mcp.tweekit.io/mcp/',
    json={
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {
            'name': 'convert',
            'arguments': {
                'apiKey': 'xxx',
                'apiSecret': 'xxx',
                'inext': 'doc',
                'outfmt': 'pdf',
                'blob': blob
            }
        },
        'id': 1
    }
)
print(response.json())
"""

result = manager.execute_with_files(code, files)
```

### 2. Resume Screening Workflow

Process resume → convert → analyze:

```python
# 1. Convert DOC to PDF
# 2. Extract text with TweekIT
# 3. Analyze with Groq
# All in isolated E2B sandbox
```

### 3. Image Optimization Pipeline

Process images safely before serving:

```python
# 1. User uploads any format
# 2. E2B sandbox converts with TweekIT
# 3. Optimize for web (WebP, resize)
# 4. Return optimized asset
```

## Groq Analysis Helper

The helper module at `scripts/groq_integration.py` wraps the Groq chat
completions API with simple rate-limit handling and ready-to-use prompts
for hackathon demos. Install the SDK (`pip install groq`), export
`GROQ_API_KEY`, then run:

```bash
python scripts/groq_integration.py --prompt-key document_summary --content "Sample content to analyze"
```

You can pass longer content via STDIN and select from presets such as
`resume_analysis`, `data_insights`, `support_ticket_triage`, or
`compliance_review`. The module can also be imported directly:

```python
from scripts.groq_integration import analyze_with_groq, DEMO_PROMPTS

analysis = analyze_with_groq(
    content=converted_text,
    prompt=DEMO_PROMPTS["resume_analysis"],
)
print(analysis.content)
```

This keeps Groq usage consistent across sandbox scripts and the demo app.

## Security Considerations

### Sandbox Isolation

- E2B sandboxes are fully isolated
- No access to host system
- Automatic cleanup after execution
- Network access controlled

### API Key Security

- **Never commit** API keys to git
- Store in `.env` (gitignored)
- Use environment variables in production
- Rotate keys regularly

### Timeout Protection

- Always set reasonable timeouts
- Default: 30-60 seconds
- Prevents resource exhaustion
- Automatic termination

## Troubleshooting

### "E2B_API_KEY not found"

**Solution:** Set E2B_API_KEY in `.env` or export as environment variable:

```bash
export E2B_API_KEY="your-key-here"
```

### "Sandbox timeout exceeded"

**Solution:** Increase timeout parameter:

```python
result = manager.execute_code(code, timeout=120)  # 2 minutes
```

### "TweekIT MCP connection failed"

**Solution:** Verify TweekIT credentials and endpoint:

```bash
# Test MCP endpoint directly
curl -X POST https://mcp.tweekit.io/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### "Package import error in sandbox"

**Solution:** Install packages in sandbox before use:

```python
sandbox.run_code("!pip install httpx groq")
```

## Performance Tips

1. **Reuse Sandboxes** (within timeout limits)
   ```python
   with Sandbox() as sandbox:
       # Run multiple operations
       sandbox.run_code(code1)
       sandbox.run_code(code2)
   ```

2. **Parallel Execution** for independent tasks
   ```python
   # Use async/await or threading for parallel MCP calls
   ```

3. **Optimize Timeout** based on workload
   ```python
   # Short tasks: timeout=30
   # File processing: timeout=60
   # Heavy workloads: timeout=120
   ```

## Next Steps

1. **Run Tests**: `python scripts/e2b_demo_agent.py`
2. **Build Demo App**: See `HACKATHON_PARALLEL_WORKSTREAMS.md` Workstream 4
3. **Deploy Frontend**: Streamlit app with E2B integration
4. **Record Video**: Demo for hackathon submission

## Resources

- **E2B Documentation**: https://e2b.dev/docs
- **E2B Dashboard**: https://e2b.dev/dashboard
- **TweekIT MCP Docs**: README.md
- **Groq API Docs**: https://console.groq.com/docs

## Support

- **E2B Issues**: https://github.com/e2b-dev/e2b/issues
- **TweekIT Support**: support@tweekit.io
- **Hackathon Questions**: See HACKATHON_PARALLEL_WORKSTREAMS.md

## License

This integration is part of the TweekIT MCP Server project. See LICENSE for details.

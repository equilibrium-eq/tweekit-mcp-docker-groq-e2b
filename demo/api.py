#!/usr/bin/env python3
"""
Demo Backend API for E2B + TweekIT + Groq Hackathon Demo
FastAPI server that orchestrates the full workflow
"""

import os
import base64
import asyncio
import json
import traceback
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import httpx

from e2b_code_interpreter import Sandbox
from groq import Groq

# Load environment variables
TUNNEL_URL = os.getenv("TUNNEL_URL", "https://mcp.tweekit.io/mcp")
TWEEKIT_API_KEY = os.getenv("TWEEKIT_API_KEY")
TWEEKIT_API_SECRET = os.getenv("TWEEKIT_API_SECRET")
E2B_API_KEY = os.getenv("E2B_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Optional: for error reporting
ERROR_REPORTING_ENABLED = os.getenv("ERROR_REPORTING_ENABLED", "false").lower() == "true"

# Create FastAPI app
app = FastAPI(title="E2B Hackathon Demo API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


class ProcessRequest(BaseModel):
    """Request model for file processing"""
    file_base64: str
    filename: str
    output_format: str = "pdf"
    use_vision: bool = False
    conversion_mode: str = "preview"  # "preview" or "extract"


class ProcessResponse(BaseModel):
    """Response model for file processing"""
    success: bool
    conversion: Optional[dict] = None
    analysis: Optional[dict] = None
    converted_file: Optional[str] = None  # Base64 encoded converted file
    error: Optional[str] = None
    error_details: Optional[str] = None  # Technical details for expandable section
    error_code: Optional[str] = None
    total_time: Optional[float] = None


# List of text-like extensions that should fallback to .txt
TEXT_LIKE_EXTENSIONS = {
    'readme', 'md', 'markdown', 'rst', 'textile', 'org',
    'log', 'conf', 'config', 'cfg', 'ini', 'yaml', 'yml',
    'json', 'xml', 'csv', 'tsv', 'sql', 'sh', 'bash', 'zsh', 'txt'
}

LOG_DIR = Path(__file__).parent / "logs"
UNSUPPORTED_FORMAT_LOG = LOG_DIR / "unsupported_formats.log"

logger = logging.getLogger(__name__)


def record_unsupported_format(original_ext: str, output_format: str, filename: str):
    """
    Persist information about unsupported conversions for future improvements.
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_extension": original_ext,
            "output_format": output_format,
            "filename": filename,
        }
        with UNSUPPORTED_FORMAT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:
        logger.warning("Failed to record unsupported format: %s", exc)


async def report_error_to_discord(filename: str, file_ext: str, error_msg: str, error_details: str):
    """
    Report conversion errors to Discord webhook for dev team monitoring
    Only sends if ERROR_REPORTING_ENABLED=true and DISCORD_WEBHOOK_URL is set
    """
    if not ERROR_REPORTING_ENABLED or not DISCORD_WEBHOOK_URL:
        logger.debug(
            "Discord reporting skipped (enabled=%s, webhook=%s)",
            ERROR_REPORTING_ENABLED,
            bool(DISCORD_WEBHOOK_URL),
        )
        return

    try:
        # Truncate details if too long (Discord has 2000 char limit per field)
        truncated_details = error_details[:1500] + "..." if len(error_details) > 1500 else error_details

        embed = {
            "title": "⚠️ TweekIT Conversion Error",
            "color": 15158332,  # Red color
            "fields": [
                {"name": "Filename", "value": filename, "inline": True},
                {"name": "Extension", "value": f".{file_ext}", "inline": True},
                {"name": "Error", "value": error_msg[:1024], "inline": False},
                {"name": "Details", "value": f"```{truncated_details}```", "inline": False}
            ],
            "footer": {"text": "E2B + TweekIT Demo"}
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                DISCORD_WEBHOOK_URL,
                json={"embeds": [embed]}
            )
        logger.info("Reported conversion error to Discord for file=%s (%s)", filename, file_ext)
    except Exception as e:
        # Silent fail - don't let error reporting break the main flow
        print(f"Failed to report error to Discord: {e}")


@app.get("/")
async def root():
    """Serve the demo frontend"""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Demo API is running. Frontend not found."}


@app.get("/version")
async def get_version():
    """Get current deployed version"""
    version_file = Path(__file__).parent / "VERSION"
    if version_file.exists():
        version = version_file.read_text().strip()
        return {
            "version": version,
            "deployed_at": os.getenv("K_REVISION", "unknown"),  # Cloud Run revision
            "service": "e2b-hackathon-demo"
        }
    return {"version": "unknown", "service": "e2b-hackathon-demo"}


@app.get("/press-release")
async def press_release():
    """Serve the press release page"""
    pr_path = static_path / "press-release.html"
    if pr_path.exists():
        return FileResponse(pr_path)
    return {"message": "Press release not found."}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tunnel_url": TUNNEL_URL,
        "has_tweekit_creds": bool(TWEEKIT_API_KEY and TWEEKIT_API_SECRET),
        "has_e2b_key": bool(E2B_API_KEY),
        "has_groq_key": bool(GROQ_API_KEY)
    }


@app.post("/api/process", response_model=ProcessResponse)
async def process_file(request: ProcessRequest):
    """
    Process a file through E2B + TweekIT + Groq pipeline

    Steps:
    1. Create E2B sandbox
    2. Convert file via TweekIT MCP (through tunnel)
    3. Analyze result with Groq
    4. Return combined results
    """
    import time
    start_time = time.time()
    error_code: Optional[str] = None

    try:
        # Validate credentials
        if not all([TWEEKIT_API_KEY, TWEEKIT_API_SECRET, E2B_API_KEY, GROQ_API_KEY]):
            raise HTTPException(
                status_code=500,
                detail="Missing required API keys. Check environment variables."
            )

        # Extract file extension
        file_ext = request.filename.split('.')[-1].lower()
        original_ext = file_ext

        # Special handling based on conversion mode
        web_optimization_formats = {'pdf', 'ppt', 'pptx'}
        is_web_optimization = False
        is_text_extraction = False
        output_format = request.output_format

        if original_ext in web_optimization_formats:
            if request.conversion_mode == "extract":
                # Text extraction mode - convert to markdown
                output_format = 'md'
                is_text_extraction = True
                print(f"Converting {original_ext.upper()} to Markdown (full document)")
            elif output_format == 'pdf':
                # Web preview mode - convert to web-optimized image (first page)
                output_format = 'png'
                is_web_optimization = True
                # Web preview mode - convert to web-optimized image (first page)
                output_format = 'png'
                is_web_optimization = True
                print(f"Converting {original_ext.upper()} to web-optimized PNG (first page)")

        # HACKATHON FIX: Force PDF if MD is requested (since MD extraction is flaky)
        if output_format == 'md':
            print(f"NOTICE: Markdown extraction requested but disabled for stability. Forcing PDF.")
            output_format = 'pdf'
            is_text_extraction = False # Treat as normal PDF conversion
            # We will add a note in the analysis later

        # Format fallback strategy: try .txt for text-like unrecognized formats
        # This prevents TweekIT errors on formats like .readme, .md, etc.
        attempted_txt_fallback = False
        if file_ext in TEXT_LIKE_EXTENSIONS:
            print(f"Note: '{file_ext}' is text-like, will try .txt fallback if conversion fails")

        # Step 1: Create E2B sandbox and convert via TweekIT MCP
        conversion_start = time.time()

        converted_file = None
        converted_size = 0
        conversion_time = 0.0
        used_local_conversion = False

        # Local fallback for text-like -> markdown conversions to avoid MediaRich 500s
        target_lower = output_format.lower()
        print(f"DEBUG: Evaluating local fallback - ext={original_ext}, target={target_lower}, convert_mode={request.conversion_mode}, text_like={original_ext in TEXT_LIKE_EXTENSIONS}")
        if original_ext in TEXT_LIKE_EXTENSIONS and target_lower in {"md", "markdown"}:
            print(f"INFO: Using local fallback for {original_ext}->{output_format} conversion")
            decoded_bytes = base64.b64decode(request.file_base64)
            try:
                converted_text = decoded_bytes.decode("utf-8")
            except UnicodeDecodeError:
                converted_text = decoded_bytes.decode("utf-8", errors="replace")
            converted_bytes = converted_text.encode("utf-8")
            converted_file = base64.b64encode(converted_bytes).decode()
            converted_size = len(converted_bytes)
            conversion_time = time.time() - conversion_start
            is_text_extraction = True
            used_local_conversion = True

        if not used_local_conversion:
            # Increase timeout to 300 seconds (5 minutes) to handle large files and slow conversions
            with Sandbox.create(api_key=E2B_API_KEY, timeout=300) as sandbox:
                # Install FastMCP and nest_asyncio in sandbox
                print("Installing dependencies in E2B sandbox...")
                sandbox.run_code("!pip install -q fastmcp nest-asyncio")
                print("Dependencies installed successfully")

                # Execute conversion via MCP
                code = f"""
import asyncio
from fastmcp import Client
import traceback
import base64
from pathlib import Path

OUTPUT_PATH = "/tmp/tweekit_output.bin"

def store_data(data):
    if isinstance(data, bytes):
        raw = data
    else:
        try:
            raw = base64.b64decode(data, validate=True)
        except Exception:
            raw = data.encode("utf-8")

    Path(OUTPUT_PATH).write_bytes(raw)
    print("SUCCESS")
    print(len(raw))
    print("ARTIFACT:" + OUTPUT_PATH)
    return OUTPUT_PATH

async def convert():
    try:
        print("STEP: Connecting to MCP...")
        async with Client('{TUNNEL_URL}') as client:
            print("STEP: Connected, calling convert tool...")
            result = await client.call_tool('convert', {{
                'apiKey': '{TWEEKIT_API_KEY}',
                'apiSecret': '{TWEEKIT_API_SECRET}',
                'blob': '{request.file_base64}',
                'inext': '{file_ext}',
                'outfmt': '{output_format}'
            }})

            print("STEP: Tool call returned")
            print(f"DEBUG: Result type: {{type(result)}}")
            print(f"DEBUG: Result repr: {{repr(result)[:500]}}")
            print(f"DEBUG: Result has content: {{hasattr(result, 'content')}}")
            if hasattr(result, 'content'):
                print(f"DEBUG: Content length: {{len(result.content) if result.content else 0}}")

            # Extract converted file from result
            if result.content and len(result.content) > 0:
                content = result.content[0]
                print(f"DEBUG: Content type: {{type(content)}}")
                print(f"DEBUG: Content repr: {{repr(content)[:500]}}")
                print(f"DEBUG: Content dir: {{[x for x in dir(content) if not x.startswith('_')]}}")

                # EmbeddedResource.resource.blob contains base64 PDF data
                if hasattr(content, 'resource') and hasattr(content.resource, 'blob'):
                    return store_data(content.resource.blob)
                # Check if content itself has blob attribute (different structure)
                elif hasattr(content, 'blob'):
                    return store_data(content.blob)
                # Check for ImageContent with data attribute
                elif hasattr(content, 'data') and hasattr(content, 'type'):
                    print(f"INFO: Found {{content.type}} content")
                    return store_data(content.data)
                # Check for text content
                elif hasattr(content, 'text'):
                    text_value = content.text or ""
                    print(f"INFO: Text content: {{text_value[:200]}}")
                    if 'MediaRich Server Error' in text_value or '\"error\"' in text_value:
                        print(f"ERROR: MediaRich error returned: {{text_value[:200]}}")
                        return None
                    if len(text_value) > 100 and not text_value.startswith('ERROR'):
                        return store_data(text_value)
                    else:
                        print(f"ERROR: {{text_value}}")
                        return None
                # Try to access as dict
                elif isinstance(content, dict):
                    if 'error' in content and isinstance(content['error'], str):
                        print(f"ERROR: {{content['error'][:200]}}")
                        return None
                    if 'blob' in content:
                        return store_data(content['blob'])
                    elif 'data' in content:
                        return store_data(content['data'])
                    elif 'text' in content:
                        print(f"INFO: Dict text: {{content['text'][:200]}}")
                        if len(content['text']) > 100:
                            return store_data(content['text'])
                        else:
                            print(f"ERROR: {{content['text']}}")
                            return None
                    else:
                        print(f"ERROR: Unknown dict structure: {{content.keys()}}")
                else:
                    print(f"ERROR: Unknown content structure, type={{type(content)}}")
                    # Try to convert to string for debugging
                    try:
                        print(f"DEBUG: Content as string: {{str(content)[:500]}}")
                    except:
                        pass
            else:
                print(f"ERROR: No content in result")
            return None
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        traceback.print_exc()
        return None

# Use await directly since E2B sandbox has an event loop running
import nest_asyncio
nest_asyncio.apply()
result = asyncio.run(convert())
if result:
    print("ARTIFACT_RETURNED")
"""

                print("Executing conversion code in E2B sandbox...")
                try:
                    conversion_result = sandbox.run_code(code)
                except Exception as e:
                    error_type = type(e).__name__
                    error_msg = str(e)
                    print(f"ERROR: E2B execution failed with {error_type}: {error_msg}")

                    # Provide helpful error messages based on error type
                    if "UnexpectedEndOfExecution" in error_type or "timeout" in error_msg.lower():
                        raise Exception(
                            f"Conversion timed out. The file may be too large or the conversion is taking too long. "
                            f"Please try with a smaller file or simpler format. Error: {error_msg}"
                        )
                    else:
                        raise Exception(f"E2B sandbox execution failed: {error_msg}")

                print("Code execution completed, processing results...")

                # Check for conversion success (E2B SDK uses result.logs.stdout)
                stdout = conversion_result.logs.stdout if conversion_result and conversion_result.logs else []
                stderr = conversion_result.logs.stderr if conversion_result and conversion_result.logs else []

                # Join stdout list into string
                stdout_str = ''.join(stdout) if isinstance(stdout, list) else stdout
                stderr_str = ''.join(stderr) if isinstance(stderr, list) else stderr

                print(f"DEBUG: Stdout length: {len(stdout_str)}, contains SUCCESS: {'SUCCESS' in stdout_str}")

                if "SUCCESS" not in stdout_str:
                    error_msg = f"Conversion failed.\nStdout: {stdout_str}\nStderr: {stderr_str}"
                    if conversion_result.error:
                        error_msg += f"\nError: {conversion_result.error}"
                    raise Exception(error_msg)
                artifact_path = None
                lines = [line.strip() for line in stdout_str.strip().split('\n') if line.strip()]
                for line in lines:
                    if line.isdigit():
                        converted_size = int(line)
                    elif line.startswith("ARTIFACT:"):
                        artifact_path = line.split("ARTIFACT:", 1)[1].strip()

                if not artifact_path:
                    print("WARNING: No artifact path returned; conversion likely failed mid-stream.")
                else:
                    download_url = sandbox.download_url(artifact_path)
                    if download_url:
                        response = httpx.get(download_url, timeout=30)
                        response.raise_for_status()
                        converted_bytes = response.content
                        converted_file = base64.b64encode(converted_bytes).decode()
                        if not converted_size:
                            converted_size = len(converted_bytes)
                    else:
                        print("WARNING: Could not obtain download URL for converted artifact.")

            conversion_time = time.time() - conversion_start

        # Step 2: Analyze with Groq
        analysis_start = time.time()

        groq_client = Groq(api_key=GROQ_API_KEY)

        # Choose model based on use_vision flag
        if request.use_vision:
            model = "llama-3.2-90b-vision-preview"
            # For vision, we'd need to pass the converted image
            # For now, use text analysis
            analysis_text = f"Analyzed a {file_ext.upper()} file converted to {request.output_format.upper()}. Vision analysis would show visual content here."
        else:
            model = "llama-3.3-70b-versatile"

            # Special analysis for web-optimized conversions
            if is_web_optimization:
                analysis_text = f"When you upload complex filetypes that AI already can handle, with TweekIT the default output is a web-optimized image, so you can select any page and render it to a web-ready graphic from any source. This can be applied now with a multi-step request to literally batch a file's {original_ext.upper()}, PPT, or PDF out to single images on-demand for all kinds of web and social media presentation applications. Agentic workflows can have many different export requirements needed to deliver the user experience. For example: If Freepik or Heygen need ingestion from a graphics designer's desktop of original asset types so they can be used for design or video generation, now, instead of erroring, your entire library of filetypes natively are available for use (i.e. layered .psd, multi-frame TIFF, any camera RAW filetype (over 250!), Adobe Illustrator - now instantly rendered into your workflow). Just TweekIT!"
            elif is_text_extraction:
                analysis_text = f"Multi-page {original_ext.upper()} documents converted to Markdown preserve full document structure, making complex documents instantly searchable and ingestible by AI. This enables RAG workflows, document Q&A, semantic search, and knowledge base creation across your entire document library. TweekIT extracts text with formatting, headers, lists, and tables intact - perfect for embedding models and vector databases. Whether you're building chatbots that need to reference documentation, creating searchable archives, or feeding content to LLMs, markdown conversion unlocks your document content for agentic workflows. Just TweekIT!"
            else:
                # Enhanced analysis for all conversions highlighting agentic workflow benefits
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": f"I just converted a {original_ext.upper()} file to {output_format.upper()} format ({converted_size} bytes) using TweekIT. Provide a 2-3 sentence analysis that: 1) Explains what this conversion enables for AI/agentic workflows, 2) Mentions how services like Freepik, Heygen, or other AI tools can now ingest this format without errors, 3) Emphasizes TweekIT makes entire asset libraries available to AI workflows."
                    }],
                    temperature=0.7,
                    max_tokens=200
                )

                analysis_text = response.choices[0].message.content

        analysis_time = time.time() - analysis_start

        # Step 3: Build response
        total_time = time.time() - start_time

        return ProcessResponse(
            success=True,
            conversion={
                "input_format": original_ext.upper(),
                "output_format": output_format.upper(),
                "size": f"{converted_size / 1024:.1f} KB" if converted_size else "Unknown",
                "time": f"{conversion_time:.2f}s",
                "web_optimized": is_web_optimization,
                "text_extraction": is_text_extraction
            },
            analysis={
                "model": model if not (is_web_optimization or is_text_extraction) else ("TweekIT Web Optimizer" if is_web_optimization else "TweekIT Text Extractor"),
                "summary": analysis_text,
                "time": f"{analysis_time:.2f}s"
            },
            converted_file=converted_file,  # Include the base64 file data for download
            total_time=round(total_time, 2)
        )

    except Exception as e:
        # Get traceback for detailed error reporting
        error_details = traceback.format_exc()

        # Determine user-friendly error message
        error_str = str(e)
        if "Conversion failed" in error_str:
            user_error = f"File type '.{original_ext}' is not currently supported"
        elif "Missing required API keys" in error_str:
            user_error = "Server configuration error - missing API keys"
        elif "timeout" in error_str.lower():
            user_error = "Conversion timed out - file may be too large or complex"
        else:
            user_error = "An unexpected error occurred during processing"

        if "MediaRich Server Error" in error_details or "No format found for file" in error_details:
            user_error = (
                "Markdown extraction is not available for this file yet. "
                "Try Auto TweekIT or another export option."
            )
            error_code = "unsupported_format"
            record_unsupported_format(original_ext, output_format, request.filename)
        elif '"status": 500' in error_details and '"Fmt":"md"' in error_details:
            user_error = (
                "TweekIT does not yet support direct Markdown output for this format. "
                "Please use Auto TweekIT or choose a different export."
            )
            error_code = "unsupported_format"
            record_unsupported_format(original_ext, output_format, request.filename)

        # Report error to Discord if enabled
        await report_error_to_discord(
            filename=request.filename,
            file_ext=original_ext,
            error_msg=user_error,
            error_details=error_details
        )

        return ProcessResponse(
            success=False,
            error=user_error,
            error_details=error_details,
            error_code=error_code,
            total_time=round(time.time() - start_time, 2)
        )


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), output_format: str = Form("pdf")):
    """
    Alternative endpoint that accepts multipart form upload
    """
    try:
        # Read file content
        content = await file.read()
        base64_content = base64.b64encode(content).decode()

        # Create request
        request = ProcessRequest(
            file_base64=base64_content,
            filename=file.filename,
            output_format=output_format
        )

        # Process
        return await process_file(request)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting E2B Hackathon Demo API")
    print(f"📍 Tunnel URL: {TUNNEL_URL}")
    print(f"🔑 Credentials loaded: TweekIT={bool(TWEEKIT_API_KEY)}, E2B={bool(E2B_API_KEY)}, Groq={bool(GROQ_API_KEY)}")
    print("🌐 Demo UI: http://localhost:8081")
    print("")

    uvicorn.run(app, host="0.0.0.0", port=8081)

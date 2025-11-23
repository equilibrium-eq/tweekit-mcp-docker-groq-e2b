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
from typing import Optional
from pathlib import Path

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
    total_time: Optional[float] = None


# List of text-like extensions that should fallback to .txt
TEXT_LIKE_EXTENSIONS = {
    'readme', 'md', 'markdown', 'rst', 'textile', 'org',
    'log', 'conf', 'config', 'cfg', 'ini', 'yaml', 'yml',
    'json', 'xml', 'csv', 'tsv', 'sql', 'sh', 'bash', 'zsh'
}


async def report_error_to_discord(filename: str, file_ext: str, error_msg: str, error_details: str):
    """
    Report conversion errors to Discord webhook for dev team monitoring
    Only sends if ERROR_REPORTING_ENABLED=true and DISCORD_WEBHOOK_URL is set
    """
    if not ERROR_REPORTING_ENABLED or not DISCORD_WEBHOOK_URL:
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
                print(f"Converting {original_ext.upper()} to web-optimized PNG (first page)")

        # Format fallback strategy: try .txt for text-like unrecognized formats
        # This prevents TweekIT errors on formats like .readme, .md, etc.
        attempted_txt_fallback = False
        if file_ext in TEXT_LIKE_EXTENSIONS:
            print(f"Note: '{file_ext}' is text-like, will try .txt fallback if conversion fails")

        # Step 1: Create E2B sandbox and convert via TweekIT MCP
        conversion_start = time.time()

        with Sandbox.create(api_key=E2B_API_KEY, timeout=60) as sandbox:
            # Install FastMCP and nest_asyncio in sandbox
            sandbox.run_code("!pip install -q fastmcp nest-asyncio")

            # Execute conversion via MCP
            code = f"""
import asyncio
from fastmcp import Client
import traceback

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
                    print("SUCCESS")
                    print(len(content.resource.blob))
                    return content.resource.blob
                # Check if content itself has blob attribute (different structure)
                elif hasattr(content, 'blob'):
                    print("SUCCESS")
                    print(len(content.blob))
                    return content.blob
                # Check for ImageContent with data attribute
                elif hasattr(content, 'data') and hasattr(content, 'type'):
                    print(f"INFO: Found {{content.type}} content")
                    print("SUCCESS")
                    print(len(content.data))
                    return content.data
                # Check for text content
                elif hasattr(content, 'text'):
                    # Could be TextContent or an error message
                    print(f"INFO: Text content: {{content.text[:200]}}")
                    # If text looks like base64, try using it
                    if len(content.text) > 100 and not content.text.startswith('ERROR'):
                        print("SUCCESS")
                        print(len(content.text))
                        return content.text
                    else:
                        print(f"ERROR: {{content.text}}")
                        return None
                # Try to access as dict
                elif isinstance(content, dict):
                    if 'blob' in content:
                        print("SUCCESS")
                        print(len(content['blob']))
                        return content['blob']
                    elif 'data' in content:
                        print("SUCCESS")
                        print(len(content['data']))
                        return content['data']
                    elif 'text' in content:
                        print(f"INFO: Dict text: {{content['text'][:200]}}")
                        if len(content['text']) > 100:
                            print("SUCCESS")
                            print(len(content['text']))
                            return content['text']
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
"""

            conversion_result = sandbox.run_code(code)

            # Check for conversion success (E2B SDK uses result.logs.stdout)
            stdout = conversion_result.logs.stdout if conversion_result and conversion_result.logs else []
            stderr = conversion_result.logs.stderr if conversion_result and conversion_result.logs else []

            # Join stdout list into string
            stdout_str = ''.join(stdout) if isinstance(stdout, list) else stdout
            stderr_str = ''.join(stderr) if isinstance(stderr, list) else stderr

            if "SUCCESS" not in stdout_str:
                # If conversion failed and this is a text-like format, try .txt fallback
                if original_ext in TEXT_LIKE_EXTENSIONS and not attempted_txt_fallback:
                    print(f"Initial conversion of .{original_ext} failed, trying .txt fallback...")
                    attempted_txt_fallback = True
                    file_ext = 'txt'

                    # Retry conversion with .txt extension
                    code_retry = f"""
import asyncio
from fastmcp import Client
import traceback

async def convert():
    try:
        print("STEP: Retrying with .txt extension...")
        async with Client('{TUNNEL_URL}') as client:
            result = await client.call_tool('convert', {{
                'apiKey': '{TWEEKIT_API_KEY}',
                'apiSecret': '{TWEEKIT_API_SECRET}',
                'blob': '{request.file_base64}',
                'inext': 'txt',
                'outfmt': '{output_format}'
            }})

            print(f"DEBUG: Retry result type: {{type(result)}}")
            if result.content and len(result.content) > 0:
                content = result.content[0]
                print(f"DEBUG: Retry content type: {{type(content)}}")

                if hasattr(content, 'resource') and hasattr(content.resource, 'blob'):
                    print("SUCCESS")
                    print(len(content.resource.blob))
                    return content.resource.blob
                elif hasattr(content, 'blob'):
                    print("SUCCESS")
                    print(len(content.blob))
                    return content.blob
                elif hasattr(content, 'text'):
                    if len(content.text) > 100 and not content.text.startswith('ERROR'):
                        print("SUCCESS")
                        print(len(content.text))
                        return content.text
                    else:
                        print(f"ERROR: {{content.text}}")
                        return None
                elif isinstance(content, dict):
                    if 'blob' in content:
                        print("SUCCESS")
                        print(len(content['blob']))
                        return content['blob']
                    elif 'text' in content and len(content['text']) > 100:
                        print("SUCCESS")
                        print(len(content['text']))
                        return content['text']
                    else:
                        print(f"ERROR: Unknown dict structure: {{content.keys()}}")
                else:
                    print(f"ERROR: Unknown content structure, type={{type(content)}}")
            else:
                print(f"ERROR: No content in result")
            return None
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
        traceback.print_exc()
        return None

import nest_asyncio
nest_asyncio.apply()
result = asyncio.run(convert())
"""
                    conversion_result = sandbox.run_code(code_retry)
                    stdout = conversion_result.logs.stdout if conversion_result and conversion_result.logs else []
                    stderr = conversion_result.logs.stderr if conversion_result and conversion_result.logs else []
                    stdout_str = ''.join(stdout) if isinstance(stdout, list) else stdout
                    stderr_str = ''.join(stderr) if isinstance(stderr, list) else stderr

                    if "SUCCESS" not in stdout_str:
                        # .txt fallback also failed
                        error_msg = f"Conversion failed for .{original_ext} (tried .txt fallback).\nStdout: {stdout_str}\nStderr: {stderr_str}"
                        if conversion_result.error:
                            error_msg += f"\nError: {conversion_result.error}"
                        raise Exception(error_msg)
                    else:
                        print(f"✅ .txt fallback succeeded for .{original_ext}")
                else:
                    # Not a text-like format or already tried fallback
                    error_msg = f"Conversion failed.\nStdout: {stdout_str}\nStderr: {stderr_str}"
                    if conversion_result.error:
                        error_msg += f"\nError: {conversion_result.error}"
                    raise Exception(error_msg)


            # Extract size from output
            lines = stdout_str.strip().split('\n')
            converted_size = int(lines[-1]) if len(lines) > 1 else 0
            
            # Extract the converted file data from the sandbox result
            # The convert() function returns the base64 data, which E2B captures as the result value
            converted_file = None
            if hasattr(conversion_result, 'results') and conversion_result.results:
                # E2B stores function return values in results
                converted_file = conversion_result.results
            elif hasattr(conversion_result, 'result'):
                converted_file = conversion_result.result
            
            # If not found in results, the data might be in a different location
            # For now, set to None to prevent the NameError (download will be disabled)
            if not converted_file:
                print("WARNING: Converted file data not found in sandbox result. Download will be disabled.")
                converted_file = None

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

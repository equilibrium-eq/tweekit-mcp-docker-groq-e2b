#!/usr/bin/env python3
"""
E2B Demo Agent - Tests TweekIT and Groq MCP connections from E2B sandbox

This script creates an E2B sandbox and tests connectivity to:
1. TweekIT MCP Server (media conversion)
2. Groq API (LLM analysis)

Usage:
    python scripts/e2b_demo_agent.py

Environment Variables Required:
    E2B_API_KEY - E2B API key (from https://e2b.dev/dashboard)
    GROQ_API_KEY - Groq API key (from https://console.groq.com)
    TWEEKIT_API_KEY - TweekIT API key
    TWEEKIT_API_SECRET - TweekIT API secret
"""

import os
import sys
import json
import base64
from typing import Dict, Any
from e2b_code_interpreter import Sandbox


GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


class E2BDemoAgent:
    """E2B sandbox agent that orchestrates TweekIT and Groq"""

    def __init__(self):
        """Initialize E2B demo agent with API keys"""
        self.e2b_api_key = os.getenv("E2B_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.tweekit_api_key = os.getenv("TWEEKIT_API_KEY")
        self.tweekit_api_secret = os.getenv("TWEEKIT_API_SECRET")

        # Validate required keys
        self._validate_config()

    def _validate_config(self):
        """Validate all required API keys are present"""
        missing = []
        if not self.e2b_api_key:
            missing.append("E2B_API_KEY")
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        if not self.tweekit_api_key:
            missing.append("TWEEKIT_API_KEY")
        if not self.tweekit_api_secret:
            missing.append("TWEEKIT_API_SECRET")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Set them in .env file or export them before running."
            )

    def test_tweekit_connection(self) -> Dict[str, Any]:
        """
        Test TweekIT MCP server connection from E2B sandbox

        Returns:
            Dict with test results and connection status
        """
        print("\n=== Testing TweekIT MCP Connection ===")

        try:
            with Sandbox.create(api_key=self.e2b_api_key, timeout=60) as sandbox:
                print("Installing dependencies in E2B sandbox...")
                sandbox.run_code("!pip install -q httpx nest_asyncio")

                print("Testing TweekIT MCP server connectivity...")
                code = """
import asyncio
import json
import httpx
import nest_asyncio

BASE_URL = "https://mcp.tweekit.io/mcp"
PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {"name": "e2b-demo-agent", "version": "0.1.0"}

async def handshake(client: httpx.AsyncClient) -> str:
    response = await client.get(
        BASE_URL,
        headers={"Accept": "text/event-stream"}
    )
    session_id = response.headers.get("mcp-session-id")
    if not session_id:
        for line in response.text.splitlines():
            if line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    session_id = data.get("sessionId")
                    if session_id:
                        break
                except json.JSONDecodeError:
                    continue
    if not session_id:
        if response.status_code not in (200, 400):
            response.raise_for_status()
        raise RuntimeError("Handshake succeeded but no mcp-session-id header was returned")
    return session_id

def parse_sse(text: str):
    payload = {}
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                payload = json.loads(line[5:].strip())
                break
            except json.JSONDecodeError:
                continue
    return payload or {"raw": text}

def build_headers(session_id: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": session_id,
    }

async def send_request(client: httpx.AsyncClient, session_id: str, payload: dict) -> dict | None:
    response = await client.post(
        BASE_URL,
        headers=build_headers(session_id),
        json=payload
    )
    if response.status_code == 202:
        return None
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    if "text/event-stream" in content_type:
        return parse_sse(response.text)
    try:
        return response.json()
    except json.JSONDecodeError:
        return {"raw": response.text}

async def initialize_session(client: httpx.AsyncClient, session_id: str):
    init_payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        },
    }
    init_response = await send_request(client, session_id, init_payload)
    if isinstance(init_response, dict) and init_response.get("error"):
        raise RuntimeError(f"Initialize failed: {init_response['error']}")

    # Send initialized notification (fire-and-forget)
    await send_request(
        client,
        session_id,
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": None,
        },
    )

async def main():
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        session_id = await handshake(client)
        await initialize_session(client, session_id)

        payload = await send_request(
            client,
            session_id,
            {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
        ) or {}

        if isinstance(payload, dict) and payload.get("error"):
            raise RuntimeError(f"tools/list failed: {payload['error']}")

        tools_block = payload.get("result") if isinstance(payload, dict) else None
        if isinstance(tools_block, dict) and "tools" not in tools_block:
            tools_block = tools_block.get("data", tools_block)

        tools = tools_block.get("tools") if isinstance(tools_block, dict) else None
        if isinstance(tools, list):
            names = [tool.get("name") for tool in tools]
            print("✓ TweekIT MCP Connected!")
            print(f"✓ Found {len(names)} tools: {names}")
        else:
            raise RuntimeError(f"Unexpected tools/list response: {payload}")

nest_asyncio.apply()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
"""
                result = sandbox.run_code(code)
                return self._format_result(result)

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(e)
            }

    def test_tweekit_conversion(self, test_image_path: str = None) -> Dict[str, Any]:
        """
        Test actual TweekIT conversion from E2B sandbox

        Args:
            test_image_path: Path to test image file (uses built-in test if None)

        Returns:
            Dict with conversion results
        """
        print("\n=== Testing TweekIT Conversion ===")

        # Use test.png from repo if no path provided
        if test_image_path and os.path.exists(test_image_path):
            with open(test_image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
        else:
            # Small test PNG (1x1 red pixel)
            image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

        try:
            with Sandbox.create(api_key=self.e2b_api_key, timeout=120) as sandbox:
                print("Installing dependencies...")
                sandbox.run_code("!pip install -q httpx nest_asyncio")

                print("Converting image via TweekIT MCP...")
                code = f"""
import asyncio
import json
import httpx
import nest_asyncio

BASE_URL = "https://mcp.tweekit.io/mcp"
PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {{"name": "e2b-demo-agent", "version": "0.1.0"}}

async def handshake(client: httpx.AsyncClient) -> str:
    response = await client.get(
        BASE_URL,
        headers={{"Accept": "text/event-stream"}}
    )
    session_id = response.headers.get("mcp-session-id")
    if not session_id:
        for line in response.text.splitlines():
            if line.startswith("data:"):
                try:
                    data = json.loads(line[5:].strip())
                    session_id = data.get("sessionId")
                    if session_id:
                        break
                except json.JSONDecodeError:
                    continue
    if not session_id:
        if response.status_code not in (200, 400):
            response.raise_for_status()
        raise RuntimeError("Handshake succeeded but no mcp-session-id header was returned")
    return session_id

def parse_sse(text: str):
    payload = {{}}
    for line in text.splitlines():
        if line.startswith("data:"):
            try:
                payload = json.loads(line[5:].strip())
                break
            except json.JSONDecodeError:
                continue
    return payload or {{"raw": text}}

def build_headers(session_id: str) -> dict[str, str]:
    return {{
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "mcp-session-id": session_id,
    }}

async def send_request(client: httpx.AsyncClient, session_id: str, payload: dict) -> dict | None:
    response = await client.post(
        BASE_URL,
        headers=build_headers(session_id),
        json=payload
    )
    if response.status_code == 202:
        return None
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    if "text/event-stream" in content_type:
        return parse_sse(response.text)
    try:
        return response.json()
    except json.JSONDecodeError:
        return {{"raw": response.text}}

async def initialize_session(client: httpx.AsyncClient, session_id: str):
    init_payload = {{
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {{
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {{}},
            "clientInfo": CLIENT_INFO,
        }},
    }}
    init_response = await send_request(client, session_id, init_payload)
    if isinstance(init_response, dict) and init_response.get("error"):
        raise RuntimeError(f"Initialize failed: {{init_response['error']}}")

    await send_request(
        client,
        session_id,
        {{
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": None,
        }},
    )

def decode_length(payload):
    if isinstance(payload, dict):
        result_block = payload.get("result") or payload.get("data") or payload
        if isinstance(result_block, dict):
            content = result_block.get("content")
            if isinstance(content, list) and content:
                part = content[0]
                if isinstance(part, dict):
                    if "blob" in part:
                        return len(part["blob"])
                    if "data" in part:
                        return len(part["data"])
                    if "text" in part:
                        return len(part["text"])
            if "result" in result_block and isinstance(result_block["result"], dict):
                return decode_length(result_block["result"])
    return 0

async def main():
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        session_id = await handshake(client)
        await initialize_session(client, session_id)

        payload = {{
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {{
                "name": "convert",
                "arguments": {{
                    "apiKey": "{self.tweekit_api_key}",
                    "apiSecret": "{self.tweekit_api_secret}",
                    "blob": "{image_data}",
                    "inext": "png",
                    "outfmt": "png",
                    "width": 50,
                    "height": 50
                }}
            }}
        }}
        result_payload = await send_request(
            client,
            session_id,
            payload
        )
        if isinstance(result_payload, dict) and result_payload.get("error"):
            raise RuntimeError(f"convert failed: {{result_payload['error']}}")

        size = decode_length(result_payload)
        if size:
            print("✓ TweekIT Conversion Returned payload")
            print(f"✓ Payload size: {{size}} bytes")
        else:
            print("⚠️ Unable to determine payload size from response")
            print(result_payload)

nest_asyncio.apply()
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
"""
                result = sandbox.run_code(code)
                return self._format_result(result)

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(e)
            }

    def test_groq_connection(self) -> Dict[str, Any]:
        """
        Test Groq API connection from E2B sandbox

        Returns:
            Dict with test results
        """
        print("\n=== Testing Groq API Connection ===")

        try:
            with Sandbox.create(api_key=self.e2b_api_key, timeout=60) as sandbox:
                print("Installing Groq SDK in E2B sandbox...")
                sandbox.run_code("!pip install -q groq")

                print("Testing Groq API...")
                code = f"""
from groq import Groq

try:
    client = Groq(api_key='{self.groq_api_key}')

    response = client.chat.completions.create(
        model='{GROQ_MODEL}',
        messages=[
            {{'role': 'user', 'content': 'Say "E2B + Groq working!" in one sentence.'}}
        ],
        temperature=0.7,
        max_tokens=50
    )

    print("✓ Groq API Connected!")
    print(f"✓ Model: {{response.model}}")
    print(f"✓ Response: {{response.choices[0].message.content}}")

except Exception as e:
    print(f"✗ Groq connection failed: {{str(e)}}")
"""

                result = sandbox.run_code(code)
                return self._format_result(result)

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(e)
            }

    @staticmethod
    def _format_result(result: Any) -> Dict[str, Any]:
        """
        Normalize E2B sandbox execution results into a consistent dict.

        The E2B SDK wraps execution output inside `result.logs`. We treat any
        `✗` marker written by the sandbox code as a failure signal so the caller
        does not need to parse stdout manually.
        """
        stdout_raw = result.logs.stdout if result and result.logs else ""
        stderr_raw = result.logs.stderr if result and result.logs else ""

        if isinstance(stdout_raw, list):
            stdout = "".join(stdout_raw)
        else:
            stdout = stdout_raw or ""

        if isinstance(stderr_raw, list):
            stderr = "".join(stderr_raw)
        else:
            stderr = stderr_raw or ""

        stdout = str(stdout)
        stderr = str(stderr)
        has_error_marker = "✗" in stdout or "✗" in stderr
        return {
            "success": result.error is None and not has_error_marker,
            "stdout": stdout,
            "stderr": stderr,
            "error": str(result.error) if getattr(result, "error", None) else None
        }

    def run_full_demo(self):
        """
        Run complete demo: TweekIT connection, conversion, and Groq analysis
        """
        print("\n" + "="*60)
        print("E2B DEMO AGENT - FULL INTEGRATION TEST")
        print("="*60)

        results = {
            "tweekit_connection": None,
            "tweekit_conversion": None,
            "groq_connection": None
        }

        # Test 1: TweekIT MCP Connection
        try:
            results["tweekit_connection"] = self.test_tweekit_connection()
            if results["tweekit_connection"]["success"]:
                print("\n✓ TweekIT Connection: PASSED")
                print(results["tweekit_connection"]["stdout"])
            else:
                print("\n✗ TweekIT Connection: FAILED")
                print(
                    results["tweekit_connection"]["error"]
                    or results["tweekit_connection"]["stderr"]
                    or results["tweekit_connection"]["stdout"]
                )
        except Exception as e:
            print(f"\n✗ TweekIT Connection Test Error: {e}")

        # Test 2: TweekIT Conversion
        try:
            results["tweekit_conversion"] = self.test_tweekit_conversion()
            if results["tweekit_conversion"]["success"]:
                print("\n✓ TweekIT Conversion: PASSED")
                print(results["tweekit_conversion"]["stdout"])
            else:
                print("\n✗ TweekIT Conversion: FAILED")
                print(
                    results["tweekit_conversion"]["error"]
                    or results["tweekit_conversion"]["stderr"]
                    or results["tweekit_conversion"]["stdout"]
                )
        except Exception as e:
            print(f"\n✗ TweekIT Conversion Test Error: {e}")

        # Test 3: Groq Connection
        try:
            results["groq_connection"] = self.test_groq_connection()
            if results["groq_connection"]["success"]:
                print("\n✓ Groq Connection: PASSED")
                print(results["groq_connection"]["stdout"])
            else:
                print("\n✗ Groq Connection: FAILED")
                print(
                    results["groq_connection"]["error"]
                    or results["groq_connection"]["stderr"]
                    or results["groq_connection"]["stdout"]
                )
        except Exception as e:
            print(f"\n✗ Groq Connection Test Error: {e}")

        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)

        all_passed = all(
            r and r["success"]
            for r in results.values()
            if r is not None
        )

        for test_name, result in results.items():
            if result:
                status = "✓ PASSED" if result["success"] else "✗ FAILED"
                print(f"{test_name}: {status}")
            else:
                print(f"{test_name}: ✗ NOT RUN")

        if all_passed:
            print("\n🎉 ALL TESTS PASSED! E2B integration ready for hackathon demo.")
        else:
            print("\n⚠️  Some tests failed. Check errors above and verify API keys.")

        return results


def main():
    """Main entry point"""
    try:
        agent = E2BDemoAgent()
        results = agent.run_full_demo()

        # Exit with appropriate code
        all_passed = all(
            r and r["success"]
            for r in results.values()
            if r is not None
        )
        sys.exit(0 if all_passed else 1)

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nSetup instructions:")
        print("1. Copy .env.example to .env")
        print("2. Get E2B API key from https://e2b.dev/dashboard")
        print("3. Get Groq API key from https://console.groq.com")
        print("4. Get TweekIT credentials from https://www.tweekit.io")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

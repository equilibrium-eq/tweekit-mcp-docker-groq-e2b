#!/usr/bin/env python3
"""
TweekIT MCP Client with Streamable HTTP Session Handshake

Implements the proper handshake flow for TweekIT's streamable HTTP endpoint:
1. GET /mcp with Accept: text/event-stream → get mcp-session-id
2. POST with session ID + both content-type headers

This module can be used standalone or imported into E2B sandboxes.
"""

import httpx
import json
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class TweekITMCPClient:
    """
    Client for TweekIT MCP Server with proper streamable HTTP handshake
    """

    def __init__(
        self,
        base_url: str = "https://mcp.tweekit.io/mcp/",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize TweekIT MCP client

        Args:
            base_url: MCP server base URL
            api_key: TweekIT API key
            api_secret: TweekIT API secret
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/') + '/'
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def connect(self) -> str:
        """
        Establish MCP session with handshake

        Returns:
            Session ID string

        Raises:
            Exception if handshake fails
        """
        # Step 1: GET /mcp with text/event-stream to initiate session
        response = self.client.get(
            self.base_url,
            headers={
                'Accept': 'text/event-stream',
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"MCP handshake failed: {response.status_code} - {response.text}"
            )

        # Extract session ID from response headers
        self.session_id = response.headers.get('mcp-session-id')

        if not self.session_id:
            # Some implementations may send it in SSE data
            # Try to parse from event stream
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data:'):
                    try:
                        data = json.loads(line[5:].strip())
                        if 'sessionId' in data:
                            self.session_id = data['sessionId']
                            break
                    except json.JSONDecodeError:
                        continue

        if not self.session_id:
            raise Exception("Failed to obtain MCP session ID from handshake")

        return self.session_id

    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call an MCP tool

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            request_id: Optional request ID (auto-generated if None)

        Returns:
            Tool response as dict

        Raises:
            Exception if not connected or call fails
        """
        if not self.session_id:
            raise Exception("Not connected. Call connect() first.")

        if request_id is None:
            request_id = id(arguments)

        # Add credentials to arguments if available
        if self.api_key and 'apiKey' not in arguments:
            arguments['apiKey'] = self.api_key
        if self.api_secret and 'apiSecret' not in arguments:
            arguments['apiSecret'] = self.api_secret

        # Step 2: POST with session ID and both headers
        response = self.client.post(
            self.base_url,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
                'mcp-session-id': self.session_id,
            },
            json={
                'jsonrpc': '2.0',
                'method': 'tools/call',
                'params': {
                    'name': tool_name,
                    'arguments': arguments
                },
                'id': request_id
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"Tool call failed: {response.status_code} - {response.text[:500]}"
            )

        # Parse response (may be JSON or SSE)
        content_type = response.headers.get('content-type', '')

        if 'application/json' in content_type:
            result = response.json()
        elif 'text/event-stream' in content_type:
            # Parse SSE stream
            result = self._parse_sse(response.text)
        else:
            # Try JSON parse as fallback
            try:
                result = response.json()
            except:
                result = {'result': response.text}

        # Check for JSONRPC errors
        if isinstance(result, dict) and 'error' in result:
            raise Exception(f"MCP error: {result['error']}")

        return result

    def list_tools(self) -> Dict[str, Any]:
        """
        List available tools

        Returns:
            Tools list response

        Raises:
            Exception if not connected or list fails
        """
        if not self.session_id:
            raise Exception("Not connected. Call connect() first.")

        response = self.client.post(
            self.base_url,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream',
                'mcp-session-id': self.session_id,
            },
            json={
                'jsonrpc': '2.0',
                'method': 'tools/list',
                'id': 1
            }
        )

        if response.status_code != 200:
            raise Exception(
                f"Tools list failed: {response.status_code} - {response.text[:500]}"
            )

        content_type = response.headers.get('content-type', '')

        if 'application/json' in content_type:
            return response.json()
        elif 'text/event-stream' in content_type:
            return self._parse_sse(response.text)
        else:
            try:
                return response.json()
            except:
                return {'result': response.text}

    def convert(
        self,
        blob: str,
        inext: str,
        outfmt: str,
        width: int = 0,
        height: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Convert a file using TweekIT

        Args:
            blob: Base64-encoded file content
            inext: Input file extension (e.g., 'png', 'doc')
            outfmt: Output format (e.g., 'pdf', 'png')
            width: Output width (0 = no resize)
            height: Output height (0 = no resize)
            **kwargs: Additional conversion parameters

        Returns:
            Conversion result
        """
        arguments = {
            'blob': blob,
            'inext': inext,
            'outfmt': outfmt,
            'width': width,
            'height': height,
            **kwargs
        }

        return self.call_tool('convert', arguments)

    def _parse_sse(self, text: str) -> Dict[str, Any]:
        """
        Parse Server-Sent Events format

        Args:
            text: SSE response text

        Returns:
            Parsed result dict
        """
        lines = text.strip().split('\n')
        result = {}

        for line in lines:
            if line.startswith('data:'):
                try:
                    data = json.loads(line[5:].strip())
                    # Merge data into result
                    if isinstance(data, dict):
                        result.update(data)
                    else:
                        result['data'] = data
                except json.JSONDecodeError:
                    result['data'] = line[5:].strip()

        return result if result else {'result': text}

    def close(self):
        """Close HTTP client"""
        self.client.close()


# Standalone test functions
def test_connection(api_key: str, api_secret: str) -> bool:
    """Test TweekIT MCP connection with handshake"""
    try:
        with TweekITMCPClient(api_key=api_key, api_secret=api_secret) as client:
            print(f"✓ Connected with session ID: {client.session_id}")

            # Try to list tools
            tools = client.list_tools()
            print(f"✓ Listed tools: {tools}")

            return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_conversion(api_key: str, api_secret: str, test_blob: str) -> bool:
    """Test TweekIT file conversion"""
    try:
        with TweekITMCPClient(api_key=api_key, api_secret=api_secret) as client:
            print(f"✓ Connected with session ID: {client.session_id}")

            # Test conversion
            result = client.convert(
                blob=test_blob,
                inext='png',
                outfmt='png',
                width=50,
                height=50
            )

            print(f"✓ Conversion successful: {len(str(result))} bytes")
            return True

    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False


if __name__ == "__main__":
    import os

    # Get credentials from environment
    api_key = os.getenv('TWEEKIT_API_KEY')
    api_secret = os.getenv('TWEEKIT_API_SECRET')

    if not api_key or not api_secret:
        print("❌ Set TWEEKIT_API_KEY and TWEEKIT_API_SECRET environment variables")
        exit(1)

    print("Testing TweekIT MCP Client with Streamable HTTP Handshake")
    print("=" * 60)

    # Test connection
    print("\n1. Testing connection handshake...")
    test_connection(api_key, api_secret)

    # Test conversion
    print("\n2. Testing file conversion...")
    # Small test PNG (1x1 red pixel)
    test_blob = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    test_conversion(api_key, api_secret, test_blob)

    print("\n" + "=" * 60)
    print("✅ TweekIT MCP Client tests complete")

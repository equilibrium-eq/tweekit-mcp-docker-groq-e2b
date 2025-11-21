"""
E2B Code Interpreter Integration POC for TweekIT MCP Server

This module demonstrates integration between TweekIT media conversion
and E2B's sandboxed code execution environment.

Features:
- Execute code in isolated E2B sandboxes
- Process files within sandbox environments
- Safe execution of untrusted code
- Automatic sandbox cleanup
"""

import os
from typing import Optional, Dict, Any, List
from e2b_code_interpreter import Sandbox


class E2BSandboxManager:
    """Manages E2B sandbox lifecycle and code execution"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize E2B sandbox manager

        Args:
            api_key: E2B API key (defaults to E2B_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        if not self.api_key:
            raise ValueError(
                "E2B_API_KEY not found. Set it in .env or pass as parameter.\n"
                "Get your API key from https://e2b.dev/dashboard"
            )

    def execute_code(
        self,
        code: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code in E2B sandbox

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds (default: 30)

        Returns:
            Dict containing execution results with keys:
            - success: bool indicating execution success
            - stdout: standard output from code
            - stderr: standard error from code
            - error: error message if execution failed
        """
        try:
            with Sandbox(api_key=self.api_key, timeout=timeout) as sandbox:
                execution = sandbox.run_code(code)

                return {
                    "success": not execution.error,
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr,
                    "error": str(execution.error) if execution.error else None,
                    "results": execution.results if hasattr(execution, 'results') else []
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(e),
                "results": []
            }

    def execute_with_files(
        self,
        code: str,
        files: Dict[str, bytes],
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute code with file uploads in E2B sandbox

        Args:
            code: Python code to execute
            files: Dict mapping filename to file content (bytes)
            timeout: Execution timeout in seconds (default: 60)

        Returns:
            Dict containing execution results (same format as execute_code)
        """
        try:
            with Sandbox(api_key=self.api_key, timeout=timeout) as sandbox:
                # Upload files to sandbox
                for filename, content in files.items():
                    sandbox.files.write(filename, content)

                # Execute code
                execution = sandbox.run_code(code)

                return {
                    "success": not execution.error,
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr,
                    "error": str(execution.error) if execution.error else None,
                    "results": execution.results if hasattr(execution, 'results') else []
                }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": str(e),
                "results": []
            }

    def list_available_packages(self) -> List[str]:
        """
        List pre-installed packages in E2B sandbox

        Returns:
            List of package names
        """
        code = """
import subprocess
result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
print(result.stdout)
"""
        result = self.execute_code(code)
        if result["success"]:
            return result["stdout"].strip().split("\n")
        return []


def poc_example_basic():
    """Basic E2B POC example"""
    print("=== E2B Basic POC Example ===\n")

    manager = E2BSandboxManager()

    # Simple calculation
    code = """
import math
result = math.sqrt(144)
print(f"Square root of 144 is: {result}")
"""

    print("Executing code in E2B sandbox...")
    result = manager.execute_code(code)

    if result["success"]:
        print("✓ Execution successful!")
        print(f"Output: {result['stdout']}")
    else:
        print("✗ Execution failed!")
        print(f"Error: {result['error']}")


def poc_example_image_processing():
    """E2B POC with image processing using PIL"""
    print("\n=== E2B Image Processing POC ===\n")

    manager = E2BSandboxManager()

    # Image processing with PIL
    code = """
from PIL import Image
import numpy as np

# Create a simple gradient image
width, height = 200, 200
img_array = np.zeros((height, width, 3), dtype=np.uint8)

for y in range(height):
    for x in range(width):
        img_array[y, x] = [x % 256, y % 256, (x + y) % 256]

img = Image.fromarray(img_array)
img.save('gradient.png')
print(f"Created gradient image: {img.size}, mode: {img.mode}")
"""

    print("Processing image in E2B sandbox...")
    result = manager.execute_code(code, timeout=45)

    if result["success"]:
        print("✓ Image processing successful!")
        print(f"Output: {result['stdout']}")
    else:
        print("✗ Image processing failed!")
        print(f"Error: {result['error']}")


def poc_example_with_integration():
    """POC demonstrating TweekIT + E2B integration concept"""
    print("\n=== E2B + TweekIT Integration Concept ===\n")

    manager = E2BSandboxManager()

    # Simulate processing workflow
    code = """
import base64
import json

# This simulates receiving a base64-encoded image from TweekIT
# In real integration, this would come from TweekIT API response

print("Step 1: Received image data from TweekIT")
print("Step 2: Processing image in E2B sandbox")
print("Step 3: Applying transformations")
print("Step 4: Image processing complete")

result = {
    "status": "success",
    "processed": True,
    "output_format": "png"
}
print(json.dumps(result, indent=2))
"""

    print("Running integration workflow...")
    result = manager.execute_code(code)

    if result["success"]:
        print("✓ Integration workflow successful!")
        print(f"Output:\n{result['stdout']}")
    else:
        print("✗ Integration workflow failed!")
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    """Run POC examples"""
    try:
        poc_example_basic()
        poc_example_image_processing()
        poc_example_with_integration()

        print("\n=== E2B Integration POC Complete ===")
        print("\nNext steps:")
        print("1. Set E2B_API_KEY in .env file")
        print("2. Run: python e2b_integration.py")
        print("3. Integrate with TweekIT MCP server endpoints")

    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

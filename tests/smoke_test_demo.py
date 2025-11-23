#!/usr/bin/env python3
"""
Smoke Test Suite for TweekIT Demo
Tests different conversion scenarios across all conversion modes and file types.

Usage:
    python tests/smoke_test_demo.py
    python tests/smoke_test_demo.py --url http://localhost:8081
"""

import httpx
import base64
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Test server URL
BASE_URL = "http://localhost:8081"

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class SmokeTestRunner:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.tests = []

    def log(self, message: str, color: str = RESET):
        print(f"{color}{message}{RESET}")

    def create_test_pdf(self) -> bytes:
        """Create a minimal test PDF"""
        # Minimal PDF with one page
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<<>>>>endobj
4 0 obj<</Length 44>>stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000056 00000 n
0000000115 00000 n
0000000227 00000 n
trailer<</Size 5/Root 1 0 R>>
startxref
318
%%EOF
"""
        return pdf_content

    def create_test_image(self) -> bytes:
        """Create a minimal test PNG"""
        # 1x1 red pixel PNG
        png_content = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        return png_content

    async def test_health(self) -> bool:
        """Test health endpoint"""
        self.log("\n" + "="*60, BLUE)
        self.log("Testing: Health Check Endpoint", BLUE)
        self.log("="*60, BLUE)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                data = response.json()

                self.log(f"Status: {data.get('status')}", GREEN if data.get('status') == 'healthy' else RED)
                self.log(f"TweekIT Creds: {'✓' if data.get('has_tweekit_creds') else '✗'}")
                self.log(f"E2B Key: {'✓' if data.get('has_e2b_key') else '✗'}")
                self.log(f"Groq Key: {'✓' if data.get('has_groq_key') else '✗'}")

                if data.get('status') == 'healthy':
                    self.passed += 1
                    self.log("✓ Health check PASSED", GREEN)
                    return True
                else:
                    self.failed += 1
                    self.log("✗ Health check FAILED", RED)
                    return False

        except Exception as e:
            self.failed += 1
            self.log(f"✗ Health check FAILED: {e}", RED)
            return False

    async def test_conversion(self,
                            test_name: str,
                            file_data: bytes,
                            filename: str,
                            conversion_mode: str,
                            output_format: str,
                            groq_model: str = "llama-3.2-90b-vision-preview",
                            page_number: int = 1) -> bool:
        """Test a single conversion scenario"""

        self.log(f"\n{'='*60}", BLUE)
        self.log(f"Testing: {test_name}", BLUE)
        self.log(f"{'='*60}", BLUE)
        self.log(f"  File: {filename}")
        self.log(f"  Mode: {conversion_mode}")
        self.log(f"  Output Format: {output_format}")
        self.log(f"  Groq Model: {groq_model}")

        try:
            # Encode file to base64
            file_base64 = base64.b64encode(file_data).decode('utf-8')

            payload = {
                "file_base64": file_base64,
                "filename": filename,
                "output_format": output_format,
                "groq_model": groq_model,
                "conversion_mode": conversion_mode,
                "page_number": page_number
            }

            start_time = time.time()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/process",
                    json=payload
                )

                elapsed = time.time() - start_time

                if response.status_code != 200:
                    self.failed += 1
                    self.log(f"✗ FAILED: HTTP {response.status_code}", RED)
                    self.log(f"  Response: {response.text[:200]}", RED)
                    return False

                data = response.json()

                if not data.get('success'):
                    self.failed += 1
                    self.log(f"✗ FAILED: {data.get('error', 'Unknown error')}", RED)
                    if data.get('error_details'):
                        self.log(f"  Details: {data['error_details'][:200]}", RED)
                    return False

                # Check if we got a converted file
                has_file = bool(data.get('converted_file'))
                has_analysis = bool(data.get('analysis', {}).get('summary'))

                self.log(f"  ⏱️  Time: {elapsed:.2f}s", YELLOW)
                self.log(f"  📄 Converted File: {'✓' if has_file else '✗'}")
                self.log(f"  🤖 AI Analysis: {'✓' if has_analysis else '✗'}")
                self.log(f"  📊 Model: {data.get('analysis', {}).get('model', 'N/A')}")

                if has_file:
                    conv = data.get('conversion', {})
                    self.log(f"  📦 Format: {conv.get('input_format')} → {conv.get('output_format')}")
                    self.log(f"  📏 Size: {conv.get('size', 'N/A')}")

                self.passed += 1
                self.log(f"✓ {test_name} PASSED", GREEN)
                return True

        except httpx.TimeoutException:
            self.failed += 1
            self.log(f"✗ FAILED: Request timed out", RED)
            return False
        except Exception as e:
            self.failed += 1
            self.log(f"✗ FAILED: {str(e)}", RED)
            return False

    async def run_all_tests(self):
        """Run all smoke tests"""
        self.log("\n" + "="*60, BLUE)
        self.log("🚀 TWEEKIT DEMO SMOKE TEST SUITE", BLUE)
        self.log("="*60 + "\n", BLUE)

        # Test 1: Health check
        await self.test_health()

        # Create test files
        test_pdf = self.create_test_pdf()
        test_image = self.create_test_image()

        # Test 2: PDF to Image (Web Image Mode)
        await self.test_conversion(
            test_name="PDF → PNG (Web Image Mode)",
            file_data=test_pdf,
            filename="test.pdf",
            conversion_mode="preview",
            output_format="png"
        )

        # Test 3: PDF to Image with different model
        await self.test_conversion(
            test_name="PDF → PNG (Different Groq Model)",
            file_data=test_pdf,
            filename="test.pdf",
            conversion_mode="preview",
            output_format="png",
            groq_model="llama-3.3-70b-versatile"
        )

        # Test 4: Image to PDF
        await self.test_conversion(
            test_name="PNG → PDF",
            file_data=test_image,
            filename="test.png",
            conversion_mode="extract",
            output_format="pdf"
        )

        # Test 5: PDF to Markdown (Extract Mode)
        await self.test_conversion(
            test_name="PDF → Markdown (Extract Mode)",
            file_data=test_pdf,
            filename="test.pdf",
            conversion_mode="extract",
            output_format="md"
        )

        # Test 6: Auto TweekIT Mode
        await self.test_conversion(
            test_name="PDF (Auto TweekIT Mode)",
            file_data=test_pdf,
            filename="test.pdf",
            conversion_mode="auto",
            output_format="pdf"
        )

        # Test 7: Web Image with JPG output
        await self.test_conversion(
            test_name="PDF → JPG (Web Image)",
            file_data=test_pdf,
            filename="test.pdf",
            conversion_mode="preview",
            output_format="jpg"
        )

        # Test 8: Web Image with GIF output
        await self.test_conversion(
            test_name="PDF → GIF (Web Image)",
            file_data=test_pdf,
            filename="test.pdf",
            conversion_mode="preview",
            output_format="gif"
        )

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0

        self.log("\n" + "="*60, BLUE)
        self.log("📊 TEST SUMMARY", BLUE)
        self.log("="*60, BLUE)
        self.log(f"Total Tests: {total}")
        self.log(f"✓ Passed: {self.passed}", GREEN)
        self.log(f"✗ Failed: {self.failed}", RED if self.failed > 0 else GREEN)
        self.log(f"Success Rate: {success_rate:.1f}%", GREEN if success_rate >= 80 else YELLOW if success_rate >= 50 else RED)
        self.log("="*60 + "\n", BLUE)

        if self.failed > 0:
            sys.exit(1)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run TweekIT Demo smoke tests")
    parser.add_argument("--url", default=BASE_URL, help="Base URL of the demo server")
    args = parser.parse_args()

    runner = SmokeTestRunner(base_url=args.url)
    await runner.run_all_tests()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

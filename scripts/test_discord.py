#!/usr/bin/env python3
import asyncio
import httpx
import sys
import os

async def send_test_message(webhook_url):
    print(f"Testing webhook: {webhook_url[:20]}...")
    
    embed = {
        "title": "🧪 TweekIT Webhook Test",
        "description": "This is a test message from the E2B Hackathon Demo.",
        "color": 5763719,  # Green
        "fields": [
            {"name": "Status", "value": "Active", "inline": True},
            {"name": "Environment", "value": "Test Script", "inline": True}
        ],
        "footer": {"text": "TweekIT + E2B + Groq"}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={"embeds": [embed]}
            )
            response.raise_for_status()
            print("✅ Test message sent successfully!")
            return True
    except Exception as e:
        print(f"❌ Failed to send test message: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = os.getenv("DISCORD_WEBHOOK_URL")
        
    if not url:
        print("Usage: python test_discord.py <webhook_url>")
        sys.exit(1)
        
    asyncio.run(send_test_message(url))

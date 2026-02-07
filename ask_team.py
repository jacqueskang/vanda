#!/usr/bin/env python3
"""
Simple CLI tool to ask questions to your AI business team.
Usage: python ask_team.py "Your question here"
"""

import sys
import json
import httpx
import asyncio
from typing import Optional

ENDPOINT = "http://127.0.0.1:8088/chat"

async def ask_team(question: str) -> None:
    """Send a question to the business team and print the response."""
    if not question.strip():
        print("Error: Please provide a question")
        sys.exit(1)
    
    payload = {
        "messages": [
            {
                "role": "user",
                "text": question
            }
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n[*] Asking team: {question}\n")
            print("-" * 60)
            
            response = await client.post(ENDPOINT, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check different response formats
                if isinstance(result, dict):
                    if "output" in result:
                        print(result["output"])
                    elif "response" in result:
                        print(result["response"])
                    elif "messages" in result and result["messages"]:
                        # Print all messages
                        for msg in result["messages"]:
                            if isinstance(msg, dict):
                                content = msg.get("content") or msg.get("text") or str(msg)
                                print(content)
                            else:
                                print(msg)
                    else:
                        print(json.dumps(result, indent=2))
                else:
                    print(result)
                    
            else:
                print(f"Error: Server returned status {response.status_code}")
                print(response.text)
                sys.exit(1)
                
            print("-" * 60)
            
    except httpx.ConnectError:
        print(f"Error: Cannot connect to {ENDPOINT}")
        print("Make sure the business team is running: python business_team.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python ask_team.py \"Your question here\"")
        print("\nExamples:")
        print('  python ask_team.py "Design our MVP"')
        print('  python ask_team.py "What are the top 3 technical challenges?"')
        print('  python ask_team.py "Create a 6-month roadmap"')
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    asyncio.run(ask_team(question))

if __name__ == "__main__":
    main()

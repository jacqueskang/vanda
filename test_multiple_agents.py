#!/usr/bin/env python3
"""Test script for multiple agents functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from vanda_team.agents import get_or_create_agents, AGENT_METADATA
from agent_framework import ChatMessage, Role

async def test_multiple_agents():
    """Test if multiple agents can be run in parallel."""
    print("=" * 60)
    print("TESTING MULTIPLE AGENTS FEATURE")
    print("=" * 60)
    
    agents, router = await get_or_create_agents()
    
    print(f"\n[✓] Available agents: {list(agents.keys())}")
    print(f"[✓] Agent metadata: {list(AGENT_METADATA.keys())}")
    
    # Test 1: Verify agents dict keys
    requested = ['strategy', 'analyst', 'builder']
    selected = [a for a in requested if a in agents]
    
    print(f"\n[TEST 1] Agent filtering:")
    print(f"  Requested: {requested}")
    print(f"  Available keys in agents dict: {list(agents.keys())}")
    print(f"  Selected: {selected}")
    
    # Test 2: Run agents in parallel
    print(f"\n[TEST 2] Running {len(selected)} agents in parallel...")
    
    async def run_agent(agent_key):
        msg = ChatMessage(role=Role.USER, text="What is AI?")
        response = await agents[agent_key].run([msg])
        return {
            "agent": agent_key,
            "agent_label": f"{AGENT_METADATA[agent_key]['name']} ({AGENT_METADATA[agent_key]['role']})",
            "status": "complete"
        }
    
    try:
        results = await asyncio.gather(*[run_agent(a) for a in selected])
        print(f"[✓] Received {len(results)} responses:")
        for i, r in enumerate(results, 1):
            print(f"    {i}. {r['agent_label']} ({r['agent']})")
        
        if len(results) > 1:
            print("\n[✓] SUCCESS: Multiple agents working correctly!")
            return True
        else:
            print("\n[✗] FAILURE: Only one response received")
            return False
            
    except Exception as e:
        print(f"[✗] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_multiple_agents())
    sys.exit(0 if success else 1)

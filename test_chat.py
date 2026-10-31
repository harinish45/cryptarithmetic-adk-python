"""
Interactive test harness for cryptarithmetic ADK chat agent.
Requires GOOGLE_API_KEY in environment.
"""
import sys
import os
import asyncio
import warnings

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

warnings.filterwarnings('ignore')


async def test() -> None:
    from api.index import chat_endpoint, ChatRequest
    print("Testing ADK Chat Agent with 'Solve SEND + MORE = MONEY'...")
    r = await chat_endpoint(ChatRequest(message='Solve SEND + MORE = MONEY'))
    print('TOOLS:', r.tool_calls)
    print('REPLY:', r.reply[:500])
    print('SID:', r.session_id[:8])


if __name__ == '__main__':
    if not os.environ.get('GOOGLE_API_KEY') and not os.environ.get('GEMINI_API_KEY'):
        print('NOTE: Set GOOGLE_API_KEY in your environment to test live Gemini LLM integration.')
        print('PowerShell: $env:GOOGLE_API_KEY = "YOUR_API_KEY"')
    asyncio.run(test())

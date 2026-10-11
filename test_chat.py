import sys, os
sys.path.insert(0, r'c:\Documents\Projects\AI\cryptarithmetic-adk-py')

# Set GOOGLE_API_KEY in your environment before running this test.
# PowerShell: $env:GOOGLE_API_KEY = "YOUR_NEW_API_KEY"
# Do not commit API keys to source control.
if not os.environ.get('GOOGLE_API_KEY'):
    raise RuntimeError('Set GOOGLE_API_KEY in your environment before running this test.')

import asyncio, warnings
warnings.filterwarnings('ignore')

async def test():
    from api.index import chat, ChatRequest
    r = await chat(ChatRequest(message='Solve SEND + MORE = MONEY'))
    print('TOOLS:', r.tool_calls)
    print('REPLY:', r.reply[:500])
    print('SID:', r.session_id[:8])

asyncio.run(test())

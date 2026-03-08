import sys, os
sys.path.insert(0, r'c:\Documents\Projects\AI\cryptarithmetic-adk-py')
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDI8txYikB3fgAHmitEYkaVgNcjnRtvT_E'
import asyncio, warnings
warnings.filterwarnings('ignore')

async def test():
    from api.index import chat, ChatRequest
    r = await chat(ChatRequest(message='Solve SEND + MORE = MONEY'))
    print('TOOLS:', r.tool_calls)
    print('REPLY:', r.reply[:500])
    print('SID:', r.session_id[:8])

asyncio.run(test())

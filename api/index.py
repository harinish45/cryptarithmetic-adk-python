"""
ADK-powered chat backend.
Single /api/chat endpoint — the ADK Runner + Gemini handles all logic.
The solver tools are called automatically based on user's natural language.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import uuid

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from cryptarithmetic_agent.agent import root_agent

app = FastAPI(title="Cryptarithmetic ADK Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ADK Setup ───────────────────────────────────────────────────────────────
session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="cryptarithmetic",
    session_service=session_service,
)

# ─── Request / Response Models ────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_calls: list[str] = []

# ─── Routes ──────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "description": "Cryptarithmetic ADK Chat API"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Use or create a session ID
    session_id = req.session_id or str(uuid.uuid4())

    # Ensure ADK session exists
    existing = await session_service.get_session(
        app_name="cryptarithmetic",
        user_id="web-user",
        session_id=session_id,
    )
    if not existing:
        await session_service.create_session(
            app_name="cryptarithmetic",
            user_id="web-user",
            session_id=session_id,
        )

    # Build the user message for ADK
    user_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=req.message)],
    )

    reply_text = ""
    tool_calls_used = []

    # Run the agent and collect all events
    async for event in runner.run_async(
        user_id="web-user",
        session_id=session_id,
        new_message=user_message,
    ):
        # Collect final text response from the agent (not tool calls)
        if hasattr(event, "is_final_response") and event.is_final_response():
            if hasattr(event, "content") and event.content:
                for part in (event.content.parts or []):
                    if hasattr(part, "text") and part.text:
                        reply_text += part.text

        # Collect tool call names for transparency display
        if hasattr(event, "content") and event.content:
            for part in (event.content.parts or []):
                if hasattr(part, "function_call") and part.function_call:
                    name = getattr(part.function_call, "name", None)
                    if name and name not in tool_calls_used:
                        tool_calls_used.append(name)

    return ChatResponse(
        reply=reply_text or "I'm ready to help! Try asking me to solve a puzzle like `SEND + MORE = MONEY`.",
        session_id=session_id,
        tool_calls=tool_calls_used,
    )

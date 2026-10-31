"""
FastAPI REST API & ADK Agent Chat Backend
Endpoints:
  - GET  /health, /api/health
  - POST /solve, /api/solve
  - POST /explain, /api/explain
  - POST /validate, /api/validate
  - POST /chat, /api/chat
  - GET  /history, /api/history
"""
from __future__ import annotations

import logging
import os
import sys
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from cryptarithmetic_agent.agent import (
    root_agent,
    solve_puzzle,
    validate_puzzle,
    explain_solution,
)

logger = logging.getLogger("cryptarithmetic_api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Cryptarithmetic ADK Solver API",
    description="REST API and ADK Agent for solving and explaining cryptarithmetic puzzles.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Pydantic Request & Response Models ───────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["cryptarithmetic-adk-python"])
    version: str = Field(..., examples=["1.0.0"])


class SolveRequest(BaseModel):
    expression: str = Field(..., examples=["SEND + MORE = MONEY"])
    max_solutions: int = Field(default=5, ge=1, le=50, examples=[5])


class SolutionItem(BaseModel):
    mapping: dict[str, int]
    substituted: str


class SolverStatsModel(BaseModel):
    nodes_explored: int
    backtracks: int
    solve_time_ms: float


class SolveResponse(BaseModel):
    success: bool
    solutions: list[SolutionItem]
    stats: Optional[SolverStatsModel] = None
    reasoning_trace: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ExplainRequest(BaseModel):
    expression: str = Field(..., examples=["SEND + MORE = MONEY"])
    hint_level: int = Field(default=1, ge=1, le=3, examples=[1])


class ExplainResponse(BaseModel):
    success: bool
    expression: str
    level: int
    hints: list[str]
    reasoning_steps: list[str]
    column_equations: list[str]
    deductions: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class ValidateRequest(BaseModel):
    expression: str = Field(..., examples=["SEND + MORE = MONEY"])


class ValidateResponse(BaseModel):
    valid: bool
    solvable: bool
    unique_letters: int
    letters: list[str]
    leading_letters: list[str]
    operands: list[str]
    result: str
    solutions_count: int
    error: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., examples=["Solve SEND + MORE = MONEY"])
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_calls: list[str] = Field(default_factory=list)


# In-memory history cache
SESSION_HISTORY: dict[str, list[dict[str, str]]] = {}


# ─── Core Solver Endpoints ───────────────────────────────────────────────────

@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    """Root endpoint returning API service information."""
    return {
        "status": "ok",
        "service": "Cryptarithmetic ADK Solver API",
        "docs_url": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
@app.get("/api/health", response_model=HealthResponse, tags=["General"])
def health_check() -> HealthResponse:
    """Service health and liveness probe."""
    return HealthResponse(
        status="healthy",
        service="cryptarithmetic-adk-python",
        version="1.0.0"
    )


@app.post("/solve", response_model=SolveResponse, tags=["Solver"])
@app.post("/api/solve", response_model=SolveResponse, tags=["Solver"])
def solve_endpoint(req: SolveRequest) -> SolveResponse:
    """Solve cryptarithmetic puzzle and return solutions with reasoning trace."""
    res = solve_puzzle(expression=req.expression, max_solutions=req.max_solutions)
    stats_data = res.get("stats")
    stats_model = SolverStatsModel(**stats_data) if stats_data else None

    return SolveResponse(
        success=res.get("success", False),
        solutions=[SolutionItem(**s) for s in res.get("solutions", [])],
        stats=stats_model,
        reasoning_trace=res.get("reasoning_trace", []),
        metadata=res.get("metadata", {}),
        error=res.get("error")
    )


@app.post("/explain", response_model=ExplainResponse, tags=["Solver"])
@app.post("/api/explain", response_model=ExplainResponse, tags=["Solver"])
def explain_endpoint(req: ExplainRequest) -> ExplainResponse:
    """Generate progressive hints and column-by-column deduction steps."""
    res = explain_solution(expression=req.expression, hint_level=req.hint_level)
    return ExplainResponse(
        success=res.get("success", False),
        expression=res.get("expression", req.expression),
        level=res.get("level", req.hint_level),
        hints=res.get("hints", []),
        reasoning_steps=res.get("reasoning_steps", []),
        column_equations=res.get("column_equations", []),
        deductions=res.get("deductions", []),
        error=res.get("error")
    )


@app.post("/validate", response_model=ValidateResponse, tags=["Solver"])
@app.post("/api/validate", response_model=ValidateResponse, tags=["Solver"])
def validate_endpoint(req: ValidateRequest) -> ValidateResponse:
    """Validate puzzle syntax, token alphabets, unique letters count, and solvability."""
    res = validate_puzzle(expression=req.expression)
    return ValidateResponse(
        valid=res.get("valid", False),
        solvable=res.get("solvable", False),
        unique_letters=res.get("unique_letters", 0),
        letters=res.get("letters", []),
        leading_letters=res.get("leading_letters", []),
        operands=res.get("operands", []),
        result=res.get("result", ""),
        solutions_count=res.get("solutions_count", 0),
        error=res.get("error")
    )


@app.get("/history", tags=["History"])
@app.get("/api/history", tags=["History"])
def get_history(session_id: Optional[str] = None) -> dict[str, Any]:
    """Retrieve chat session history."""
    if session_id:
        return {"session_id": session_id, "messages": SESSION_HISTORY.get(session_id, [])}
    return {"total_sessions": len(SESSION_HISTORY), "sessions": list(SESSION_HISTORY.keys())}


# ─── ADK Conversational Agent Endpoint ────────────────────────────────────────

def _record_session_message(session_id: str, role: str, text: str) -> None:
    """Append message to session memory."""
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = []
    SESSION_HISTORY[session_id].append({"role": role, "text": text})


@app.post("/chat", response_model=ChatResponse, tags=["Agent"])
@app.post("/api/chat", response_model=ChatResponse, tags=["Agent"])
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """Conversational endpoint executing Google ADK runner with Gemini."""
    session_id: str = req.session_id or str(uuid.uuid4())
    _record_session_message(session_id, "user", req.message)

    api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        fallback_msg: str = (
            "GOOGLE_API_KEY is not configured. For direct solving without an API key, "
            "use the /solve or /validate endpoints, or set GOOGLE_API_KEY."
        )
        _record_session_message(session_id, "ai", fallback_msg)
        return ChatResponse(reply=fallback_msg, session_id=session_id, tool_calls=[])

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types as genai_types

        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="cryptarithmetic",
            session_service=session_service,
        )

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

        user_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=req.message)],
        )

        reply_text = ""
        tool_calls_used: list[str] = []

        async for event in runner.run_async(
            user_id="web-user",
            session_id=session_id,
            new_message=user_message,
        ):
            if hasattr(event, "is_final_response") and event.is_final_response():
                if hasattr(event, "content") and event.content:
                    for part in (event.content.parts or []):
                        if hasattr(part, "text") and part.text:
                            reply_text += part.text

            if hasattr(event, "content") and event.content:
                for part in (event.content.parts or []):
                    if hasattr(part, "function_call") and part.function_call:
                        name = getattr(part.function_call, "name", None)
                        if name and name not in tool_calls_used:
                            tool_calls_used.append(name)

        final_reply: str = (
            reply_text or "I'm ready to help! Try asking me to solve a puzzle like SEND + MORE = MONEY."
        )
        _record_session_message(session_id, "ai", final_reply)
        return ChatResponse(reply=final_reply, session_id=session_id, tool_calls=tool_calls_used)

    except Exception as exc:
        logger.exception("Error executing ADK runner: %s", exc)
        err_msg = f"Agent encountered an error: {str(exc)}"
        _record_session_message(session_id, "ai", err_msg)
        return ChatResponse(reply=err_msg, session_id=session_id, tool_calls=[])

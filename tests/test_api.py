"""
Unit and integration tests for FastAPI REST endpoints.
Covers /health, /solve, /explain, /validate, /history, and /chat.
"""
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test GET / returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_endpoints() -> None:
    """Test GET /health and GET /api/health."""
    for path in ["/health", "/api/health"]:
        response = client.get(path)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "cryptarithmetic-adk-python"
        assert data["version"] == "1.0.0"


def test_solve_endpoint_valid() -> None:
    """Test POST /solve with valid puzzle."""
    payload = {"expression": "SEND + MORE = MONEY", "max_solutions": 1}
    response = client.post("/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["solutions"]) == 1
    assert data["solutions"][0]["substituted"] == "9567 + 1085 = 10652"
    assert data["stats"]["solve_time_ms"] > 0
    assert len(data["reasoning_trace"]) > 0


def test_solve_endpoint_multi_addend() -> None:
    """Test POST /api/solve with multi-addend expression."""
    payload = {"expression": "FORTY + TEN + TEN = SIXTY", "max_solutions": 1}
    response = client.post("/api/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["solutions"]) == 1
    assert "29786 + 850 + 850 = 31486" in data["solutions"][0]["substituted"]


def test_solve_endpoint_invalid_syntax() -> None:
    """Test POST /solve with malformed puzzle expression."""
    payload = {"expression": "INVALID PUZZLE"}
    response = client.post("/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["solutions"] == []
    assert data["error"] is not None


def test_explain_endpoint() -> None:
    """Test POST /explain and /api/explain."""
    for path in ["/explain", "/api/explain"]:
        payload = {"expression": "SEND + MORE = MONEY", "hint_level": 2}
        response = client.post(path, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["level"] == 2
        assert len(data["hints"]) > 0
        assert len(data["column_equations"]) == 5


def test_validate_endpoint_valid_solvable() -> None:
    """Test POST /validate for valid solvable puzzle."""
    payload = {"expression": "SEND + MORE = MONEY"}
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["solvable"] is True
    assert data["unique_letters"] == 8
    assert data["error"] is None


def test_validate_endpoint_invalid_syntax() -> None:
    """Test POST /validate for invalid syntax."""
    payload = {"expression": "BAD_EXPRESSION"}
    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["solvable"] is False
    assert data["error"] is not None


def test_history_endpoint() -> None:
    """Test GET /history endpoint."""
    response = client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert "sessions" in data


def test_chat_endpoint_fallback_without_key() -> None:
    """Test POST /api/chat gracefully advises user when GOOGLE_API_KEY is not set."""
    payload = {"message": "Solve SEND + MORE = MONEY"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "session_id" in data

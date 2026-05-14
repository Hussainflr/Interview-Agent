from fastapi.testclient import TestClient

from backend.main import app


def test_openai_models_endpoint_for_lobechat():
    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200
    model_ids = {item["id"] for item in response.json()["data"]}
    assert "interview-agent-local" in model_ids


def test_openai_chat_endpoint_routes_greeting_without_model_call():
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "interview-agent-local",
            "messages": [{"role": "user", "content": "hello"}],
            "stream": False,
        },
    )
    assert response.status_code == 200
    content = response.json()["choices"][0]["message"]["content"]
    assert "ready" in content.lower()

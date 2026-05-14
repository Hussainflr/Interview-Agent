from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from agents.interview_agent import InterviewAgent
from backend.config import get_settings
from backend.openai_compat import OpenAIChatRequest, chat_completions_response, models_response
from backend.websocket import interview_ws_handler
from mcp.manager import MCPManager
from providers.registry import available_providers
from providers.router import ModelRouter

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Local Interview Agent", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SessionStartRequest(BaseModel):
    role: str | None = None
    difficulty: Literal["beginner", "intermediate", "advanced"] | None = None
    interview_type: Literal["technical", "behavioral", "HR", "leadership", "scenario-based"] | None = None
    cv_text: str = ""
    job_description: str = ""


class MessageRequest(BaseModel):
    text: str


class ProviderRequest(BaseModel):
    provider: Literal["ollama", "lmstudio", "openai_compatible", "openai", "anthropic", "gemini", "xai"]
    model: str
    privacy_mode: Literal["local_only", "hybrid", "cloud_allowed"] = "local_only"


class MCPToolCallRequest(BaseModel):
    server_id: str
    tool_name: str
    arguments: dict[str, Any] = {}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Local Interview Agent API is running"}


@app.get("/v1/models")
def openai_models() -> dict[str, Any]:
    return models_response()


@app.post("/v1/chat/completions")
def openai_chat_completions(payload: OpenAIChatRequest):
    return chat_completions_response(payload)


@app.get("/api/config")
def config() -> dict[str, Any]:
    settings = get_settings()
    interview = settings.get("interview", {})
    llm = settings.get("llm", {})
    return {
        "roles": interview.get("roles", []),
        "difficulties": interview.get("difficulties", []),
        "types": interview.get("types", []),
        "provider": llm.get("provider"),
        "model": llm.get("model"),
        "privacy_mode": settings.get("routing", {}).get("privacy_mode", "local_only"),
        "providers": available_providers(settings),
        "mcp": {
            "enabled": settings.get("mcp", {}).get("enabled", False),
            "require_user_approval": settings.get("mcp", {}).get("require_user_approval", True),
            "expose_tool_descriptions_to_model": settings.get("mcp", {}).get("expose_tool_descriptions_to_model", False),
        },
    }


@app.post("/api/provider")
def provider(payload: ProviderRequest) -> dict[str, Any]:
    settings = get_settings()
    settings["llm"]["provider"] = payload.provider
    settings["llm"]["model"] = payload.model.strip()
    settings["routing"]["privacy_mode"] = payload.privacy_mode
    return {"ok": True, "provider": payload.provider, "model": payload.model, "privacy_mode": payload.privacy_mode}


@app.get("/api/health/model")
def model_health() -> dict[str, Any]:
    return InterviewAgent(get_settings()).health()


@app.get("/api/providers")
def providers() -> list[dict[str, Any]]:
    return available_providers(get_settings())


@app.get("/api/providers/health")
def providers_health() -> list[dict[str, Any]]:
    return ModelRouter(get_settings()).health_all()


@app.get("/api/providers/{provider_name}/models")
def provider_models(provider_name: str) -> dict[str, Any]:
    try:
        models = ModelRouter(get_settings()).model_list(provider_name)
    except Exception as exc:
        return {"provider": provider_name, "models": [], "error": str(exc)}
    return {"provider": provider_name, "models": models}


@app.get("/api/mcp/servers")
def mcp_servers() -> list[dict[str, Any]]:
    return MCPManager(get_settings()).list_servers()


@app.get("/api/mcp/tools")
def mcp_tools() -> list[dict[str, Any]]:
    return MCPManager(get_settings()).discover_tools()


@app.post("/api/mcp/tools/call")
def mcp_tool_call(payload: MCPToolCallRequest) -> dict[str, Any]:
    try:
        return MCPManager(get_settings()).call_tool(payload.server_id, payload.tool_name, payload.arguments)
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.get("/api/sessions")
def list_sessions() -> list[dict[str, Any]]:
    return InterviewAgent(get_settings()).list_sessions()


@app.post("/api/session/start")
def start_session(payload: SessionStartRequest) -> dict[str, Any]:
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    return InterviewAgent(get_settings()).start_session(data)


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    try:
        return InterviewAgent(get_settings()).get_session(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/session/{session_id}/message")
def send_message(session_id: str, payload: MessageRequest) -> dict[str, Any]:
    try:
        return InterviewAgent(get_settings()).handle_message(session_id, payload.text)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/session/{session_id}/export")
def export_session(session_id: str, format: Literal["markdown", "pdf"] = "markdown"):
    settings = get_settings()
    agent = InterviewAgent(settings)
    try:
        markdown_path = agent.export_markdown(session_id, settings["app"]["report_dir"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if format == "markdown":
        return FileResponse(markdown_path, media_type="text/markdown", filename=markdown_path.name)

    pdf_path = markdown_path.with_suffix(".pdf")
    try:
        _markdown_to_pdf(markdown_path, pdf_path)
    except RuntimeError as exc:
        return PlainTextResponse(str(exc), status_code=501)
    return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path.name)


@app.post("/api/upload/text")
async def upload_text(file: UploadFile = File(...)) -> dict[str, str]:
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="ignore")
    return {"filename": file.filename or "upload.txt", "text": text[:12000]}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await interview_ws_handler(websocket)


def _markdown_to_pdf(markdown_path: Path, pdf_path: Path) -> None:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:
        raise RuntimeError("PDF export needs reportlab. Run: pip install reportlab") from exc

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    story = []
    for raw_line in markdown_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 8))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["Title"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["Heading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["Heading3"]))
        else:
            story.append(Paragraph(line.replace("&", "&amp;"), styles["BodyText"]))
    doc.build(story)

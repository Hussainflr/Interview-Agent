from __future__ import annotations

from typing import Any

from agents.interview_agent import classify_intent, heuristic_evaluation
from backend.config import ROOT_DIR, get_settings
from providers.router import ModelRouter


INTERVIEW_MODEL_ID = "interview-agent-local"


def lobe_model_list() -> list[dict[str, Any]]:
    return [
        {
            "id": INTERVIEW_MODEL_ID,
            "object": "model",
            "created": 0,
            "owned_by": "local-interview-agent",
        },
        {
            "id": "interview-agent-hybrid",
            "object": "model",
            "created": 0,
            "owned_by": "local-interview-agent",
        },
    ]


def respond_to_lobechat(messages: list[dict[str, str]], model: str = INTERVIEW_MODEL_ID) -> str:
    user_text = _latest_user_message(messages)
    route = classify_intent(user_text)
    if route["intent"] != "interview_answer":
        return route["response"]

    settings = get_settings()
    router = ModelRouter(settings)
    sensitive = _looks_sensitive(messages)
    mode = _infer_mode(messages)
    fallback = heuristic_evaluation(user_text)
    system = (ROOT_DIR / "prompts" / "evaluate_answer.md").read_text(encoding="utf-8")
    prompt = f"""
You are embedded inside LobeChat as a production AI interview coach.

Interview mode: {mode}
Conversation context:
{_compact_history(messages)}

Candidate answer:
{user_text}
""".strip()
    evaluation = router.generate_json(system, prompt, fallback, task="evaluator", sensitive=sensitive)

    strengths = "; ".join(evaluation.get("strengths", []))
    weaknesses = "; ".join(evaluation.get("weaknesses", []))
    rubric = evaluation.get("rubric", {})
    rubric_text = "\n".join(f"- {key.replace('_', ' ').title()}: {value}/20" for key, value in rubric.items())

    return f"""## Interview Feedback

**Score:** {evaluation.get("score", 0)}/100

**Strengths:** {strengths}

**Improve:** {weaknesses}

### Rubric
{rubric_text}

### Stronger Answer
{evaluation.get("improved_answer", "")}

### Follow-up Question
{evaluation.get("follow_up_question", "Can you share a more specific example with measurable impact?")}"""


def _latest_user_message(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _compact_history(messages: list[dict[str, str]]) -> str:
    recent = messages[-10:]
    return "\n".join(f"{item.get('role', 'user')}: {item.get('content', '')[:1200]}" for item in recent)


def _looks_sensitive(messages: list[dict[str, str]]) -> bool:
    text = "\n".join(item.get("content", "") for item in messages).lower()
    markers = ["resume", "cv", "job description", "phone", "email", "address", "salary", "passport"]
    return any(marker in text for marker in markers)


def _infer_mode(messages: list[dict[str, str]]) -> str:
    text = "\n".join(item.get("content", "") for item in messages[-6:]).lower()
    for mode in ["system design", "technical", "behavioral", "leadership", "hr", "ml", "ai", "un", "ingo"]:
        if mode in text:
            return mode
    return "adaptive interview coaching"

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from backend.config import ROOT_DIR, get_settings
from backend.storage import SessionStore
from providers.base import ProviderError
from providers.router import ModelRouter

logger = logging.getLogger(__name__)

GREETING_RE = re.compile(r"^\s*(hi|hello|hey|salam|assalam|good\s+(morning|afternoon|evening))[\s!.]*$", re.I)
HARMFUL_TERMS = {"kill yourself", "terrorist instructions", "make a bomb", "self harm", "suicide"}
ABUSIVE_TERMS = {"fuck you", "idiot", "shut up", "stupid"}

QUESTION_FALLBACKS = {
    "technical": "Walk me through a recent technical problem you solved. What trade-offs did you consider?",
    "behavioral": "Tell me about a time you handled a difficult situation at work. What did you do?",
    "HR": "Why are you interested in this role, and what makes you a strong fit?",
    "leadership": "Describe a time you influenced a team without relying on authority.",
    "scenario-based": "Imagine a critical project is behind schedule. How would you assess the situation and respond?",
}


class InterviewAgent:
    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or get_settings()
        self.router = ModelRouter(self.settings)
        self.store = SessionStore(self.settings["app"]["session_dir"])

    def start_session(self, profile: dict[str, Any]) -> dict[str, Any]:
        profile = self._normalize_profile(profile)
        session = self.store.create(profile)
        question = self._generate_question(session)
        self._append(session, "assistant", question, kind="question")
        self.store.save(session)
        return self._public_session(session)

    def handle_message(self, session_id: str, text: str) -> dict[str, Any]:
        session = self.store.get(session_id)
        clean_text = (text or "").strip()
        route = classify_intent(clean_text)

        if route["intent"] != "interview_answer":
            response = route["response"]
            self._append(session, "user", clean_text, kind=route["intent"])
            self._append(session, "assistant", response, kind="guidance")
            self.store.save(session)
            return {"route": route, "reply": response, "session": self._public_session(session)}

        self._append(session, "user", clean_text, kind="answer")
        evaluation = self._evaluate(session, clean_text)
        session["scores"].append(float(evaluation.get("score", 0)))
        session["improvement_areas"] = _merge_areas(
            session.get("improvement_areas", []),
            evaluation.get("weaknesses", []),
        )

        reply = _format_feedback(evaluation)
        self._append(session, "assistant", reply, kind="feedback", metadata=evaluation)
        follow_up = evaluation.get("follow_up_question") or self._generate_question(session, last_answer=clean_text)
        self._append(session, "assistant", follow_up, kind="question")
        self.store.save(session)

        return {
            "route": route,
            "reply": reply,
            "next_question": follow_up,
            "evaluation": evaluation,
            "session": self._public_session(session),
        }

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._public_session(self.store.get(session_id))

    def list_sessions(self) -> list[dict[str, Any]]:
        return self.store.list()

    def export_markdown(self, session_id: str, report_dir: str) -> Path:
        session = self.store.get(session_id)
        report_path = Path(report_dir)
        report_path.mkdir(parents=True, exist_ok=True)
        path = report_path / f"interview-report-{session_id}.md"
        path.write_text(_session_to_markdown(session), encoding="utf-8")
        return path

    def health(self) -> dict[str, Any]:
        return self.router.health().__dict__

    def _normalize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        app = self.settings["app"]
        return {
            "role": profile.get("role") or app.get("default_role", "Software Engineer"),
            "difficulty": profile.get("difficulty") or app.get("default_difficulty", "intermediate"),
            "interview_type": profile.get("interview_type") or app.get("default_interview_type", "technical"),
            "provider": self.settings["llm"]["provider"],
            "model": self.settings["llm"]["model"],
            "privacy_mode": self.settings.get("routing", {}).get("privacy_mode", "local_only"),
            "cv_text": _truncate(profile.get("cv_text", ""), 3500),
            "job_description": _truncate(profile.get("job_description", ""), 3500),
        }

    def _generate_question(self, session: dict[str, Any], last_answer: str = "") -> str:
        profile = session["profile"]
        fallback = QUESTION_FALLBACKS.get(profile["interview_type"], QUESTION_FALLBACKS["technical"])
        system = _read_prompt("interview_question.md")
        user = f"""
Role: {profile['role']}
Difficulty: {profile['difficulty']}
Interview type: {profile['interview_type']}
CV context: {profile.get('cv_text') or 'Not provided'}
Job description: {profile.get('job_description') or 'Not provided'}
Last answer: {last_answer or 'This is the first question.'}
Recent session:
{_recent_messages(session)}
""".strip()
        try:
            sensitive = bool(profile.get("cv_text") or profile.get("job_description"))
            question = self.router.generate(system, user, task="interviewer", sensitive=sensitive)
            return question or fallback
        except ProviderError as exc:
            logger.warning("Question generation fallback: %s", exc)
            return f"{fallback} (Local model note: {exc})"

    def _evaluate(self, session: dict[str, Any], answer: str) -> dict[str, Any]:
        profile = session["profile"]
        fallback = heuristic_evaluation(answer)
        system = _read_prompt("evaluate_answer.md")
        user = f"""
Role: {profile['role']}
Difficulty: {profile['difficulty']}
Interview type: {profile['interview_type']}
CV context: {profile.get('cv_text') or 'Not provided'}
Job description: {profile.get('job_description') or 'Not provided'}
Current answer: {answer}
Recent session:
{_recent_messages(session)}
""".strip()
        sensitive = bool(profile.get("cv_text") or profile.get("job_description"))
        evaluation = self.router.generate_json(system, user, fallback, task="evaluator", sensitive=sensitive)
        return _clean_evaluation(evaluation, fallback)

    def _append(
        self,
        session: dict[str, Any],
        role: str,
        content: str,
        *,
        kind: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        session["messages"].append(
            {
                "role": role,
                "content": content,
                "kind": kind,
                "metadata": metadata or {},
            }
        )

    def _public_session(self, session: dict[str, Any]) -> dict[str, Any]:
        scores = session.get("scores", [])
        return {
            **session,
            "average_score": round(sum(scores) / len(scores), 1) if scores else None,
            "latest_score": scores[-1] if scores else None,
        }


def classify_intent(text: str) -> dict[str, str]:
    lowered = text.lower().strip()
    if not lowered:
        return {"intent": "empty", "response": "I did not catch that. Please type or say your answer when ready."}
    if any(term in lowered for term in HARMFUL_TERMS):
        return {
            "intent": "unsafe",
            "response": "I cannot help with harmful content. I can help you practice interview answers or reframe a workplace scenario safely.",
        }
    if any(term in lowered for term in ABUSIVE_TERMS):
        return {
            "intent": "abusive",
            "response": "Let us keep the practice respectful. Share an interview answer or ask for interview preparation help.",
        }
    if GREETING_RE.match(text):
        return {
            "intent": "greeting",
            "response": "Hello. I am ready when you are. Choose a role and send your first answer, or start a new mock interview.",
        }
    if len(lowered.split()) < 4 and not lowered.endswith("?"):
        return {
            "intent": "unclear",
            "response": "Please give a fuller answer so I can score it fairly, or ask a specific interview-prep question.",
        }
    if any(word in lowered for word in ["weather", "recipe", "movie", "sports score"]):
        return {
            "intent": "unrelated",
            "response": "I am focused on interview preparation. Paste an answer, CV, or job description and I will help you practice.",
        }
    return {"intent": "interview_answer", "response": ""}


def heuristic_evaluation(answer: str) -> dict[str, Any]:
    words = answer.split()
    length_score = min(20, max(4, len(words) // 6))
    structure_score = 16 if any(marker in answer.lower() for marker in ["first", "second", "because", "result", "impact"]) else 9
    relevance = 14 if len(words) >= 25 else 8
    depth = 15 if len(words) >= 60 else 9
    role_fit = 12
    total = relevance + min(20, length_score) + depth + structure_score + role_fit
    return {
        "score": min(100, total),
        "strengths": ["You provided a direct answer."],
        "weaknesses": ["Add a concrete example, measurable impact, and a clearer structure."],
        "improved_answer": "I would answer with a concise situation, the action I personally took, the trade-offs I considered, and the measurable result.",
        "rubric": {
            "relevance": relevance,
            "clarity": min(20, length_score),
            "depth": depth,
            "structure": structure_score,
            "role_fit": role_fit,
        },
        "follow_up_question": "Can you give a specific example with the impact or result you achieved?",
    }


def _clean_evaluation(evaluation: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    result = {**fallback, **(evaluation or {})}
    result["score"] = max(0, min(100, int(result.get("score", fallback["score"]))))
    for key in ["strengths", "weaknesses"]:
        value = result.get(key)
        result[key] = value if isinstance(value, list) and value else fallback[key]
    rubric = result.get("rubric") if isinstance(result.get("rubric"), dict) else fallback["rubric"]
    result["rubric"] = {key: max(0, min(20, int(rubric.get(key, 0)))) for key in fallback["rubric"]}
    result["improved_answer"] = str(result.get("improved_answer") or fallback["improved_answer"])
    result["follow_up_question"] = str(result.get("follow_up_question") or fallback["follow_up_question"])
    return result


def _format_feedback(evaluation: dict[str, Any]) -> str:
    strengths = "; ".join(evaluation.get("strengths", []))
    weaknesses = "; ".join(evaluation.get("weaknesses", []))
    return (
        f"Score: {evaluation.get('score', 0)}/100\n\n"
        f"Strengths: {strengths}\n\n"
        f"Improve: {weaknesses}\n\n"
        f"Suggested answer: {evaluation.get('improved_answer', '')}"
    )


def _session_to_markdown(session: dict[str, Any]) -> str:
    scores = session.get("scores", [])
    average = round(sum(scores) / len(scores), 1) if scores else "No scored answers yet"
    profile = session.get("profile", {})
    lines = [
        "# Interview Report",
        "",
        f"- Role: {profile.get('role')}",
        f"- Difficulty: {profile.get('difficulty')}",
        f"- Interview type: {profile.get('interview_type')}",
        f"- Average score: {average}",
        f"- Improvement areas: {', '.join(session.get('improvement_areas', [])) or 'None yet'}",
        "",
        "## Conversation",
        "",
    ]
    for message in session.get("messages", []):
        role = "AI" if message["role"] == "assistant" else "You"
        lines.extend([f"### {role} - {message.get('kind')}", "", message["content"], ""])
    return "\n".join(lines)


def _recent_messages(session: dict[str, Any]) -> str:
    max_items = int(get_settings()["interview"].get("max_history_items", 12))
    messages = session.get("messages", [])[-max_items:]
    return "\n".join(f"{m['role']}: {m['content']}" for m in messages)


def _read_prompt(name: str) -> str:
    return (ROOT_DIR / "prompts" / name).read_text(encoding="utf-8")


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text[:limit]


def _merge_areas(existing: list[str], new_items: list[str]) -> list[str]:
    merged = list(existing)
    for item in new_items:
        normalized = str(item).strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged[:8]

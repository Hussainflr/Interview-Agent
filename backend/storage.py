from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class SessionStore:
    def __init__(self, session_dir: str):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        session = {
            "id": str(uuid4()),
            "created_at": now,
            "updated_at": now,
            "profile": payload,
            "messages": [],
            "scores": [],
            "improvement_areas": [],
            "status": "active",
        }
        self.save(session)
        return session

    def get(self, session_id: str) -> dict[str, Any]:
        path = self._path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Session {session_id} not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, session: dict[str, Any]) -> None:
        session["updated_at"] = _now()
        self._path(session["id"]).write_text(json.dumps(session, indent=2), encoding="utf-8")

    def list(self) -> list[dict[str, Any]]:
        sessions = []
        for path in sorted(self.session_dir.glob("*.json"), reverse=True):
            data = json.loads(path.read_text(encoding="utf-8"))
            sessions.append(
                {
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "profile": data.get("profile", {}),
                    "average_score": _average(data.get("scores", [])),
                    "message_count": len(data.get("messages", [])),
                }
            )
        return sessions

    def _path(self, session_id: str) -> Path:
        safe_id = "".join(ch for ch in session_id if ch.isalnum() or ch in {"-", "_"})
        return self.session_dir / f"{safe_id}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _average(scores: list[float]) -> float | None:
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


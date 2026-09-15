import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = """CREATE TABLE IF NOT EXISTS events (
 event_id TEXT PRIMARY KEY,
 event_schema TEXT NOT NULL,
 event_type TEXT NOT NULL,
 occurred_at TEXT NOT NULL,
 round_id TEXT NOT NULL,
 actor_kind TEXT NOT NULL,
 actor_id TEXT NOT NULL,
 sequence INTEGER NOT NULL UNIQUE,
 payload_json TEXT NOT NULL,
 causation_id TEXT,
 correlation_id TEXT NOT NULL
)"""

class EventStore:
    """SQLite append-only event store. Existing event rows are never updated or deleted."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(_SCHEMA)
            db.commit()

    def read_all(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT event_id,event_schema,event_type,occurred_at,round_id,actor_kind,actor_id,sequence,payload_json,causation_id,correlation_id FROM events ORDER BY sequence").fetchall()
        keys = ["event_id","event_schema","event_type","occurred_at","round_id","actor_kind","actor_id","sequence","payload_json","causation_id","correlation_id"]
        result=[]
        for row in rows:
            item=dict(zip(keys,row)); item["actor"]={"kind":item.pop("actor_kind"),"id":item.pop("actor_id")}; item["payload"]=json.loads(item.pop("payload_json")); result.append(item)
        return result

    def append(self, event_type: str, round_id: str, actor: str, payload: dict[str, Any], event_id: str | None = None) -> dict[str, Any]:
        event_id = event_id or f"evt_{self._next_sequence():06d}"
        sequence = self._next_sequence()
        event = {"event_schema":"factor.event.v1","event_id":event_id,"event_type":event_type,"occurred_at":datetime.now(timezone.utc).isoformat(),"round_id":round_id,"actor":{"kind":"runtime","id":actor},"sequence":sequence,"payload":payload,"causation_id":None,"correlation_id":f"round_{round_id}"}
        try:
            with sqlite3.connect(self.path) as db:
                db.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?)", (event_id,event["event_schema"],event_type,event["occurred_at"],round_id,"runtime",actor,sequence,json.dumps(payload,sort_keys=True),None,event["correlation_id"]))
                db.commit()
        except sqlite3.IntegrityError as exc:
            raise FileExistsError(f"event already exists or sequence conflict: {event_id}") from exc
        return event

    def _next_sequence(self) -> int:
        with sqlite3.connect(self.path) as db:
            return int(db.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM events").fetchone()[0])

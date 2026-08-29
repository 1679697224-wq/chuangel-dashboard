"""SQLite 持久层；正式 KPI 只读取已发布版本绑定的数据。"""

import json
from functools import wraps
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, Iterable, List, Optional

from .auth import hash_password


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
  username TEXT PRIMARY KEY,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  scopes_json TEXT NOT NULL,
  data_scope_json TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  username TEXT NOT NULL REFERENCES users(username),
  expires_at INTEGER NOT NULL,
  revoked_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS review_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  source_system TEXT NOT NULL,
  source_key TEXT NOT NULL,
  raw_value_json TEXT NOT NULL,
  suggestion_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'UNCONFIRMED',
  confidence REAL,
  confirmed_by TEXT,
  confirmed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(entity_type, source_system, source_key)
);
CREATE TABLE IF NOT EXISTS governance_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  version_type TEXT NOT NULL,
  version_name TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'DRAFT',
  payload_json TEXT NOT NULL,
  created_by TEXT NOT NULL,
  confirmed_by TEXT,
  published_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT
);
CREATE TABLE IF NOT EXISTS metric_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  metric_code TEXT NOT NULL,
  scope_key TEXT NOT NULL,
  metric_value TEXT,
  unit TEXT NOT NULL,
  caliber TEXT NOT NULL,
  source_system TEXT NOT NULL,
  source_record_count INTEGER NOT NULL DEFAULT 0,
  version_id INTEGER NOT NULL REFERENCES governance_versions(id),
  calculated_at TEXT NOT NULL,
  conflict INTEGER NOT NULL DEFAULT 0,
  UNIQUE(metric_code, scope_key, version_id)
);
CREATE TABLE IF NOT EXISTS pipeline_records (
  trace_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  source_system TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  raw_json TEXT NOT NULL,
  cleaned_json TEXT NOT NULL,
  mapped_json TEXT NOT NULL,
  mapping_version TEXT,
  extracted_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


ALL_ADMIN_SCOPES = [
    "dashboard:view",
    "review:view",
    "review:confirm",
    "review:publish",
    "sandbox:view",
    "api:inspect",
]


def synchronized(method):
    """串行化同一 SQLite 连接的跨请求访问，避免浏览器并发请求竞争。"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.connection = sqlite3.connect(str(self.path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    @synchronized
    def close(self) -> None:
        self.connection.close()

    @synchronized
    def bootstrap_admin(self, username: str, password: str) -> None:
        if not username or not password:
            return
        existing = self.connection.execute(
            "SELECT username FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            return
        self.connection.execute(
            "INSERT INTO users(username,password_hash,role,scopes_json,data_scope_json) "
            "VALUES(?,?,?,?,?)",
            (
                username,
                hash_password(password),
                "system_admin",
                json.dumps(ALL_ADMIN_SCOPES),
                json.dumps({"type": "all", "values": []}),
            ),
        )
        self.connection.commit()

    @synchronized
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        row = self.connection.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["scopes"] = json.loads(result.pop("scopes_json"))
        result["data_scope"] = json.loads(result.pop("data_scope_json"))
        return result

    @synchronized
    def save_session(self, session_id: str, username: str, expires_at: int) -> None:
        self.connection.execute(
            "INSERT INTO sessions(session_id,username,expires_at) VALUES(?,?,?)",
            (session_id, username, expires_at),
        )
        self.connection.commit()

    @synchronized
    def session_active(self, session_id: str, username: str, now: int) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM sessions WHERE session_id=? AND username=? "
            "AND expires_at>? AND revoked_at IS NULL",
            (session_id, username, now),
        ).fetchone()
        return bool(row)

    @synchronized
    def revoke_session(self, session_id: str) -> None:
        self.connection.execute(
            "UPDATE sessions SET revoked_at=CURRENT_TIMESTAMP WHERE session_id=?",
            (session_id,),
        )
        self.connection.commit()

    @synchronized
    def list_review_items(
        self, entity_type: str = "", status: str = ""
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if entity_type:
            clauses.append("entity_type = ?")
            params.append(entity_type)
        if status:
            clauses.append("status = ?")
            params.append(status)
        sql = "SELECT * FROM review_items"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id"
        rows = self.connection.execute(sql, params).fetchall()
        return [self._decode_review_row(row) for row in rows]

    @staticmethod
    def _decode_review_row(row: sqlite3.Row) -> Dict[str, Any]:
        result = dict(row)
        result["raw_value"] = json.loads(result.pop("raw_value_json"))
        result["suggestion"] = json.loads(result.pop("suggestion_json"))
        return result

    @synchronized
    def upsert_review_item(
        self,
        entity_type: str,
        source_system: str,
        source_key: str,
        raw_value: Dict[str, Any],
        suggestion: Dict[str, Any],
        confidence: Optional[float],
    ) -> int:
        self.connection.execute(
            "INSERT INTO review_items(entity_type,source_system,source_key,raw_value_json,"
            "suggestion_json,confidence) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(entity_type,source_system,source_key) DO UPDATE SET "
            "raw_value_json=excluded.raw_value_json,suggestion_json=excluded.suggestion_json,"
            "confidence=excluded.confidence,updated_at=CURRENT_TIMESTAMP",
            (
                entity_type,
                source_system,
                source_key,
                json.dumps(raw_value, ensure_ascii=False),
                json.dumps(suggestion, ensure_ascii=False),
                confidence,
            ),
        )
        row = self.connection.execute(
            "SELECT id FROM review_items WHERE entity_type=? AND source_system=? AND source_key=?",
            (entity_type, source_system, source_key),
        ).fetchone()
        self.connection.commit()
        return int(row["id"])

    @synchronized
    def create_version(
        self,
        version_type: str,
        version_name: str,
        item_ids: Iterable[int],
        actor: str,
        publish: bool,
    ) -> Dict[str, Any]:
        ids = [int(value) for value in item_ids]
        if not ids:
            raise ValueError("至少选择一个复核项")
        placeholders = ",".join("?" for _ in ids)
        rows = self.connection.execute(
            "SELECT * FROM review_items WHERE id IN ({})".format(placeholders), ids
        ).fetchall()
        if len(rows) != len(ids):
            raise ValueError("存在无效复核项")
        invalid = [row["id"] for row in rows if row["entity_type"] != version_type]
        if invalid:
            raise ValueError("复核项类型与版本类型不一致")
        payload = [self._decode_review_row(row) for row in rows]
        status = "PUBLISHED" if publish else "DRAFT"
        with self.connection:
            if publish:
                self.connection.execute(
                    "UPDATE governance_versions SET status='SUPERSEDED' "
                    "WHERE version_type=? AND status='PUBLISHED'",
                    (version_type,),
                )
            cursor = self.connection.execute(
                "INSERT INTO governance_versions(version_type,version_name,status,payload_json,"
                "created_by,confirmed_by,published_by,published_at) "
                "VALUES(?,?,?,?,?,?,?,CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END)",
                (
                    version_type,
                    version_name,
                    status,
                    json.dumps(payload, ensure_ascii=False),
                    actor,
                    actor,
                    actor if publish else None,
                    1 if publish else 0,
                ),
            )
            self.connection.execute(
                "UPDATE review_items SET status='CONFIRMED',confirmed_by=?,"
                "confirmed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP "
                "WHERE id IN ({})".format(placeholders),
                [actor] + ids,
            )
            self.audit(
                actor,
                "review.publish" if publish else "review.confirm",
                "governance_version",
                str(cursor.lastrowid),
                {"version_name": version_name, "item_ids": ids},
                commit=False,
            )
        return self.get_version(int(cursor.lastrowid))

    @synchronized
    def publish_version(self, version_id: int, actor: str) -> Dict[str, Any]:
        version = self.get_version(version_id)
        if not version:
            raise ValueError("版本不存在")
        if version["status"] != "DRAFT":
            raise ValueError("只有 DRAFT 版本可以发布")
        with self.connection:
            self.connection.execute(
                "UPDATE governance_versions SET status='SUPERSEDED' "
                "WHERE version_type=? AND status='PUBLISHED'",
                (version["version_type"],),
            )
            self.connection.execute(
                "UPDATE governance_versions SET status='PUBLISHED',published_by=?,"
                "published_at=CURRENT_TIMESTAMP WHERE id=?",
                (actor, version_id),
            )
            self.audit(
                actor,
                "review.publish",
                "governance_version",
                str(version_id),
                {"version_name": version["version_name"]},
                commit=False,
            )
        return self.get_version(version_id)

    @synchronized
    def get_version(self, version_id: int) -> Optional[Dict[str, Any]]:
        row = self.connection.execute(
            "SELECT * FROM governance_versions WHERE id=?", (version_id,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        return result

    @synchronized
    def list_versions(self) -> List[Dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM governance_versions ORDER BY id DESC"
        ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            results.append(item)
        return results

    @synchronized
    def published_payload(self, version_type: str) -> List[Dict[str, Any]]:
        row = self.connection.execute(
            "SELECT payload_json FROM governance_versions "
            "WHERE version_type=? AND status='PUBLISHED' ORDER BY id DESC LIMIT 1",
            (version_type,),
        ).fetchone()
        return json.loads(row["payload_json"]) if row else []

    @synchronized
    def audit(
        self,
        actor: str,
        action: str,
        target_type: str,
        target_id: Optional[str],
        detail: Dict[str, Any],
        commit: bool = True,
    ) -> None:
        self.connection.execute(
            "INSERT INTO audit_log(actor,action,target_type,target_id,detail_json) "
            "VALUES(?,?,?,?,?)",
            (actor, action, target_type, target_id, json.dumps(detail, ensure_ascii=False)),
        )
        if commit:
            self.connection.commit()

    @synchronized
    def audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["detail"] = json.loads(item.pop("detail_json"))
            results.append(item)
        return results

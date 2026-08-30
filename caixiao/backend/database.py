"""SQLite 持久层；正式 KPI 只读取已发布版本绑定的数据。"""

import json
from functools import wraps
from pathlib import Path
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

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
  raw_code TEXT NOT NULL DEFAULT '',
  raw_name TEXT NOT NULL DEFAULT '',
  history_mapping_json TEXT NOT NULL DEFAULT '[]',
  suggested_display_name TEXT NOT NULL DEFAULT '',
  display_name TEXT NOT NULL DEFAULT '',
  business_unit TEXT NOT NULL DEFAULT '',
  channel TEXT NOT NULL DEFAULT '',
  store_shop TEXT NOT NULL DEFAULT '',
  inventory_class TEXT NOT NULL DEFAULT '',
  decision_json TEXT NOT NULL DEFAULT '{}',
  version_name TEXT NOT NULL DEFAULT '',
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
  before_json TEXT NOT NULL DEFAULT '[]',
  after_json TEXT NOT NULL DEFAULT '[]',
  reason TEXT NOT NULL DEFAULT '',
  affected_metrics_json TEXT NOT NULL DEFAULT '[]',
  created_by TEXT NOT NULL,
  confirmed_by TEXT,
  confirmed_at TEXT,
  published_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT
);
CREATE TABLE IF NOT EXISTS sales_facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_system TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  trade_no TEXT NOT NULL,
  line_id TEXT NOT NULL,
  create_time TEXT,
  pay_time TEXT,
  audit_time TEXT,
  consign_time TEXT,
  complete_time TEXT,
  modified_time TEXT,
  trade_status TEXT NOT NULL,
  quantity REAL NOT NULL,
  payment REAL NOT NULL,
  warehouse_raw_name TEXT NOT NULL,
  channel_raw_name TEXT NOT NULL,
  store_raw_name TEXT NOT NULL DEFAULT '',
  goods_no TEXT NOT NULL,
  sku_raw TEXT NOT NULL,
  source_api TEXT NOT NULL,
  raw_json_reference TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  synced_at TEXT NOT NULL,
  sync_job_id TEXT NOT NULL,
  UNIQUE(source_system, trade_no, line_id)
);
CREATE INDEX IF NOT EXISTS idx_sales_facts_pay_time ON sales_facts(pay_time);
CREATE INDEX IF NOT EXISTS idx_sales_facts_modified_time ON sales_facts(modified_time);
CREATE INDEX IF NOT EXISTS idx_sales_facts_status ON sales_facts(trade_status);
CREATE TABLE IF NOT EXISTS inventory_facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_system TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  snapshot_time TEXT NOT NULL,
  warehouse_raw_name TEXT NOT NULL,
  sku_raw TEXT NOT NULL,
  quantity REAL NOT NULL,
  amount REAL NOT NULL,
  source_api TEXT NOT NULL,
  raw_json_reference TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  synced_at TEXT NOT NULL,
  sync_job_id TEXT NOT NULL,
  UNIQUE(source_system, source_record_id, snapshot_time)
);
CREATE INDEX IF NOT EXISTS idx_inventory_facts_snapshot ON inventory_facts(snapshot_time);
CREATE TABLE IF NOT EXISTS inventory_aging_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_system TEXT NOT NULL,
  source_record_id TEXT NOT NULL,
  sku_raw TEXT NOT NULL,
  warehouse_raw_name TEXT NOT NULL,
  age_days INTEGER NOT NULL,
  quantity REAL NOT NULL,
  amount REAL NOT NULL,
  source_reference TEXT NOT NULL,
  caliber TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  synced_at TEXT NOT NULL,
  sync_job_id TEXT NOT NULL,
  confirmation_status TEXT NOT NULL DEFAULT 'UNCONFIRMED',
  UNIQUE(source_system, source_record_id, sync_job_id)
);
CREATE INDEX IF NOT EXISTS idx_inventory_aging_days ON inventory_aging_records(age_days);
CREATE TABLE IF NOT EXISTS action_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action_code TEXT NOT NULL UNIQUE,
  action_type TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  business_unit TEXT NOT NULL DEFAULT '',
  channel TEXT NOT NULL DEFAULT '',
  store_shop TEXT NOT NULL DEFAULT '',
  sku TEXT NOT NULL DEFAULT '',
  source_reference TEXT NOT NULL DEFAULT '',
  reason TEXT NOT NULL DEFAULT '',
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sync_state (
  domain TEXT PRIMARY KEY,
  strategy TEXT NOT NULL,
  cursor_field TEXT NOT NULL,
  cursor_value TEXT,
  lookback_days INTEGER NOT NULL DEFAULT 0,
  last_job_id TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
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
        self._migrate_governance_versions()
        self._migrate_review_items()
        self.connection.commit()

    def _migrate_governance_versions(self) -> None:
        """兼容V1本地数据库；不修改任何业务值。"""
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(governance_versions)").fetchall()
        }
        additions = {
            "before_json": "TEXT NOT NULL DEFAULT '[]'",
            "after_json": "TEXT NOT NULL DEFAULT '[]'",
            "reason": "TEXT NOT NULL DEFAULT ''",
            "affected_metrics_json": "TEXT NOT NULL DEFAULT '[]'",
            "confirmed_at": "TEXT",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.connection.execute(
                    "ALTER TABLE governance_versions ADD COLUMN {} {}".format(name, definition)
                )

    def _migrate_review_items(self) -> None:
        """为旧本地库补齐只读原始字段和人工展示字段。"""
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(review_items)").fetchall()
        }
        additions = {
            "raw_code": "TEXT NOT NULL DEFAULT ''",
            "raw_name": "TEXT NOT NULL DEFAULT ''",
            "history_mapping_json": "TEXT NOT NULL DEFAULT '[]'",
            "suggested_display_name": "TEXT NOT NULL DEFAULT ''",
            "display_name": "TEXT NOT NULL DEFAULT ''",
            "business_unit": "TEXT NOT NULL DEFAULT ''",
            "channel": "TEXT NOT NULL DEFAULT ''",
            "store_shop": "TEXT NOT NULL DEFAULT ''",
            "inventory_class": "TEXT NOT NULL DEFAULT ''",
            "decision_json": "TEXT NOT NULL DEFAULT '{}'",
            "version_name": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                self.connection.execute(
                    "ALTER TABLE review_items ADD COLUMN {} {}".format(name, definition)
                )
        rows = self.connection.execute(
            "SELECT id,source_key,raw_value_json,suggestion_json,raw_code,raw_name,"
            "suggested_display_name FROM review_items"
        ).fetchall()
        for row in rows:
            raw = json.loads(row["raw_value_json"] or "{}")
            suggestion = json.loads(row["suggestion_json"] or "{}")
            raw_code = row["raw_code"] or row["source_key"]
            raw_name = row["raw_name"] or str(raw.get("name") or raw_code)
            suggested = row["suggested_display_name"] or str(
                suggestion.get("display_name") or suggestion.get("canonical") or suggestion.get("name") or ""
            )
            self.connection.execute(
                "UPDATE review_items SET raw_code=?,raw_name=?,suggested_display_name=? WHERE id=?",
                (raw_code, raw_name, suggested, row["id"]),
            )

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
        result["history_mapping"] = json.loads(result.pop("history_mapping_json"))
        result["decision"] = json.loads(result.pop("decision_json"))
        result["store/shop"] = result["store_shop"]
        result["version"] = result["version_name"]
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
        raw_code: str = "",
        raw_name: str = "",
        history_mapping: Any = None,
        suggested_display_name: str = "",
    ) -> int:
        immutable_code = str(raw_code or source_key).strip()
        immutable_name = str(raw_name or raw_value.get("name") or immutable_code).strip()
        immutable_history = [] if history_mapping is None else history_mapping
        if not immutable_code or not immutable_name:
            raise ValueError("raw_code 和 raw_name 必填")
        suggested_name = str(
            suggested_display_name
            or suggestion.get("display_name")
            or suggestion.get("canonical")
            or suggestion.get("name")
            or ""
        ).strip()
        existing = self.connection.execute(
            "SELECT * FROM review_items WHERE entity_type=? AND source_system=? AND source_key=?",
            (entity_type, source_system, source_key),
        ).fetchone()
        if existing:
            existing_history = json.loads(existing["history_mapping_json"] or "[]")
            if (
                existing["raw_code"] != immutable_code
                or existing["raw_name"] != immutable_name
                or existing_history != immutable_history
            ):
                raise ValueError("raw_code、raw_name 和 history_mapping 创建后永久只读")
            self.connection.execute(
                "UPDATE review_items SET suggestion_json=?,suggested_display_name=?,"
                "confidence=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (
                    json.dumps(suggestion, ensure_ascii=False),
                    suggested_name,
                    confidence,
                    existing["id"],
                ),
            )
            item_id = int(existing["id"])
        else:
            cursor = self.connection.execute(
                "INSERT INTO review_items(entity_type,source_system,source_key,raw_value_json,"
                "suggestion_json,raw_code,raw_name,history_mapping_json,suggested_display_name,confidence) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    entity_type,
                    source_system,
                    source_key,
                    json.dumps(raw_value, ensure_ascii=False),
                    json.dumps(suggestion, ensure_ascii=False),
                    immutable_code,
                    immutable_name,
                    json.dumps(immutable_history, ensure_ascii=False),
                    suggested_name,
                    confidence,
                ),
            )
            item_id = int(cursor.lastrowid)
        self.connection.commit()
        return item_id

    @synchronized
    def update_review_decisions(
        self, item_ids: Iterable[int], decisions: Iterable[Mapping[str, Any]]
    ) -> None:
        ids = [int(value) for value in item_ids]
        indexed = {int(item.get("item_id", 0)): dict(item) for item in decisions}
        forbidden = {"raw_code", "raw_name", "history_mapping", "raw_value", "source_key"}
        allowed = {
            "item_id", "display_name", "business_unit", "channel", "store_shop",
            "store/shop", "inventory_class", "value",
        }
        for item_id in ids:
            decision = indexed.get(item_id, {})
            if forbidden.intersection(decision):
                raise ValueError("raw_code、raw_name 和 history_mapping 永久只读")
            unknown = set(decision) - allowed
            if unknown:
                raise ValueError("决策包含不支持字段：{}".format(",".join(sorted(unknown))))
            row = self.connection.execute(
                "SELECT entity_type,suggested_display_name,suggestion_json FROM review_items WHERE id=?",
                (item_id,),
            ).fetchone()
            if not row:
                raise ValueError("存在无效复核项")
            display_name = str(
                decision.get("display_name") or row["suggested_display_name"] or ""
            ).strip()
            if row["entity_type"] in {"warehouse_mapping", "channel_mapping", "sku_mapping"} and not display_name:
                raise ValueError("映射项必须由 PO 确认 display_name")
            value = decision.get("value")
            if value is None:
                value = json.loads(row["suggestion_json"] or "{}")
            if not isinstance(value, dict):
                raise ValueError("value 必须是对象")
            self.connection.execute(
                "UPDATE review_items SET display_name=?,business_unit=?,channel=?,store_shop=?,"
                "inventory_class=?,decision_json=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (
                    display_name,
                    str(decision.get("business_unit") or "").strip(),
                    str(decision.get("channel") or "").strip(),
                    str(decision.get("store_shop") or decision.get("store/shop") or "").strip(),
                    str(decision.get("inventory_class") or value.get("inventory_class") or "").strip(),
                    json.dumps(value, ensure_ascii=False),
                    item_id,
                ),
            )
        self.connection.commit()

    @staticmethod
    def _review_value(row: Mapping[str, Any]) -> Dict[str, Any]:
        value = dict(row.get("decision") or row.get("suggestion") or {})
        if row["entity_type"] in {"warehouse_mapping", "channel_mapping", "sku_mapping"}:
            value.update(
                {
                    "canonical": row["display_name"],
                    "display_name": row["display_name"],
                    "business_unit": row["business_unit"],
                    "channel": row["channel"],
                    "store_shop": row["store_shop"],
                    "inventory_class": row["inventory_class"],
                }
            )
        return value

    @synchronized
    def create_version(
        self,
        version_type: str,
        version_name: str,
        item_ids: Iterable[int],
        actor: str,
        publish: bool,
        reason: str,
        affected_metrics: Iterable[str],
        decisions: Iterable[Mapping[str, Any]] = (),
    ) -> Dict[str, Any]:
        ids = [int(value) for value in item_ids]
        if not ids:
            raise ValueError("至少选择一个复核项")
        self.update_review_decisions(ids, decisions)
        placeholders = ",".join("?" for _ in ids)
        rows = self.connection.execute(
            "SELECT * FROM review_items WHERE id IN ({})".format(placeholders), ids
        ).fetchall()
        if len(rows) != len(ids):
            raise ValueError("存在无效复核项")
        invalid = [row["id"] for row in rows if row["entity_type"] != version_type]
        if invalid:
            raise ValueError("复核项类型与版本类型不一致")
        decoded_rows = [self._decode_review_row(row) for row in rows]
        payload = [
            {
                "source_key": row["source_key"],
                "source_system": row["source_system"],
                "raw_code": row["raw_code"],
                "raw_name": row["raw_name"],
                "history_mapping": row["history_mapping"],
                "before": row["history_mapping"],
                "value": self._review_value(row),
                "review_item_id": row["id"],
            }
            for row in decoded_rows
        ]
        previous = self.published_version(version_type)
        before = previous["after"] if previous else []
        metrics = sorted({str(value) for value in affected_metrics if str(value)})
        status = "PUBLISHED" if publish else "DRAFT"
        event_time = datetime.now(timezone.utc).isoformat()
        with self.connection:
            if publish:
                self.connection.execute(
                    "UPDATE governance_versions SET status='SUPERSEDED' "
                    "WHERE version_type=? AND status='PUBLISHED'",
                    (version_type,),
                )
            cursor = self.connection.execute(
                "INSERT INTO governance_versions(version_type,version_name,status,payload_json,"
                "before_json,after_json,reason,affected_metrics_json,created_by,confirmed_by,"
                "confirmed_at,published_by,published_at) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    version_type,
                    version_name,
                    status,
                    json.dumps(payload, ensure_ascii=False),
                    json.dumps(before, ensure_ascii=False),
                    json.dumps(payload, ensure_ascii=False),
                    reason,
                    json.dumps(metrics, ensure_ascii=False),
                    actor,
                    actor,
                    event_time,
                    actor if publish else None,
                    event_time if publish else None,
                ),
            )
            self.connection.execute(
                "UPDATE review_items SET status='CONFIRMED',version_name=?,confirmed_by=?,"
                "confirmed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP "
                "WHERE id IN ({})".format(placeholders),
                [version_name, actor] + ids,
            )
            self.audit(
                actor,
                "review.publish" if publish else "review.confirm",
                "governance_version",
                str(cursor.lastrowid),
                {
                    "version_name": version_name,
                    "before": before,
                    "after": payload,
                    "reason": reason,
                    "affected_metrics": metrics,
                    "confirmed_by": actor,
                    "confirmed_at": event_time,
                    "published_by": actor if publish else None,
                    "published_at": event_time if publish else None,
                },
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
        event_time = datetime.now(timezone.utc).isoformat()
        with self.connection:
            self.connection.execute(
                "UPDATE governance_versions SET status='SUPERSEDED' "
                "WHERE version_type=? AND status='PUBLISHED'",
                (version["version_type"],),
            )
            self.connection.execute(
                "UPDATE governance_versions SET status='PUBLISHED',published_by=?,"
                "published_at=? WHERE id=?",
                (actor, event_time, version_id),
            )
            self.audit(
                actor,
                "review.publish",
                "governance_version",
                str(version_id),
                {
                    "version_name": version["version_name"],
                    "before": version["before"],
                    "after": version["after"],
                    "reason": version["reason"],
                    "affected_metrics": version["affected_metrics"],
                    "confirmed_by": version["confirmed_by"],
                    "confirmed_at": version["confirmed_at"],
                    "published_by": actor,
                    "published_at": event_time,
                },
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
        result["before"] = json.loads(result.pop("before_json"))
        result["after"] = json.loads(result.pop("after_json"))
        result["affected_metrics"] = json.loads(result.pop("affected_metrics_json"))
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
            item["before"] = json.loads(item.pop("before_json"))
            item["after"] = json.loads(item.pop("after_json"))
            item["affected_metrics"] = json.loads(item.pop("affected_metrics_json"))
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
    def published_version(self, version_type: str) -> Optional[Dict[str, Any]]:
        row = self.connection.execute(
            "SELECT id FROM governance_versions WHERE version_type=? AND status='PUBLISHED' "
            "ORDER BY id DESC LIMIT 1",
            (version_type,),
        ).fetchone()
        return self.get_version(int(row["id"])) if row else None

    @synchronized
    def upsert_sales_facts(self, records: Iterable[Dict[str, Any]]) -> int:
        fields = (
            "source_system", "source_record_id", "trade_no", "line_id", "create_time",
            "pay_time", "audit_time", "consign_time", "complete_time", "modified_time",
            "trade_status", "quantity", "payment", "warehouse_raw_name", "channel_raw_name",
            "store_raw_name", "goods_no", "sku_raw", "source_api", "raw_json_reference",
            "extracted_at", "synced_at", "sync_job_id",
        )
        values = [tuple(record.get(field, "") for field in fields) for record in records]
        if not values:
            return 0
        updates = ",".join(
            "{0}=excluded.{0}".format(field)
            for field in fields
            if field not in {"source_system", "trade_no", "line_id"}
        )
        with self.connection:
            self.connection.executemany(
                "INSERT INTO sales_facts({}) VALUES({}) "
                "ON CONFLICT(source_system,trade_no,line_id) DO UPDATE SET {}".format(
                    ",".join(fields), ",".join("?" for _ in fields), updates
                ),
                values,
            )
        return len(values)

    @synchronized
    def list_sales_facts(self, sku_raw: str = "") -> List[Dict[str, Any]]:
        sql = "SELECT * FROM sales_facts"
        params: List[Any] = []
        if sku_raw:
            sql += " WHERE sku_raw=?"
            params.append(sku_raw)
        sql += " ORDER BY pay_time,trade_no,line_id"
        return [dict(row) for row in self.connection.execute(sql, params).fetchall()]

    @synchronized
    def upsert_inventory_facts(self, records: Iterable[Dict[str, Any]]) -> int:
        fields = (
            "source_system", "source_record_id", "snapshot_time", "warehouse_raw_name",
            "sku_raw", "quantity", "amount", "source_api", "raw_json_reference",
            "extracted_at", "synced_at", "sync_job_id",
        )
        values = [tuple(record.get(field, "") for field in fields) for record in records]
        if not values:
            return 0
        updates = ",".join(
            "{0}=excluded.{0}".format(field)
            for field in fields
            if field not in {"source_system", "source_record_id", "snapshot_time"}
        )
        with self.connection:
            self.connection.executemany(
                "INSERT INTO inventory_facts({}) VALUES({}) "
                "ON CONFLICT(source_system,source_record_id,snapshot_time) DO UPDATE SET {}".format(
                    ",".join(fields), ",".join("?" for _ in fields), updates
                ),
                values,
            )
        return len(values)

    @synchronized
    def list_inventory_facts(self, sku_raw: str = "") -> List[Dict[str, Any]]:
        sql = "SELECT * FROM inventory_facts"
        params: List[Any] = []
        if sku_raw:
            sql += " WHERE sku_raw=?"
            params.append(sku_raw)
        sql += " ORDER BY snapshot_time,warehouse_raw_name,sku_raw"
        return [dict(row) for row in self.connection.execute(sql, params).fetchall()]

    @synchronized
    def upsert_inventory_aging_records(self, records: Iterable[Dict[str, Any]]) -> int:
        fields = (
            "source_system", "source_record_id", "sku_raw", "warehouse_raw_name",
            "age_days", "quantity", "amount", "source_reference", "caliber",
            "extracted_at", "synced_at", "sync_job_id", "confirmation_status",
        )
        values = [tuple(record.get(field, "") for field in fields) for record in records]
        if not values:
            return 0
        updates = ",".join(
            "{0}=excluded.{0}".format(field)
            for field in fields
            if field not in {"source_system", "source_record_id", "sync_job_id"}
        )
        with self.connection:
            self.connection.executemany(
                "INSERT INTO inventory_aging_records({}) VALUES({}) "
                "ON CONFLICT(source_system,source_record_id,sync_job_id) DO UPDATE SET {}".format(
                    ",".join(fields), ",".join("?" for _ in fields), updates
                ),
                values,
            )
        return len(values)

    @synchronized
    def list_inventory_aging_records(self) -> List[Dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM inventory_aging_records ORDER BY age_days,sku_raw,warehouse_raw_name"
        ).fetchall()
        return [dict(row) for row in rows]

    @synchronized
    def upsert_action(self, record: Mapping[str, Any]) -> int:
        fields = (
            "action_code", "action_type", "title", "status", "business_unit", "channel",
            "store_shop", "sku", "source_reference", "reason", "created_by",
        )
        values = tuple(record.get(field, "") for field in fields)
        updates = ",".join(
            "{0}=excluded.{0}".format(field)
            for field in fields
            if field not in {"action_code", "created_by"}
        )
        self.connection.execute(
            "INSERT INTO action_ledger({}) VALUES({}) ON CONFLICT(action_code) DO UPDATE SET {},"
            "updated_at=CURRENT_TIMESTAMP".format(
                ",".join(fields), ",".join("?" for _ in fields), updates
            ),
            values,
        )
        row = self.connection.execute(
            "SELECT id FROM action_ledger WHERE action_code=?", (record["action_code"],)
        ).fetchone()
        self.connection.commit()
        return int(row["id"])

    @synchronized
    def list_actions(self, status: str = "") -> List[Dict[str, Any]]:
        sql = "SELECT * FROM action_ledger"
        params: List[Any] = []
        if status:
            sql += " WHERE status=?"
            params.append(status)
        sql += " ORDER BY updated_at DESC,id DESC"
        return [dict(row) for row in self.connection.execute(sql, params).fetchall()]

    @synchronized
    def save_sync_state(self, state: Dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO sync_state(domain,strategy,cursor_field,cursor_value,lookback_days,last_job_id) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(domain) DO UPDATE SET strategy=excluded.strategy,"
            "cursor_field=excluded.cursor_field,cursor_value=excluded.cursor_value,"
            "lookback_days=excluded.lookback_days,last_job_id=excluded.last_job_id,"
            "updated_at=CURRENT_TIMESTAMP",
            (
                state["domain"], state["strategy"], state["cursor_field"],
                state.get("cursor_value"), int(state.get("lookback_days", 0)),
                state.get("last_job_id"),
            ),
        )
        self.connection.commit()

    @synchronized
    def get_sync_state(self, domain: str) -> Optional[Dict[str, Any]]:
        row = self.connection.execute(
            "SELECT * FROM sync_state WHERE domain=?", (domain,)
        ).fetchone()
        return dict(row) if row else None

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

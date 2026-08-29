"""既有快照只读检查器；结果永远标记为 Sandbox 快照验证。"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


ALLOWED_SNAPSHOT_FILES = {
    "sales": ("sales_agg.json", "api_agg_828.json", "agg_summary.json"),
    "inventory": ("inventory_agg.json", "inventory_export.json", "agg_summary.json"),
}


class SnapshotAdapter:
    def __init__(self, directory: str):
        self.directory = Path(directory).resolve() if directory else None

    def inspect(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "mode": "sandbox",
            "label": "快照验证",
            "formal_kpi_enabled": False,
            "configured": bool(self.directory),
            "files": [],
        }
        if not self.directory or not self.directory.is_dir():
            result["status"] = "待接入"
            return result
        allowed_names = {name for names in ALLOWED_SNAPSHOT_FILES.values() for name in names}
        for path in sorted(self.directory.iterdir()):
            if path.name not in allowed_names or not path.is_file():
                continue
            raw = path.read_bytes()
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                result["files"].append(
                    {"name": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "valid": False}
                )
                continue
            if isinstance(parsed, list):
                shape = {"type": "list", "records": len(parsed)}
                keys: List[str] = sorted(
                    {str(key) for row in parsed[:50] if isinstance(row, dict) for key in row.keys()}
                )
            elif isinstance(parsed, dict):
                shape = {"type": "object", "records": len(parsed)}
                keys = sorted(str(key) for key in parsed.keys())
            else:
                shape = {"type": type(parsed).__name__, "records": 1}
                keys = []
            result["files"].append(
                {
                    "name": path.name,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "valid": True,
                    "shape": shape,
                    "top_level_fields": keys,
                    "data_values_exposed": False,
                }
            )
        result["status"] = "快照验证" if result["files"] else "待接入"
        return result

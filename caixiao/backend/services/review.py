"""人工复核、版本确认和发布门禁。"""

from typing import Any, Dict, Iterable, Mapping

from ..database import Database
from ..models import VERSION_PREFIXES


class ReviewService:
    def __init__(self, database: Database):
        self.database = database

    def confirm(
        self,
        version_type: str,
        version_name: str,
        item_ids: Iterable[int],
        actor: str,
        publish: bool = False,
        reason: str = "",
        affected_metrics: Iterable[str] = (),
        decisions: Iterable[Mapping[str, Any]] = (),
    ) -> Dict[str, Any]:
        expected = VERSION_PREFIXES.get(version_type)
        if not expected:
            raise ValueError("不支持的版本类型")
        if not version_name.startswith(expected):
            raise ValueError("版本名称必须以 {} 开头".format(expected))
        suffix = version_name[len(expected) :]
        if not suffix.isdigit() or int(suffix) < 1:
            raise ValueError("版本号必须是正整数")
        if not str(reason).strip():
            raise ValueError("人工确认必须填写 reason")
        return self.database.create_version(
            version_type,
            version_name,
            item_ids,
            actor,
            publish,
            str(reason).strip(),
            affected_metrics,
            decisions,
        )

    def publish(self, version_id: int, actor: str) -> Dict[str, Any]:
        return self.database.publish_version(version_id, actor)

    def formal_dimensions(self, version_type: str):
        """只返回已发布版本中的人工确认项。"""
        return self.database.published_payload(version_type)

    def is_formal_eligible(self, required_types: Iterable[str]) -> Dict[str, Any]:
        missing = [
            version_type
            for version_type in required_types
            if not self.database.published_payload(version_type)
        ]
        return {
            "eligible": not missing,
            "missing_published_versions": missing,
            "gate": "人工确认并发布后方可进入正式经营 KPI",
        }

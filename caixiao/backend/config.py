"""环境配置。所有真实凭据只从进程环境读取。"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, Tuple


ROOT_DIR = Path(__file__).resolve().parents[2]


def _csv(name: str, default: str) -> Tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("{} 必须为 true 或 false".format(name))


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    db_path: Path
    allowed_origins: Tuple[str, ...]
    token_secret: str
    bootstrap_user: str
    bootstrap_password: str
    session_ttl_seconds: int
    sandbox_snapshot_dir: str
    jky: Dict[str, str]
    demo_mode: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        db_value = os.getenv("CAIXIAO_DB_PATH", "caixiao/runtime/caixiao.sqlite3")
        db_path = Path(db_value)
        if not db_path.is_absolute():
            db_path = ROOT_DIR / db_path
        return cls(
            host=os.getenv("CAIXIAO_HOST", "127.0.0.1"),
            port=int(os.getenv("CAIXIAO_PORT", "8010")),
            db_path=db_path,
            allowed_origins=_csv(
                "CAIXIAO_ALLOWED_ORIGINS",
                "http://127.0.0.1:8010,http://localhost:8010",
            ),
            token_secret=os.getenv("CAIXIAO_TOKEN_SECRET", ""),
            bootstrap_user=os.getenv("CAIXIAO_BOOTSTRAP_USER", ""),
            bootstrap_password=os.getenv("CAIXIAO_BOOTSTRAP_PASSWORD", ""),
            session_ttl_seconds=int(os.getenv("CAIXIAO_SESSION_TTL_SECONDS", "28800")),
            sandbox_snapshot_dir=os.getenv("CAIXIAO_SANDBOX_SNAPSHOT_DIR", ""),
            jky={
                "base_url": os.getenv("JKY_BASE_URL", ""),
                "app_key": os.getenv("JKY_APP_KEY", ""),
                "app_secret": os.getenv("JKY_APP_SECRET", ""),
                "access_token": os.getenv("JKY_ACCESS_TOKEN", ""),
                "sales_endpoint": os.getenv("JKY_SALES_ENDPOINT", ""),
                "inventory_endpoint": os.getenv("JKY_INVENTORY_ENDPOINT", ""),
                "purchase_endpoint": os.getenv("JKY_PURCHASE_ENDPOINT", ""),
                "transfer_endpoint": os.getenv("JKY_TRANSFER_ENDPOINT", ""),
            },
            demo_mode=_bool("DEMO_MODE", False),
        )

    def validate_for_server(self) -> None:
        if len(self.token_secret) < 32:
            raise ValueError("CAIXIAO_TOKEN_SECRET 必须至少 32 个字符")
        if "*" in self.allowed_origins:
            raise ValueError("CAIXIAO_ALLOWED_ORIGINS 禁止使用通配符 *")
        if bool(self.bootstrap_user) != bool(self.bootstrap_password):
            raise ValueError("初始化账号和密码必须同时提供或同时留空")
        if self.bootstrap_password and len(self.bootstrap_password) < 12:
            raise ValueError("CAIXIAO_BOOTSTRAP_PASSWORD 至少 12 个字符")

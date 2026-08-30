"""旧看板脚本的运行时经营数据入口；仓库内不保存真实金额或数量。"""

import json
import os
from pathlib import Path


ENV_FILE = "CHUANGEL_BUSINESS_DATA_FILE"
ENV_ALLOW_MOCK = "CHUANGEL_ALLOW_MOCK_BUSINESS_DATA"


def load_runtime_business_data():
    path_text = os.environ.get(ENV_FILE, "").strip()
    if not path_text:
        raise RuntimeError("必须通过 {} 注入私有运行时数据文件".format(ENV_FILE))
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError("运行时经营数据文件不存在")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("运行时经营数据必须是JSON对象")
    mode = payload.get("data_mode")
    if mode == "MOCK" and os.environ.get(ENV_ALLOW_MOCK) != "1":
        raise RuntimeError("Mock数据必须明确设置 {}=1".format(ENV_ALLOW_MOCK))
    if mode not in {"RUNTIME_PRIVATE", "MOCK"}:
        raise RuntimeError("data_mode 必须明确为 RUNTIME_PRIVATE 或 MOCK")
    missing = [name for name in ("inv_category", "inv_machine") if name not in payload]
    if missing:
        raise RuntimeError("运行时经营数据缺少必要分区")
    return payload

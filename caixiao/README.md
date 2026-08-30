# 采销经营驾驶舱 V1

本工程与现有总部看板共存，采用 Python 标准库、SQLite 和原生 HTML/CSS/JavaScript，无需安装依赖。当前面向开发与 Review，不是生产版本。

## 本地启动

在仓库根目录执行：

```bash
export CAIXIAO_TOKEN_SECRET='请替换为至少32位随机字符串'
export CAIXIAO_BOOTSTRAP_USER='review-admin'
export CAIXIAO_BOOTSTRAP_PASSWORD='请替换为至少12位本地强密码'
python3 -m caixiao.backend.app
```

访问：`http://127.0.0.1:8010/cx/`。

如需只读检查仓库既有聚合快照，可额外指定：

```bash
export CAIXIAO_SANDBOX_SNAPSHOT_DIR='/绝对路径/吉客云数据'
```

该目录只用于 Sandbox 文件身份和结构验证，不会把快照值写入正式 KPI。

## 页面

| 路径 | 页面 |
|---|---|
| `/cx/` | 采销作战首页 |
| `/cx/sku` | SKU 360 |
| `/cx/inventory-purchase` | 库存&采购全链路 |
| `/cx/apple-policy` | Apple政策经营 |
| `/cx/review-mapping` | 映射与口径复核中心 |
| `/cx/review-api` | 吉客云 API 复核中心 |
| `/cx/sandbox` | Sandbox 差异验证 |

## 数据门禁

`事实数据 → 映射版本 → 口径版本 → 正式 KPI`。待复核、已确认未发布或含未映射事实时均返回“待确认”和缺失清单。当前没有真实吉客云连接，因此不会产生正式经营值。

## 测试

```bash
python3 caixiao/tests/run_with_coverage.py
```

该命令运行完整测试并生成机器可读的 `caixiao/coverage.xml`。完整接口、部署与测试记录见 `caixiao/docs/`。

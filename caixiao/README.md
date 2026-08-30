# 采销经营驾驶舱 V1

本工程与现有总部看板共存，采用 Python 标准库、SQLite 和原生 HTML/CSS/JavaScript，无需安装依赖。当前为可运行、可交互、可人工复核的 V1 框架，不是生产版本。

## 本地启动

在仓库根目录执行：

```bash
export CAIXIAO_TOKEN_SECRET='请替换为至少32位随机字符串'
export CAIXIAO_BOOTSTRAP_USER='review-admin'
export CAIXIAO_BOOTSTRAP_PASSWORD='请替换为至少12位本地强密码'
export DEMO_MODE='false'
python3 -m caixiao.backend.app
```

访问：`http://127.0.0.1:8010/cx/`。

### 演示模式

将 `DEMO_MODE` 改为 `true` 后启动。该模式只读取纯 Mock `DemoAdapter`，页面顶部固定显示“演示数据，仅用于页面及流程验证”，不会连接吉客云、APR、正式事实库或 Sandbox 快照。

```bash
export DEMO_MODE='true'
export CAIXIAO_TOKEN_SECRET='请替换为至少32位本地随机字符串'
export CAIXIAO_BOOTSTRAP_USER='请设置本地演示账号'
export CAIXIAO_BOOTSTRAP_PASSWORD='请设置至少12位本地演示密码'
python3 -m caixiao.backend.app
```

`DEMO_MODE=false` 时，缺少真实事实或已发布版本的字段只显示“待接入/待确认”，不会自动回退到演示数字。

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

三类数据严格隔离：

- `FORMAL`：只允许已确认并发布的真实事实、映射与口径进入正式 KPI；
- `SANDBOX`：只做快照、旧新逻辑与多口径差异验证；
- `DEMO`：只做页面和业务流程演示，任何演示数字都不能进入正式经营视图。

## 测试

```bash
python3 caixiao/tests/run_with_coverage.py
```

该命令运行完整测试并生成机器可读的 `caixiao/coverage.xml`。完整接口、部署与测试记录见 `caixiao/docs/`。

本轮页面、模式、截图、未接入项和人工验收清单见 `caixiao/docs/FRAMEWORK_COMPLETION_V1.md`。

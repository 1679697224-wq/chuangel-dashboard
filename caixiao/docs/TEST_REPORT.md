# 采销经营驾驶舱 V1 测试报告

状态：2026-08-30 最终本地复检通过，待 WorkBuddy 独立 Review。

## 自动测试

- 命令：`python3 -m unittest discover -s caixiao/tests -v`
- 结果：38 项通过，0 失败，0 错误。
- 覆盖范围：认证、配置、吉客云禁用保护、快照白名单、五时间字段、库存关系检查、人工确认/发布版本、正式 KPI 门禁、统一 API、CORS、动作词表、四业务页面。
- 核心领域语句覆盖：610 / 660，92.4%。统计模块为适配器、认证、数据库、模型、数据管线、指标和复核服务；HTTP 传输层另由 API 合同测试覆盖。
- 工具：Python 标准库 `trace`，未安装外部依赖。

## API 与安全检查

- 未登录访问正式指标：HTTP 401。
- 非白名单 Origin 预检：HTTP 403，无 `Access-Control-Allow-Origin`。
- 19 个要求/辅助 GET 接口合同逐项返回 200（登录后）。
- 正式指标对象包含 `value`、`caliber`、`source`、`updated_at`、`conflict`、`unit`。
- 无真实数据时所有正式指标 `value=null`、`status=待接入`，`generated_business_data=false`。
- 待复核项和 DRAFT 版本无法进入正式维度；发布后仅对应类型具备正式维度资格。
- Sandbox 明确返回隔离标识，快照数据值不输出到正式视图。

## 浏览器检查

- 实际启动后端并通过登录页进入系统。
- PC 1440×900：4 个业务页面、映射/口径复核、API 复核和 Sandbox 共 7 个页面全部可见、导航正常。
- 移动端 375×812：菜单可展开、页面可切换、文档宽度未超过视口，无横向溢出。
- 浏览器控制台错误：0。
- 首次浏览器并发检查发现 SQLite 共享连接竞争，已通过数据库连接级可重入锁修复，并重新完成 38 项自动测试。

## 受保护现网文件

以下 SHA-256 在开发前后完全一致：

| 文件 | SHA-256 |
|---|---|
| `登录权限系统/boss-dashboard-v6.html` | `cca775b82da19564cb6b62ffbe1e8be155e472a5e712f8d86b653de9a19d87c2` |
| `登录权限系统/shure-dashboard-v6.html` | `b5961a0583fc5f0fc12d06cc33e5dde6565c9b7d3854cc080f4eb0dcf75c2ab9` |
| `登录权限系统/app.py` | `7270f020b2c9506e77c65a390068fb3b5b5bfd1223e8573e33af590c0369d8d0` |
| `登录权限系统/users.json` | `4330775cbd9f72853e4ec563d298bbaca93f38954043f02682bea007db9151e7` |
| `客流爬虫/config.json` | `c43426cd2fe037e6ff07a9bff7c724d04d6c1cac852cf8cd9b6fb0cc3662cbe5` |

## 仓库卫生

- 未新增或提交 `.env`、SQLite 运行库、Excel/CSV、原始经营明细、密钥或证书。
- JavaScript `node --check` 通过；Python 模块编译检查通过。
- 未连接吉客云、泛中台、AI、钉钉或其他真实系统。

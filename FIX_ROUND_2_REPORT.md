# 采销经营驾驶舱 V1 · Codex Fix Round 2 报告

## 1. 审查对象与范围

- WorkBuddy Round 2 基准提交：`8b5b4b9234cc0b82fbad42685f4c8f7fdf77c6c7`。
- 整改分支：`fix/caixiao-v1-review2`。
- 审查结论输入：P0 代码层已清零，P1 剩余5项。
- 本轮只处理5项P1；未执行P2、真实生产联调或生产部署。
- 最终 Review 对象以 Codex 交付回复中的完整提交哈希及远端分支头为准。

## 2. P1-1 真实经营数据清理

- 从 `dsh_keys/master_fill.py`、`master_fill2.py`、`master_fill3.py` 删除库存类别与分仓金额/数量常量。
- 新增 `dsh_keys/runtime_business_data.py`，仅从 `CHUANGEL_BUSINESS_DATA_FILE` 指向的仓库外 JSON 读取运行数据。
- 正式私有数据必须声明 `RUNTIME_PRIVATE`；Mock 必须声明 `MOCK` 并显式开启测试开关。缺少文件、模式或必要分区即阻断，无源码数字兜底。
- 已检查 `dsh_keys/` 其他历史脚本；新采销正式链路持续禁止导入该目录，旧看板一次性替换模板不是新正式数据源。
- 详见 `SENSITIVE_BUSINESS_DATA_CLEANUP.md`；文件未记录原始数值。

## 3. P1-2 客流 Token 整改

- 删除当前 Git 树中原已跟踪的运行期 Token 缓存文件；未读取或输出 Token 原文。
- `客流爬虫/lib/ipva.js` 改为支持环境变量或仓库外私有运行文件，默认私有文件权限为仅当前用户可读写。
- `.gitignore` 已覆盖客流 Token、私有会话文件和运行期数据；新增空占位 `.env.example`。
- 未修改登录、验证码、门店树和客流抓取业务逻辑。
- 详见 `TRAFFIC_TOKEN_ROTATION_REQUIRED.md`。PO 仍须轮换/撤销旧 Token 并评估 Git 历史风险。

## 4. P1-3 复核中心重构

- 复核数据模型已拆分 `raw_code`、`raw_name`、`history_mapping`、`suggested_display_name`、`display_name`、`business_unit`、`channel`、`store/shop`、`inventory_class`、`status`、`version`。
- 发现后 `raw_code`、`raw_name`、`history_mapping` 在数据库层不可变；API 主动拒绝 raw 字段修改请求；前端无 raw 字段编辑控件。
- PO 可确认 `display_name` 和映射决策；只有已确认并已发布的版本才进入正式维度和 KPI。
- 保留 before/after、reason、affected_metrics、确认/发布人及时间审计字段。

## 5. P1-4 正式数据接口

| 接口 | 最小可用链路 | 阻断原则 |
|---|---|---|
| `GET /api/v1/sales/daily` | 已发布销售口径+调整规则+映射版本→按日聚合，支持 start/end/channel 等可用筛选 | 版本/映射缺失返回待确认 |
| `GET /api/v1/inventory/aging` | 读取已结构化库龄记录，输出 `<90 / 90-180 / 180-360 / 360+` 数量与金额 | 无数据待接入；未确认或未映射待确认 |
| `GET /api/v1/anomaly/list` | 实现缺货、高库存、长库龄、慢动销、政策风险的读取模型 | 阈值未确认/未发布时不形成正式结论；政策数据无来源时待接入 |
| `GET /api/v1/action/list` | 读取动作台账，支持待确认/已确认/执行中/已完成/已取消 | 状态为闭集词汇，写入需独立授权与审计 |

新增了受权限保护的结构化库龄写入和动作台账写入端点，但本轮没有写入真实数据。

## 6. P1-5 前端交互

- 业务板块只能从 Apple线下/APR、Apple电商、Shure电商、Apple渠道/3PP分销中选择，不再自由输入。
- 日期快捷项包括今日、昨日、本周、本月、自定义。
- 对比口径包括不对比、环比/上一周期、同比、目标、差额；目标数据无来源时明确提示待接入。
- 首页异常、商品列表和库存表均使用 `/cx/sku?sku=...` URL 下钻。SKU 页初始状态优先读取 URL，刷新不丢失。
- 本地浏览器发现并修复了“目标”选择后提示未即时刷新的问题。

## 7. 测试与覆盖率

- 自动测试：79项通过，0失败，0错误。
- 相比 Round 1 的63项，新墖16项。
- 机器可读报告：`caixiao/coverage.xml`。
- 实测覆盖率：626 / 1,563 个可执行语句行，40.05%。
- 新增重点场景：raw name/code不可改、display name确认/发布、四个接口、库龄与阈值门禁、日期快捷区间、SKU URL恢复、业务板块枚举、敏感经营数据和 Token 源码扫描。

## 8. 浏览器验证

- 四个业务板块闭集选项正确。
- “本月”产生当月起止日期；“目标”应用后显示“目标数据待接入”。
- `/cx/sku?sku=SKU-URL-ROUND2` 在刷新前后均恢复同一 SKU 值。此标识仅用于本地交互验证，不是经营数据。
- 复核中心展示 raw 列，但不存在 raw 编辑输入。
- 375×812 下页面宽度375，无横向溢出，移动菜单可见。
- 浏览器控制台 warning/error 为0。

## 9. 已知问题与待确认

- Token/经营常量在 Git 历史中的风险不因当前树删除而消失，由 PO/安全管理员完成轮换、日志核查与历史处置决策。
- 库龄起算字段、异常阈值、映射版本、目标数据和对比周期规则仍待 PO 确认。
- 真实吉客云及客流联调未执行；当前接口是受门禁的最小可用链路，不代表生产验收。

## 10. Review Round 3 建议检查

1. 扫描三个 `master_fill` 和仓库当前树，确认未出现原经营值或 Token。
2. 尝试从 API 修改 raw 字段，确认请求被拒绝；确认 display name 只在发布后进入正式维度。
3. 通过无版本、未确认数据和已发布测试数据分别调用四个接口，检查待接入/待确认/正式计算边界。
4. 检查异常阈值未发布时不形成正式结论，政策风险无来源时待接入。
5. 复测目标待接入提示、SKU URL 刷新恢复和375px响应式布局。

本报告不是生产上线批准。本轮完成后停止，等待 WorkBuddy Review Round 3。

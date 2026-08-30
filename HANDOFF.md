# HANDOFF — 采销经营驾驶舱 V1 Fix Round 2

## 交付状态

- WorkBuddy Round 2 基准提交：`8b5b4b9234cc0b82fbad42685f4c8f7fdf77c6c7`。
- 整改分支：`fix/caixiao-v1-review2`。
- 状态：5项 P1 已完成代码整改与本地验证，待 WorkBuddy Review Round 3。
- Review 对象：以 Codex 最终交付回复中的完整提交哈希及远端 `fix/caixiao-v1-review2` 分支头为准，不在同一提交中回写自身哈希。
- `main`：未合并、未移动。
- 正式环境：未部署。
- 真实生产系统：未连接吉客云、客流、钉钉或其他生产数据源。

## 5项 P1 完成情况

1. **敏感经营数据**：`master_fill.py`、`master_fill2.py`、`master_fill3.py` 的真实经营常量已删除，改为 `CHUANGEL_BUSINESS_DATA_FILE` 指向的仓库外运行时 JSON；Mock 必须显式标记并开启开发开关。
2. **客流 Token**：从当前 Git 树移除已跟踪的 Token 缓存，改为环境变量或仓库外私有文件；客流登录、验证码、门店树和抓取业务逻辑不变。
3. **复核中心**：`raw_code`、`raw_name`、`history_mapping` 全链只读；`display_name` 及映射决策由 PO 确认，仅“已确认+已发布”可进入正式看板。
4. **正式数据接口**：`/sales/daily`、`/inventory/aging`、`/anomaly/list`、`/action/list` 已从 stub 转为最小可用链路；无数据或无已发布口径时返回待接入/待确认，不生成经营数字。
5. **前端交互**：四个业务板块为闭集选项；日期快捷区间、五个对比口径、目标待接入提示和 SKU URL 下钻/刷新恢复已完成。

## 安全交接

- `SENSITIVE_BUSINESS_DATA_CLEANUP.md` 只记录位置、类型和整改方式，不包含原数值。
- `TRAFFIC_TOKEN_ROTATION_REQUIRED.md` 只记录需 PO 轮换/确认的 Token 类型，不包含 Token 原文。
- 删除当前文件不能解除 Git 历史风险；PO 仍须完成旧凭据轮换、日志核查和传播范围评估。

## 测试与检查

- 自动测试：79项通过，0失败，0错误。
- 覆盖率：626 / 1,563 个可执行语句行，40.05%；机器可读报告 `caixiao/coverage.xml`。
- 源码扫描：三个 `master_fill` 文件敏感经营常量匹配为0；`dsh_keys` 凭据字面量赋值匹配为0；客流 Token 缓存已不在当前工作树和跟踪清单中。
- 浏览器：四业务板块闭集、本月日期区间、目标待接入、SKU URL恢复、raw字段无编辑入口均通过；375×812 无横向溢出；控制台 warning/error 为0。

## 待 PO / WorkBuddy

- PO/客流系统管理员确认并轮换历史 Token，核查访问日志和 Git 历史传播范围。
- PO 审批库龄起算规则、异常阈值、映射版本和运营动作责任归属。
- WorkBuddy 重点审查当前树与 Git 历史风险的区分、raw不可变约束、四个数据接口的门禁、阈值未发布阻断和 SKU URL 恢复。

## 范围边界

本轮没有执行 P2、真实吉客云/客流生产联调或生产部署；没有合并 `main`。交付后停止开发，等待 WorkBuddy Review Round 3。

# 采销经营驾驶舱 Framework Completion 测试报告

状态：2026-08-30 本地自动、API和浏览器检查通过，待PO业务体验与WorkBuddy独立Review。

## 自动测试

- 命令：`python3 caixiao/tests/run_with_coverage.py`
- 结果：88项通过，0失败，0错误。
- 相比Fix Round 2的79项，本轮新增9项Framework Completion测试。
- 机器可读报告：`caixiao/coverage.xml`（Cobertura兼容结构）。
- 实测覆盖：643 / 1,740个可执行语句行，36.95%。
- 统计方法：Python标准库 `trace` + AST可执行语句行；覆盖率下降源于新增纯Mock演示适配器与大量返回分支，不通过无价值测试追逐百分比。

## 本轮新增验证

- `DEMO_MODE=true/false`精确解析，非法值拒绝。
- Demo上下文明确返回DEMO、固定演示标识、无正式KPI资格、无真实连接。
- 销售、趋势、SKU、库存、库龄、采购、政策、异常、动作和客流Demo接口全部有明确数据分类。
- Demo模式禁止写正式销售、库存、库龄、动作和复核发现表。
- Demo复核确认/发布只写进程内存，raw字段仍由API强制只读。
- Sandbox继续保持SANDBOX数据分类，与Demo和Formal隔离。
- 七个页面路由全部可访问。
- 前端包含三政策拆分、双WOI、客流合同、AI五段输出和固定数据标识。
- 正式模式没有自动回退Demo的代码路径。

前两轮ETL、销售状态、调整规则、KPI门禁、三库存、双WOI、Sandbox差异、版本审计、敏感数据和客流Token测试全部保留并通过。

## 浏览器验收

- 使用本地临时账号和纯Mock Demo Adapter完成登录；没有使用正式账号、凭据或生产数据。
- 七个页面的主标题、Demo固定横幅、页面路由和内容均加载正确。
- 首页完整展示销售目标、毛利、三库存、双WOI、库龄、三类政策、风险Top10、动作和APR客流。
- SKU 360通过URL恢复到指定演示SKU，页面刷新不依赖sessionStorage。
- 映射复核中心完成“选择对象→人工确认→立即发布”，页面出现成功提示，raw字段无编辑入口。
- Sandbox交互输入旧/新结构化记录后输出销售额、差额、差异率、订单/渠道/门店/SKU差异，并保持正式KPI关闭。
- 1280px桌面端七页横向溢出均为0；浏览器控制台warning/error为0。
- 375×812移动端页面宽度375、横向溢出0、KPI单列、筛选可用、移动导航能打开。
- 保存7张桌面端和1张移动端截图到 `caixiao/docs/screenshots/framework-complete/`。

## 源码与安全检查

- Python编译、前端JavaScript语法和Git差异空白检查通过。
- `.env.example`只提供空占位和开关说明；没有提交本地登录值、密钥或真实凭据。
- 纯Mock演示数据只位于Demo Adapter，并持续标识；不含真实经营明细、客户信息或正式政策。
- FORMAL缺数据时显示待接入；SANDBOX和DEMO都不能进入正式KPI。
- 既有三个`master_fill`和客流Token安全测试继续通过。

## 范围说明

本轮没有连接真实吉客云、APR、IPVA/客流、钉钉或生产数据库，没有安装依赖、部署生产、合并`main`或执行P2扩展。测试通过不等于生产验收。

# TODO

## TY-AI 采销驾驶舱 V1

- [x] 建立独立 `caixiao/` 工程与运行环境
- [x] 建立环境配置、SQLite 数据模型与安全鉴权
- [x] 建立人工确认、草稿与发布版本机制
- [x] 建立统一 `/api/v1/` 接口与 Sandbox 隔离框架
- [x] 建立映射/口径复核中心与吉客云 API 确认卡
- [x] 建立采销作战首页、SKU 360、库存&采购、Apple 政策四个页面
- [x] Fix Round 1：移除当前源码中的吉客云硬编码凭据并建立轮换清单
- [x] Fix Round 1：重构 modified 增量销售事实同步与 pay_time 版本口径
- [x] Fix Round 1：完成状态复核、销售调整规则和真实 Sandbox 差异引擎
- [x] Fix Round 1：完成全链 KPI 门禁、三库存、双WOI及阻断测试
- [x] Fix Round 1：完成全局筛选、SKU下钻、审计字段和浏览器验证
- [x] WorkBuddy 完成 Round 2 Review，确认 P0 代码层清零并提出5项P1
- [x] Fix Round 2：清理三个 `master_fill` 的敏感经营常量并建立私有运行时注入
- [x] Fix Round 2：移除当前树客流 Token 缓存并建立环境/仓库外私有文件注入
- [x] Fix Round 2：完成 raw/display 复核模型、raw强制只读和确认/发布门禁
- [x] Fix Round 2：实现 sales/daily、inventory/aging、anomaly/list、action/list 最小可用链路
- [x] Fix Round 2：完成业务板块枚举、日期快捷、对比口径和 SKU URL 下钻
- [x] 生成 88 项测试结果及机器可读 `coverage.xml`
- [x] Framework Completion：建立FORMAL/SANDBOX/DEMO三模式严格隔离
- [x] Framework Completion：完成纯Mock Demo Adapter和固定演示标识
- [x] Framework Completion：补齐七个页面的完整经营与复核内容
- [x] Framework Completion：补齐SKU URL下钻、全局筛选、人工确认发布和Sandbox交互
- [x] Framework Completion：完成PC与375px移动端浏览器检查并保存8张截图
- [ ] PO 对V1页面结构、信息层级和演示流程进行第一次业务体验
- [ ] WorkBuddy 对 `feature/caixiao-framework-complete` 执行独立Review
- [ ] PO 完成吉客云旧凭据撤销、轮换和泄露范围核查
- [ ] PO/客流系统管理员完成历史 Token 轮换和传播范围核查
- [ ] WorkBuddy 对 `fix/caixiao-v1-review2` 执行 Review Round 3
- [ ] WorkBuddy 使用真实吉客云文档/凭据完成接口联调
- [ ] 业务负责人逐项确认 `BUSINESS_CONFIRMATION_REQUIRED.md`
- [ ] 通过正式身份、权限和数据范围验收
- [ ] 经单独授权后进入试点部署

## P2 延后项（本轮不执行）

- [ ] 市场价与价格治理
- [ ] 合同、发票及结算扩展
- [ ] 完整钉钉 H5
- [ ] AI 预测
- [ ] 其他新增业务页面

> 当前完成仅代表代码交付待 Review，不代表生产验收或正式数据接入。

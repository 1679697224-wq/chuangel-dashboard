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
- [x] 生成 63 项测试结果及机器可读 `coverage.xml`
- [ ] PO 完成吉客云旧凭据撤销、轮换和泄露范围核查
- [ ] WorkBuddy 对 `fix/caixiao-v1-review1` 执行 Review Round 2
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

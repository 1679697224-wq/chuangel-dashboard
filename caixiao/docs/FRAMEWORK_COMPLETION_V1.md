# 采销经营驾驶舱 V1 · Framework Completion 交付说明

状态：本地开发与验收检查完成，待 PO 页面体验与 WorkBuddy 独立 Review。当前不是生产系统。

## 1. 本轮定位

V1 面向采销经理、品牌操盘手与经营分析人员，形成“发现问题 → 判断影响 → 形成建议 → 人工确认”的日常工作入口。本轮完成产品框架、页面、交互和演示链路，不连接真实吉客云、APR、客流、钉钉或生产数据库。

## 2. 页面路由

| 页面 | 路径 | 本轮可验证内容 |
|---|---|---|
| 采销作战首页 | `/cx/` | 销售、目标、毛利、三库存、双WOI、库龄、政策、Top风险、动作与客流 |
| SKU 360 | `/cx/sku?sku=DEMO-APL-PH-001` | 主档、7/14/28/90销量、价格/成本/毛利、三库存、双WOI、库龄、渠道、仓库、DG/政策与风险 |
| 库存&采购全链路 | `/cx/inventory-purchase` | 库存→需求→采购→在途→到货→入库→分配→门店/渠道 |
| Apple政策经营 | `/cx/apple-policy` | DG SI、DG ST、单店补贴独立台账与扩展位 |
| 映射与口径复核 | `/cx/review-mapping` | raw只读、系统建议、人工display_name、确认、发布和版本审计 |
| 吉客云 API 复核 | `/cx/review-api` | 销售/库存/采购/调拨确认卡与销售六时间字段 |
| Sandbox | `/cx/sandbox` | 销售和库存预置差异、快照身份、交互式差异与五时间复算 |

默认访问：`http://127.0.0.1:8010/cx/`。本地端口被占用时可通过 `CAIXIAO_PORT` 修改。

## 3. 三种数据模式

| 模式 | 开启方式 | 数据来源 | 正式KPI资格 | 页面标识 |
|---|---|---|---|---|
| FORMAL | `DEMO_MODE=false` | 正式事实库、已发布映射与口径 | 满足完整门禁后允许 | 正式门禁；缺失显示待接入 |
| SANDBOX | `/cx/sandbox`及其接口 | 允许的快照或请求内验证记录 | 永不允许 | 验证数据，不代表正式经营口径 |
| DEMO | `DEMO_MODE=true` | 纯 Mock Demo Adapter | 永不允许 | 固定顶部演示横幅 |

模式之间不存在自动回退：FORMAL 缺数据不会调用 Demo；Demo 不读取正式事实或真实系统；Sandbox 结果不能进入正式 KPI。

## 4. Demo 范围

- Apple线下：APR和即时零售复用正式维护的10家门店主数据；
- Apple电商：羽通-JD、啟韬-Suning；
- 舒尔电商：天猫、京东；
- 分销渠道：分销；
- Demo SKU、仓库、订单、目标、政策、风险和动作均为纯 Mock，并在页面持续标识。

## 5. 人工复核与AI边界

复核链路为：系统识别 → AI/规则建议 → 人工确认 → 发布版本。`raw_code`、`raw_name`、`history_mapping` 前端无编辑入口，API拒绝修改；`display_name`由PO确认。Demo确认/发布只写当前进程内存。

AI只输出：发现问题、数据证据、可能原因、建议动作、待确认事项。销售额、库存、毛利和口径由确定性程序计算；AI无执行权。

## 6. 本地启动

在仓库根目录设置本地运行参数后启动：

```bash
export DEMO_MODE='true'
export CAIXIAO_TOKEN_SECRET='请设置至少32位本地随机字符串'
export CAIXIAO_BOOTSTRAP_USER='请设置本地演示账号'
export CAIXIAO_BOOTSTRAP_PASSWORD='请设置至少12位本地演示密码'
python3 -m caixiao.backend.app
```

正式门禁预览只需将 `DEMO_MODE` 改为 `false`。不要在文档、代码或Git中保存实际密码或密钥。

## 7. 页面截图

- `caixiao/docs/screenshots/framework-complete/01-home-desktop.png`
- `caixiao/docs/screenshots/framework-complete/02-sku-desktop.png`
- `caixiao/docs/screenshots/framework-complete/03-inventory-desktop.png`
- `caixiao/docs/screenshots/framework-complete/04-policy-desktop.png`
- `caixiao/docs/screenshots/framework-complete/05-review-mapping-desktop.png`
- `caixiao/docs/screenshots/framework-complete/06-review-api-desktop.png`
- `caixiao/docs/screenshots/framework-complete/07-sandbox-desktop.png`
- `caixiao/docs/screenshots/framework-complete/08-home-mobile-375.png`

## 8. 尚未接入的真实能力

- 吉客云销售、库存、采购、调拨正式API与凭据；
- 正式仓库/库位、渠道、门店、店铺、SKU/SPU映射；
- APR真实门店与O2O范围、IPVA/客流自动与手工数据；
- 正式销售状态、退款/退货/红冲、业务日与订单去重口径；
- 正式采购、调拨、在途、库龄和异常阈值；
- Apple DG SI、DG ST、单店补贴正式政策、目标、实际与结算；
- 正式目标、价格、成本、毛利、政策、市场价、合同、发票；
- 复杂RBAC、钉钉免登、AI预测和自动复盘。

## 9. PO体验重点

1. 首页信息优先级是否符合采销经理每日使用习惯；
2. SKU 360主档、经营指标、渠道/仓库、政策与风险层级是否合理；
3. 库存→采购→门店/渠道是否需要增加或调整环节；
4. DG SI、DG ST、单店补贴三类政策的正式字段、周期与目标来源；
5. 映射复核清单是否适合批量业务确认；
6. API确认卡是否足够让业务、IT和WorkBuddy共同联调；
7. 演示数据丰富度和移动端使用体验是否满足首次汇报。

## 10. 范围声明

本轮没有合并 `main`、没有部署生产、没有真实系统连接、没有安装依赖、没有执行P2扩展。完成仅表示V1 Framework Completion已交付待体验与Review。

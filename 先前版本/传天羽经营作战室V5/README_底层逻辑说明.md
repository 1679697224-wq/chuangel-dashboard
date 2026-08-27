# 传天羽经营看板 V2.2 —— 底层逻辑文档

> 本文档供接手方/其他 AI 理解系统结构、数据流与扩展方式。看板地址：`http://localhost:8002`（本地服务，需手动启动）。

---

## 一、系统架构

```
┌─────────────┐   ┌──────────────┐   ┌──────────┐   ┌──────────────┐
│  数据源      │ → │ 构建脚本      │ → │ data.json│ → │ Flask 服务    │ → 浏览器
│ (Excel/JSON) │   │ (python)     │   │ (统一数据)│   │ (app.py :8002)│
└─────────────┘   └──────────────┘   └──────────┘   └──────┬───────┘
                                                           │ /api/data（页面数据）
                                                           │ /api/ai（AI问答→ollama）
                                                           └→ templates/index.html（单页看板）
```

**核心原则：数据与展示分离。** 所有数据源通过构建脚本汇聚成 `data.json`，前端只消费 `data.json`，不直接读 Excel。换数据源/换设计互不干扰。

---

## 二、目录结构（~/Desktop/APR项目/看板V2/）

| 文件 | 作用 |
|---|---|
| `app.py` | Flask 服务：渲染页面、`/api/data` 返回数据、`/api/ai` 调 ollama 大模型回答老板提问 |
| `build_data.py` | 主构建脚本：读吉客云抓取数据 → 计算环比/达成预测 → 合并库存/产品结构/花名册 → 输出 `data.json` |
| `build_inv.py` | 解析商务《库存分析表_260807.xlsx》→ `inv_data.json`（金额口径、剔虚拟品、库龄预警） |
| `build_apr.py` | 解析《销售分析表2026.xlsx》→ `apr_struct.json`（四大主机/配件占比，2026-8真实数据） |
| `build_roster.py` | 解析花名册 .xls → `roster.json`（37人档案，非敏感字段+标准职级） |
| `data.json` | 前端唯一数据源（由 build_data.py 生成） |
| `templates/index.html` | 单页看板（V2.2：首页/三大模块/二级目录/AI助手，约 92KB） |
| `*.json`（inv_data/apr_struct/roster） | 各构建脚本的中间产物 |

---

## 三、数据流详解

### 3.1 数据源与口径

| 数据 | 来源 | 更新方式 |
|---|---|---|
| 全公司日销售/订单/渠道/门店 | 吉客云抓取（`~/.openclaw/workspace/brief_web/jky_sales*.json`） | 每天自动抓取，`build_data.py` 重新生成 |
| APR 月度（销售/毛利/客流/转化/销售员） | 吉客云（`brief_web/apr_data.json`） | 同上 |
| 库存（金额/分类/仓位/库龄） | 商务《库存分析表_260807.xlsx》（桌面） | 商务每日更新 → 重跑 `build_inv.py` |
| APR 产品结构（主机/配件占比） | 《销售分析表2026.xlsx》 | 每月更新 → 重跑 `build_apr.py` |
| 员工档案 | 花名册《江苏传天羽…在职员工20260811.xls》（桌面） | 人事更新 → 重跑 `build_roster.py` |
| 电商流量/费用/竞品 | 未接入（当前为模拟数据，已标"模拟数据"） | 电商后台数据到位后接入 |

### 3.2 构建流程（顺序执行）

```bash
# 在 看板V2 目录下（用 3.12 版 python，系统 python3 无 flask/xlrd）
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 build_inv.py     # 库存
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 build_apr.py     # 产品结构
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 build_roster.py  # 花名册
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 build_data.py    # 合并 → data.json
```

### 3.3 关键计算逻辑（build_data.py）

- **环比**：日报=当日 vs 前一日；周报=区间 vs 前一区间；月报=8月累计（同比去年待接入）
- **达成率预测**：`月累计 / 已过天数 × 31 = 预测月末`，再除月目标得预测达成率
- **时间进度**：`已过天数 / 31`
- **毛利率**：`APR毛利合计 / APR销售合计`（吉客云口径）
- **销售员字段**：线上/线下/3PP/主机拆分、ACS、毛利排名、配件占比（来自 apr_data.json）

---

## 四、data.json 结构（前端消费）

```json
{
  "today": "2026-08-11",                 // 数据日期
  "series": [                            // 日序列（吉客云 8/1-8/11）
    {"date":"2026-08-10","amount_wan":181.1,"orders":343,
     "channel":{"APR门店":{"amount_wan":57.7,"orders":142}, ...},
     "stores":{...}}
  ],
  "channels": [...],                     // 今日渠道（含环比）
  "stores_today": [...],                 // 今日门店
  "apr": {                               // APR 月度
    "sales":664.3,"task":2180,"rate":30.5,"profit":23.52,"pm":3.54,
    "time_progress":32.3,"gap":-1.8,
    "forecast_month_end":2059.4,"forecast_rate":94.5,
    "stores":[{name,sales,task,rate,profit,pm,traffic,orders,conv,apt,acs,pp,forecast,forecast_rate}],
    "salespersons":[{name,store,pos,task,sales,rate,offline,online,pp_sales,pp_rate,profit,profit_rank,profit_rate,offline_profit_rate,acs,high_sell,pp_amount_pct,host_qty,pp_qty}]
  },
  "inventory_biz": {                     // 商务库存（金额口径）
    "total":{"qty":19467,"amount":2322.07},
    "category":[{name,qty,amount,pct}],  // 苹果主机/原装配件/舒尔/第三方配件
    "warehouse":[{name,qty,amount,pct}], // 仓位分布（饼图）
    "aging":{"0~30天":1044.56,...},      // 库龄分段（金额）
    "aging_risk":[{wh,name,brand,cat,age,qty,amount}],  // 高库龄TOP15
    "aging_risk_amount":858.44,"aging_risk_pct":37.0,
    "severe_amount":120.86,"severe_count":1325,
    "virtual_removed":{"count":...,"amount":0,"items":[...]}
  },
  "apr_struct": {"host":{...},"acc":{...}},  // 产品结构（2026-8真实）
  "roster": { "王畅": {"hire_date","tenure","rank","edu","school","major",...} },  // 花名册
  "ecomm": {"apple":{...},"shure":{...}}
}
```

---

## 五、API 接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/` | GET | 看板页面 |
| `/api/data` | GET | 返回完整 data.json |
| `/api/ai` | POST `{"q":"问题"}` | AI 问答：拼装看板数据摘要 → ollama `qwen3:8b`（think:false）→ 返回 `{"answer":"..."}` |

**AI 上下文**（app.py `build_context()`）：把 data.json 压缩成文本摘要（销售/渠道/APR/门店/销售员/库存/库龄/产品结构），模型基于真实数据回答，数据缺失的维度会明说"待接入"。

---

## 六、前端架构（templates/index.html）

单文件 SPA，无框架，原生 JS + 手写 SVG/div 图表。

- **页面结构**：`page-home`（公司首页/一屏快照）独立于三大模块；经营模块含 `bizoverview`（总览）/`analytics`（经营分析）/`apr`/`ec`/`shure`/`inventory`；`mgmt`/`risk` 为管理/风控
- **导航**：`setModule(m)` 动态渲染二级导航（顶部 nav-sub + 侧边栏），侧边栏 = 当前页锚点目录（scroll-spy，`IntersectionObserver` 高亮当前位置）
- **时间维度**：`S.mode`（day/week/month）+ 起止日期，`rangeDays()/prevRangeDays()/agg()` 做区间聚合，全页面联动
- **图表**：折线=SVG polyline；饼图=CSS conic-gradient；条形=div+width%；进度=div
- **销售员详情**：点击 TOP5 卡片 → `openSp(idx)` 弹层（Hero+四指标+员工档案+销售结构+业绩明细）
- **板块AI**：`genBoardAI('apr'|'ec'|'shure')` → 调 /api/ai 生成该板块深度分析
- **重点风控**：事项进度表 + 业务反馈表单（`openItemForm` 更新进度/备注）+ 老板批复指派（`openApprove` → 改责任人/时限/要求），数据存前端内存（原型），正式版接后端/台账/钉钉

---

## 七、启动 / 部署

```bash
# 启动（端口8002）
cd ~/Desktop/APR项目/看板V2
nohup /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 app.py > /tmp/kanban_v2.log 2>&1 &

# 公网临时链接（给同事看）
nohup /opt/homebrew/bin/cloudflared tunnel --url http://127.0.0.1:8002 --no-autoupdate > /tmp/cf_8002.log 2>&1 &
# URL 从日志提取：grep -o "https://[a-z0-9-]*\.trycloudflare\.com" /tmp/cf_8002.log

# 重启流程（端口占用时）
PID=$(lsof -ti :8002); [ -n "$PID" ] && kill $PID
```

---

## 八、待接入 / 扩展点

1. **电商平台数据**：UV/转化/ROAS/退款/推广费（需求清单已发给电商负责人），接入后替换模拟数据
2. **同比去年**：需去年销售数据文件 → `build_data.py` 加同比计算
3. **任务指标**：每月正式下发后更新 `apr.stores[].task`（Siri 会提前提供）
4. **重点事项持久化**：目前存前端内存，重启丢失；建议接 SQLite（app.py 加 `/api/items` 读写）
5. **钉钉/企微集成**：老板批复后通过机器人推送通知责任人（app.py 加 webhook 调用）
6. **花名册更新**：人事发新文件到桌面 → 重跑 build_roster.py

---

*版本：V2.2 · 2026-08-11 · 传天羽经营看板*

---

## 九、V2.2 增量数据源（2026-08-11 晚）

| 数据 | 脚本 | 说明 |
|---|---|---|
| 电商分平台（京东羽通/苏宁啟韬/舒尔·天猫） | `build_ecomm.py [天数]` | 调吉客云 getShopOrderLiseInfo 按 shopName 归一化聚合 → `ecomm_platform.json`（近7天） |
| 竞品监控清单 | `build_compete.py` | 解析《京东平台竞争产品信息统计.xlsx》→ `compete.json`（3店铺269产品，可跳转） |
| 机况结构（常规机/样机/残次机） | `build_inv.py`（已升级） | 从库存表总览库龄分析区提取，样机=门店固定陈列不纳入滞销预警 |
| 最低库存覆盖预警 | `build_inv.py`（已升级） | APR最低库存要求(72SKU) vs 当前库存，零库存/低于要求自动预警 |

**电商分平台店铺归一化规则**（build_ecomm.normalize_platform）：
- 含"羽通" → 京东羽通；含"啟韬/启韬" → 苏宁啟韬；含"舒尔" → 舒尔·天猫/京东/其他

**推广费/佣金/ROAS 数据源**：吉客云无此数据，需电商负责人从平台后台导出（京东商智/京准通、苏宁数据罗盘），约定固定格式Excel放共享目录后写解析脚本（同商务库存表模式）。

---

## 十、V3 老板反馈版（2026-08-11 17:13）

基于 V3 全站重设计（苹果风格、四驾驶舱、左侧工作台）融合老板会议反馈：
- **国补专项**：单独列出（重点事项驾驶舱，含协商风险提示）
- **风险控制驾驶舱**：业务链全链路风险点（采购端/销售端/回款风险/库存中间/日常运维）+ 人/财/物/合规维度
- **盘点管理**：月度固定复盘（库存差异/资金安全/账目安全/现场收银/废单排查）
- **渠道命名统一**：合计→APR门店/京东羽通/苏宁啟韬/舒尔电商/3PP拓展（build_data 用 ecomm_platform 拆分）
- **毛利率口径说明**：pm_note（3.54%为含线上综合口径，不含线上约3.1%待财务确认）
- **电商页重构**：汇总结果（销售额/订单/客单价/毛利率/推广）+ 各店铺分析（京东羽通/苏宁啟韬）+ 流量转化与同行比较
- **销售员全排名**：全员30人排名表（销售额/完成率/毛利/毛利率/ACS/3PP/利润贡献），点击行看详情
- **新增重点事项**：老板可直接在看板新增事项
- 服务端口：8003（独立，不覆盖看板V2的8002）
- 运行：cd ~/Desktop/APR项目/看板V3_老板反馈版 && python3 app.py → http://127.0.0.1:8003

---

## 十一、V3.1 老板反馈优化（2026-08-11 17:35）

Siri 反馈 + 老板录音第二轮优化：
- **首页**：CTY 文字 → 公司logo图片（logo_cty.png，浅色底）；日期控件加大美化 + 📅快捷选择按钮（今天/昨天/近3天/近7天）
- **销售员全员录入**：花名册37人全接入（含无销售数据人员，排名表标"待更新"，排在最后）
- **电商用词**："区间销售"→"销售额"；电商页=汇总结果/各店铺分析/流量转化与同行比较
- **渠道命名规范**：羽通｜京东、啟韬｜苏宁（公司店铺名在前，平台在后）；Shure 统一用英文名
- **Apple电商隔离 Shure**：分平台数据过滤 Shure，单独 Shure电商 渠道
- **四驾驶舱拆分**：经营驾驶舱 / 管理驾驶舱 / 重点事项驾驶舱（国补专项+事项推进+老板批复）/ 风险控制驾驶舱（风险点全链路+盘点管理+实时监控），导航左侧工作台 4 项 + emoji 图标
- **盘点报告模板**：page-pandianreport（管理模块下），格式参考财务《镇江店盘点报告2026.7.29》（盘点时间/盘点人/门店情况/唯一码差异表/寄存主机），后续门店盘点按此模板
- 服务：http://127.0.0.1:8003

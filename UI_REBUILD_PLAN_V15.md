# 采销经营驾驶舱 V1.5 UI 重构计划

## Preflight 结论

- 基线：`e268a6035a652fbaa16b245ec477d6509ab4e987`。
- 分支：`feature/caixiao-design-system-v15`。
- 现有前台为原生 HTML/CSS/JavaScript rendering helper，适合在不更换技术栈的前提下统一组件语言。
- 五组一级菜单、13 个业务页面、三级筛选、SKU URL 下钻、业务表格、Demo/Formal 隔离、管理员权限边界和数据闸门均已存在。
- 当前主要问题：Token 名称仍偏临时；筛选没有清楚分组；首页 KPI 过多且层级弱；SKU 360 缺少首屏经营判断与趋势层；表格数字对齐和首列固定不足；移动端密度与折叠细节可继续统一；业务正文仍有重复“演示”措辞。

## 修改范围

| 文件 | 处理 |
|---|---|
| `DESIGN.md` | 新建设计系统，作为以后唯一视觉规范 |
| `caixiao/frontend/index.html` | 增加筛选语义容器和可访问性细节，不改变菜单与路由 |
| `caixiao/frontend/assets/app.css` | 以语义 Token 重建整体样式、响应式和组件状态 |
| `caixiao/frontend/assets/app.js` | 复用现有 helper，重排首页与 SKU 360，清理业务页重复技术/演示文案 |
| `caixiao/tests/test_design_system_v15.py` | 增加设计系统与业务不回归测试 |
| 交付文档与截图 | 完成审计、对比、测试、浏览器和交接证据 |

## 明确不修改

- `caixiao/backend/` 业务逻辑、API、Adapter、数据库、事实表、映射、版本、人工确认门禁和权限；
- `caixiao/frontend/assets/filter-utils.js` 已确认的三级业务关系；
- 五组一级菜单、13 个业务路由和指标业务名称；
- 旧总部看板、登录系统、客流正式配置和真实数据文件；
- main 分支与生产环境。

## 复用与重构

- 复用：`sectionTitle`、`panel`、`metricCard`、`businessTable`、`statusTag`、图表 helper、全局筛选状态、路由和权限判断。
- 重构：语义 Token、Sidebar、Topbar、FilterGroup、KPI 类型、ChartCard、TableCard、Progress、Empty/Error/Loading、移动导航。
- 首页：由连续 KPI 墙改为“销售达成、库存健康、政策风险、今日行动”四个经营焦点，再展开趋势、结构、异常和动作。
- SKU 360：重排为九段，首屏新增经营判断，销售窗口形成可读趋势证据。
- 库存采购：保持业务链不变，增强阶段状态和工作台表格关系。

## 验证策略

1. 保留并运行全部已有测试；
2. 增加 DESIGN、Token、菜单/筛选/路由/Logo/Demo 隔离/关键指标/375 结构测试；
3. Demo 模式启动独立验收服务，不连接真实系统；
4. 浏览器逐页检查 13 个业务页面、八组经营范围和 1440/1280/375 三档；
5. 保存 14 张统一视觉回归截图；
6. 检查控制台错误/警告、404、死链、页面级横向溢出；
7. 更新交接并仅提交/推送本特性分支。

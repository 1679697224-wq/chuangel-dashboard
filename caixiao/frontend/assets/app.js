"use strict";

const savedFilters = JSON.parse(sessionStorage.getItem("caixiao.globalFilters") || "{}");
const { BUSINESS_UNITS, quickDateRange, skuFromSearch, compareNotice } = window.CaixiaoFilters;
const skuFromUrl = skuFromSearch(window.location.search);
const state = {
  user: null, route: "home", selectedSku: skuFromUrl || sessionStorage.getItem("caixiao.selectedSku") || "",
  filters: { businessUnit:"", brand:"", channel:"", start:"", end:"", compare:"none", datePreset:"custom", ...savedFilters }
};
const page = document.getElementById("page");
const app = document.getElementById("app");
const loginView = document.getElementById("loginView");

const routeMap = {
  "/cx": "home", "/cx/": "home", "/cx/sku": "sku",
  "/cx/inventory-purchase": "inventory", "/cx/apple-policy": "policy",
  "/cx/review-mapping": "review-mapping", "/cx/review-api": "review-api",
  "/cx/sandbox": "sandbox"
};

const titles = {
  home: ["经营控制台", "采销作战首页"], sku: ["商品控制台", "SKU 360"],
  inventory: ["供应链控制台", "库存&采购全链路"], policy: ["政策控制台", "Apple政策经营"],
  "review-mapping": ["人工复核中心", "数据映射与口径复核"],
  "review-api": ["人工复核中心", "吉客云 API 取数逻辑复核"],
  sandbox: ["隔离验证环境", "Sandbox 差异验证"]
};

async function api(path, options = {}) {
  const config = { credentials: "same-origin", ...options };
  if (config.body && typeof config.body !== "string") {
    config.headers = { "Content-Type": "application/json", ...(config.headers || {}) };
    config.body = JSON.stringify(config.body);
  }
  const response = await fetch(path, config);
  const data = await response.json().catch(() => ({}));
  if (response.status === 401) { showLogin(); throw new Error("请先登录"); }
  if (!response.ok) throw new Error(data.message || data.error || "请求失败");
  return data;
}

function filterQuery() {
  const names = {businessUnit:"business_unit",brand:"brand",channel:"channel",start:"start",end:"end",compare:"compare"};
  const query = new URLSearchParams();
  Object.entries(names).forEach(([stateKey, apiKey]) => { if (state.filters[stateKey] && state.filters[stateKey] !== "none") query.set(apiKey, state.filters[stateKey]); });
  return query.toString() ? `?${query}` : "";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
}

function metricCards(metrics, colors = []) {
  return `<div class="metric-grid">${metrics.map((item, index) => `
    <article class="metric-card ${colors[index] || ""}">
      <div class="metric-label">${escapeHtml(item.name)}</div>
      <div class="metric-value ${item.value == null ? "pending-value" : ""}">${item.value == null ? escapeHtml(item.status || "待接入") : escapeHtml(item.value)}${item.value == null ? "" : escapeHtml(item.unit)}</div>
      <div class="metric-meta" title="${escapeHtml(item.caliber)}">${escapeHtml(item.caliber)}</div>
    </article>`).join("")}</div>`;
}

function renderGlobalFilters() {
  const filters = state.filters;
  document.getElementById("globalFilters").innerHTML = `<form id="globalFilterForm">
    <label>业务板块<select name="businessUnit"><option value="">全部已授权板块</option>${BUSINESS_UNITS.map(value=>`<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("")}</select></label>
    <label>品牌<input name="brand" value="${escapeHtml(filters.brand)}" placeholder="字段待接入"></label>
    <label>渠道<input name="channel" value="${escapeHtml(filters.channel)}" placeholder="按已发布渠道"></label>
    <label>开始日期<input name="start" type="date" value="${escapeHtml(filters.start)}"></label>
    <label>结束日期<input name="end" type="date" value="${escapeHtml(filters.end)}"></label>
    <label>对比口径<select name="compare"><option value="none">不对比</option><option value="previous">环比/上一周期</option><option value="year_on_year">同比</option><option value="target">目标</option><option value="difference">差额</option></select></label>
    <div class="date-shortcuts" aria-label="日期快捷区间"><button type="button" data-range="today">今日</button><button type="button" data-range="yesterday">昨日</button><button type="button" data-range="week">本周</button><button type="button" data-range="month">本月</button><button type="button" data-range="custom">自定义</button></div>
    <button class="secondary" type="submit">应用</button>
    <button id="resetFilters" class="ghost light" type="button">重置</button>
  </form><small id="filterNotice">${compareNotice(filters.compare)}</small>`;
  const form = document.getElementById("globalFilterForm");
  form.businessUnit.value = filters.businessUnit;
  form.compare.value = filters.compare;
  document.querySelectorAll("[data-range]").forEach(button => {
    button.classList.toggle("active", button.dataset.range === filters.datePreset);
    button.addEventListener("click", () => {
      const preset = button.dataset.range;
      if (preset !== "custom") {
        const range = quickDateRange(preset);
        form.start.value = range.start; form.end.value = range.end;
      }
      state.filters.datePreset = preset;
      document.querySelectorAll("[data-range]").forEach(item=>item.classList.toggle("active", item===button));
    });
  });
  [form.start, form.end].forEach(input=>input.addEventListener("change",()=>{
    state.filters.datePreset="custom";
    document.querySelectorAll("[data-range]").forEach(item=>item.classList.toggle("active",item.dataset.range==="custom"));
  }));
  form.addEventListener("submit", event => {
    event.preventDefault();
    state.filters = { ...Object.fromEntries(new FormData(form).entries()), datePreset:state.filters.datePreset || "custom" };
    sessionStorage.setItem("caixiao.globalFilters", JSON.stringify(state.filters));
    document.getElementById("filterNotice").textContent = compareNotice(state.filters.compare);
    navigate(window.location.pathname, false);
  });
  document.getElementById("resetFilters").addEventListener("click", () => {
    state.filters = { businessUnit:"", brand:"", channel:"", start:"", end:"", compare:"none", datePreset:"custom" };
    sessionStorage.setItem("caixiao.globalFilters", JSON.stringify(state.filters));
    renderGlobalFilters(); navigate(window.location.pathname, false);
  });
}

function pendingMetrics(names) {
  return names.map(([code, name, unit = ""]) => ({ code, name, value: null, unit, caliber: "真实来源、字段映射与发布版本确认后展示" }));
}

function emptyState(title = "待接入", text = "真实数据接入并通过人工复核后展示") {
  return `<div class="empty"><div><div class="empty-icon">—</div><strong>${escapeHtml(title)}</strong><span>${escapeHtml(text)}</span></div></div>`;
}

function sectionTitle(title, sub = "", actions = "") {
  return `<div class="section-title"><div><h2>${escapeHtml(title)}</h2><p>${escapeHtml(sub)}</p></div><div class="section-actions">${actions}</div></div>`;
}

function hero(title, text, badge = "数据待接入") {
  return `<section class="hero"><div><h2>${escapeHtml(title)}</h2><p>${escapeHtml(text)}</p></div><div class="hero-badge"><strong>${escapeHtml(badge)}</strong><small>正式经营视图</small></div></section>`;
}

function panel(title, body, extra = "") {
  return `<section class="panel"><div class="panel-head"><h3>${escapeHtml(title)}</h3>${extra}</div><div class="panel-body ${body.includes('class="table-scroll"') ? "flush" : ""}">${body}</div></section>`;
}

function skuLink(sku, label = sku) {
  return sku ? `<a class="sku-link" href="/cx/sku?sku=${encodeURIComponent(sku)}" data-sku="${escapeHtml(sku)}">${escapeHtml(label)}</a>` : "—";
}

async function renderHome() {
  const [sales, inventory, purchase, daily, anomalies, actions] = await Promise.all([
    api(`/api/v1/sales/summary${filterQuery()}`), api(`/api/v1/inventory/summary${filterQuery()}`), api(`/api/v1/purchase/summary${filterQuery()}`),
    api(`/api/v1/sales/daily${filterQuery()}`), api("/api/v1/anomaly/list"), api("/api/v1/action/list")
  ]);
  const metrics = [...sales.data.slice(0,2), ...inventory.data.slice(0,3), ...(sales.woi?.data || [])];
  page.innerHTML = hero("一屏掌握销售、库存、采购与政策风险", "所有经营数值必须来自真实接口，并在口径、映射和版本通过人工确认后进入本页。") +
    sectionTitle("核心经营指标", "付款销售、现货/在途/经营库存与双WOI；缺少发布版本时逐项显示待确认") + metricCards(metrics, ["gold","green","","red","green","gold",""]) +
    sectionTitle("采销联动作战", "从经营异常到闭环动作，当前不生成静态 AI 经营结论") +
    `<div class="two-col">${panel("按日销售趋势", daily.rows?.length ? `<div class="table-scroll"><table><thead><tr><th>日期</th><th>销售额</th><th>订单数</th><th>口径</th></tr></thead><tbody>${daily.rows.map(row=>`<tr><td>${escapeHtml(row.date)}</td><td>${escapeHtml(row.sales_amount)}</td><td>${escapeHtml(row.order_count)}</td><td>${escapeHtml(row.caliber)}</td></tr>`).join("")}</tbody></table></div>` : emptyState(daily.message || "待接入"))}${panel("动作台账", actions.data?.length ? `<div class="table-scroll"><table><thead><tr><th>动作</th><th>SKU</th><th>状态</th></tr></thead><tbody>${actions.data.map(item=>`<tr><td>${escapeHtml(item.title)}</td><td>${skuLink(item.sku)}</td><td>${escapeHtml(item.status)}</td></tr>`).join("")}</tbody></table></div>` : emptyState("待接入", "动作必须由授权人员确认并留痕"))}</div>` +
    sectionTitle("经营异常", "阈值未发布时只显示待确认，不形成正式结论") +
    panel("异常清单", `<div class="table-scroll"><table><thead><tr><th>类型</th><th>SKU</th><th>状态</th></tr></thead><tbody>${(anomalies.data || []).map(item=>`<tr><td>${escapeHtml(item.type)}</td><td>${skuLink(item.sku)}</td><td>${escapeHtml(item.status)}</td></tr>`).join("")}</tbody></table></div>`) +
    sectionTitle("正式经营链路", "发布门禁状态") +
    `<div class="workflow"><div class="flow-step active"><strong>系统识别</strong>原始对象</div><div class="flow-step"><strong>AI/规则建议</strong>不替代决策</div><div class="flow-step"><strong>人工确认</strong>映射与口径</div><div class="flow-step"><strong>发布版本</strong>可追溯</div><div class="flow-step"><strong>指标计算</strong>正式口径</div><div class="flow-step"><strong>经营看板</strong>授权范围</div><div class="flow-step"><strong>行动闭环</strong>审计留痕</div></div>`;
  void purchase;
}

async function renderSku() {
  const skus = await api("/api/v1/dim/skus");
  const available = skus.data.map(item => ({ key:item.source_key, name:item.value?.display_name || item.value?.canonical || item.source_key }));
  const urlSku = skuFromSearch(window.location.search);
  const selected = urlSku || state.selectedSku || available[0]?.key || "UNSELECTED";
  state.selectedSku = selected === "UNSELECTED" ? "" : selected;
  const query = filterQuery();
  const result = await api(`/api/v1/sales/sku/${encodeURIComponent(selected)}${query}`);
  const metrics = [...(result.sales?.data || []), ...(result.inventory?.data || []), ...(result.woi?.data || [])];
  const windows = result.sales_windows || {};
  page.innerHTML = hero("SKU 360：从销售表现看到库存、采购与政策", "SKU/SPU 通过人工映射并发布前，不进入正式商品经营视图。", `${result.eligible_sku_count} 个已发布 SKU`) +
    `<section class="panel"><div class="panel-body"><form id="skuSearchForm" class="form-grid"><label>SKU / SPU 搜索<input name="sku" list="skuOptions" value="${escapeHtml(selected === "UNSELECTED" ? "" : selected)}" placeholder="输入已发布 SKU 来源键" required><datalist id="skuOptions">${available.map(item=>`<option value="${escapeHtml(item.key)}">${escapeHtml(item.name)}</option>`).join("")}</datalist></label><label>渠道范围<input value="${escapeHtml(state.filters.channel || "全部已授权渠道")}" disabled></label><div class="wide"><button class="primary" type="submit">查看 SKU 详情</button></div></form></div></section>` +
    sectionTitle("销量窗口", "7/14/28/90 天分别计算；缺数据项独立显示待接入") + metricCards([[7,windows["7"]],[14,windows["14"]],[28,windows["28"]],[90,windows["90"]]].map(([days,value])=>({name:`近${days}天销量`,value,unit:"台",status:"待接入",caliber:"按已发布 sales_caliber 与状态调整版本"})),["gold","green","",""]) +
    sectionTitle("商品经营概览", "销售、现货、在途、经营库存和双WOI均经过人工发布门禁") + metricCards(metrics,["gold","green","","red","green","gold",""]) +
    sectionTitle("已发布商品列表", "点击SKU进入URL可恢复的商品详情") +
    panel("商品入口", available.length ? `<div class="table-scroll"><table><thead><tr><th>SKU</th><th>展示名</th></tr></thead><tbody>${available.map(item=>`<tr><td>${skuLink(item.key)}</td><td>${escapeHtml(item.name)}</td></tr>`).join("")}</tbody></table></div>` : emptyState()) +
    sectionTitle("全链路画像", "销售 → 库存 → 采购 → 调拨 → 政策") +
    `<div class="equal-col">${panel("渠道与价格表现", `<div class="callout"><strong>渠道</strong><br>${escapeHtml((result.dimensions?.channels || []).join("、") || "待接入")}<br><strong>价格</strong><br>${escapeHtml(result.price || "待接入")}</div>`)}${panel("仓库与库龄", `<div class="callout"><strong>仓库</strong><br>${escapeHtml((result.dimensions?.warehouses || []).join("、") || "待接入")}<br><strong>库龄</strong><br>${escapeHtml(result.aging || "待接入")}</div>`)}${panel("采购与到货", emptyState())}${panel("DG / 政策", `<div class="callout"><strong>${escapeHtml(result.dg_policy || "待接入")}</strong><br>正式政策不得由 AI 生成</div>`)}</div>`;
  document.getElementById("skuSearchForm").addEventListener("submit", event => {
    event.preventDefault(); state.selectedSku = new FormData(event.currentTarget).get("sku").trim();
    sessionStorage.setItem("caixiao.selectedSku", state.selectedSku);
    history.replaceState({}, "", `/cx/sku?sku=${encodeURIComponent(state.selectedSku)}`);
    renderSku();
  });
}

async function renderInventory() {
  const [inventory, purchase, aging, skus] = await Promise.all([api(`/api/v1/inventory/summary${filterQuery()}`), api(`/api/v1/purchase/summary${filterQuery()}`), api("/api/v1/inventory/aging"), api("/api/v1/dim/skus")]);
  page.innerHTML = hero("库存与采购全链路", "现货、在途、经营库存三口径并列；未确认仓库不会静默进入任何经营库存。") +
    sectionTitle("库存与采购总览", "不简单累计全部仓库，不将未确认数据写入 KPI") + metricCards([...inventory.data, ...purchase.data], ["","gold","green","red"]) +
    sectionTitle("库存结构", "仓库/库位映射发布后展示") +
    `<div class="two-col">${panel("三库存口径", `<div class="three-col">${["现货库存","在途库存","经营库存"].map(name=>`<div class="callout"><strong>${name}</strong><br>按已发布仓库分类计算</div>`).join("")}</div>`)}${panel("库龄", aging.rows?.length ? `<div class="table-scroll"><table><thead><tr><th>区间</th><th>数量</th><th>金额</th><th>状态</th></tr></thead><tbody>${aging.rows.map(item=>`<tr><td>${escapeHtml(item.bucket)}</td><td>${escapeHtml(item.quantity ?? "待接入")}</td><td>${escapeHtml(item.amount ?? "待接入")}</td><td>${escapeHtml(item.status)}</td></tr>`).join("")}</tbody></table></div>` : emptyState())}</div>` +
    sectionTitle("库存商品入口", "点击已发布SKU进入SKU 360") +
    panel("SKU库存表", skus.data?.length ? `<div class="table-scroll"><table><thead><tr><th>SKU</th><th>展示名</th></tr></thead><tbody>${skus.data.map(item=>`<tr><td>${skuLink(item.source_key)}</td><td>${escapeHtml(item.value?.display_name || item.value?.canonical || "待确认")}</td></tr>`).join("")}</tbody></table></div>` : emptyState()) +
    sectionTitle("采购与调拨", "采购单、状态、ETA 和调拨明细待真实接口确认") +
    panel("采购—到货—入库—调拨追踪", `<div class="table-scroll"><table><thead><tr><th>业务单据</th><th>SKU</th><th>仓库</th><th>状态</th><th>预计到货</th><th>来源</th></tr></thead><tbody><tr><td colspan="6">${emptyState()}</td></tr></tbody></table></div>`);
}

async function renderPolicy() {
  const policy = await api("/api/v1/policy/summary");
  page.innerHTML = hero("Apple 政策经营", "政策条款、适用范围、目标与实际达成必须来自已确认政策及真实经营数据。") +
    sectionTitle("政策经营总览", policy.reason) + metricCards(pendingMetrics([["policy_target","政策目标","元"],["policy_actual","达成金额","元"],["policy_rate","达成率","%"],["policy_rebate","预计返点","元"]]),["gold","green","","red"]) +
    sectionTitle("政策台账与适用范围", "版本、期间、渠道、SKU/SPU 和计算方式全链路留痕") +
    `<div class="two-col">${panel("有效政策", emptyState())}${panel("政策风险与差异", emptyState("待接入", "当前不生成任何静态 AI 政策结论"))}</div>`;
}

function reviewItemRows(items) {
  if (!items.length) return `<tr><td colspan="12">${emptyState("暂无待复核对象", "由受控识别API写入后出现")}</td></tr>`;
  return items.map(item => `<tr data-review-id="${item.id}"><td><input class="review-select" type="checkbox" value="${item.id}" ${item.status !== "UNCONFIRMED" ? "disabled" : ""}></td><td class="code">${escapeHtml(item.raw_code)}</td><td>${escapeHtml(item.raw_name)}</td><td>${escapeHtml(JSON.stringify(item.history_mapping))}</td><td>${escapeHtml(item.suggested_display_name || "—")}</td><td><input class="decision-display-name" value="${escapeHtml(item.display_name || item.suggested_display_name || "")}" ${item.status !== "UNCONFIRMED" ? "disabled" : ""}></td><td><select class="decision-business-unit" ${item.status !== "UNCONFIRMED" ? "disabled" : ""}><option value="">待确认</option>${BUSINESS_UNITS.map(value=>`<option value="${escapeHtml(value)}" ${item.business_unit===value?"selected":""}>${escapeHtml(value)}</option>`).join("")}</select></td><td><input class="decision-channel" value="${escapeHtml(item.channel || "")}" ${item.status !== "UNCONFIRMED" ? "disabled" : ""}></td><td><input class="decision-store" value="${escapeHtml(item.store_shop || "")}" ${item.status !== "UNCONFIRMED" ? "disabled" : ""}></td><td><select class="decision-inventory-class" ${item.status !== "UNCONFIRMED" ? "disabled" : ""}><option value="">待确认</option>${["SPOT","IN_TRANSIT","EXCLUDE"].map(value=>`<option value="${value}" ${item.inventory_class===value?"selected":""}>${value}</option>`).join("")}</select></td><td><span class="tag ${item.status === "UNCONFIRMED" ? "pending" : "published"}">${escapeHtml(item.status)}</span></td><td class="code">${escapeHtml(item.version || "—")}</td></tr>`).join("");
}

async function renderReviewMapping() {
  const [items, versions] = await Promise.all([api("/api/v1/review/items"), api("/api/v1/review/versions")]);
  page.innerHTML = hero("映射与口径复核中心", "系统识别与建议只进入待复核池；人工确认后形成草稿，发布版本后才具备正式 KPI 资格。", `${items.data.filter(i=>i.status==="UNCONFIRMED").length} 项待复核`) +
    sectionTitle("人工确认", "raw_code、raw_name、history_mapping 由系统识别后永久只读") +
    panel("确认并形成版本", `<form id="confirmForm" class="form-grid"><label>版本类型<select name="version_type"><option value="warehouse_mapping">warehouse_mapping</option><option value="channel_mapping">channel_mapping</option><option value="sku_mapping">sku_mapping</option><option value="sales_caliber">sales_caliber</option><option value="inventory_caliber">inventory_caliber</option><option value="sales_adjustment_rules">sales_adjustment_rules</option><option value="anomaly_thresholds">anomaly_thresholds</option></select></label><label>版本名称<input name="version_name" value="warehouse_mapping_v1" required></label><label class="wide">确认/发布原因<textarea name="reason" required></textarea></label><label class="wide">受影响指标（逗号分隔）<input name="affected_metrics" required placeholder="sales_amount,paid_orders"></label><label class="inline-check wide"><input name="publish" type="checkbox">确认后立即发布（需要发布权限）</label><div class="callout warning wide"><strong>只读边界：</strong>原始编码、原始名称和历史映射不在任何人工编辑请求中提交；只有PO确认的展示名与映射规则在发布后进入正式看板。</div><button class="primary wide" type="submit">确认所选对象</button><div id="confirmMessage" class="wide"></div></form>`) +
    sectionTitle("待复核池", "仓库、库位、渠道、门店、店铺、SKU、SPU、API字段与口径统一处理") +
    panel("识别与建议清单", `<div class="table-scroll"><table><thead><tr><th>选择</th><th>raw_code</th><th>raw_name</th><th>history_mapping</th><th>建议展示名</th><th>PO展示名</th><th>业务板块</th><th>渠道</th><th>门店/店铺</th><th>库存分类</th><th>状态</th><th>版本</th></tr></thead><tbody>${reviewItemRows(items.data)}</tbody></table></div>`) +
    sectionTitle("版本记录", "草稿与发布历史") +
    panel("人工确认版本", `<div class="table-scroll"><table><thead><tr><th>版本</th><th>类型</th><th>状态</th><th>原因</th><th>影响指标</th><th>确认人/时间</th><th>发布人/时间</th></tr></thead><tbody>${versions.data.length ? versions.data.map(v=>`<tr><td class="code">${escapeHtml(v.version_name)}</td><td>${escapeHtml(v.version_type)}</td><td><span class="tag ${v.status==="PUBLISHED"?"published":"pending"}">${escapeHtml(v.status)}</span></td><td>${escapeHtml(v.reason)}</td><td>${escapeHtml((v.affected_metrics||[]).join("、"))}</td><td>${escapeHtml(v.confirmed_by)}<br>${escapeHtml(v.confirmed_at||"—")}</td><td>${escapeHtml(v.published_by||"—")}<br>${escapeHtml(v.published_at || "—")}</td></tr>`).join("") : `<tr><td colspan="7">暂无版本</td></tr>`}</tbody></table></div>`);
  bindReviewForms();
}

function bindReviewForms() {
  const confirmForm = document.getElementById("confirmForm");
  confirmForm.addEventListener("submit", async event => {
    event.preventDefault(); const selected = [...document.querySelectorAll(".review-select:checked")].map(item=>Number(item.value)); const values = new FormData(confirmForm);
    const decisions = selected.map(itemId => {
      const row = document.querySelector(`[data-review-id="${itemId}"]`);
      return { item_id:itemId, display_name:row.querySelector(".decision-display-name").value.trim(), business_unit:row.querySelector(".decision-business-unit").value, channel:row.querySelector(".decision-channel").value.trim(), store_shop:row.querySelector(".decision-store").value.trim(), inventory_class:row.querySelector(".decision-inventory-class").value };
    });
    try {
      await api("/api/v1/review/confirm", { method:"POST", body:{ version_type:values.get("version_type"), version_name:values.get("version_name"), item_ids:selected, decisions, publish:values.get("publish")==="on", reason:values.get("reason"), affected_metrics:String(values.get("affected_metrics")||"").split(",").map(value=>value.trim()).filter(Boolean) }});
      toast("人工确认版本已保存"); await renderReviewMapping();
    } catch (error) { document.getElementById("confirmMessage").textContent = error.message; }
  });
  confirmForm.version_type.addEventListener("change", () => { confirmForm.version_name.value = `${confirmForm.version_type.value}_v1`; });
}

async function renderReviewApi() {
  const cards = await api("/api/v1/review/api-cards");
  page.innerHTML = hero("吉客云 API 取数逻辑复核", "销售、库存、采购、调拨分别核对端点、鉴权、字段和口径；当前未配置真实凭据，不伪造返回。", "4 个数据域") +
    sectionTitle("API 确认卡", "WorkBuddy 在实际环境完成文档与接口联调") +
    `<div class="equal-col">${cards.data.map(card=>`<article class="api-card"><div class="api-card-head"><div><h3>${escapeHtml(card.name)}</h3><span class="code">${escapeHtml(card.domain)}</span></div><span class="tag pending">${escapeHtml(card.status)}</span></div><dl><dt>端点</dt><dd>${escapeHtml(card.endpoint)}</dd><dt>缺少配置</dt><dd>${escapeHtml(card.missing.join("、") || "无")}</dd><dt>正式 KPI</dt><dd>禁止</dd></dl><div class="pipeline">${card.pipeline.map(step=>`<span>${escapeHtml(step)}</span>`).join("")}</div></article>`).join("")}</div>` +
    sectionTitle("销售五时间字段", "任何正式统计时间选择前都保留源事实") +
    panel("字段保留门禁", `<div class="workflow">${["create_time","pay_time","audit_time","consign_time","complete_time","modified_time"].map((name,index)=>`<div class="flow-step ${index===1?"active":""}"><strong>${name}</strong>${index===1?"发布口径的主时间":"事实层独立保留"}</div>`).join("")}</div><div class="callout warning"><strong>同步原则：</strong>优先按 modified_time 增量；不稳定时滚动回溯并 upsert。禁止用 consign_time 窗口决定付款销售事实是否入库。</div>`);
}

async function renderSandbox() {
  const compare = await api("/api/v1/sandbox/compare");
  const files = compare.snapshot.files || [];
  page.innerHTML = hero("Sandbox 差异验证", "未确认映射、快照和多口径复算只能在隔离环境中使用，不向正式经营视图泄漏。", compare.snapshot.status || "待接入") +
    sectionTitle("隔离状态", "正式视图与快照验证物理分开") +
    `<div class="equal-col">${panel("正式经营视图", `<div class="callout"><strong>${escapeHtml(compare.formal.message)}</strong><br>${escapeHtml(compare.formal.gate.gate)}</div>`)}${panel("既有快照", `<div class="callout warning"><strong>${escapeHtml(compare.snapshot.label)}</strong><br>${escapeHtml(files.length ? `识别 ${files.length} 个允许的快照文件，仅展示结构和哈希` : "未配置 Sandbox 快照目录")}</div>`)}</div>` +
    sectionTitle("快照文件身份", "不在页面输出真实经营值") +
    panel("结构检查", `<div class="table-scroll"><table><thead><tr><th>文件</th><th>SHA-256</th><th>结构</th><th>数据值</th></tr></thead><tbody>${files.length ? files.map(file=>`<tr><td>${escapeHtml(file.name)}</td><td class="code">${escapeHtml(file.sha256)}</td><td>${escapeHtml(JSON.stringify(file.shape || {}))}</td><td><span class="tag sandbox">不暴露</span></td></tr>`).join("") : `<tr><td colspan="4">${emptyState("快照待接入", "设置 CAIXIAO_SANDBOX_SNAPSHOT_DIR 后只读验证")}</td></tr>`}</tbody></table></div>`) +
    sectionTitle("真实差异比较", "销售支持订单/渠道/门店/SKU差异，库存支持数量/金额/仓库/SKU/映射差异") +
    panel("Sandbox 差异引擎", `<form id="diffForm" class="stack-form"><label>数据域<select name="domain"><option value="sales">销售</option><option value="inventory">库存</option></select></label><label>旧逻辑记录（JSON数组）<textarea name="old_records" placeholder='[]'></textarea></label><label>新事实记录（JSON数组）<textarea name="new_records" placeholder='[]'></textarea></label><button class="primary" type="submit">执行差异比较</button><pre id="diffResult" class="code"></pre></form>`) +
    sectionTitle("五时间口径复算工具", "输入仅在本次请求内计算，不写入正式指标") +
    panel("Sandbox 复算", `<form id="recomputeForm" class="stack-form"><label>金额字段<input name="amount_field" value="amount"></label><label>JSON 记录数组<textarea name="records" placeholder='[{"create_time":"...","pay_time":"...","amount":0}]'></textarea></label><button class="primary" type="submit">隔离复算</button><pre id="recomputeResult" class="code"></pre></form>`);
  document.getElementById("diffForm").addEventListener("submit", async event => {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    try { const result = await api("/api/v1/sandbox/compare", {method:"POST",body:{domain:values.get("domain"),old_records:JSON.parse(values.get("old_records")||"[]"),new_records:JSON.parse(values.get("new_records")||"[]")}}); document.getElementById("diffResult").textContent=JSON.stringify(result,null,2); }
    catch(error){ document.getElementById("diffResult").textContent=error.message; }
  });
  document.getElementById("recomputeForm").addEventListener("submit", async event => {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    try { const result = await api("/api/v1/sandbox/recompute-times", {method:"POST", body:{records:JSON.parse(values.get("records")||"[]"),amount_field:values.get("amount_field")}}); document.getElementById("recomputeResult").textContent=JSON.stringify(result,null,2); }
    catch(error){ document.getElementById("recomputeResult").textContent=error.message; }
  });
}

const renderers = { home:renderHome, sku:renderSku, inventory:renderInventory, policy:renderPolicy, "review-mapping":renderReviewMapping, "review-api":renderReviewApi, sandbox:renderSandbox };

async function navigate(path, push = true) {
  state.route = routeMap[path] || "home";
  if (push && window.location.pathname !== path) history.pushState({}, "", path);
  document.querySelectorAll("#mainNav a").forEach(link => link.classList.toggle("active", link.dataset.route === state.route));
  document.getElementById("pageEyebrow").textContent = titles[state.route][0];
  document.getElementById("pageTitle").textContent = titles[state.route][1];
  document.title = `${titles[state.route][1]}｜采销经营驾驶舱`;
  page.innerHTML = emptyState("正在加载", "读取已授权的正式接口");
  try { await renderers[state.route](); } catch (error) { page.innerHTML = `<div class="callout warning"><strong>加载失败</strong><br>${escapeHtml(error.message)}</div>`; }
  document.querySelector(".sidebar").classList.remove("open");
}

function showLogin() { app.hidden = true; loginView.hidden = false; }
function showApp(user) { state.user=user; document.getElementById("userName").textContent=user.username; loginView.hidden=true; app.hidden=false; renderGlobalFilters(); navigate(window.location.pathname,false); }
function toast(message) { const node=document.createElement("div"); node.className="toast"; node.textContent=message; document.body.appendChild(node); setTimeout(()=>node.remove(),2600); }

document.getElementById("loginForm").addEventListener("submit", async event => {
  event.preventDefault(); const error=document.getElementById("loginError"); error.textContent="";
  try { await api("/api/v1/auth/login", {method:"POST",body:{username:document.getElementById("username").value,password:document.getElementById("password").value}}); showApp(await api("/api/v1/auth/me")); }
  catch (exception) { error.textContent=exception.message; }
});
document.getElementById("logoutButton").addEventListener("click", async()=>{ try{await api("/api/v1/auth/logout",{method:"POST"});}finally{showLogin();} });
document.getElementById("menuButton").addEventListener("click",()=>document.querySelector(".sidebar").classList.toggle("open"));
document.getElementById("mainNav").addEventListener("click",event=>{const link=event.target.closest("a");if(link){event.preventDefault();navigate(link.getAttribute("href"));}});
window.addEventListener("popstate",()=>navigate(window.location.pathname,false));
setInterval(()=>{document.getElementById("clock").textContent=new Date().toLocaleString("zh-CN",{hour12:false});},1000);

api("/api/v1/auth/me").then(showApp).catch(showLogin);

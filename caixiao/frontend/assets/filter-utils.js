"use strict";

(function expose(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.CaixiaoFilters = api;
})(typeof window !== "undefined" ? window : globalThis, function build() {
  const BUSINESS_UNITS = ["Apple线下", "Apple电商", "舒尔电商", "分销渠道"];
  const APR_STORES = [
    "徐州彭城店", "无锡店", "连云港店", "太原店", "宿州店",
    "镇江店", "运城店", "日照店", "徐州宝龙店", "苏家屯店",
  ];
  const CHANNELS_BY_UNIT = {
    "Apple线下": ["APR", "即时零售"],
    "Apple电商": ["京东", "苏宁"],
    "舒尔电商": ["天猫", "京东"],
    "分销渠道": ["分销"],
  };
  const STORES_BY_SCOPE = {
    "Apple线下::APR": APR_STORES,
    "Apple线下::即时零售": APR_STORES,
    "Apple电商::京东": ["京东羽通分期免息店"],
    "Apple电商::苏宁": ["苏宁啟韬专卖店"],
    "舒尔电商::天猫": ["舒尔官方旗舰店"],
    "舒尔电商::京东": ["京东舒尔自营专卖店"],
    "分销渠道::分销": [],
  };
  const LEGACY_BUSINESS_UNITS = { "Apple线下/APR": "Apple线下", "Shure电商": "舒尔电商" };
  const LEGACY_CHANNELS = {
    "APR门店": "APR", "O2O / 即时零售": "即时零售",
    "羽通 - 京东": "京东", "啟韬 - 苏宁": "苏宁", "3PP": "分销",
  };

  function localDate(value = new Date()) {
    const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }
  function quickDateRange(preset, now = new Date()) {
    if (!["today", "yesterday", "week", "month", "custom"].includes(preset)) throw new Error("不支持的日期快捷区间");
    const end = new Date(now); const start = new Date(now);
    if (preset === "yesterday") { start.setDate(start.getDate() - 1); end.setDate(end.getDate() - 1); }
    if (preset === "week") start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
    if (preset === "month") start.setDate(1);
    return preset === "custom" ? null : { start: localDate(start), end: localDate(end) };
  }
  function skuFromSearch(search) { return new URLSearchParams(search || "").get("sku") || ""; }
  function compareNotice(compare) {
    return compare === "target"
      ? "目标数据待接入时不生成目标对比结果。"
      : "业务板块、渠道、门店/店铺、日期及对比口径在所有业务页面继承。";
  }
  function channelsForUnit(unit) { return unit && CHANNELS_BY_UNIT[unit] ? CHANNELS_BY_UNIT[unit].slice() : []; }
  function storesForUnitChannel(unit, channel) { return (STORES_BY_SCOPE[`${unit}::${channel}`] || []).slice(); }
  function normalizeGlobalFilters(input = {}) {
    const output = { businessUnit:"", channel:"", store:"", start:"", end:"", compare:"none", datePreset:"month", ...input };
    delete output.brand;
    output.businessUnit = LEGACY_BUSINESS_UNITS[output.businessUnit] || output.businessUnit;
    output.channel = LEGACY_CHANNELS[output.channel] || output.channel;
    if (!BUSINESS_UNITS.includes(output.businessUnit)) {
      output.businessUnit = ""; output.channel = ""; output.store = ""; return output;
    }
    if (!channelsForUnit(output.businessUnit).includes(output.channel)) {
      output.channel = ""; output.store = ""; return output;
    }
    const stores = storesForUnitChannel(output.businessUnit, output.channel);
    if (output.store && !stores.includes(output.store)) output.store = "";
    return output;
  }
  return {
    BUSINESS_UNITS, APR_STORES, CHANNELS_BY_UNIT, STORES_BY_SCOPE,
    channelsForUnit, storesForUnitChannel, normalizeGlobalFilters,
    localDate, quickDateRange, skuFromSearch, compareNotice,
  };
});

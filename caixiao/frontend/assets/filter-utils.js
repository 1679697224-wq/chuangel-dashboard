"use strict";

(function expose(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.CaixiaoFilters = api;
})(typeof window !== "undefined" ? window : globalThis, function build() {
  const BUSINESS_UNITS = ["Apple线下/APR", "Apple电商", "Shure电商", "Apple渠道/3PP分销"];

  function localDate(value = new Date()) {
    const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }

  function quickDateRange(preset, now = new Date()) {
    if (!["today", "yesterday", "week", "month", "custom"].includes(preset)) {
      throw new Error("不支持的日期快捷区间");
    }
    const end = new Date(now); const start = new Date(now);
    if (preset === "yesterday") { start.setDate(start.getDate() - 1); end.setDate(end.getDate() - 1); }
    if (preset === "week") start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
    if (preset === "month") start.setDate(1);
    return preset === "custom" ? null : { start: localDate(start), end: localDate(end) };
  }

  function skuFromSearch(search) {
    return new URLSearchParams(search || "").get("sku") || "";
  }

  function compareNotice(compare) {
    return compare === "target"
      ? "目标数据待接入；当前不会生成目标对比结果。"
      : "筛选条件在页面间继承；未接入字段会返回待接入，不会静默伪造过滤结果。";
  }

  return { BUSINESS_UNITS, localDate, quickDateRange, skuFromSearch, compareNotice };
});

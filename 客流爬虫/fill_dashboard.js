#!/usr/bin/env node
/**
 * 把客流数据填入看板 APR_STORES flow/conv + APR_TOTAL
 * 用法: node fill_dashboard.js [flowJsonPath]
 *   flowJsonPath 缺省读取 data/flow_202608.json
 *   转化率 = 吉客云成交单数(by_apr_store) ÷ 客流 × 100
 */
import { readFileSync, writeFileSync, existsSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;
const cfg = JSON.parse(readFileSync(path.join(ROOT, 'config.json'), 'utf8'));

// 1. 读客流数据
const flowArg = process.argv[2] || path.join(ROOT, 'data', 'flow_202608.json');
if (!existsSync(flowArg)) {
  console.error('❌ 找不到客流数据: ' + flowArg + '，先运行 node fetch_flow.js');
  process.exit(1);
}
const flowData = JSON.parse(readFileSync(flowArg, 'utf8'));
const storeFlow = {}; // 看板店名 -> flow
for (const [sitekey, info] of Object.entries(flowData.stores || {})) {
  const dashName = cfg.stores[sitekey] ? cfg.stores[sitekey].name : info.name;
  storeFlow[dashName] = info.flowTotal;
}

// 2. 读成交单数（吉客云聚合）
let ordersMap = {};
const ordersSrc = cfg.dashboard.ordersSource;
if (ordersSrc && existsSync(ordersSrc)) {
  const agg = JSON.parse(readFileSync(ordersSrc, 'utf8'));
  const byStore = agg.by_apr_store || {};
  for (const [k, v] of Object.entries(byStore)) ordersMap[k] = v.orders;
}
// 兜底：config 内固定单数
const fallbackOrders = cfg.orders || {};
const orders = { ...fallbackOrders, ...ordersMap };

// 3. 看板文件
const dashPath = cfg.dashboard.path;
if (!existsSync(dashPath)) {
  console.error('❌ 看板文件不存在: ' + dashPath);
  process.exit(1);
}
let html = readFileSync(dashPath, 'utf8');

// 备份
const bak = dashPath.replace(/\.html$/, '_客流备份_' + new Date().toISOString().slice(0, 16).replace(/[:T]/g, '') + '.html');
copyFileSync(dashPath, bak);
console.log('📦 备份: ' + bak);

// 4. 逐店替换 flow/conv
let totalFlow = 0, totalOrders = 0;
const rows = [];
for (const [dashName, flow] of Object.entries(storeFlow)) {
  const ord = orders[dashName] || 0;
  const convStr = ord > 0 && flow > 0 ? (ord / flow * 100).toFixed(2) : 'null';
  const flowNum = flow || 0;
  totalFlow += flowNum;
  totalOrders += ord;
  const re = new RegExp("(\\{ name:'" + dashName + "'[^\\}]*?\\bflow:)[^,]+(,[^\\}]*?\\bconv:)[^,]+");
  const matched = html.match(re);
  if (!matched) {
    console.warn('  ⚠️ 未找到 ' + dashName + ' 的行，跳过');
    continue;
  }
  const newLine = matched[0];
  const newVal = matched[1] + flowNum + matched[2] + convStr;
  if (newLine === newVal) {
    console.log('  ✓ ' + dashName + ' 已是最新（flow=' + flowNum + ' conv=' + convStr + '%）');
    rows.push({ name: dashName, flow: flowNum, conv: convStr, orders: ord });
    continue;
  }
  html = html.replace(re, (m, g1, g2) => g1 + flowNum + g2 + convStr);
  rows.push({ name: dashName, flow: flowNum, conv: convStr, orders: ord });
  console.log('  ✅ ' + dashName + ': flow=' + flowNum + ' conv=' + convStr + '%');
}

// 5. APR_TOTAL
const totalConv = totalOrders > 0 && totalFlow > 0 ? (totalOrders / totalFlow * 100).toFixed(2) : 'null';
html = html.replace(/(let APR_TOTAL = \{[^\}]*?\bflow:)[^,]+(,[^\}]*?\bconv:)[^,]+/, (m, g1, g2) => g1 + totalFlow + g2 + totalConv);
console.log('  ✅ APR_TOTAL: flow=' + totalFlow + ' conv=' + totalConv + '%');

writeFileSync(dashPath, html);
console.log('💾 已写入: ' + dashPath);
console.log('');
console.log('汇总：');
for (const r of rows) console.log('  ' + r.name.padEnd(8) + r.flow + ' 人次 | 转化率 ' + r.conv + '%');
console.log('  合计 ' + totalFlow + ' 人次 | 转化率 ' + totalConv + '%');

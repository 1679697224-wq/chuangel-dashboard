#!/usr/bin/env node
/**
 * 抓取门店客流（进店客流）
 * 用法: node fetch_flow.js [开始日期] [结束日期] [--refresh-sites] [--manual 验证码]
 *   e.g. node fetch_flow.js 2026/08/01 2026/08/26
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { IpvaClient } from './lib/ipva.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;

// 解析参数
const args = process.argv.slice(2);
let dates = [];
let refreshSites = false;
let manualCode = '';
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--refresh-sites') refreshSites = true;
  else if (args[i] === '--manual') manualCode = args[++i] || '';
  else if (/^\d{4}\/\d{2}\/\d{2}$/.test(args[i])) dates.push(args[i]);
}
const dateBegin = dates[0] || '2026/08/01';
const dateEnd = dates[1] || (dates[0] || '2026/08/26');

const cfg = JSON.parse(readFileSync(path.join(ROOT, 'config.json'), 'utf8'));
mkdirSync(path.join(ROOT, 'data'), { recursive: true });

console.log('🚀 抓取客流：' + dateBegin + ' ~ ' + dateEnd + (refreshSites ? '（刷新门店树）' : ''));
const client = new IpvaClient();

// 1. 登录
const ok = await client.ensureLogin(12, manualCode);
if (!ok) {
  console.error('❌ 登录失败：自动识别验证码多次未通过。');
  console.error('   请打开 ' + path.join(ROOT, 'captcha_manual.png') + ' 查看验证码，');
  console.error('   把 4 个字符写入 ' + path.join(ROOT, 'captcha_answer.txt') + '，再运行一次。');
  process.exit(1);
}

// 2. 门店树（用配置里的门店 key，可选刷新）
const storeMap = cfg.stores; // sitekey -> {name, siteName}
if (refreshSites) {
  console.log('🌳 刷新门店树...');
  await client.refreshSites(dateBegin, dateEnd);
}

// 3. 逐店抓每日客流
const results = {};
for (const [sitekey, info] of Object.entries(storeMap)) {
  const days = await client.getFlowTrend(sitekey, dateBegin, dateEnd);
  const validDays = days.filter(d => d.flow != null && d.flow > 0);
  const total = validDays.reduce((a, d) => a + d.flow, 0);
  results[sitekey] = {
    name: info.name,
    siteName: info.siteName,
    flowTotal: total,
    validDays: validDays.length,
    days: days
  };
  console.log('  📊 ' + info.name.padEnd(8) + ' 客流 ' + String(total).padEnd(7) + '（有效 ' + validDays.length + ' 天）');
  await new Promise(r => setTimeout(r, 350));
}

// 4. 保存
const out = {
  period: { begin: dateBegin, end: dateEnd },
  fetchedAt: new Date().toISOString(),
  total: Object.values(results).reduce((a, r) => a + r.flowTotal, 0),
  stores: results
};
const outFile = path.join(ROOT, 'data', 'flow_' + dateBegin.slice(0, 7).replace('/', '') + '.json');
writeFileSync(outFile, JSON.stringify(out, null, 1));
console.log('✅ 完成，已保存: ' + outFile);
console.log('   总客流: ' + out.total);

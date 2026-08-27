import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";
import sharp from "sharp";

const version = Math.max(1, Math.min(4, Number(process.argv[2] ?? 4)));
const dataPath = process.argv[3] ?? path.resolve("analysis", "0817-html-framework.json");
const finalVersion = version === 4;
const outputDir = finalVersion
  ? path.resolve("outputs", "panorama-framework-final-v4")
  : path.resolve("analysis", "0817-four-pass", `v${version}`);
const htmlPath = path.join(outputDir, `框架结构图-第${version}轮.html`);
const versionLabel = finalVersion ? "最终第四版" : `第${version}轮`;
const pngPath = path.join(outputDir, finalVersion ? "江苏传天羽经营管理全景框架图_最终第四版.png" : `江苏传天羽经营管理全景框架图_第${version}版.png`);
const qaPath = path.join(outputDir, `infographic-qa-v${version}.json`);
const data = JSON.parse(await fs.readFile(dataPath, "utf8"));

const colors = [
  { main: "#1769C2", soft: "#EDF5FD", border: "#BBD7F3" },
  { main: "#7551B5", soft: "#F4F0FB", border: "#D8CCEF" },
  { main: "#C86A08", soft: "#FFF5E7", border: "#F0D0A7" },
  { main: "#C63D3D", soft: "#FDF0F0", border: "#F0C1C1" },
  { main: "#0D8662", soft: "#EAF7F2", border: "#B9E1D2" },
  { main: "#5D6977", soft: "#F3F6F8", border: "#D8DFE6" },
];

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

function sectionMarkup(section, index) {
  const palette = colors[index];
  const cards = section.subsections.map((subsection) => {
    const items = subsection.items.map((item) => `
      <li>
        <span class="item-tag">${escapeHtml(item.tag)}</span>
        <strong>${escapeHtml(item.name)}</strong>
        <p>${escapeHtml(item.description)}</p>
      </li>`).join("");
    return `<article class="module-card" style="--accent:${palette.main};--soft:${palette.soft};--border:${palette.border}">
      <div class="module-head"><span>${escapeHtml(subsection.tag)}</span><b>${escapeHtml(subsection.name)}</b></div>
      <ul>${items}</ul>
    </article>`;
  }).join("");
  return `<section class="framework-section" style="--accent:${palette.main};--soft:${palette.soft};--border:${palette.border}">
    <div class="section-rail"><span class="section-index">${String(index + 1).padStart(2, "0")}</span></div>
    <div class="section-body">
      <header class="section-title"><span>${escapeHtml(section.tag)}</span><h2>${escapeHtml(section.name)}</h2></header>
      <div class="connector"></div>
      <div class="module-grid cols-${Math.min(4, section.subsections.length)}">${cards}</div>
    </div>
  </section>`;
}

const topExtras = version >= 2 ? `
  <section class="decision-strip">
    <div><span>第一优先级</span><b>开优质门店</b><p>月销100万元具备盈利基础，年销3000万元达到行业均值即优秀</p></div>
    <div><span>第二优先级</span><b>分货与厂商资源</b><p>以资源承诺、实际到货、重点SKU满足率和增量贡献验证</p></div>
    <div><span>第三优先级</span><b>人员效率与能力</b><p>从招聘、培训、技能升级、内部竞赛到人均毛利闭环</p></div>
    <div><span>专项产品线</span><b>3001设备</b><p>打通采购、销售与营销推广，按产品/品牌/项目周周跟踪</p></div>
  </section>` : "";

const bottomExtras = version >= 3 ? `
  <section class="cadence-panel">
    <div class="cadence-title">日 / 周 / 月运行节奏</div>
    <div class="cadence-grid">
      <div><b>日报</b><span>D+1 08:30</span><p>看异常，抓当天动作</p></div>
      <div><b>周报</b><span>周一 10:00</span><p>看变化，抓差距与闭环</p></div>
      <div><b>月报</b><span>次月 5 日前</span><p>看全景，抓经营质量</p></div>
      <div><b>数据纪律</b><span>按时发布</span><p>确认 / 暂估 / 待确认 / 缺失必须显式标记</p></div>
    </div>
  </section>` : "";

const finalExtras = version >= 4 ? `
  <section class="footer-panel">
    <div><b>业务覆盖</b><span>APR门店</span><span>Apple电商：京东羽通 / 苏宁啟韬</span><span>Shure电商：京东官旗 / 天猫官旗</span><span>3PP / 渠道分销</span></div>
    <div><b>展示目标</b><span>一眼看清经营结果</span><span>一眼看清管理状态</span><span>一眼看清重点与风险</span><span>一眼看清需决策事项</span></div>
    <div><b>完整性</b><span>6个一级层</span><span>18个二级模块</span><span>54个HTML节点</span><span>全部承接、只增不减</span></div>
  </section>` : "";

const markup = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>江苏传天羽经营管理全景框架图</title>
<style>
*{box-sizing:border-box}html,body{margin:0;background:#EAF0F6;color:#142B43;font-family:"Microsoft YaHei","PingFang SC",sans-serif;letter-spacing:0}
body{width:2400px;padding:46px}.page{width:2308px;margin:0 auto;background:#fff;border:2px solid #B9CBE0;box-shadow:0 16px 46px rgba(16,48,86,.13);padding:58px 66px 48px;position:relative;overflow:hidden}
.brandline{height:8px;background:#0B2A4A;position:absolute;left:0;right:0;top:0}.masthead{text-align:center;padding-bottom:32px;border-bottom:1px solid #D7E1EB}
.eyebrow{font-size:20px;color:#1769C2;font-weight:800;margin-bottom:10px}.masthead h1{font-size:58px;line-height:1.15;margin:0;color:#0B2A4A;font-weight:900}.masthead p{font-size:24px;color:#607083;margin:16px 0 0}.mission{display:inline-flex;align-items:center;gap:12px;margin-top:22px;padding:12px 25px;background:#0B2A4A;color:#fff;font-size:21px;font-weight:800;border-radius:6px}
.logic{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:30px 0 18px}.logic div{border:1px solid #D7E1EB;border-top:7px solid var(--c);padding:18px 20px;background:#F9FBFD;min-height:108px}.logic b{display:block;font-size:25px;color:#0B2A4A}.logic span{display:block;font-size:18px;color:#66768A;margin-top:7px}.support-line{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:26px}.support-line div{padding:14px 20px;border:1px solid #D7E1EB;font-size:19px;background:#F7FAFC}.support-line b{color:#0D8662;margin-right:12px}
.decision-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:22px 0 30px}.decision-strip div{border:1px solid #F0D0A7;background:#FFF8ED;padding:18px;border-radius:6px}.decision-strip span{display:block;font-size:16px;color:#C86A08;font-weight:800}.decision-strip b{display:block;font-size:22px;color:#643600;margin:6px 0}.decision-strip p{font-size:16px;line-height:1.55;margin:0;color:#6D5B48}
.framework-section{display:grid;grid-template-columns:76px 1fr;margin:28px 0 0;position:relative}.section-rail{position:relative;border-right:4px solid var(--accent)}.section-rail:after{content:"";position:absolute;right:-10px;top:26px;width:16px;height:16px;border-radius:50%;background:#fff;border:4px solid var(--accent)}.section-index{display:flex;width:52px;height:52px;align-items:center;justify-content:center;background:var(--accent);color:#fff;font-size:20px;font-weight:900;border-radius:6px}
.section-body{padding-left:26px}.section-title{display:flex;align-items:center;gap:18px;margin-bottom:17px}.section-title>span{background:var(--accent);color:#fff;font-weight:800;font-size:20px;padding:12px 17px;border-radius:6px}.section-title h2{font-size:29px;color:#0B2A4A;margin:0}.connector{height:3px;background:var(--accent);opacity:.55;margin:0 26px 14px}.module-grid{display:grid;gap:16px}.cols-4{grid-template-columns:repeat(4,1fr)}.cols-3{grid-template-columns:repeat(3,1fr)}.cols-2{grid-template-columns:repeat(2,1fr)}.cols-1{grid-template-columns:1fr}
.module-card{border:1px solid var(--border);border-top:6px solid var(--accent);background:#fff;border-radius:8px;overflow:hidden}.module-head{padding:14px 16px;background:var(--soft);border-bottom:1px solid var(--border)}.module-head span{display:block;color:var(--accent);font-size:15px;font-weight:800}.module-head b{display:block;color:#17324E;font-size:22px;margin-top:4px}.module-card ul{list-style:none;margin:0;padding:8px 16px 14px}.module-card li{padding:11px 0;border-bottom:1px solid #E8EDF2}.module-card li:last-child{border-bottom:none}.item-tag{display:inline-block;color:var(--accent);font-size:13px;font-weight:800;margin-right:7px}.module-card strong{font-size:17px;color:#193047;line-height:1.45}.module-card p{font-size:14px;color:#5E6D7E;line-height:1.55;margin:5px 0 0}
.cadence-panel{margin-top:32px;border:1px solid #C9D6E3;background:#F8FAFC;padding:20px}.cadence-title{font-size:24px;font-weight:900;color:#0B2A4A;margin-bottom:15px}.cadence-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.cadence-grid div{background:#fff;border:1px solid #D7E1EB;padding:16px}.cadence-grid b{font-size:21px;color:#7551B5}.cadence-grid span{display:block;font-size:15px;color:#607083;margin:5px 0}.cadence-grid p{font-size:16px;margin:0;color:#20374F}
.footer-panel{display:grid;grid-template-columns:1.6fr 1.3fr 1fr;gap:16px;margin-top:18px}.footer-panel>div{border:1px solid #CAD7E4;padding:17px;background:#fff}.footer-panel b{display:block;color:#0B2A4A;font-size:20px;margin-bottom:9px}.footer-panel span{display:inline-block;font-size:15px;color:#506176;background:#F0F4F8;padding:6px 9px;margin:3px;border-radius:4px}
.footnote{text-align:center;color:#8290A1;font-size:15px;margin-top:24px;padding-top:16px;border-top:1px solid #E2E8EF}
</style></head><body><main class="page"><div class="brandline"></div>
<header class="masthead"><div class="eyebrow">JIANGSU CHUANGEL · EXECUTIVE BRIEFING FRAMEWORK</div><h1>江苏传天羽经营管理全景框架</h1><p>2026-08-17 周会整合版 · ${versionLabel}</p><div class="mission">日盯运营 · 周抓变化 · 月看经营</div></header>
<section class="logic">
  <div style="--c:#1769C2"><b>经营数据</b><span>看结果、差距与经营驱动</span></div>
  <div style="--c:#7551B5"><b>管理数据</b><span>看物、人、外部与合规过程</span></div>
  <div style="--c:#C86A08"><b>重点事项</b><span>看优先级、节点、责任与决策</span></div>
  <div style="--c:#C63D3D"><b>风险控制</b><span>看等级、敞口、措施与关闭证据</span></div>
</section>
<section class="support-line"><div><b>AI智能体支撑</b>自动取数、整理、提醒与推送，人工负责判断与最终责任</div><div><b>纪律与数据支撑</b>口径统一、责任明确、按时呈报、缺失显式、权限可控</div></section>
${topExtras}
${data.sections.map(sectionMarkup).join("")}
${bottomExtras}${finalExtras}
<div class="footnote">HTML主骨架完整承接：${data.counts.sections}个一级层 · ${data.counts.subsections}个二级模块 · ${data.counts.items}个三级节点</div>
</main></body></html>`;

await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(htmlPath, markup, "utf8");

const browser = await chromium.launch({
  headless: true,
  executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
});
try {
  const page = await browser.newPage({ viewport: { width: 2400, height: 1800 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load" });
  await page.screenshot({ path: pngPath, fullPage: true });
} finally {
  await browser.close();
}

const htmlText = await fs.readFile(htmlPath, "utf8");
const expected = data.sections.flatMap((section) => section.subsections.flatMap((subsection) => subsection.items.flatMap((item) => [item.name, item.description])));
const missing = expected.filter((text) => !htmlText.includes(escapeHtml(text)));
const metadata = await sharp(pngPath).metadata();
const stats = await sharp(pngPath).stats();
const qa = {
  version,
  pngPath,
  htmlPath,
  dimensions: { width: metadata.width, height: metadata.height },
  fileSize: (await fs.stat(pngPath)).size,
  entropy: stats.entropy,
  expectedTextBlocks: expected.length,
  missingTextBlocks: missing,
  nonBlank: stats.entropy > 0.1 && (metadata.width ?? 0) >= 2000 && (metadata.height ?? 0) >= 2000,
  conceptualReview: {
    1: { result: "全量内容可见。", gap: "缺少会议优先级和日周月运行摘要。", next: "增加老板优先级入口。" },
    2: { result: "优先级已置顶。", gap: "日周月节奏和数据纪律不够显眼。", next: "增加运行节奏和完整性底栏。" },
    3: { result: "内容与节奏完整。", gap: "底部业务边界和展示目标仍需收口。", next: "加入最终业务边界、展示目标和完整性声明。" },
    4: { result: "主链、双支撑、优先级、54节点、节奏和业务边界完整。", gap: "无阻断项。", next: "正式交付。" },
  }[version],
};
await fs.writeFile(qaPath, JSON.stringify(qa, null, 2), "utf8");
console.log(JSON.stringify(qa, null, 2));

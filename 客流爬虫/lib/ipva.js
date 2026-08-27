/**
 * IPVA 客流系统 API 客户端（汇纳科技 apple.winneryun.com）
 * 登录 + 门店树 + 客流趋势抓取，token 自动轮换
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');

// ---------- 配置 ----------
const RSA_PUB = [
  "-----BEGIN PUBLIC KEY-----",
  "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC7PyjMEuniN6BPn8oqzIZ6AO1NjSTO9R3adCCIwKfKIEoWXXM+tHDpktdPKSaAsWJPTNAGvEvtxOfzXib/EMXKqD0eUy5MatfpRjRdf1hJVimmfrb09Qx2j7CsKLy7nD23m4xubdYBwvkjMwt/L3JxB5D6qryW1wei/j1c+/OCxQIDAQAB",
  "-----END PUBLIC KEY-----"
].join("\n");

function loadConfig() {
  return JSON.parse(readFileSync(path.join(ROOT, 'config.json'), 'utf8'));
}

function tokenFile() { return path.join(ROOT, 'data', 'token.txt'); }
function sitesFile() { return path.join(ROOT, 'data', 'sites.json'); }

// ---------- 工具 ----------
const sleep = ms => new Promise(r => setTimeout(r, ms));

function rsaEncrypt(plain) {
  return crypto.publicEncrypt(
    { key: RSA_PUB, padding: crypto.constants.RSA_PKCS1_PADDING },
    Buffer.from(plain)
  ).toString('base64');
}

// ---------- OCR 验证码 ----------
function ocrCaptcha(gifPath) {
  const cfg = loadConfig();
  const bin = path.resolve(ROOT, cfg.ocr.binary);
  if (!existsSync(bin)) return '';
  let best = '';
  for (const scale of [300, 400, 500, 600, 800]) {
    const png = gifPath.replace(/\.gif$/, '_' + scale + '.png');
    try {
      execSync('sips -s format png "' + gifPath + '" --out "' + png + '" -Z ' + scale + ' >/dev/null 2>&1');
      const out = execSync('"' + bin + '" "' + png + '" 0 0 2>/dev/null', { encoding: 'utf8' });
      const text = out.split(/\s+/).filter(Boolean).join('');
      if (text.length > best.length) best = text;
    } catch {}
  }
  try {
    const png = gifPath.replace(/\.gif$/, '_n.png');
    execSync('sips -s format png "' + gifPath + '" --out "' + png + '" >/dev/null 2>&1');
    const out = execSync('"' + bin + '" "' + png + '" 0 0 2>/dev/null', { encoding: 'utf8' });
    const text = out.split(/\s+/).filter(Boolean).join('');
    if (text.length > best.length) best = text;
  } catch {}
  return best.trim();
}

// ---------- API ----------
export class IpvaClient {
  constructor() {
    this.cfg = loadConfig();
    this.base = this.cfg.system.base;
    this.token = '';
    this.userId = '';
    this.userName = '';
    if (existsSync(tokenFile())) {
      try {
        const saved = JSON.parse(readFileSync(tokenFile(), 'utf8'));
        this.token = saved.token || '';
        this.userId = saved.userId || '';
        this.userName = saved.userName || '';
      } catch {}
    }
  }

  headers() {
    const h = {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Content-Type': 'application/json',
      'Origin': 'https://apple.winneryun.com',
      'Referer': 'https://apple.winneryun.com/login'
    };
    if (this.token) h.Authorization = this.token;
    return h;
  }

  saveToken() {
    writeFileSync(tokenFile(), JSON.stringify({
      token: this.token, userId: this.userId, userName: this.userName, savedAt: new Date().toISOString()
    }, null, 1));
  }

  async post(path, body) {
    const resp = await fetch(this.base + path, {
      method: 'POST', headers: this.headers(), body: JSON.stringify(body)
    });
    const newAuth = resp.headers.get('authorization');
    if (newAuth) this.token = newAuth;
    const text = await resp.text();
    let json = {};
    try { json = JSON.parse(text); } catch {}
    return { status: resp.status, json, text };
  }

  tokenValid() {
    if (!this.token) return false;
    try {
      const jwt = this.token.replace(/^Bearer\s+/i, '');
      const payload = JSON.parse(Buffer.from(jwt.split('.')[1], 'base64url').toString());
      if (payload.exp) return payload.exp * 1000 > Date.now() + 5 * 60 * 1000;
      return true;
    } catch { return false; }
  }

  async login(maxAttempts = 12, manualCode = '') {
    const { user, password } = this.cfg.system;
    for (let i = 0; i < maxAttempts; i++) {
      const id = Math.floor(Math.random() * 900 + 100);
      const cap = await this.post('/Captcha/getCaptcha', {
        menuId: '', userId: '', lang: 'zh-cn', Params: { Id: id }
      });
      if (cap.json.code !== '0' || !cap.json.msg) { await sleep(800); continue; }
      const gif = path.join(ROOT, 'data', 'cap.gif');
      writeFileSync(gif, Buffer.from(cap.json.msg.code, 'base64'));
      let code = manualCode;
      if (!code) code = ocrCaptcha(gif);
      if (!code) {
        try {
          execSync('sips -s format png "' + gif + '" --out "' + path.join(ROOT, 'captcha_manual.png') + '" -Z 600 >/dev/null 2>&1');
        } catch {}
        const ansFile = path.join(ROOT, 'captcha_answer.txt');
        if (existsSync(ansFile)) {
          code = readFileSync(ansFile, 'utf8').trim();
          if (code) { try { writeFileSync(ansFile, ''); } catch {} }
        }
        if (!code) {
          console.log('  ⚠️ 验证码识别失败，请打开 ' + path.join(ROOT, 'captcha_manual.png') + ' 并把 4 个字符写入 captcha_answer.txt 后重试');
          await sleep(3000);
          continue;
        }
      }
      const loginResp = await this.post('/Login/loginSystem', {
        menuId: '', userId: '', lang: 'zh-cn',
        params: { UserName: user, PassWord: rsaEncrypt(password), Id: String(id), Code: code }
      });
      if (loginResp.json.code === '0') {
        this.userId = loginResp.json.msg.userID;
        this.userName = loginResp.json.msg.realName;
        this.saveToken();
        console.log('  ✅ 登录成功：' + this.userName + '（' + this.userId + '）');
        return true;
      }
      console.log('  ❌ 第 ' + (i + 1) + ' 次验证码错误（OCR=' + JSON.stringify(code) + '）');
      await sleep(900);
    }
    return false;
  }

  async ensureLogin(maxAttempts = 12, manualCode = '') {
    if (this.tokenValid() && this.userId) {
      console.log('  🔑 复用已有登录（token 有效）');
      return true;
    }
    console.log('  🔐 需要登录...');
    return this.login(maxAttempts, manualCode);
  }

  async getSites(parentKey, dateBegin, dateEnd) {
    const biz = this.cfg.business;
    const body = {
      userId: this.userId, lang: 'zh-cn', menuId: biz.menuId,
      params: {
        businessKey: biz.businessKey, dateType: 'd',
        startDate: dateBegin, endDate: dateEnd,
        sitekey: parentKey, accurateType: '', async: '2'
      }
    };
    const r = await this.post('/SiteTree/GetTrafficSites', body);
    return (r.json && r.json.msg) || [];
  }

  async refreshSites(dateBegin, dateEnd) {
    const all = new Map();
    const queue = ['G00001'];
    let guard = 0;
    while (queue.length && guard < 500) {
      const parent = queue.shift();
      guard++;
      const nodes = await this.getSites(parent, dateBegin, dateEnd);
      for (const n of nodes) {
        if (!all.has(n.sitekey)) {
          all.set(n.sitekey, { sitekey: n.sitekey, name: n.name, siteType: n.siteType, pId: n.pId, isLeaf: !!n.isLeaf });
          if (!n.isLeaf) queue.push(n.sitekey);
        }
      }
      await sleep(250);
    }
    writeFileSync(sitesFile(), JSON.stringify([...all.values()], null, 1));
    return [...all.values()];
  }

  async getSitesCached(dateBegin, dateEnd, refresh = false) {
    if (!refresh && existsSync(sitesFile())) {
      try { return JSON.parse(readFileSync(sitesFile(), 'utf8')); } catch {}
    }
    return this.refreshSites(dateBegin, dateEnd);
  }

  async getFlowTrend(sitekey, dateBegin, dateEnd) {
    const biz = this.cfg.business;
    const body = {
      userId: this.userId, lang: 'zh-cn', menuId: biz.menuId,
      params: {
        indicator: 1, selType: 0, isClose: 0,
        module: biz.module, accurateType: '',
        dateType: 'd', beginDate: dateBegin, endDate: dateEnd,
        SiteTreeSelects: [{ source: '0', type: '0', code: sitekey, operators: [] }]
      }
    };
    const r = await this.post('/PassengerGeneral/trafficFlowTrendChart', body);
    const days = ((r.json && r.json.msg) || []).map(d => ({
      date: (d.hour || '').slice(0, 10),
      flow: d.currValue == null ? null : Number(d.currValue)
    }));
    return days;
  }
}

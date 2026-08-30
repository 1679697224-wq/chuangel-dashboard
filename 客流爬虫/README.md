# 门店客流爬虫（IPVA 客流分析系统 → 经营看板）

自动登录汇纳科技客流系统（apple.winneryun.com），抓取 10 家门店的进店客流，
按「吉客云成交单数 ÷ 客流」计算转化率，写入经营看板 `APR_STORES` 的 flow/conv。

## 目录

| 文件 | 作用 |
|---|---|
| `config.json` | 系统账号、门店 sitekey 映射、看板路径（改这里） |
| `fetch_flow.js` | 抓取每日客流 → `data/flow_YYYYMM.json` |
| `fill_dashboard.js` | 客流+转化率写入看板（自动备份原文件） |
| `run_daily.sh` | 每日一键：抓取 + 填表 |
| `lib/ipva.js` | 登录/门店树/客流 API 封装（token 自动轮换） |
| `bin/ocr_v2` | 验证码 OCR（Vision 框架，含源码 ocr_v2.m） |
| `data/` | 门店树缓存和客流数据；token不再保存在仓库目录 |

Token通过 `IPVA_ACCESS_TOKEN` 环境变量注入，或由 `IPVA_TOKEN_FILE` 指向仓库外的私有运行时文件。未指定路径时使用用户私有目录，文件权限为仅当前用户可读写。

## 使用

```bash
cd "/Users/lili/Desktop/deepseek harness/客流爬虫"

# 抓 8 月 1~26 日客流
node fetch_flow.js 2026/08/01 2026/08/26

# 填进看板（先备份，再逐店替换 flow/conv + APR_TOTAL）
node fill_dashboard.js

# 每日自动（月初 ~ 昨天）
./run_daily.sh
```

## 每日定时（macOS 用 launchd 或 cron 二选一）

**launchd（推荐）**，每天 08:30 运行，把下面内容存为 `~/Library/LaunchAgents/com.chuangel.keiliu.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.chuangel.keiliu</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>/Users/lili/Desktop/deepseek harness/客流爬虫/run_daily.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>
  <key>StandardOutPath</key><string>/Users/lili/Desktop/deepseek harness/客流爬虫/data/launchd.out.log</string>
  <key>StandardErrorPath</key><string>/Users/lili/Desktop/deepseek harness/客流爬虫/data/launchd.err.log</string>
</dict></plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.chuangel.keiliu.plist
```

**cron**：`crontab -e` 加一行
```
30 8 * * * /bin/bash "/Users/lili/Desktop/deepseek harness/客流爬虫/run_daily.sh" >> "/Users/lili/Desktop/deepseek harness/客流爬虫/data/cron.log" 2>&1
```

## 验证码说明（重要）

系统登录有 4 字中文验证码，机器识别成功率不高。设计了两级回退：

1. 自动：`bin/ocr_v2` 多尺度 OCR 试 12 次（约 1 分钟）；
2. 人工：自动失败后生成 `captcha_manual.png`，把看到的 4 个字符写入 `captcha_answer.txt`，
   再运行一次即可（脚本会读取该文件）。

Token 缓存 2 小时有效，期间抓取无需重新登录。

## 数据口径

- 客流：客流系统「进店客流」口径，按日趋势求和；
- 转化率：吉客云已支付成交单数（`吉客云数据/sales_agg.json` 的 by_apr_store）÷ 客流 × 100；
- 镇江店 8/1-11 系统无数据（重开），按实际有效天数汇总；
- 徐州宝龙店 = 系统登记「徐州复兴苏宁广场店」（已与业务确认）。

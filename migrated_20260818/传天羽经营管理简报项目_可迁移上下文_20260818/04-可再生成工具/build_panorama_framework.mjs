import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const version = Math.max(1, Math.min(4, Number(process.argv[2] ?? 4)));
const sourceWorkbookPath = process.argv[3];
const htmlJsonPath = process.argv[4] ?? path.resolve("analysis", "0817-html-framework.json");
if (!sourceWorkbookPath) throw new Error("Source workbook path is required");

const finalVersion = version === 4;
const outputDir = finalVersion
  ? path.resolve("outputs", "panorama-framework-final-v4")
  : path.resolve("analysis", "0817-four-pass", `v${version}`);
const previewDir = path.join(outputDir, "workbook-previews");
const outputPath = path.join(
  outputDir,
  finalVersion
    ? "江苏传天羽经营管理全景简报框架_最终第四版.xlsx"
    : `江苏传天羽经营管理全景简报框架_第${version}版.xlsx`,
);

const htmlData = JSON.parse(await fs.readFile(htmlJsonPath, "utf8"));
const sourceWorkbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourceWorkbookPath));
const workbook = Workbook.create();

const C = {
  navy: "#0B2A4A", navy2: "#133F6D", blue: "#1769C2", blueSoft: "#EAF3FC",
  purple: "#7454B7", purpleSoft: "#F2EEFB", amber: "#C96A08", amberSoft: "#FFF3E3",
  red: "#C63D3D", redSoft: "#FCEBEC", green: "#0C8461", greenSoft: "#E8F6F0",
  cyan: "#147E98", cyanSoft: "#E8F5F8", gray: "#5D6977", graySoft: "#F3F6F8",
  line: "#D7E0E8", line2: "#E8EDF2", text: "#193047", white: "#FFFFFF",
  input: "#FFF7DF", formula: "#E8F2FF",
};
const border = { preset: "all", style: "thin", color: C.line };
const softBorder = { preset: "all", style: "thin", color: C.line2 };

function columnName(number) {
  let n = number;
  let result = "";
  while (n > 0) {
    n -= 1;
    result = String.fromCharCode(65 + (n % 26)) + result;
    n = Math.floor(n / 26);
  }
  return result;
}

function nonEmpty(row) {
  return row.some((value) => value !== null && value !== undefined && String(value).trim() !== "");
}

function trimRows(values) {
  const rows = values.map((row) => [...row]);
  while (rows.length && !nonEmpty(rows.at(-1))) rows.pop();
  return rows;
}

function sectionColor(name) {
  if (name.includes("经营数据")) return [C.blue, C.blueSoft];
  if (name.includes("管理数据")) return [C.purple, C.purpleSoft];
  if (name.includes("重点事项")) return [C.amber, C.amberSoft];
  if (name.includes("风控")) return [C.red, C.redSoft];
  if (name.includes("AI") || name.includes("智能体")) return [C.green, C.greenSoft];
  return [C.gray, C.graySoft];
}

function baseSheet(sheet, range) {
  sheet.showGridLines = false;
  const used = sheet.getRange(range);
  used.format.font = { name: "Microsoft YaHei", size: 9, color: C.text };
  used.format.verticalAlignment = "center";
  used.format.wrapText = true;
}

function setWidths(sheet, widths) {
  for (const [col, width] of Object.entries(widths)) sheet.getRange(`${col}:${col}`).format.columnWidth = width;
}

function titleBand(sheet, lastCol, title, subtitle) {
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: C.navy, font: { name: "Microsoft YaHei", size: 18, bold: true, color: C.white },
    horizontalAlignment: "left", verticalAlignment: "center",
  };
  sheet.getRange(`A1:${lastCol}1`).format.rowHeight = 34;
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: C.blueSoft, font: { name: "Microsoft YaHei", size: 9, color: C.gray },
    horizontalAlignment: "left", verticalAlignment: "center",
  };
  sheet.getRange(`A2:${lastCol}2`).format.rowHeight = 24;
}

function noteBand(sheet, row, lastCol, text, tone = "blue") {
  const tones = { blue: [C.blueSoft, C.blue], green: [C.greenSoft, C.green], amber: [C.amberSoft, C.amber], red: [C.redSoft, C.red], gray: [C.graySoft, C.gray] };
  const [fill, color] = tones[tone] ?? tones.blue;
  sheet.getRange(`A${row}:${lastCol}${row}`).merge();
  sheet.getRange(`A${row}`).values = [[text]];
  sheet.getRange(`A${row}:${lastCol}${row}`).format = {
    fill, font: { bold: true, color, size: 9 }, horizontalAlignment: "left", verticalAlignment: "center", wrapText: true,
  };
  sheet.getRange(`A${row}:${lastCol}${row}`).format.rowHeight = 28;
}

function sectionBand(sheet, row, lastCol, text, color = C.blue) {
  sheet.getRange(`A${row}:${lastCol}${row}`).merge();
  sheet.getRange(`A${row}`).values = [[text]];
  sheet.getRange(`A${row}:${lastCol}${row}`).format = {
    fill: color, font: { bold: true, color: C.white, size: 11 }, horizontalAlignment: "left", verticalAlignment: "center",
  };
  sheet.getRange(`A${row}:${lastCol}${row}`).format.rowHeight = 26;
}

function styleHeader(range) {
  range.format = {
    fill: C.navy2, font: { name: "Microsoft YaHei", size: 9, bold: true, color: C.white },
    horizontalAlignment: "center", verticalAlignment: "center", wrapText: true, borders: border,
  };
  range.format.rowHeight = 30;
}

function styleBody(range) {
  range.format = {
    fill: C.white, font: { name: "Microsoft YaHei", size: 9, color: C.text },
    horizontalAlignment: "left", verticalAlignment: "center", wrapText: true, borders: softBorder,
  };
}

function genericWidths(count) {
  const widths = {};
  for (let i = 1; i <= count; i += 1) widths[columnName(i)] = i <= 2 ? 14 : i <= 4 ? 24 : 29;
  return widths;
}

function sourceValues(sheetName) {
  const sourceSheet = sourceWorkbook.worksheets.getItem(sheetName);
  return trimRows(sourceSheet.getUsedRange(false)?.values ?? []);
}

function buildSourceTable(sourceName, destName, options = {}) {
  const values = sourceValues(sourceName);
  const colCount = Math.max(...values.map((row) => row.length));
  const lastCol = columnName(colCount);
  const sheet = workbook.worksheets.add(destName);
  baseSheet(sheet, `A1:${lastCol}${Math.max(8, values.length + (options.extraRows?.length ?? 0) + 2)}`);
  titleBand(sheet, lastCol, options.title ?? values[0]?.[0] ?? destName, options.subtitle ?? values[1]?.[0] ?? "");
  noteBand(sheet, 3, lastCol, options.note ?? values[2]?.[0] ?? "主表只保留结论与异常，明细进入附表。", options.noteTone ?? "blue");
  const headers = [...(values[3] ?? [])];
  while (headers.length < colCount) headers.push("");
  sheet.getRange(`A4:${lastCol}4`).values = [headers];
  styleHeader(sheet.getRange(`A4:${lastCol}4`));
  const dataRows = values.slice(4).filter(nonEmpty).map((row) => {
    const copy = [...row];
    while (copy.length < colCount) copy.push("");
    return copy.slice(0, colCount);
  });
  if (options.extraRows?.length) {
    for (const row of options.extraRows) {
      const copy = [...row];
      while (copy.length < colCount) copy.push("");
      dataRows.push(copy.slice(0, colCount));
    }
  }
  if (dataRows.length) {
    sheet.getRange(`A5:${lastCol}${dataRows.length + 4}`).values = dataRows;
    styleBody(sheet.getRange(`A5:${lastCol}${dataRows.length + 4}`));
    for (let row = 5; row <= dataRows.length + 4; row += 1) sheet.getRange(`A${row}:${lastCol}${row}`).format.rowHeight = options.rowHeight ?? 48;
  }
  const widths = options.widths ?? genericWidths(colCount);
  setWidths(sheet, widths);
  sheet.freezePanes.freezeRows(4);
  if (options.colorByCategory) {
    dataRows.forEach((row, index) => {
      const category = String(row[options.categoryColumn ?? 1] ?? "");
      const [color, fill] = sectionColor(category);
      sheet.getRange(`A${index + 5}:B${index + 5}`).format.fill = fill;
      sheet.getRange(`A${index + 5}:B${index + 5}`).format.font = { bold: true, color, size: 9 };
    });
  }
  return sheet;
}

function flatHtmlItems() {
  const rows = [];
  htmlData.sections.forEach((section, sIndex) => {
    section.subsections.forEach((subsection, subIndex) => {
      subsection.items.forEach((item, itemIndex) => {
        rows.push({
          id: `H${sIndex + 1}.${subIndex + 1}.${itemIndex + 1}`,
          section: section.name,
          sectionTag: section.tag,
          subsection: subsection.name,
          subsectionTag: subsection.tag,
          tag: item.tag,
          name: item.name,
          description: item.description,
        });
      });
    });
  });
  return rows;
}

const htmlItems = flatHtmlItems();

function supplementFor(item) {
  const key = `${item.name} ${item.description}`;
  if (key.includes("开优质店")) return "会议明确苹果线下第一优先级；按月销100万元、年销3000万元等经营标准持续验证店效。";
  if (key.includes("分货")) return "会议明确第二优先级；同步跟踪厂商/总代沟通、资源承诺、实际到货及增量贡献。";
  if (key.includes("人员工作效率") || key.includes("人效")) return "会议明确第三优先级；用人均销售、人均毛利、同岗差距和培养结果衡量。";
  if (key.includes("收银结算")) return "会议纪要表述为收银、非单、库存周转、样机、物料和结算管理；主呈现采用规范口径，HTML原文保留。";
  if (key.includes("智能体")) return "承接会议部署：公司级经营数据/重点事项智能体与岗位智能体分层建设，人工负责确认、例外判断和最终责任。";
  if (key.includes("日报") || key.includes("周报") || key.includes("月报")) return "承接第五版日周月模板、数据责任、预警和附表规则。";
  if (item.section.includes("经营数据")) return "承接第五版经营指标、业务板块、指标口径和下钻附表。";
  if (item.section.includes("管理数据")) return "按会议确定的物、人、外部资源、内部合规四维管理框架落表。";
  if (item.section.includes("重点事项")) return "进入统一事项台账，保留唯一ID、原截止日、责任人、下一节点和验证证据。";
  if (item.section.includes("风控")) return "进入红黄风险规则与升级路径；事件类重大风险不受金额阈值限制。";
  if (item.section.includes("纪律")) return "进入运行纪律、数据责任与呈报时效；缺失数据必须显式标记。";
  return "按HTML主框架保留，并由对应专题表承接。";
}

function cadenceFor(item) {
  const key = `${item.section} ${item.subsection} ${item.name}`;
  if (key.includes("日报")) return ["必呈", "复盘", "汇总"];
  if (key.includes("周报")) return ["异常", "必呈", "汇总"];
  if (key.includes("月报")) return ["异常", "趋势", "必呈"];
  if (item.section.includes("风控")) return ["事件触发/异常", "变化与闭环", "全景复盘"];
  if (item.section.includes("重点事项")) return ["节点/异常", "进度闭环", "专项复盘"];
  if (item.section.includes("AI")) return ["自动巡检", "建设进展", "成效复盘"];
  if (item.section.includes("纪律")) return ["执行检查", "质量复盘", "制度评价"];
  if (item.section.includes("管理数据")) return ["经营影响异常", "过程趋势", "组织/流程复盘"];
  return ["结果与异常", "趋势与驱动", "经营质量"];
}

function ownerFor(item) {
  const key = `${item.section} ${item.subsection} ${item.name}`;
  if (/APR|门店|开优质店/.test(key)) return "APR负责人/店长；总经办复核";
  if (/Apple电商/.test(key)) return "Apple电商负责人；财务复核";
  if (/Shure|舒尔/.test(key)) return "Shure电商负责人；财务复核";
  if (/3PP|渠道分销/.test(key)) return "3PP/采销负责人；财务复核";
  if (/资金|结算|应收|返利/.test(key)) return "财务/采销；总经办复核";
  if (/人员|编制|人效|考勤|培训|招聘/.test(key)) return "综合办/人事；业务负责人";
  if (/供应商|分货|产品流转|采购|库存/.test(key)) return "采销/商务；业务负责人";
  if (/风险|合规|纪律|越权|合同/.test(key)) return "责任部门；财务/总经办复核";
  if (/智能体|数据上线|工具选型/.test(key)) return "智能体责任人；总经办统一管理";
  return "对应责任部门；总经办汇总";
}

function carrierFor(item) {
  if (item.section.includes("经营数据")) return "日/周/月主表 + 经营附表";
  if (item.section.includes("管理数据")) return "管理四维流程表 + 异常清单";
  if (item.section.includes("重点事项")) return "重点事项台账 + 老板批复闭环";
  if (item.section.includes("风控")) return "风险台账 + 红黄预警规则";
  if (item.section.includes("AI")) return "AI智能体应用表 + 自动任务日志";
  return "运行纪律表 + 数据责任时效表";
}

function buildOverview() {
  const sheet = workbook.worksheets.add("0-老板审阅总纲");
  baseSheet(sheet, "A1:J31");
  const versionLabel = finalVersion ? "最终第四版" : `第${version}轮`;
  titleBand(sheet, "J", `江苏传天羽经营管理全景简报框架 · ${versionLabel}`, "日盯运营 · 周抓变化 · 月看经营 | HTML为完整主骨架，会议纪要与第五版仅作补充");
  noteBand(sheet, 3, "J", "核心主线：经营结果 → 管理过程 → 重点事项 → 风险控制；AI智能体与纪律/数据责任作为双支撑。", "blue");

  sectionBand(sheet, 5, "J", "一、老板看什么", C.blue);
  const core = [
    ["01", "经营数据", "公司卖了多少、赚了多少、目标进度如何", "销售/毛利/达成/驱动/板块/库存资金", "结论、差距、原因、动作"],
    ["02", "管理数据", "经营过程是否顺畅、组织是否支撑", "物/人/外部资源/内部合规", "异常、责任、节点、证据"],
    ["03", "重点事项", "公司最重要的事是否真正推进", "开优质店/分货资源/人员效率/3001/项目闭环", "进度、下一节点、需决策"],
    ["04", "风控", "风险是否识别、处置并关闭", "资金/客户/定价/营销/收银结算/合规", "红黄分级、敞口、时限、验证"],
  ];
  sheet.getRange("A6:J6").values = [["序号", "核心层", "老板问题", "覆盖范围", "最终输出", "", "", "", "", ""]];
  sheet.getRange("E6:J6").merge();
  styleHeader(sheet.getRange("A6:J6"));
  core.forEach((row, index) => {
    const r = 7 + index;
    sheet.getRange(`A${r}`).values = [[row[0]]];
    sheet.getRange(`B${r}`).values = [[row[1]]];
    sheet.getRange(`C${r}:D${r}`).merge(); sheet.getRange(`C${r}`).values = [[row[2]]];
    sheet.getRange(`E${r}:G${r}`).merge(); sheet.getRange(`E${r}`).values = [[row[3]]];
    sheet.getRange(`H${r}:J${r}`).merge(); sheet.getRange(`H${r}`).values = [[row[4]]];
    styleBody(sheet.getRange(`A${r}:J${r}`));
    const [color, fill] = sectionColor(row[1]);
    sheet.getRange(`A${r}:B${r}`).format = { fill, font: { bold: true, color }, horizontalAlignment: "center", verticalAlignment: "center", borders: softBorder };
    sheet.getRange(`A${r}:J${r}`).format.rowHeight = 42;
  });

  sectionBand(sheet, 12, "J", "二、双支撑与运行节奏", C.green);
  const support = [
    ["AI智能体", "公司大智能体 + 岗位智能体 + 自动化任务", "自动取数/整理/提醒/推送；人工确认例外和结果", "一周搭建、二周使用、三周复盘"],
    ["纪律与保障", "汇报纪律 + 数据责任 + 权限 + 复核", "有目标、有完成率、有复盘、有计划；缺失显式标记", "日报08:30、周一10:00、次月5日"],
  ];
  sheet.getRange("B13:D13").merge(); sheet.getRange("E13:G13").merge(); sheet.getRange("H13:J13").merge();
  sheet.getRange("A13").values = [["支撑层"]]; sheet.getRange("B13").values = [["核心内容"]];
  sheet.getRange("E13").values = [["运行方式"]]; sheet.getRange("H13").values = [["节奏/红线"]];
  styleHeader(sheet.getRange("A13:J13"));
  support.forEach((row, index) => {
    const r = 14 + index;
    sheet.getRange(`A${r}`).values = [[row[0]]];
    sheet.getRange(`B${r}:D${r}`).merge(); sheet.getRange(`B${r}`).values = [[row[1]]];
    sheet.getRange(`E${r}:G${r}`).merge(); sheet.getRange(`E${r}`).values = [[row[2]]];
    sheet.getRange(`H${r}:J${r}`).merge(); sheet.getRange(`H${r}`).values = [[row[3]]];
    styleBody(sheet.getRange(`A${r}:J${r}`));
    sheet.getRange(`A${r}`).format = { fill: index ? C.graySoft : C.greenSoft, font: { bold: true, color: index ? C.gray : C.green }, horizontalAlignment: "center", borders: softBorder };
    sheet.getRange(`A${r}:J${r}`).format.rowHeight = 44;
  });

  sectionBand(sheet, 17, "J", "三、日周月分层", C.purple);
  sheet.getRange("B18:C18").merge(); sheet.getRange("D18:E18").merge(); sheet.getRange("F18:G18").merge(); sheet.getRange("H18:I18").merge();
  sheet.getRange("A18").values = [["周期"]]; sheet.getRange("B18").values = [["管理目的"]];
  sheet.getRange("D18").values = [["老板重点"]]; sheet.getRange("F18").values = [["比较口径"]];
  sheet.getRange("H18").values = [["输出动作"]]; sheet.getRange("J18").values = [["呈报时间"]];
  styleHeader(sheet.getRange("A18:J18"));
  const cadence = [
    ["日报", "看异常、抓当天动作", "红灯/缺口/到期/需决策", "目标进度、上周同日、数据状态", "责任人+今日动作+完成节点", "D+1 08:30"],
    ["周报", "看变化、抓差距与闭环", "趋势/驱动/排名/整改效果", "上周、同比、近4周、月度进度", "下周量化目标+资源需求", "周一10:00"],
    ["月报", "看全景、抓经营质量", "损益/现金/资产/组织/战略", "预算、同比、上月、滚动预测", "资源配置+下月三项决策", "次月5日前"],
  ];
  cadence.forEach((row, index) => {
    const r = 19 + index;
    sheet.getRange(`A${r}`).values = [[row[0]]];
    sheet.getRange(`B${r}:C${r}`).merge(); sheet.getRange(`B${r}`).values = [[row[1]]];
    sheet.getRange(`D${r}:E${r}`).merge(); sheet.getRange(`D${r}`).values = [[row[2]]];
    sheet.getRange(`F${r}:G${r}`).merge(); sheet.getRange(`F${r}`).values = [[row[3]]];
    sheet.getRange(`H${r}:I${r}`).merge(); sheet.getRange(`H${r}`).values = [[row[4]]];
    sheet.getRange(`J${r}`).values = [[row[5]]];
    styleBody(sheet.getRange(`A${r}:J${r}`));
    sheet.getRange(`A${r}`).format = { fill: C.purpleSoft, font: { bold: true, color: C.purple }, horizontalAlignment: "center", borders: softBorder };
    sheet.getRange(`A${r}:J${r}`).format.rowHeight = 45;
  });

  sectionBand(sheet, 23, "J", "四、当前业务边界与会议优先级", C.amber);
  sheet.getRange("A24:J24").values = [["四大经营板块", "APR门店", "Apple电商", "Shure电商", "3PP/渠道分销", "", "", "", "", ""]];
  sheet.getRange("E24:J24").merge(); styleHeader(sheet.getRange("A24:J24"));
  sheet.getRange("A25:J25").values = [["实际范围", "线下授权门店", "京东羽通 / 苏宁啟韬", "京东官方旗舰店 / 天猫官方旗舰店", "客户/品牌/项目/分销", "", "", "", "", ""]];
  sheet.getRange("E25:J25").merge(); styleBody(sheet.getRange("A25:J25")); sheet.getRange("A25:J25").format.rowHeight = 40;
  sheet.getRange("A27:J27").values = [["会议优先级", "第一：开优质门店", "第二：厂商/总代分货资源", "第三：人员效率与能力建设", "专项：3001设备产品线", "", "", "", "", ""]];
  sheet.getRange("E27:J27").merge(); styleHeader(sheet.getRange("A27:J27"));
  sheet.getRange("A28:J28").values = [["评价原则", "结果为先", "口径统一", "异常必有动作", "决策必须闭环", "AI提升效率", "数据透明", "权限可控", "证据关闭", "不静默补数"]];
  styleBody(sheet.getRange("A28:J28")); sheet.getRange("A28:J28").format.rowHeight = 38;
  setWidths(sheet, { A: 14, B: 18, C: 23, D: 23, E: 23, F: 20, G: 20, H: 21, I: 21, J: 22 });
  sheet.freezePanes.freezeRows(3);
}

function buildDetail() {
  const sheet = workbook.worksheets.add("1-全景框架明细");
  baseSheet(sheet, `A1:L${htmlItems.length + 6}`);
  titleBand(sheet, "L", "HTML全景框架 · 54节点完整承接表", "每一行对应HTML中的一个三级节点；原始节点与原始说明完整保留，其他文件只补充不覆盖");
  noteBand(sheet, 3, "L", `完整性基线：6个一级层、18个二级模块、${htmlItems.length}个三级节点。最终校验见“15-完整性校验”。`, "green");
  const headers = ["框架ID", "一级层", "二级模块", "原标签", "管理节点", "HTML原始说明（不可删）", "会议/第五版补充", "落地载体", "日报", "周报", "月报", "责任与复核"];
  sheet.getRange("A4:L4").values = [headers]; styleHeader(sheet.getRange("A4:L4"));
  const rows = htmlItems.map((item) => {
    const cadence = cadenceFor(item);
    return [item.id, item.section, item.subsection, item.tag, item.name, item.description, supplementFor(item), carrierFor(item), ...cadence, ownerFor(item)];
  });
  sheet.getRange(`A5:L${rows.length + 4}`).values = rows; styleBody(sheet.getRange(`A5:L${rows.length + 4}`));
  rows.forEach((row, index) => {
    const excelRow = index + 5;
    const [color, fill] = sectionColor(row[1]);
    sheet.getRange(`A${excelRow}:B${excelRow}`).format.fill = fill;
    sheet.getRange(`A${excelRow}:B${excelRow}`).format.font = { bold: true, color, size: 9 };
    sheet.getRange(`A${excelRow}`).format.horizontalAlignment = "center";
    sheet.getRange(`I${excelRow}:K${excelRow}`).format.horizontalAlignment = "center";
    sheet.getRange(`A${excelRow}:L${excelRow}`).format.rowHeight = row[5].length > 90 ? 68 : 54;
  });
  setWidths(sheet, { A: 11, B: 28, C: 27, D: 16, E: 34, F: 54, G: 49, H: 30, I: 15, J: 15, K: 15, L: 31 });
  sheet.freezePanes.freezeRows(4); sheet.freezePanes.freezeColumns(2);
}

const managementRows = [
  ["物", "采购订单→商品规划→产品流转", "需求/采购/到货/分货/上架/销售/退换", "订单、到货、缺货、周转、库龄、异常流转", "重大缺口/异常", "流程效率/差异", "周转与资产质量", "采销/商务/业务", "断货、超期、越权", "补货/调拨/清库/纠偏"],
  ["物", "资金流转与结算", "收入入账/付款/退款/对账/结算", "收付款、应收应付、异常退款、账实差异", "越线异常", "回款/结算进度", "现金与营运资金", "财务/业务", "异常退款、账实不符", "冻结-核对-升级"],
  ["物", "合同档案流转与归档", "起草/审批/签署/履约/归档/续期", "合同状态、关键条款、到期、证据", "重大异常", "节点跟踪", "合同全景", "综合办/财务/业务", "越权、漏签、逾期", "补签/升级/归档"],
  ["物", "门店生命周期", "选址/开店/装修升级/续约/新签/退出", "项目预算、节点、店效、续约条件", "关键节点", "进度与偏差", "投资回报", "APR/项目负责人", "延期、超支、证照", "决策/整改/验收"],
  ["物", "库存与返利管理", "周转/量级/物料/返利预计确认到账", "库存、90天+/180天+、返利、条件、到账", "风险SKU/逾期", "消化与确认", "减值/利润质量", "采销/财务", "超龄、缺货、返利落空", "采购/清库/催收"],
  ["人", "人员规划与缺编", "门店员工→店长→总部岗位", "编制、在岗、缺编、关键岗位保障", "经营影响异常", "缺口趋势", "组织配置", "人事/业务负责人", "关键岗位空缺", "招聘/临时替补"],
  ["人", "能力与岗位匹配", "定位/胜任/组合搭配/调整", "胜任度、绩效、关键能力、后备", "重大错配", "人员诊断", "人才盘点", "人事/业务负责人", "能力不匹配", "调岗/辅导/替换"],
  ["人", "人效与人均毛利", "销售/毛利/人数/工时统一口径", "人均销售、人均毛利、人工成本率、同岗差距", "极端异常", "趋势/排名", "组织效能", "人事/财务/业务", "低效持续", "激励/培训/调整"],
  ["人", "招聘→培训→升级→竞赛", "新人培养与老员工升级", "招聘质量、培训/认证、技能提升、竞赛结果", "关键逾期", "完成与效果", "能力复盘", "人事/业务", "培养失败/认证过期", "补训/调整"],
  ["外部", "供应商资源整合", "苹果/总代/品牌资源沟通", "分货承诺、交付、政策、返利、资源", "供应异常", "承诺兑现", "依赖与谈判", "采销/业务", "断供、政策变化", "备选/谈判/备货"],
  ["外部", "客户单位与业务关系", "重点客户/项目/回款/续约", "销售、毛利、合同、应收、信用、项目节点", "重大客户异常", "客户进展", "集中度/信用", "3PP/业务/财务", "逾期、流失、争议", "催收/维护/升级"],
  ["外部", "外围营商环境", "市场/商圈/竞品/政策", "竞品价格、客流、商圈变化、政策事件", "事件触发", "变化判断", "策略复盘", "业务/内容营销", "政策/竞争突变", "调价/活动/选址"],
  ["合规", "考勤与制度执行", "基础制度/排班/异常留痕", "严重缺勤、制度违反、劳动合规", "影响经营例外", "异常趋势", "制度评价", "人事/综合办", "经营中断/劳动风险", "替补/处理/修订"],
  ["合规", "经营纪律与证据", "价格/合同/采购/付款/盘点/权限", "负毛利、低价、越权、盘点差异、审批证据", "事件触发", "异常清单", "内控复盘", "财务/综合办/业务", "越权、舞弊、重大差异", "整改/问责/审计"],
];

function buildManagement() {
  const sheet = workbook.worksheets.add("6-管理四维流程");
  baseSheet(sheet, `A1:J${managementRows.length + 6}`);
  titleBand(sheet, "J", "管理数据四维流程", "按会议原意围绕业务流程展开：物 · 人 · 外部资源 · 内部合规");
  noteBand(sheet, 3, "J", "管理数据不是行政流水账，只报告影响经营结果、资源配置、执行质量和风险闭环的过程信息。", "amber");
  const headers = ["维度", "管理主题", "流程/对象", "指标与证据", "日报", "周报", "月报", "第一责任", "风险触发", "管理输出"];
  sheet.getRange("A4:J4").values = [headers]; styleHeader(sheet.getRange("A4:J4"));
  sheet.getRange(`A5:J${managementRows.length + 4}`).values = managementRows; styleBody(sheet.getRange(`A5:J${managementRows.length + 4}`));
  managementRows.forEach((row, index) => {
    const r = index + 5; const palette = row[0] === "物" ? [C.blue, C.blueSoft] : row[0] === "人" ? [C.purple, C.purpleSoft] : row[0] === "外部" ? [C.cyan, C.cyanSoft] : [C.gray, C.graySoft];
    sheet.getRange(`A${r}`).format = { fill: palette[1], font: { bold: true, color: palette[0] }, horizontalAlignment: "center", borders: softBorder };
    sheet.getRange(`A${r}:J${r}`).format.rowHeight = 54;
  });
  setWidths(sheet, { A: 10, B: 27, C: 36, D: 43, E: 17, F: 18, G: 20, H: 24, I: 29, J: 29 });
  sheet.freezePanes.freezeRows(4);
}

const priorityRows = [
  ["P1", "第一优先级", "开优质门店", "形成可持续5-10年的线下经营单元", "一年1个=进步；单店月销100万元具备盈利基础；年销3000万元达到行业均值即优秀", "选址/谈判/筹备异常", "新增线索、项目节点、店效", "投资回报与复制模型", "APR负责人/项目负责人", "选址、投资、合同、资源授权", "开店验收+达产验证"],
  ["P2", "第二优先级", "分货与厂商/总代资源", "保障核心产品资源与增长机会", "资源沟通、分货承诺、实际到货、重点SKU满足率、增量销售/毛利", "断货/承诺未兑现", "资源兑现与差距", "供应依赖与谈判结果", "采销/品牌负责人", "资源置换、备货、价格政策", "到货/销售/毛利结果"],
  ["P3", "第三优先级", "人员效率与能力建设", "缩小优秀与一般员工差距", "人均销售、人均毛利、同岗差距、培训认证、优秀岗位收入提升30%-50%的会议目标", "关键岗位/严重低效", "排名、改善动作", "人才盘点与机制优化", "人事/业务负责人", "编制、激励、调整、培训预算", "绩效与能力改善"],
  ["P4", "专项产品线", "3001设备产品线", "打通采购、销售与营销推广全链路", "周周推荐；按产品/品牌/项目跟踪销售、毛利、库存、营销与客户反馈", "重点节点/异常", "推荐与动销进展", "产品线经营复盘", "采销/业务/营销", "选品、价格、库存、投放", "销售与库存验证"],
  ["P5", "运行闭环", "重点事项台账", "让会议决定和老板交办可追溯", "唯一ID、实际进度、时间进度、原截止日、下一节点、责任人、验证证据", "到期/落后/逾期", "完成率与滚动", "承诺兑现率", "事项责任人/总经办", "跨部门资源与优先级", "结果证据"],
  ["P6", "决策闭环", "老板批复→执行→验证", "让批复形成经营结果", "关联事项ID、接收确认、执行动作、完成时间、结果验证、关闭日期", "未确认/逾期", "批复执行清单", "决策有效性复盘", "总经办/事项责任人", "方案A/B、建议结论、最晚批复", "验证后关闭"],
];

function buildPriority() {
  const sheet = workbook.worksheets.add("7-重点事项优先级");
  baseSheet(sheet, `A1:K${priorityRows.length + 6}`);
  titleBand(sheet, "K", "重点事项优先级与闭环", "会议优先级不埋在日报明细中，单独建立目标、节点、责任、决策和验证链");
  noteBand(sheet, 3, "K", "重点事项统一进入台账：原截止日不得覆盖，未完成滚入下周，已完成必须有结果证据。", "amber");
  const headers = ["ID", "层级", "重点事项", "战略意图", "衡量标准", "日报", "周报", "月报", "第一责任", "需老板决策", "关闭证据"];
  sheet.getRange("A4:K4").values = [headers]; styleHeader(sheet.getRange("A4:K4"));
  sheet.getRange(`A5:K${priorityRows.length + 4}`).values = priorityRows; styleBody(sheet.getRange(`A5:K${priorityRows.length + 4}`));
  priorityRows.forEach((row, index) => {
    const r = index + 5; sheet.getRange(`A${r}:B${r}`).format = { fill: C.amberSoft, font: { bold: true, color: C.amber }, horizontalAlignment: "center", borders: softBorder };
    sheet.getRange(`A${r}:K${r}`).format.rowHeight = 70;
  });
  setWidths(sheet, { A: 9, B: 18, C: 28, D: 35, E: 55, F: 23, G: 27, H: 28, I: 25, J: 34, K: 25 });
  sheet.freezePanes.freezeRows(4);
}

const aiRows = [
  ["AI01", "公司级", "经营管理智能体", "九大数据包、日周月规则、事项风险台账", "自动汇总、勾稽、识别异常、生成老板摘要", "确认口径、判断例外、承担最终责任", "日/周/月简报、风险提醒、决策清单", "日报/周报/月报", "总经办/经营班子", "按岗位权限", "输出可追溯、异常不漏报"],
  ["AI02", "公司级", "经营数据智能体", "ERP/平台/财务/门店/项目数据", "取数、清洗、板块勾稽、目标与趋势比较", "处理接口异常和数据争议", "经营数据包与差异清单", "每日/每周", "数据责任人/财务", "敏感财务分级", "公司合计=板块合计"],
  ["AI03", "公司级", "重点事项沟通智能体", "会议纪要、老板批复、事项台账", "提取事项、提醒节点、生成跟进消息、滚动逾期项", "确认事项归属、结果与证据", "事项台账、催办、批复闭环", "实时/每日", "总经办", "按事项权限", "ID唯一、原截止日保留"],
  ["AI04", "岗位级", "电商运营/财务做账/人事/营销智能体", "岗位SOP、数据、制度、历史输出", "完成常规分析、草拟报告、检查遗漏", "负责业务判断与最终交付", "岗位日报/分析/任务清单", "按岗位", "各岗位负责人", "岗位隔离", "至少覆盖高频重复工作"],
  ["AI05", "自动化", "月度账务盘点", "电子账、实物盘点计划、标准和差异", "定时安排、收集、比对、推送报告与要求", "现场盘点、异常确认、责任判定", "盘点报告与整改清单", "每月", "财务/仓储/业务", "账务与实物分权", "差异有责任和关闭证据"],
  ["AI06", "治理", "数据透明上线", "公司经营与管理数据", "统一入口、按权限展示、记录更新时间与状态", "定义谁可看、谁可改、谁复核", "透明可追溯的数据空间", "持续", "总经办/数据责任人", "最小权限", "无静默补数、状态可见"],
  ["AI07", "工具", "Code为核心模板 + 小龙虾补充", "逻辑推理、数据抓取、结果呈现需求", "核心推理与便捷工具互补", "选择合规场景并验证输出", "标准模板与岗位工具", "持续", "智能体责任人", "公司数据边界", "工具不替代责任"],
  ["AI08", "落地", "一周搭建→二周使用→三周复盘", "岗位工作蒸馏、流程、数据、质量标准", "形成多个辅助机器人并持续优化", "员工只处理AI无法覆盖的判断与例外", "建设清单、使用记录、复盘改进", "三周循环", "各责任人/总经办", "平台统一管理", "实际使用率与效率改善"],
];

function buildAI() {
  const sheet = workbook.worksheets.add("9-AI智能体应用");
  baseSheet(sheet, `A1:K${aiRows.length + 6}`);
  titleBand(sheet, "K", "AI智能体体系与自动化运转", "AI是简报与经营管理的支撑层：自动完成常规工作，人工负责确认、判断、授权和最终责任");
  noteBand(sheet, 3, "K", "HTML中的AI节点全部保留；会议纪要补充公司级智能体、岗位智能体、月度盘点和数据透明的落地路径。", "green");
  const headers = ["ID", "层级", "智能体/应用", "输入", "自动完成", "人工责任", "输出", "频率", "责任端口", "权限", "验收标准"];
  sheet.getRange("A4:K4").values = [headers]; styleHeader(sheet.getRange("A4:K4"));
  sheet.getRange(`A5:K${aiRows.length + 4}`).values = aiRows; styleBody(sheet.getRange(`A5:K${aiRows.length + 4}`));
  aiRows.forEach((row, index) => {
    const r = index + 5; sheet.getRange(`A${r}:C${r}`).format.fill = C.greenSoft; sheet.getRange(`A${r}:C${r}`).format.font = { bold: true, color: C.green, size: 9 };
    sheet.getRange(`A${r}:K${r}`).format.rowHeight = 62;
  });
  setWidths(sheet, { A: 9, B: 13, C: 31, D: 40, E: 43, F: 38, G: 35, H: 17, I: 25, J: 22, K: 31 });
  sheet.freezePanes.freezeRows(4);
}

const disciplineRows = [
  ["纪律", "日报/周报/月报是公司规则", "有目标、有完成率、有复盘、有计划；禁止流水账", "按规定时点呈报", "总经办/全员", "不合格退回并记录"],
  ["纪律", "汇报质量红线", "先写给自己再写给领导；年→季→月→周→日层层清晰", "每次汇报", "各责任人", "新人容错后仍不达标按制度处理"],
  ["逻辑", "一目了然、有主到次、分层级", "先结论后数据，先异常后明细，先影响后动作", "日/周/月", "总经办", "老板首页只留结论与异常"],
  ["逻辑", "围绕公司重点工作线", "各岗位围绕经营结果、重点事项和风险开展工作", "持续", "各部门负责人", "偏离主线的流水事项不进主表"],
  ["数据", "九大数据包责任", "公司销售/APR/电商/3PP/财务/营销/客服/人事/事项", "按数据包时限", "各板块责任人", "财务/总经办复核"],
  ["数据", "状态与缺口显式", "确认/暂估/待确认/缺失；注明截止时点与修复时间", "每次汇总", "数据责任人", "禁止静默补数"],
  ["时效", "固定呈报时间", "日报08:30、周报周一10:00、月报次月5日", "固定", "总经办", "关键数据缺失也带标识按时发布"],
  ["权限", "数据透明但按岗授权", "该给谁看、谁可改、谁复核必须清楚", "持续", "总经办/数据责任人", "敏感数据最小权限、操作留痕"],
];

function buildDiscipline() {
  const sheet = workbook.worksheets.add("10-纪律与运行机制");
  baseSheet(sheet, `A1:F${disciplineRows.length + 6}`);
  titleBand(sheet, "F", "汇报纪律、数据责任与运行机制", "将HTML的纪律与保障层转化为可执行规则");
  noteBand(sheet, 3, "F", "核心不是表格漂亮，而是工作目标、结果、复盘、动作、责任和证据清晰。", "gray");
  sheet.getRange("A4:F4").values = [["类别", "规则", "执行标准", "频率/时点", "责任", "控制结果"]]; styleHeader(sheet.getRange("A4:F4"));
  sheet.getRange(`A5:F${disciplineRows.length + 4}`).values = disciplineRows; styleBody(sheet.getRange(`A5:F${disciplineRows.length + 4}`));
  disciplineRows.forEach((row, index) => {
    const r = index + 5; sheet.getRange(`A${r}`).format = { fill: C.graySoft, font: { bold: true, color: C.gray }, horizontalAlignment: "center", borders: softBorder };
    sheet.getRange(`A${r}:F${r}`).format.rowHeight = 52;
  });
  setWidths(sheet, { A: 13, B: 34, C: 59, D: 24, E: 28, F: 38 });
  sheet.freezePanes.freezeRows(4);
}

function buildTaskRiskTemplate() {
  const sheet = workbook.worksheets.add("13-事项风控模板");
  baseSheet(sheet, "A1:R34");
  titleBand(sheet, "R", "重点事项、风险与老板批复闭环模板", "黄色为人工填写，蓝色为公式判断；日报、周报、月报共用同一台账");
  noteBand(sheet, 3, "R", "事项/风险ID不得重复；原截止日不得覆盖；已完成/已关闭必须有验证结果；红色风险和老板批复即时更新。", "red");
  sectionBand(sheet, 5, "R", "一、重点事项台账", C.amber);
  const headers = ["事项ID", "来源", "业务板块", "事项名称", "目标结果", "责任人", "协同人", "开始日期", "原截止日", "当前截止日", "实际进度", "时间进度", "偏差", "状态", "今日/本周进展", "下一节点", "需老板介入", "决策诉求"];
  sheet.getRange("A6:R6").values = [headers]; styleHeader(sheet.getRange("A6:R6")); styleBody(sheet.getRange("A7:R14"));
  sheet.getRange("A7:K14").format.fill = C.input; sheet.getRange("O7:R14").format.fill = C.input;
  for (let r = 7; r <= 14; r += 1) {
    sheet.getRange(`L${r}`).formulas = [[`=IF(OR(H${r}="",J${r}=""),"",MAX(0,MIN(1,(TODAY()-H${r})/(J${r}-H${r}))))`]];
    sheet.getRange(`M${r}`).formulas = [[`=IF(OR(K${r}="",L${r}=""),"",K${r}-L${r})`]];
    sheet.getRange(`N${r}`).formulas = [[`=IF(A${r}="","",IF(K${r}>=1,"已完成",IF(TODAY()>J${r},"逾期",IF(M${r}<=-20%,"红色预警",IF(M${r}<=-10%,"黄色关注","正常")))))`]];
    sheet.getRange(`A${r}:R${r}`).format.rowHeight = 48;
  }
  sheet.getRange("H7:J14").format.numberFormat = "yyyy-mm-dd"; sheet.getRange("K7:M14").format.numberFormat = "0%"; sheet.getRange("L7:N14").format.fill = C.formula;
  sheet.getRange("B7:B14").dataValidation = { rule: { type: "list", values: ["老板交办", "经营会", "周会", "部门计划", "风险整改", "其他"] } };
  sheet.getRange("C7:C14").dataValidation = { rule: { type: "list", values: ["APR门店", "Apple电商", "Shure电商", "3PP/渠道分销", "职能保障", "公司级"] } };
  sheet.getRange("Q7:Q14").dataValidation = { rule: { type: "list", values: ["是", "否"] } };
  for (const [text, fill, color] of [["正常", C.greenSoft, C.green], ["黄色", C.amberSoft, C.amber], ["红色", C.redSoft, C.red], ["逾期", C.redSoft, C.red], ["已完成", C.greenSoft, C.green]]) {
    sheet.getRange("N7:N14").conditionalFormats.add("containsText", { text, format: { fill, font: { color, bold: true } } });
  }

  sectionBand(sheet, 16, "R", "二、风险与老板批复闭环", C.red);
  const riskHeaders = ["风险ID", "风险等级", "风险类型", "业务板块", "风险描述", "影响金额", "影响范围", "发生概率", "当前措施", "剩余敞口", "责任人", "截止日", "处置状态", "建议方案", "老板批复", "接收确认", "结果验证", "关闭日期"];
  sheet.getRange("A17:R17").values = [riskHeaders]; styleHeader(sheet.getRange("A17:R17")); styleBody(sheet.getRange("A18:R25")); sheet.getRange("A18:R25").format.fill = C.input;
  sheet.getRange("B18:B25").dataValidation = { rule: { type: "list", values: ["红色", "黄色", "蓝色"] } };
  sheet.getRange("C18:C25").dataValidation = { rule: { type: "list", values: ["经营", "库存", "资金", "客户/平台", "定价", "营销", "收银结算", "合规", "人员", "数据", "其他"] } };
  sheet.getRange("H18:H25").dataValidation = { rule: { type: "list", values: ["高", "中", "低"] } };
  sheet.getRange("M18:M25").dataValidation = { rule: { type: "list", values: ["未开始", "处理中", "待验证", "已关闭"] } };
  sheet.getRange("F18:F25").format.numberFormat = "#,##0;[Red](#,##0);-"; sheet.getRange("L18:L25").format.numberFormat = "yyyy-mm-dd"; sheet.getRange("R18:R25").format.numberFormat = "yyyy-mm-dd";
  sheet.getRange("B18:B25").conditionalFormats.add("containsText", { text: "红", format: { fill: C.redSoft, font: { color: C.red, bold: true } } });
  sheet.getRange("B18:B25").conditionalFormats.add("containsText", { text: "黄", format: { fill: C.amberSoft, font: { color: C.amber, bold: true } } });
  for (let r = 18; r <= 25; r += 1) sheet.getRange(`A${r}:R${r}`).format.rowHeight = 52;
  sectionBand(sheet, 27, "R", "三、关闭控制", C.navy2);
  const controls = [
    ["控制1", "ID不得重复", "同一事项跨日报/周报/月报持续追踪", "总经办"],
    ["控制2", "原截止日不得覆盖", "延期次数和管理承诺可追溯", "事项责任人"],
    ["控制3", "完成/关闭必须有验证结果", "防止以“已沟通”代替完成", "复核责任人"],
    ["控制4", "红色风险与老板批复即时更新", "不等待日报批次", "风险责任人/总经办"],
  ];
  sheet.getRange("A28:R28").values = [["控制项", "要求", "", "", "", "", "管理目的", "", "", "", "", "", "", "", "责任", "", "", ""]];
  sheet.getRange("B28:F28").merge(); sheet.getRange("G28:N28").merge(); sheet.getRange("O28:R28").merge(); styleHeader(sheet.getRange("A28:R28"));
  controls.forEach((row, index) => {
    const r = 29 + index; sheet.getRange(`A${r}`).values = [[row[0]]];
    sheet.getRange(`B${r}:F${r}`).merge(); sheet.getRange(`B${r}`).values = [[row[1]]];
    sheet.getRange(`G${r}:N${r}`).merge(); sheet.getRange(`G${r}`).values = [[row[2]]];
    sheet.getRange(`O${r}:R${r}`).merge(); sheet.getRange(`O${r}`).values = [[row[3]]]; styleBody(sheet.getRange(`A${r}:R${r}`));
  });
  setWidths(sheet, { A: 12, B: 15, C: 19, D: 25, E: 34, F: 16, G: 18, H: 15, I: 16, J: 16, K: 15, L: 15, M: 14, N: 18, O: 31, P: 25, Q: 16, R: 31 });
  sheet.freezePanes.freezeRows(6);
}

function buildCoverage() {
  const sheet = workbook.worksheets.add("15-完整性校验");
  baseSheet(sheet, `A1:H${htmlItems.length + 6}`);
  titleBand(sheet, "H", "HTML内容完整性校验", "以HTML的54个三级节点为不可删减基线，自动检查最终Excel是否完整承接");
  sheet.getRange("A3").values = [["MODEL STATUS"]]; sheet.getRange("B3").formulas = [[`=IF(COUNTIF(G5:G${htmlItems.length + 4},"缺失")=0,"PASS","FAIL")`]];
  sheet.getRange("C3").values = [["HTML节点"]]; sheet.getRange("D3").values = [[htmlItems.length]];
  sheet.getRange("E3").values = [["通过节点"]]; sheet.getRange("F3").formulas = [[`=COUNTIF(G5:G${htmlItems.length + 4},"通过")`]];
  sheet.getRange("G3").values = [["覆盖率"]]; sheet.getRange("H3").formulas = [["=F3/D3"]]; sheet.getRange("H3").format.numberFormat = "0.0%";
  styleHeader(sheet.getRange("A3:H3"));
  sheet.getRange("A4:H4").values = [["框架ID", "一级层", "二级模块", "管理节点", "关键原文", "Excel映射", "校验结果", "说明"]]; styleHeader(sheet.getRange("A4:H4"));
  const rows = htmlItems.map((item, index) => [item.id, item.section, item.subsection, item.name, item.description, `1-全景框架明细!E${index + 5}`, "", "HTML主骨架"]);
  sheet.getRange(`A5:H${rows.length + 4}`).values = rows; styleBody(sheet.getRange(`A5:H${rows.length + 4}`));
  for (let i = 0; i < rows.length; i += 1) {
    const r = i + 5;
    sheet.getRange(`G${r}`).formulas = [[`=IF(COUNTIF('1-全景框架明细'!$E$5:$E$100,D${r})>0,"通过","缺失")`]];
    sheet.getRange(`A${r}:H${r}`).format.rowHeight = rows[i][4].length > 90 ? 62 : 46;
  }
  sheet.getRange(`G5:G${rows.length + 4}`).conditionalFormats.add("containsText", { text: "通过", format: { fill: C.greenSoft, font: { color: C.green, bold: true } } });
  sheet.getRange(`G5:G${rows.length + 4}`).conditionalFormats.add("containsText", { text: "缺失", format: { fill: C.redSoft, font: { color: C.red, bold: true } } });
  setWidths(sheet, { A: 11, B: 29, C: 30, D: 38, E: 58, F: 27, G: 16, H: 20 });
  sheet.freezePanes.freezeRows(4);
}

function buildSources() {
  const sheet = workbook.worksheets.add("16-来源版本说明");
  baseSheet(sheet, "A1:H19");
  titleBand(sheet, "H", "来源、版本与口径说明", "说明内容优先级、补充关系和本次规范化处理");
  noteBand(sheet, 3, "H", "来源文件中的文字仅作为业务资料；最终框架遵循用户要求：HTML不可删，会议纪要和第五版只补充。", "gray");
  sheet.getRange("A4:H4").values = [["来源", "定位", "优先级", "承接方式", "不得改变", "允许补充", "规范化处理", "状态"]]; styleHeader(sheet.getRange("A4:H4"));
  const rows = [
    ["0817周会版HTML", "全景主骨架", "1", "6层/18模块/54节点全部进入明细与框架图", "节点与核心含义", "责任、频率、载体、口径", "原文保留；主呈现可用规范业务词", "完整承接"],
    ["最终第五版Excel", "日周月与治理结构", "2", "日报、周报、月报、板块、指标、预警、责任、台账、附表", "现行业务渠道边界", "与HTML交叉映射", "统一视觉与编号", "已承接"],
    ["0817会议纪要", "老板原意与部署依据", "3", "补充优先级、管理四维、风控流程与AI部署", "会议核心优先级", "衡量标准和落地动作", "口语转为管理表达", "已承接"],
  ];
  sheet.getRange("A5:H7").values = rows; styleBody(sheet.getRange("A5:H7"));
  for (let r = 5; r <= 7; r += 1) sheet.getRange(`A${r}:H${r}`).format.rowHeight = 62;
  sectionBand(sheet, 9, "H", "规范化说明", C.navy2);
  sheet.getRange("A10:H10").values = [["事项", "来源表达", "主呈现口径", "处理原则", "", "", "", ""]]; sheet.getRange("D10:H10").merge(); styleHeader(sheet.getRange("A10:H10"));
  const notes = [
    ["收银结算", "HTML含“输赢管理”", "收银管理/非单管理/结算管理", "会议纪要明确为收银管理；HTML原始说明仍保留在全景明细。"],
    ["责任人姓名", "HTML含个别口述姓名", "按岗位角色呈现", "避免姓名转写误差，正式分工可在责任表中固化。"],
    ["Apple电商", "多渠道泛称", "京东羽通、苏宁啟韬", "不纳入天猫；天猫仅属于Shure官方旗舰店。"],
    ["AI工具", "Code/code x及小龙虾", "Code为核心模板，小龙虾补充", "保留会议意思，工具不能替代人工责任。"],
  ];
  notes.forEach((row, index) => {
    const r = 11 + index; sheet.getRange(`A${r}`).values = [[row[0]]]; sheet.getRange(`B${r}`).values = [[row[1]]]; sheet.getRange(`C${r}`).values = [[row[2]]];
    sheet.getRange(`D${r}:H${r}`).merge(); sheet.getRange(`D${r}`).values = [[row[3]]]; styleBody(sheet.getRange(`A${r}:H${r}`)); sheet.getRange(`A${r}:H${r}`).format.rowHeight = 52;
  });
  setWidths(sheet, { A: 23, B: 31, C: 31, D: 28, E: 24, F: 24, G: 30, H: 17 });
  sheet.freezePanes.freezeRows(4);
}

buildOverview();
buildDetail();
buildSourceTable("1-日报框架", "2-日报框架", { colorByCategory: true, widths: { A: 10, B: 22, C: 25, D: 51, E: 44, F: 41, G: 23, H: 22 }, rowHeight: 55 });
buildSourceTable("2-周报框架", "3-周报框架", { colorByCategory: true, widths: { A: 10, B: 22, C: 27, D: 53, E: 44, F: 42, G: 23, H: 22 }, rowHeight: 56 });
buildSourceTable("3-月报框架", "4-月报框架", { colorByCategory: true, widths: { A: 10, B: 22, C: 28, D: 56, E: 45, F: 44, G: 24, H: 23 }, rowHeight: 58 });

if (version >= 2) {
  buildSourceTable("4-业务板块专项", "5-业务板块专项", { noteTone: "amber", widths: { A: 20, B: 32, C: 25, D: 27, E: 36, F: 32, G: 31, H: 34, I: 25, J: 28 }, rowHeight: 65 });
  buildManagement();
  buildPriority();
  const htmlRiskRows = [
    ["H-R01", "资金", "异常退款/账实差异", "超阈值即核查", "重大异常或资金安全事件", "冻结-核对-升级；说明影响与剩余敞口", "财务/总经办", "财务", "事件触发", "HTML六大风控点"],
    ["H-R02", "客户", "重大投诉/舆情/平台处罚", "重大投诉趋势", "舆情/处罚即时红色", "先报后补数据，统一对外口径", "老板/总经办", "业务负责人", "事件触发", "不受金额限制"],
    ["H-R03", "定价", "负毛利/异常优惠/价格越权", "接近授权边界", "越权或重大毛利损失", "暂停执行、核对授权、补救", "财务/老板", "业务负责人", "实时", "证据优先"],
    ["H-R04", "营销", "ROAS/贡献毛利异常", "连续下降或低于目标", "重大亏损或错误归因", "停调、校验归因、重定预算", "经营班子", "营销/业务", "日/周", "看增量贡献"],
    ["H-R05", "收银结算", "收银/非单/结算异常", "差异待核", "重大账实差异/疑似舞弊", "封存证据、核查、升级", "财务/老板", "门店/财务", "实时", "会议纪要规范口径"],
    ["H-R06", "合规", "合同/采购/付款越权", "流程偏差", "未经授权/重大合同/疑似舞弊", "停止、保全证据、专项核查", "老板/总经办", "责任部门", "实时", "事件触发"],
  ];
  buildSourceTable("6-预警与决策规则", "8-预警与决策规则", { extraRows: htmlRiskRows, noteTone: "red", widths: { A: 10, B: 16, C: 27, D: 35, E: 39, F: 42, G: 21, H: 21, I: 16, J: 29 }, rowHeight: 58 });
}

if (version >= 3) {
  buildAI();
  buildDiscipline();
  buildSourceTable("5-指标口径矩阵", "11-指标口径矩阵", { noteTone: "green", widths: { A: 10, B: 15, C: 21, D: 27, E: 48, F: 12, G: 13, H: 13, I: 13, J: 27, K: 22, L: 31 }, rowHeight: 48 });
  buildSourceTable("7-数据责任与时效", "12-数据责任与时效", { noteTone: "amber", widths: { A: 24, B: 31, C: 34, D: 24, E: 23, F: 23, G: 21, H: 25, I: 39, J: 36 }, rowHeight: 60 });
  buildTaskRiskTemplate();
  buildSourceTable("9-附表清单", "14-附表清单", { noteTone: "green", widths: { A: 10, B: 25, C: 34, D: 51, E: 16, F: 30, G: 31, H: 23, I: 30 }, rowHeight: 54 });
  buildCoverage();
}

if (version >= 4) buildSources();

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);

const previewPaths = [];
for (const sheet of workbook.worksheets.items) {
  const preview = await workbook.render({ sheetName: sheet.name, autoCrop: "all", scale: 1, format: "png" });
  const previewPath = path.join(previewDir, `${sheet.name}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  previewPaths.push(previewPath);
}

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: `第${version}轮公式错误扫描`,
});
const overviewInspect = await workbook.inspect({ kind: "table", range: "0-老板审阅总纲!A1:J28", include: "values,formulas", tableMaxRows: 30, tableMaxCols: 10 });
const detailValues = workbook.worksheets.getItem("1-全景框架明细").getRange("A5:L100").values.flat().map((value) => String(value ?? ""));
const missingItems = htmlItems.filter((item) => !detailValues.includes(item.name) || !detailValues.includes(item.description));
const coverageStatus = version >= 3 ? workbook.worksheets.getItem("15-完整性校验").getRange("B3:H3").values : [];
const qa = {
  version,
  outputPath,
  sheetCount: workbook.worksheets.items.length,
  sheets: workbook.worksheets.items.map((sheet) => sheet.name),
  htmlBaseline: htmlData.counts,
  htmlItemsExpected: htmlItems.length,
  htmlItemsMissing: missingItems,
  formulaErrors: errors.ndjson,
  coverageStatus,
  previewCount: previewPaths.length,
  conceptualReview: {
    1: { result: "三源完成合并，HTML全量进入主框架。", gap: "老板阅读顺序和业务管理层仍需增强。", next: "加入管理四维、战略优先级和风险升级。" },
    2: { result: "经营、管理、重点事项和风控形成完整主链。", gap: "AI、纪律、数据责任与可维护台账尚未全部展开。", next: "加入双支撑层、指标责任和共用台账。" },
    3: { result: "内容与运行机制完整，已具备落地条件。", gap: "仍需最终规范化说明、视觉压缩和全量复核。", next: "完成最终第四版视觉和来源校验。" },
    4: { result: "HTML 54节点、第五版结构与会议部署全部承接。", gap: "无阻断项。", next: "提交老板审阅；阈值和具体姓名可按批复固化。" },
  }[version],
  overviewInspect: overviewInspect.ndjson,
};
await fs.writeFile(path.join(outputDir, `qa-v${version}.json`), JSON.stringify(qa, null, 2), "utf8");
console.log(JSON.stringify({ version, outputPath, sheets: qa.sheets, htmlItemsMissing: missingItems.length, formulaErrors: errors.ndjson, previewCount: previewPaths.length, conceptualReview: qa.conceptualReview }, null, 2));

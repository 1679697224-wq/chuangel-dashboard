import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const root = path.resolve(process.argv[2] || ".");

const required = [
  "AGENTS.md",
  "00-先读这里.md",
  "01-项目主上下文.md",
  "02-业务背景与范围.md",
  "03-需求演进与关键决策.md",
  "04-框架与口径规则.md",
  "05-文件索引.md",
  "06-新电脑续接提示词.md",
  "project-context.json",
  "01-最终成果/江苏传天羽经营管理全景简报框架_最终第四版.xlsx",
  "01-最终成果/江苏传天羽经营管理全景框架图_最终第四版.png",
  "02-核心源资料/江苏传天羽经营管理全景框架_0817周会版.html",
  "02-核心源资料/零售企业经营管理框架与AI应用工作部署会议纪要.docx",
  "02-核心源资料/江苏传天羽经营管理简报框架_最终第五版.xlsx",
  "05-结构化数据/0817-html-framework.json",
  "05-结构化数据/qa-v4.json",
];

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(full) : [full];
  });
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

const missing = required.filter((relative) => !fs.existsSync(path.join(root, relative)));
const context = JSON.parse(fs.readFileSync(path.join(root, "project-context.json"), "utf8"));

if (context.html_baseline?.level_3_items !== 54) {
  throw new Error("project-context.json 中的 HTML 三级节点基线不是 54。");
}

const validationPath = path.join(root, "PACKAGE-VALIDATION.json");
const validation = {
  status: missing.length === 0 ? "PASS" : "FAIL",
  checked_at: new Date().toISOString(),
  required_files: required.length,
  missing_files: missing,
  html_baseline: context.html_baseline,
  current_deliverables: context.current_deliverables,
};
fs.writeFileSync(validationPath, `${JSON.stringify(validation, null, 2)}\n`, "utf8");

const files = walk(root)
  .filter((file) => path.basename(file) !== "MANIFEST-SHA256.txt")
  .sort((a, b) => a.localeCompare(b, "zh-CN"));
const totalBytes = files.reduce((sum, file) => sum + fs.statSync(file).size, 0);
const manifest = files.map((file) => {
  const relative = path.relative(root, file).split(path.sep).join("/");
  return `${sha256(file)}  ${relative}`;
});
fs.writeFileSync(path.join(root, "MANIFEST-SHA256.txt"), `${manifest.join("\n")}\n`, "utf8");

if (missing.length > 0) {
  throw new Error(`缺少 ${missing.length} 个必需文件：${missing.join(", ")}`);
}

console.log(JSON.stringify({
  status: "PASS",
  root,
  file_count: files.length + 1,
  total_bytes_excluding_manifest: totalBytes,
  required_files: required.length,
  missing_files: 0,
}, null, 2));

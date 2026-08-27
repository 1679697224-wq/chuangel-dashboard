import { createServer } from "node:http";
import { randomBytes } from "node:crypto";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));
const publicRoot = path.join(root, "public");
const runtimeRoot = path.join(root, "runtime");
const dataPath = path.join(runtimeRoot, "current-data.json");
const keyPath = path.join(runtimeRoot, "upload-key.txt");
const port = Number(process.env.BRIEFING_PORT || 8766);
const maxBodySize = 3 * 1024 * 1024;

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ".xls": "application/vnd.ms-excel",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

async function ensureUploadKey() {
  await mkdir(runtimeRoot, { recursive: true });
  try {
    return (await readFile(keyPath, "utf8")).trim();
  } catch {
    const key = `CTY-${randomBytes(5).toString("hex").toUpperCase()}`;
    await writeFile(keyPath, `${key}\n`, "utf8");
    return key;
  }
}

const uploadKey = process.env.BRIEFING_UPLOAD_KEY || await ensureUploadKey();

function send(response, status, body, headers = {}) {
  response.writeHead(status, {
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    ...headers,
  });
  response.end(body);
}

async function readRequestBody(request) {
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > maxBodySize) throw new Error("BODY_TOO_LARGE");
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function publicationId(date = new Date()) {
  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(date).reduce((acc, part) => ({ ...acc, [part.type]: part.value }), {});
  return `WEB-${parts.year}${parts.month}${parts.day}-${parts.hour}${parts.minute}`;
}

async function handleApi(request, response, pathname) {
  if (pathname !== "/api/data") return false;

  if (request.method === "GET") {
    try {
      const data = await readFile(dataPath);
      send(response, 200, data, { "content-type": "application/json; charset=utf-8" });
    } catch {
      send(response, 204, "", { "content-type": "application/json; charset=utf-8" });
    }
    return true;
  }

  if (request.method === "POST") {
    if ((request.headers["x-upload-key"] || "") !== uploadKey) {
      send(response, 401, JSON.stringify({ error: "invalid upload key" }), { "content-type": "application/json; charset=utf-8" });
      return true;
    }
    try {
      const payload = JSON.parse(await readRequestBody(request));
      if (!Array.isArray(payload.operations) || payload.operations.length < 4 || !Array.isArray(payload.items)) {
        send(response, 422, JSON.stringify({ error: "invalid briefing payload" }), { "content-type": "application/json; charset=utf-8" });
        return true;
      }
      const now = new Date();
      const batch = publicationId(now);
      const publishedAt = now.toLocaleString("zh-CN", { timeZone: "Asia/Shanghai", hour12: false }).replaceAll("/", "-");
      payload.meta = { ...(payload.meta || {}), batch, publishedAt };
      await mkdir(runtimeRoot, { recursive: true });
      await writeFile(dataPath, JSON.stringify(payload, null, 2), "utf8");
      send(response, 200, JSON.stringify({ ok: true, batch, publishedAt }), { "content-type": "application/json; charset=utf-8" });
    } catch (error) {
      const status = error.message === "BODY_TOO_LARGE" ? 413 : 400;
      send(response, status, JSON.stringify({ error: error.message }), { "content-type": "application/json; charset=utf-8" });
    }
    return true;
  }

  send(response, 405, "Method Not Allowed", { allow: "GET, POST", "content-type": "text/plain; charset=utf-8" });
  return true;
}

async function serveStatic(response, pathname) {
  const requestedPath = pathname === "/" || pathname === "/report" ? "/dashboard.html" : pathname === "/biz" ? "/dashboard.html" : pathname;
  const decoded = decodeURIComponent(requestedPath);
  const filePath = path.resolve(publicRoot, `.${decoded}`);
  if (!filePath.startsWith(`${publicRoot}${path.sep}`)) return false;
  try {
    const info = await stat(filePath);
    if (!info.isFile()) return false;
    const extension = path.extname(filePath).toLowerCase();
    const headers = { "content-type": mimeTypes[extension] || "application/octet-stream" };
    if ([".xlsx", ".xls"].includes(extension)) headers["content-disposition"] = `attachment; filename*=UTF-8''${encodeURIComponent(path.basename(filePath))}`;
    send(response, 200, await readFile(filePath), headers);
    return true;
  } catch {
    return false;
  }
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url || "/", `http://${request.headers.host || "127.0.0.1"}`);
    if (url.pathname === "/health") {
      send(response, 200, JSON.stringify({ status: "ok", data: await stat(dataPath).then(() => "published").catch(() => "built-in") }), { "content-type": "application/json; charset=utf-8" });
      return;
    }
    if (url.pathname === "/favicon.ico") {
      send(response, 204, "", { "content-type": "image/x-icon" });
      return;
    }
    if (await handleApi(request, response, url.pathname)) return;
    if (await serveStatic(response, url.pathname)) return;
    send(response, 404, "Not Found", { "content-type": "text/plain; charset=utf-8" });
  } catch (error) {
    send(response, 500, "Internal Server Error", { "content-type": "text/plain; charset=utf-8" });
    console.error(error);
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Briefing server listening on http://127.0.0.1:${port}`);
  console.log(`Upload key: ${uploadKey}`);
});

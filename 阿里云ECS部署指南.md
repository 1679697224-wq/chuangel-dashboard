# 传天羽经营看板 · 阿里云 ECS 部署指南（小白版）

> 目标：把看板放到阿里云服务器上，用「公网 IP 直接打开」，以后老板访问就是固定网址。
> 原理：看板是**纯静态网页**（数据已内嵌），只需要一台 Web 服务器（Nginx）把文件"挂"出来，不需要数据库、不需要后端。

## 0. 你需要准备

- 一台阿里云 ECS（你已经开通了）
- 知道它的**公网 IP**（控制台 → ECS 实例列表里能看到）
- 你的电脑能上网

## 1. 连接服务器（第一次）

打开你电脑的终端：
- macOS：打开「终端」App
- Windows：打开「PowerShell」或「命令提示符」

输入（把 IP 换成你的公网 IP）：

    ssh root@你的公网IP

- 第一次会问 Are you sure，输入 yes 回车；
- 然后输入密码（如果没改过密码：先去阿里云控制台 → 实例 → 更多 → 密码/密钥 → 重置实例密码，重启实例后生效）。

连上后会看到类似 root@xxx:~# 的提示符，说明成功了。

## 2. 安装 Nginx（在服务器上执行）

**如果你的系统是 Ubuntu/Debian：**

    apt update && apt install -y nginx

**如果你的系统是 Alibaba Cloud Linux / CentOS：**

    yum install -y nginx

## 3. 上传看板文件（在你自己的电脑上执行，不是服务器）

我这边已经打好一个部署包：传天羽经营看板V6/deploy.zip（解压后是 index.html + static 文件夹）。

**方式 A（推荐，一条命令）：**

    # 在你自己电脑上，cd 到 传天羽经营看板V6 目录后执行：
    scp -r deploy/* root@你的公网IP:/usr/share/nginx/html/

**方式 B（先传 zip 再解压）：**

    scp deploy.zip root@你的公网IP:/tmp/

然后在服务器上执行：

    cd /usr/share/nginx/html && rm -rf * && unzip /tmp/deploy.zip -d .
    ls   # 确认里面有 index.html 和 static 文件夹

## 4. 启动 Nginx 并设置开机自启（服务器上执行）

    systemctl enable --now nginx

或（老系统）：

    service nginx start

验证（服务器本机测试）：

    curl -I http://127.0.0.1

看到 HTTP/1.1 200 OK 就对了。

## 5. 放行 80 端口（重要！阿里云控制台操作）

1. 登录阿里云控制台 → 云服务器 ECS → 实例；
2. 点你的实例 → 右侧「安全组」→ 点安全组 ID 进入配置；
3. 「入方向」→「手动添加」→ 端口范围填 80/80，授权对象 0.0.0.0/0，协议 HTTP；
4. 保存。

## 6. 打开看板

浏览器访问：

    http://你的公网IP

看到看板就成功了。

## 7. 以后怎么更新

每次我改完看板，会重新生成部署包。你在自己电脑上：

    # 重新上传覆盖即可
    scp -r deploy/* root@你的公网IP:/usr/share/nginx/html/

刷新浏览器就能看到新版本（如果浏览器缓存旧版，按 Cmd/Ctrl+Shift+R 强制刷新）。

## 8. 常见问题

| 问题 | 排查 |
|---|---|
| 打不开网页 | ① 安全组有没有放行 80（第 5 步）② 服务器上 systemctl status nginx 是否 active ③ 服务器本机 curl -I http://127.0.0.1 是否 200 |
| 打开是 Nginx 默认欢迎页 | 文件没传到正确目录，确认 /usr/share/nginx/html 下有 index.html |
| 图片/样式没加载 | 确认 static 文件夹也在 html 目录下 |
| 忘了密码 | 控制台重置实例密码后，重启实例生效 |

## 9. 安全建议（务必做）

1. 改成强密码（或改用密钥登录）；
2. 安全组只开必要端口：22（SSH）、80（HTTP）、443（以后 HTTPS）；
3. 不要用默认密码，不要在公网裸奔 root 弱口令；
4. 后续建议：**绑定域名 + 免费 HTTPS 证书**（阿里云有免费证书，或者宝塔面板一键申请），访问变成 https://你的域名，更正式、更安全——需要时我再给你出教程。

## 10. 以后想加「AI 助手 / 实时数据」怎么办

现在的版本是静态版（数据内嵌）。如果以后要接真实数据 + AI，方案升级为：

    Nginx（静态页面） ← 反向代理 → Python/Flask 后端（app.py + gunicorn） + 数据源（极客云API/Excel）

到那一步我再给你一份「Flask + gunicorn + Nginx」部署教程，今天先把静态版跑通。

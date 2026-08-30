# 部署与运行基线

## 环境区分

| 环境 | 数据 | 用途 | Mock/快照 |
|---|---|---|---|
| 开发 | 本地空库/纯Mock Demo/经批准快照 | 开发、页面体验与单测 | Demo与Sandbox必须显著标识并隔离 |
| 测试 | 脱敏测试数据/纯Mock Demo | 集成、权限、安全测试 | 允许，禁止进入正式视图 |
| 试点 | 真实 API、受控账号 | 小范围业务验收 | 默认禁止 Mock |
| 生产 | 真实 API、正式身份 | 正式经营 | 禁止 Mock/静默混用 |

## 本地运行

配置项见 `caixiao/.env.example`。不要加载仓库中现有登录或爬虫凭据，不要把真实配置写回 Git。

```bash
export CAIXIAO_TOKEN_SECRET='至少32位随机字符串'
export CAIXIAO_BOOTSTRAP_USER='review-admin'
export CAIXIAO_BOOTSTRAP_PASSWORD='至少12位本地强密码'
export DEMO_MODE='false'
python3 -m caixiao.backend.app --check
python3 -m caixiao.backend.app
```

页面体验可临时设置 `DEMO_MODE=true`；此时只启用纯Mock Demo Adapter，固定显示演示横幅，禁止写正式事实库。试点与生产必须保持 `DEMO_MODE=false`，且不得在缺数据时自动回退Demo。

## 生产前门禁

1. 完成 WorkBuddy 代码、安全与 API 契约 Review。
2. 确认正式身份源、细粒度 RBAC、门店/渠道数据范围及审计保留期。
3. 通过吉客云接口文档、稳定源记录 ID、重试/限流/增量/补数验证。
4. 所有正式维度和口径均有已发布版本。
5. 配置 TLS、反向代理、访问日志脱敏、备份和恢复演练。
6. 使用试点授权和验收清单；不得由本任务直接部署现网。

反向代理样例见 `caixiao/deployment/nginx-caixiao.conf`，必须由运维按实际域名、证书和端口复核后使用。

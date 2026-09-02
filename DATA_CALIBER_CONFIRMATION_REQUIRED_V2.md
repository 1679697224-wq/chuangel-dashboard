# V2.0 数据口径联调证据门禁

本文件记录在专项审计中确认存在、但不能靠当前仓库静态资料证明的技术事实。它不是让 PO 选择低价值技术细节；实际联调负责人必须提供证据，PO只确认是否满足上线门禁。

| 编号 | 真实风险 | 当前证据 | PHASE 1必须补齐的验证 | 未满足时处理 |
|---|---|---|---|---|
| TC-001 | 历史销售按 consignTime 拉取、按 payTime统计会漏单 | `dsh_keys/jky_pull.py`、`pull_api_828.py` 明确使用 start/endConsignTime | 证明正式订单接口支持稳定 modified/等同更新时间；否则以真实样本验证滚动回溯+upsert覆盖迟到付款、跨月发货、退款和状态变化 | 禁止旧链成为正式源 |
| TC-002 | 订单行可能没有稳定 line_id/source_record_id | Excel只有订单编号+货品编号等，当前正式适配器未联调 | API文档和响应样本证明订单头/行稳定键；验证重跑不重复、不丢行 | 若无稳定键，PHASE 1销售接入阻塞，不得用Excel行号 |
| TC-003 | 正式销售字段合同未验证 | 当前适配器是通用 endpoint 壳 | 核验 create/pay/audit/consign/complete/modified、status、quantity、payment、warehouse/shop/goods/SKU及原始载荷引用 | 缺字段的指标返回待接入 |
| TC-004 | 库存API全量/快照语义未知 | 历史方法线索为 `erp.stockquantity.get`；Excel只含正库存行且无快照时间 | 验证API是否覆盖零库存SKU、分页截止、快照一致性、可用/锁定/在途/成本及稳定键 | 无法证明全量时，不发布缺货/零库存；库存总量标记范围 |
| TC-005 | 公司仓/平台仓/欧瑞特/在途可能重复 | 多份文件表达相近库存，无共同去重键 | 用同一时点SKU样本建立双向对账，确认所有权、保管地和重复关系 | 未确认关系一律PENDING，不相加 |
| TC-006 | Excel模板结构和刷新过程不稳定 | `分仓库存查询.xlsx` dimension错误；库存分析表公式密集 | 导入前登记模板版本、文件哈希、快照时间、字段/公式校验和异常报告 | 校验失败只进Sandbox |
| TC-007 | 历史Secret/Token泄露风险仍存在 | `CREDENTIAL_ROTATION_REQUIRED.md`、`TRAFFIC_TOKEN_ROTATION_REQUIRED.md` | PO/管理员完成轮换、最小权限和调用日志核查；新凭据仅通过受控环境注入 | 不允许生产联调/部署；本轮不读取或验证旧值 |

以上验证应形成可复核联调报告、接口字段样本（脱敏）和自动测试结果。通过后再由 `DATA_CONFIRMATION_REQUIRED_V2.md` 中的业务口径版本决定 KPI，不允许技术联调人员代替 PO 作业务裁定。

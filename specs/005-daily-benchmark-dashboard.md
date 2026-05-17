# 005: 每日定时 Benchmark 计划

## 目标

对 4 个模型每日自动运行 benchmark，跟踪模型能力变化趋势。

## 模型列表

| 模型 | 参数量 | 定位 |
|------|--------|------|
| qwen3.5-35b | 35B | 旗舰级通用模型 |
| deepseek-v2-lite-chat | 16B MoE | 中等规模 Chat 模型 |
| qwen2.5-1.5b-instruct | 1.5B | 轻量级端侧模型 |
| deepseek-r1-distill-qwen-7b | 7B | 推理蒸馏模型 |

## Benchmark 选择依据

| Benchmark | 题量 | 耗时估算 | qwen3.5-35b | deepseek-v2-lite | qwen2.5-1.5b | deepseek-r1-7b |
|-----------|------|---------|-------------|------------------|---------------|----------------|
| MMLU (5-shot) | 14042 | 2-3h | ✅ 知识面广 | ✅ 对比基线 | ❌ 1.5B 不适合 | ✅ 推理+知识 |
| C-Eval (5-shot) | 13948 | 2-3h | ✅ 中文能力 | ✅ 中文基线 | ✅ 中文核心指标 | ✅ 中文推理 |
| GSM8K (8-shot) | 1319 | 30-60min | ✅ 数学推理 | ✅ 推理基线 | ✅ 基础推理 | ✅ 推理优势 |
| HumanEval (0-shot) | 164 | 10-20min | ✅ 代码生成 | ✅ 代码基线 | ❌ 太小无意义 | ✅ 代码推理 |

**共 14 个定时任务**（qwen2.5-1.5b 仅 C-Eval + GSM8K）。

## 每日调度时间表

按模型分时间段，避免并发导致 API 过载：

```
时段           模型                    Benchmark
──────────────────────────────────────────────────
00:02         qwen3.5-35b             MMLU
00:32         qwen3.5-35b             C-Eval
01:02         deepseek-v2-lite-chat   MMLU
01:32         deepseek-v2-lite-chat   C-Eval
02:02         qwen2.5-1.5b-instruct   C-Eval
03:02         deepseek-r1-7b          MMLU
03:32         deepseek-r1-7b          C-Eval
04:02         qwen2.5-1.5b-instruct   GSM8K
06:02         qwen3.5-35b             GSM8K
06:32         qwen3.5-35b             HumanEval
07:02         deepseek-v2-lite-chat   GSM8K
07:32         deepseek-v2-lite-chat   HumanEval
08:02         deepseek-r1-7b          GSM8K
08:32         deepseek-r1-7b          HumanEval
```

- 大题量任务（MMLU、C-Eval）集中在凌晨 00:00-04:00，预留充足执行时间
- 小题量任务（GSM8K、HumanEval）放在早晨，快速完成
- qwen2.5-1.5b-instruct 的 GSM8K 放 04:02，与其他模型的 GSM8K 错开

## 种子数据

SQL 文件：`backend/seed.sql`

- API 地址、认证方式需根据实际部署修改
- 所有任务默认启用，可通过页面关闭
- 并发数默认 8，stream 默认开启
z
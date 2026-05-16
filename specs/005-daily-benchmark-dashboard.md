# 每日定时基准测试计划

## 目标模型

| # | 模型 | 参数量 |
|---|------|--------|
| 1 | qwen2.5-1.5b-instruct | 1.5B |
| 2 | deepseek-r1-distill-qwen-7b | 7B |
| 3 | deepseek-v2-lite-chat | 16B |
| 4 | qwen3.5-35b | 35B |

## 评测基准

Chat API 兼容的 5 个基准，按耗时分为两批：

| 批次 | Benchmark | 考察能力 | 单模型预估耗时（concurrent=8） |
|------|-----------|---------|------|
| 快速 | HumanEval | 代码生成 | ~2 min |
| 快速 | GSM8K | 数学推理 | ~15 min |
| 快速 | TruthfulQA | 安全对齐 | ~10 min |
| 深度 | MATH | 高等数学 | ~55 min |
| 深度 | BBH | 通用推理 | ~70 min |

## 每日执行时间表

每个模型每天跑 2 个定时任务（快速批 + 深度批），共 **8 个定时任务**。

### 快速批（HumanEval + GSM8K + TruthfulQA）

| 时间 | 模型 | 预计完成 |
|------|------|---------|
| 01:00 | qwen2.5-1.5b-instruct | ~01:30 |
| 01:30 | deepseek-r1-distill-qwen-7b | ~02:00 |
| 02:00 | deepseek-v2-lite-chat | ~02:30 |
| 02:30 | qwen3.5-35b | ~03:00 |

### 深度批（MATH + BBH）

| 时间 | 模型 | 预计完成 |
|------|------|---------|
| 03:00 | qwen2.5-1.5b-instruct | ~04:45 |
| 03:30 | deepseek-r1-distill-qwen-7b | ~05:15 |
| 04:00 | deepseek-v2-lite-chat | ~05:45 |
| 04:30 | qwen3.5-35b | ~06:15 |

> 全部完成约 06:15，整体耗时约 5 小时。模型间错开 30 分钟启动，避免 API 并发过载。

## 定时任务配置清单

| 任务名 | 模型 | Benchmark | Cron |
|--------|------|-----------|------|
| daily-quick-qwen2.5-1.5b | qwen2.5-1.5b-instruct | humaneval, gsm8k, truthfulqa_gen | `0 1 * * *` |
| daily-quick-ds-r1-7b | deepseek-r1-distill-qwen-7b | humaneval, gsm8k, truthfulqa_gen | `30 1 * * *` |
| daily-quick-ds-v2-lite | deepseek-v2-lite-chat | humaneval, gsm8k, truthfulqa_gen | `0 2 * * *` |
| daily-quick-qwen3.5-35b | qwen3.5-35b | humaneval, gsm8k, truthfulqa_gen | `30 2 * * *` |
| daily-deep-qwen2.5-1.5b | qwen2.5-1.5b-instruct | math, bbh_cot_fewshot | `0 3 * * *` |
| daily-deep-ds-r1-7b | deepseek-r1-distill-qwen-7b | math, bbh_cot_fewshot | `30 3 * * *` |
| daily-deep-ds-v2-lite | deepseek-v2-lite-chat | math, bbh_cot_fewshot | `0 4 * * *` |
| daily-deep-qwen3.5-35b | qwen3.5-35b | math, bbh_cot_fewshot | `30 4 * * *` |

## 时间线总览

```
01:00 ── qwen2.5 ── 快速批 ──┐
01:30 ── ds-r1-7b ─ 快速批 ──┤
02:00 ── ds-v2 ──── 快速批 ──┤
02:30 ── qwen3.5 ── 快速批 ──┘
03:00 ── qwen2.5 ── 深度批 ────────┐
03:30 ── ds-r1-7b ─ 深度批 ────────┤
04:00 ── ds-v2 ──── 深度批 ────────┤
04:30 ── qwen3.5 ── 深度批 ────────┘
                                   ~06:15 全部完成
```

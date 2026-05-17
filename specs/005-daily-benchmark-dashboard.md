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

**共 14 个定时任务**（qwen2.5-1.5b 仅 C-Eval + GSM8K），各自独立，单个失败不影响其他。

## 每日调度时间表

不同模型并行跑，同模型串行，30 分钟错开启动，00:00 - 07:00 内完成：

```
时间      模型                    Benchmark      并发任务数
─────────────────────────────────────────────────────────
00:02    qwen3.5-35b             MMLU           2
00:02    qwen2.5-1.5b-instruct   C-Eval        ─┘
00:32    deepseek-v2-lite-chat   MMLU           3
01:02    deepseek-r1-7b          MMLU          ─┘
02:32    qwen3.5-35b             C-Eval         4 (峰值)
02:32    qwen2.5-1.5b-instruct   GSM8K         ─┘
03:02    deepseek-v2-lite-chat   C-Eval         3
03:32    deepseek-r1-7b          C-Eval        ─┘
05:02    qwen3.5-35b             GSM8K          2
05:32    qwen3.5-35b             HumanEval     ─┘
05:32    deepseek-v2-lite-chat   GSM8K          2
06:02    deepseek-v2-lite-chat   HumanEval     ─┘
06:02    deepseek-r1-7b          GSM8K          1
06:32    deepseek-r1-7b          HumanEval     ─┘
```

- 峰值 4 个任务并行（02:32），约 32 并发请求
- 最晚 06:32 启动 HumanEval，约 06:45 全部完成

## 种子数据

预设文件：`backend/presets/daily-benchmark.json`

- 通过页面「导入计划」按钮选择 JSON 文件批量导入
- 导入前修改 `api_base`、`api_key`、`auth_type` 为实际部署值
- 所有任务默认启用，可通过页面关闭
- 并发数默认 8，stream 默认开启

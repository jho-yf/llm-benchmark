# Benchmark 评测策略与时间预估

## 按 Capability 分层跑

| 层级 | Benchmark | 考察能力 | 建议场景 |
|------|-----------|---------|---------|
| **必跑核心** | GSM8K + HumanEval | 数学推理 + 代码生成 | 每个模型必跑，最核心的两个能力指标 |
| **扩展推理** | + MATH + BBH | 高等数学 + 通用逻辑 | 需要全面评估推理能力时加跑 |
| **安全对齐** | + TruthfulQA | 真实性/幻觉 | 面向用户的产品必跑 |

ARC-Challenge / HellaSwag / MMLU 为多选题类型（loglikelihood），当前 Chat API 不支持，不用考虑。

实践中大多数模型发布报告包含 GSM8K、MATH、HumanEval、MMLU。当前可跑的是前三个 + BBH + TruthfulQA，跑 3-4 个即可给出一份有参考价值的评估报告。

## 预估时间

以单个 API 请求耗时 **2-5 秒**估算（取决于模型推理速度和网络延迟）。使用并发请求（`num_concurrent`）可显著缩短评测时间：

| num_concurrent | HumanEval | GSM8K | TruthfulQA | MATH | BBH |
|:-:|:-:|:-:|:-:|:-:|:-:|
| 1（串行） | 5-15 min | 45-110 min | 30-70 min | 3-7 h | 3.5-9 h |
| 8（默认） | 1-2 min | 6-15 min | 4-10 min | 25-55 min | 30-70 min |
| 16 | <1 min | 3-8 min | 2-5 min | 15-30 min | 18-40 min |

| Benchmark | 题目数 | Few-shot | 预估时间 |
|-----------|--------|----------|---------|
| **HumanEval** | 164 | 0 | 5-15 分钟 |
| **GSM8K** | 1,319 | 8 | 45-110 分钟 |
| **TruthfulQA** | 817 | 0 | 30-70 分钟 |
| **MATH** | ~5,000 | 4 | 3-7 小时 |
| **BBH** | 6,511 | 3 | 3.5-9 小时 |

全部 5 个跑完约 **8-18 小时**。

## 推荐评测方案

### 快速验证（确认模型可正常评测）

HumanEval（164 题，5-15 分钟出结果）

### 日常评测

HumanEval + GSM8K + TruthfulQA，约 1.5-3 小时

### 全面评测

全部 5 个 Benchmark，约 8-18 小时，建议配成定时任务执行

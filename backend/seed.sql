-- Seed data: daily benchmark scheduled jobs
-- Modify api_base, api_key, auth_type to match your deployment
-- Then run: sqlite3 backend/benchmark.db < backend/seed.sql

-- ====================================================================
-- qwen3.5-35b: MMLU, C-Eval, GSM8K, HumanEval
-- ====================================================================

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'qwen3.5-35b / MMLU (5-shot)',
  '2 0 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'qwen3.5-35b',
  1,
  '{"num_concurrent": 8}',
  'MMLU (5-shot)',
  'knowledge',
  '{"tasks": ["mmlu_generative"], "num_fewshot": {"mmlu_generative": 5}, "limit": null, "batch_size": 1}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'qwen3.5-35b / C-Eval (5-shot)',
  '32 0 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'qwen3.5-35b',
  1,
  '{"num_concurrent": 8}',
  'C-Eval (5-shot)',
  'knowledge',
  '{"tasks": ["ceval_gen"], "num_fewshot": {"ceval_gen": 5}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 32}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'qwen3.5-35b / GSM8K (8-shot)',
  '2 6 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'qwen3.5-35b',
  1,
  '{"num_concurrent": 8}',
  'GSM8K (8-shot)',
  'math',
  '{"tasks": ["gsm8k"], "num_fewshot": {"gsm8k": 8}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 512}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'qwen3.5-35b / HumanEval (0-shot)',
  '32 6 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'qwen3.5-35b',
  1,
  '{"num_concurrent": 8}',
  'HumanEval (0-shot)',
  'coding',
  '{"tasks": ["humaneval"], "num_fewshot": {"humaneval": 0}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 1024}}',
  '{"pass@1": "pass@1"}'
);

-- ====================================================================
-- deepseek-v2-lite-chat: MMLU, C-Eval, GSM8K, HumanEval
-- ====================================================================

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-v2-lite-chat / MMLU (5-shot)',
  '2 1 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-v2-lite-chat',
  1,
  '{"num_concurrent": 8}',
  'MMLU (5-shot)',
  'knowledge',
  '{"tasks": ["mmlu_generative"], "num_fewshot": {"mmlu_generative": 5}, "limit": null, "batch_size": 1}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-v2-lite-chat / C-Eval (5-shot)',
  '32 1 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-v2-lite-chat',
  1,
  '{"num_concurrent": 8}',
  'C-Eval (5-shot)',
  'knowledge',
  '{"tasks": ["ceval_gen"], "num_fewshot": {"ceval_gen": 5}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 32}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-v2-lite-chat / GSM8K (8-shot)',
  '2 7 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-v2-lite-chat',
  1,
  '{"num_concurrent": 8}',
  'GSM8K (8-shot)',
  'math',
  '{"tasks": ["gsm8k"], "num_fewshot": {"gsm8k": 8}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 512}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-v2-lite-chat / HumanEval (0-shot)',
  '32 7 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-v2-lite-chat',
  1,
  '{"num_concurrent": 8}',
  'HumanEval (0-shot)',
  'coding',
  '{"tasks": ["humaneval"], "num_fewshot": {"humaneval": 0}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 1024}}',
  '{"pass@1": "pass@1"}'
);

-- ====================================================================
-- qwen2.5-1.5b-instruct: C-Eval, GSM8K only (small model)
-- ====================================================================

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'qwen2.5-1.5b-instruct / C-Eval (5-shot)',
  '2 2 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'qwen2.5-1.5b-instruct',
  1,
  '{"num_concurrent": 8}',
  'C-Eval (5-shot)',
  'knowledge',
  '{"tasks": ["ceval_gen"], "num_fewshot": {"ceval_gen": 5}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 32}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'qwen2.5-1.5b-instruct / GSM8K (8-shot)',
  '2 4 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'qwen2.5-1.5b-instruct',
  1,
  '{"num_concurrent": 8}',
  'GSM8K (8-shot)',
  'math',
  '{"tasks": ["gsm8k"], "num_fewshot": {"gsm8k": 8}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 512}}',
  '{"accuracy": "exact_match"}'
);

-- ====================================================================
-- deepseek-r1-distill-qwen-7b: MMLU, C-Eval, GSM8K, HumanEval
-- ====================================================================

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-r1-7b / MMLU (5-shot)',
  '2 3 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-r1-distill-qwen-7b',
  1,
  '{"num_concurrent": 8}',
  'MMLU (5-shot)',
  'knowledge',
  '{"tasks": ["mmlu_generative"], "num_fewshot": {"mmlu_generative": 5}, "limit": null, "batch_size": 1}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-r1-7b / C-Eval (5-shot)',
  '32 3 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-r1-distill-qwen-7b',
  1,
  '{"num_concurrent": 8}',
  'C-Eval (5-shot)',
  'knowledge',
  '{"tasks": ["ceval_gen"], "num_fewshot": {"ceval_gen": 5}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 32}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-r1-7b / GSM8K (8-shot)',
  '2 8 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-r1-distill-qwen-7b',
  1,
  '{"num_concurrent": 8}',
  'GSM8K (8-shot)',
  'math',
  '{"tasks": ["gsm8k"], "num_fewshot": {"gsm8k": 8}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 512}}',
  '{"accuracy": "exact_match"}'
);

INSERT INTO scheduled_job (name, cron_expr, enabled, llm_provider, llm_api_base, llm_api_key, llm_auth_type, llm_model_id, llm_stream, llm_params, benchmark_name, benchmark_category, benchmark_config, benchmark_metrics)
VALUES (
  'deepseek-r1-7b / HumanEval (0-shot)',
  '32 8 * * *',
  1,
  'custom',
  'http://localhost:11434/v1',
  NULL,
  'none',
  'deepseek-r1-distill-qwen-7b',
  1,
  '{"num_concurrent": 8}',
  'HumanEval (0-shot)',
  'coding',
  '{"tasks": ["humaneval"], "num_fewshot": {"humaneval": 0}, "limit": null, "batch_size": 1, "generation_kwargs": {"max_gen_toks": 1024}}',
  '{"pass@1": "pass@1"}'
);

"""Subprocess worker for running lm-eval. Outputs JSON result to stdout."""
import json
import os
import sys


def main():
    payload_path = sys.argv[1]
    with open(payload_path) as f:
        payload = json.load(f)

    benchmark_config = payload["benchmark_config"]
    llm_config = payload["llm_config"]

    datasets_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "datasets",
    )
    os.environ.setdefault("HF_DATASETS_CACHE", os.environ.get("HF_DATASETS_CACHE", datasets_dir))
    os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

    if llm_config.get("api_key"):
        os.environ["OPENAI_API_KEY"] = llm_config["api_key"]

    from lm_eval import evaluator

    tasks = benchmark_config.get("tasks", [])
    num_fewshot = benchmark_config.get("num_fewshot", {})
    limit = benchmark_config.get("limit", None)
    batch_size = benchmark_config.get("batch_size", 1)

    task_list = tasks if isinstance(tasks, list) else [tasks]

    if isinstance(num_fewshot, dict):
        num_fewshot = next(iter(num_fewshot.values()), 0)

    base_url = llm_config["api_base"].rstrip("/")
    if not base_url.endswith("/chat/completions"):
        base_url = base_url + "/chat/completions"

    model_args_dict = {
        "model": llm_config["model_id"],
        "base_url": base_url,
        "tokenizer_backend": "cl100k",
    }
    if llm_config.get("api_key"):
        model_args_dict["api_key"] = llm_config["api_key"]

    model_args_str = ",".join(f"{k}={v}" for k, v in model_args_dict.items())

    results = evaluator.simple_evaluate(
        model="local-chat-completions",
        model_args=model_args_str,
        tasks=task_list,
        num_fewshot=num_fewshot,
        limit=limit,
        batch_size=batch_size,
        apply_chat_template=True,
    )

    if hasattr(results, "results"):
        output = {
            "results": results.results,
            "configs": getattr(results, "configs", {}),
        }
    else:
        output = {
            "results": results.get("results", {}) if isinstance(results, dict) else {},
            "configs": results.get("configs", {}) if isinstance(results, dict) else {},
        }

    sys.stdout.write(json.dumps(output))


if __name__ == "__main__":
    main()

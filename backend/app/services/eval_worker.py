"""Subprocess worker for running lm-eval. Outputs JSON result to stdout."""
import json
import os
import sys


def _patch_concurrent_gather():
    """Fix lm-eval concurrent request session lifecycle bug.

    In lm-eval v0.4.x, ``get_batched_requests`` uses ``tqdm_asyncio.gather``
    without ``return_exceptions=True``.  When one task raises, ``gather``
    cancels the remaining tasks and the ``async with ClientSession`` block
    exits, closing the aiohttp session.  Tenacity retries that are still
    waiting then hit "Session is closed".

    We patch ``get_batched_requests`` to pass ``return_exceptions=True`` and
    re-raise the first exception after all tasks have finished.
    """
    import asyncio
    import logging

    from aiohttp import ClientSession, ClientTimeout, TCPConnector
    from lm_eval.models.api_models import TemplateAPI
    from lm_eval.models.utils import chunks
    from tenacity import retry, stop_after_attempt, wait_exponential

    eval_logger = logging.getLogger("lm_eval")

    async def _patched_get_batched_requests(self, requests, cache_keys, *, generate=True, ctxlens=None, **kwargs):
        ctxlens = ctxlens if ctxlens else [None] * len(requests)
        conn = TCPConnector(limit=self._concurrent, ssl=self.verify_certificate)
        sem = asyncio.Semaphore(self._concurrent)
        async with ClientSession(
            connector=conn, timeout=ClientTimeout(total=self.timeout)
        ) as session:
            retry_fn = retry(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=0.5, min=1, max=10),
                reraise=True,
                before_sleep=lambda retry_state: eval_logger.info(
                    f"Retry attempt {retry_state.attempt_number}"
                ),
            )(self.amodel_call)
            tasks = [
                asyncio.create_task(
                    retry_fn(
                        session=session,
                        sem=sem,
                        messages=message,
                        cache_keys=cache_key,
                        generate=generate,
                        ctxlens=ctxlen,
                        **kwargs,
                    )
                )
                for message, cache_key, ctxlen in zip(
                    chunks(requests, n=self._batch_size),
                    chunks(cache_keys, n=self._batch_size),
                    chunks(ctxlens, n=self._batch_size),
                )
            ]

            from tqdm import tqdm as std_tqdm

            pbar = std_tqdm(desc="Requesting API", total=len(tasks))
            done = asyncio.gather(*tasks, return_exceptions=True)

            def _on_complete(_):
                pbar.update(1)

            for t in tasks:
                t.add_done_callback(_on_complete)

            results = await done
            pbar.close()

        # Raise first real exception after all tasks completed
        for r in results:
            if isinstance(r, Exception):
                raise r
        return results

    TemplateAPI.get_batched_requests = _patched_get_batched_requests


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

    num_concurrent = (llm_config.get("params") or {}).get("num_concurrent", 8)
    if num_concurrent > 1:
        _patch_concurrent_gather()

    from lm_eval import evaluator
    from lm_eval.tasks import TaskManager

    tasks = benchmark_config.get("tasks", [])
    num_fewshot = benchmark_config.get("num_fewshot", {})
    limit = benchmark_config.get("limit", None)
    batch_size = benchmark_config.get("batch_size", 1)
    gen_kwargs = benchmark_config.get("generation_kwargs", None)

    task_list = tasks if isinstance(tasks, list) else [tasks]

    # Expand task groups and filter out tasks incompatible with Chat API
    # Both "loglikelihood" and "multiple_choice" output types call lm.loglikelihood()
    _CHAT_INCOMPATIBLE = {"loglikelihood", "multiple_choice"}
    tm = TaskManager(include_path=None)
    resolved = []
    for t in task_list:
        try:
            task_dict = tm.load_task_or_group(t)
            if isinstance(task_dict, dict):
                for name, obj in task_dict.items():
                    ot = getattr(obj, "OUTPUT_TYPE", None) or getattr(obj, "output_type", None)
                    if ot not in _CHAT_INCOMPATIBLE:
                        resolved.append(name)
                    else:
                        sys.stderr.write(f"Skipping {name}: requires loglikelihood (incompatible with Chat API)\n")
            else:
                resolved.append(t)
        except Exception:
            resolved.append(t)
    task_list = resolved

    if not task_list:
        sys.stderr.write("No compatible tasks found after filtering.\n")
        sys.stdout.write(json.dumps({"results": {}, "configs": {}}))
        return

    if isinstance(num_fewshot, dict):
        num_fewshot = next(iter(num_fewshot.values()), 0)

    base_url = llm_config["api_base"].rstrip("/")
    if not base_url.endswith("/chat/completions"):
        base_url = base_url + "/chat/completions"

    model_args_dict = {
        "model": llm_config["model_id"],
        "base_url": base_url,
        "tokenizer_backend": "cl100k",
        "num_concurrent": num_concurrent,
        "eos_string": "</s>",
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
        gen_kwargs=gen_kwargs,
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

    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items() if not callable(v)}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    sys.stdout.write(json.dumps(_sanitize(output)))


if __name__ == "__main__":
    main()

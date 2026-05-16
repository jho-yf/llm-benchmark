"""Subprocess worker for running lm-eval. Outputs JSON result to stdout."""
import asyncio
import json
import os
import sys

os.environ.setdefault("HF_ALLOW_CODE_EVAL", "1")

# Global token usage accumulator
_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _accumulate_usage(usage):
    """Accumulate token usage from a single API response."""
    if not usage or not isinstance(usage, dict):
        return
    _token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
    _token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
    _token_usage["total_tokens"] += usage.get("total_tokens", 0)


def _patch_stream_mode():
    """Patch TemplateAPI to support streaming SSE responses.

    When ``stream: true`` is set in the request, the API returns SSE
    (Server-Sent Events) chunks instead of a single JSON body.  This
    patch intercepts the response, reads all SSE chunks, assembles the
    content from ``choices[0].delta.content``, and returns a
    non-streaming-style dict so that downstream parsing stays unchanged.
    """

    from lm_eval.models.api_models import TemplateAPI

    # --- async path (aiohttp, used when num_concurrent > 1) ---
    _orig_amodel_call = TemplateAPI.amodel_call

    async def _stream_amodel_call(self, session, sem, messages, *,
                                  generate=True, cache_keys=None,
                                  ctxlens=None, gen_kwargs=None, **kwargs):
        import copy
        from tenacity import retry, stop_after_attempt, wait_exponential

        gen_kwargs = copy.deepcopy(gen_kwargs)
        payload = self._create_payload(
            self.create_message(messages),
            generate=generate,
            gen_kwargs=gen_kwargs,
            seed=self._seed,
            **kwargs,
        )

        is_stream = payload.get("stream", False)
        cache_method = "generate_until" if generate else "loglikelihood"
        acquired = await sem.acquire()
        try:
            async with session.post(
                self.base_url, json=payload, headers=self.header,
            ) as response:
                if not response.ok:
                    error_text = await response.text()
                    import logging
                    logging.getLogger("lm_eval").warning(
                        f"API request failed! Status: {response.status}, "
                        f"Response: {error_text}. Retrying..."
                    )
                response.raise_for_status()

                if is_stream:
                    outputs = await _read_sse_async(response)
                else:
                    outputs = await response.json()
                    _accumulate_usage(outputs.get("usage"))

            tmp_answers = (
                self.parse_generations(outputs=outputs)
                if generate
                else self.parse_logprobs(
                    outputs=outputs, tokens=messages, ctxlens=ctxlens,
                )
            )

            from lm_eval.models.api_models import LMEVAL_MODEL_NONE_ANSWER_PLACEHOLDER
            answers = []
            for a in tmp_answers:
                if a is None:
                    answers.append(LMEVAL_MODEL_NONE_ANSWER_PLACEHOLDER)
                else:
                    answers.append(a)

            if cache_keys:
                for res, cache in zip(answers, cache_keys):
                    self.cache_hook.add_partial(cache_method, cache, res)
            return answers
        except BaseException as e:
            import logging
            logging.getLogger("lm_eval").error(
                f"Exception:{repr(e)}, retrying."
            )
            raise e
        finally:
            if acquired:
                sem.release()

    TemplateAPI.amodel_call = _stream_amodel_call

    # --- sync path (requests, used when num_concurrent <= 1) ---
    _orig_model_call = TemplateAPI.model_call

    def _stream_model_call(self, messages, *, generate=True,
                           gen_kwargs=None, **kwargs):
        import copy
        import requests as req
        from tenacity import RetryError

        gen_kwargs = copy.deepcopy(gen_kwargs)
        payload = self._create_payload(
            self.create_message(messages),
            generate=generate,
            gen_kwargs=gen_kwargs,
            seed=self._seed,
            **kwargs,
        )
        is_stream = payload.get("stream", False)
        try:
            response = req.post(
                self.base_url, json=payload, headers=self.header,
                verify=self.verify_certificate, stream=is_stream,
            )
            if not response.ok:
                import logging
                logging.getLogger("lm_eval").warning(
                    f"API request failed: {response.text}. Retrying..."
                )
            response.raise_for_status()

            if is_stream:
                outputs = _read_sse_sync(response)
            else:
                outputs = response.json()
                _accumulate_usage(outputs.get("usage"))
            return outputs
        except RetryError:
            import logging
            logging.getLogger("lm_eval").error(
                "API request failed after multiple retries."
            )
            return None

    TemplateAPI.model_call = _stream_model_call

    # --- patch _create_payload to inject stream:true ---
    _orig_create_payload = TemplateAPI._create_payload

    def _streaming_create_payload(self, messages, *, generate=True,
                                  gen_kwargs=None, seed=1234, eos=None,
                                  **kwargs):
        payload = _orig_create_payload(
            self, messages, generate=generate, gen_kwargs=gen_kwargs,
            seed=seed, eos=eos, **kwargs,
        )
        if self._stream_enabled:
            payload["stream"] = True
        return payload

    TemplateAPI._create_payload = _streaming_create_payload
    TemplateAPI._stream_enabled = False


async def _read_sse_async(response):
    """Read SSE stream from aiohttp response and assemble into
    a non-streaming-style response dict."""
    content_parts = []
    model_name = ""
    usage = {}

    async for raw_line in response.content:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue

        model_name = chunk.get("model", model_name)

        choices = chunk.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            if "content" in delta and delta["content"] is not None:
                content_parts.append(delta["content"])

        chunk_usage = chunk.get("usage")
        if chunk_usage:
            usage = chunk_usage

    full_content = "".join(content_parts)
    return {
        "choices": [{"index": 0, "message": {"role": "assistant", "content": full_content}}],
        "model": model_name,
        "usage": usage,
    }


def _read_sse_sync(response):
    """Read SSE stream from requests response and assemble into
    a non-streaming-style response dict."""
    content_parts = []
    model_name = ""
    usage = {}

    for raw_line in response.iter_lines():
        line = raw_line.decode("utf-8", errors="replace").strip() if isinstance(raw_line, bytes) else raw_line.strip()
        if not line or not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue

        model_name = chunk.get("model", model_name)

        choices = chunk.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            if "content" in delta and delta["content"] is not None:
                content_parts.append(delta["content"])

        chunk_usage = chunk.get("usage")
        if chunk_usage:
            usage = chunk_usage

    full_content = "".join(content_parts)
    return {
        "choices": [{"index": 0, "message": {"role": "assistant", "content": full_content}}],
        "model": model_name,
        "usage": usage,
    }


def _patch_concurrent_gather():
    """Fix lm-eval concurrent request session lifecycle bug."""
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
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    if llm_config.get("api_key"):
        os.environ["OPENAI_API_KEY"] = llm_config["api_key"]

    stream_enabled = llm_config.get("stream", True)
    num_concurrent = (llm_config.get("params") or {}).get("num_concurrent", 8)

    # Always patch stream mode so _create_payload can inject stream:true
    _patch_stream_mode()

    if num_concurrent > 1:
        _patch_concurrent_gather()

    from lm_eval import evaluator
    from lm_eval.tasks import TaskManager
    from lm_eval.models.api_models import TemplateAPI

    # Enable stream on the class so _create_payload picks it up
    TemplateAPI._stream_enabled = stream_enabled

    num_fewshot = benchmark_config.get("num_fewshot", {})
    limit = benchmark_config.get("limit", None)
    batch_size = benchmark_config.get("batch_size", 1)
    gen_kwargs = benchmark_config.get("generation_kwargs", None)

    # Auto-map multiple_choice tasks to generative variants for Chat API compatibility
    _GEN_MAP = {
        "mmlu": "mmlu_generative",
        "ceval": "ceval_gen",
        "humaneval": "humaneval_instruct",
    }

    def _map_tasks(task_list):
        if isinstance(task_list, str):
            task_list = [task_list]
        return [_GEN_MAP.get(t, t) for t in task_list]

    def _map_fewshot(num_fewshot, task_list):
        if isinstance(num_fewshot, dict):
            mapped = {}
            for k, v in num_fewshot.items():
                mapped[_GEN_MAP.get(k, k)] = v
            return mapped
        return num_fewshot

    _CHAT_INCOMPATIBLE = {"loglikelihood", "multiple_choice"}

    def _collect_output_types(obj):
        types = set()
        if isinstance(obj, dict):
            for v in obj.values():
                types |= _collect_output_types(v)
        else:
            ot = getattr(obj, "OUTPUT_TYPE", None)
            if ot is None and hasattr(obj, "config"):
                ot = getattr(obj.config, "output_type", None)
            types.add(ot)
        return types

    custom_tasks_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tasks")
    include_paths = [custom_tasks_dir] if os.path.isdir(custom_tasks_dir) else None
    tm = TaskManager(include_path=include_paths)

    def _resolve_tasks(task_list):
        """Load tasks, filter incompatible ones, return resolved list."""
        resolved = []
        for t in task_list:
            try:
                task_dict = tm.load_task_or_group(t)
                output_types = _collect_output_types(task_dict)
                if output_types & _CHAT_INCOMPATIBLE:
                    sys.stderr.write(f"Skipping {t}: requires loglikelihood (incompatible with Chat API)\n")
                else:
                    resolved.append(t)
            except Exception as e:
                sys.stderr.write(f"Skipping {t}: failed to load - {e}\n")
                sys.stderr.flush()
        return resolved

    def _run_single_benchmark(task_list, fewshot_val):
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
            num_fewshot=fewshot_val,
            limit=limit,
            batch_size=batch_size,
            apply_chat_template=True,
            gen_kwargs=gen_kwargs,
            confirm_run_unsafe_code=True,
            task_manager=tm,
        )

        if hasattr(results, "results"):
            return {
                "results": results.results,
                "configs": getattr(results, "configs", {}),
                "n-samples": getattr(results, "n-samples", {}),
                "n-shot": getattr(results, "n-shot", {}),
                "versions": getattr(results, "versions", {}),
            }
        elif isinstance(results, dict):
            return {
                "results": results.get("results", {}),
                "configs": results.get("configs", {}),
                "n-samples": results.get("n-samples", {}),
                "n-shot": results.get("n-shot", {}),
                "versions": results.get("versions", {}),
            }
        else:
            return {"results": {}, "configs": {}, "n-samples": {}, "n-shot": {}, "versions": {}}

    # Monkey-patch lm-eval build_qa_turn to handle non-string answers
    import lm_eval.api.task as _task_mod
    _orig_build_qa_turn = _task_mod.ConfigurableTask.build_qa_turn

    def _safe_build_qa_turn(self, *, q=None, c=None, a=None, gen_prefix=None, tgt_delim=' ', few_delim='\n\n'):
        if isinstance(a, list):
            a = [str(x) for x in a]
            if len(a) == 1:
                a = a[0]
        elif a is not None and not isinstance(a, str):
            a = str(a)
        return _orig_build_qa_turn(self, q=q, c=c, a=a, gen_prefix=gen_prefix, tgt_delim=tgt_delim, few_delim=few_delim)

    _task_mod.ConfigurableTask.build_qa_turn = _safe_build_qa_turn

    # --- Run benchmarks ---
    tasks_raw = benchmark_config.get("tasks", [])
    if isinstance(tasks_raw, str):
        tasks_raw = [tasks_raw]

    task_list = _map_tasks(tasks_raw)
    num_fewshot = _map_fewshot(num_fewshot, task_list)
    task_list = _resolve_tasks(task_list)

    if not task_list:
        msg = "所有任务均不兼容 Chat API（需要 loglikelihood 支持）。被过滤的任务: " + ", ".join(tasks_raw)
        sys.stderr.write(msg + "\n")
        sys.stdout.write(json.dumps({"error": msg, "results": {}, "configs": {}}))
        return

    def _sanitize(obj):
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items() if not callable(v)}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    # Run each task separately so we can show per-benchmark progress
    merged = {"results": {}, "configs": {}, "n-samples": {}, "n-shot": {}, "versions": {}}
    total = len(task_list)

    for idx, task_name in enumerate(task_list):
        sys.stderr.write(f"[benchmark {idx + 1}/{total}] {task_name} loading\n")
        sys.stderr.flush()

        # Extract fewshot for this specific task
        if isinstance(num_fewshot, dict):
            fewshot_val = num_fewshot.get(task_name, 0)
        else:
            fewshot_val = num_fewshot if isinstance(num_fewshot, int) else 0

        try:
            sys.stderr.write(f"[benchmark {idx + 1}/{total}] {task_name} running\n")
            sys.stderr.flush()
            batch = _run_single_benchmark([task_name], fewshot_val)
            for key in merged:
                if key in batch and isinstance(batch[key], dict):
                    merged[key].update(batch[key])
            sys.stderr.write(f"[benchmark {idx + 1}/{total}] {task_name} done\n")
            partial = {**merged, "token_usage": dict(_token_usage)}
            sys.stderr.write(f"[partial_result] {json.dumps(_sanitize(partial))}\n")
            sys.stderr.flush()
        except Exception as e:
            sys.stderr.write(f"[benchmark {idx + 1}/{total}] {task_name} failed: {e}\n")
            sys.stderr.flush()

    output = {**merged, "token_usage": dict(_token_usage)}
    sys.stdout.write(json.dumps(_sanitize(output)))


if __name__ == "__main__":
    main()

"""HumanEval utils with lazy code_eval loading (avoids Hub download at import time)."""
import os

_compute = None
_CODE_EVAL_LOCAL = os.path.expanduser(
    "~/.cache/huggingface/modules/evaluate_modules/metrics/"
    "evaluate-metric--code_eval/"
    "78d307ea938083398db7d9815f03ed661e9c15f60d77880ce007a8a02648f176/code_eval.py"
)


def _get_compute():
    global _compute
    if _compute is None:
        import evaluate as hf_evaluate
        if os.path.exists(_CODE_EVAL_LOCAL):
            _compute = hf_evaluate.load(_CODE_EVAL_LOCAL)
        else:
            _compute = hf_evaluate.load("code_eval")
    return _compute


def pass_at_k(references: list[str], predictions: list[list[str]], k: list[int] = None):
    assert k is not None
    if isinstance(k, int):
        k = [k]
    res = _get_compute().compute(references=references, predictions=predictions, k=k)
    return res[0]


def build_predictions_instruct(
    resps: list[list[str]], docs: list[dict]
) -> list[list[str]]:
    return [
        [
            doc["prompt"] + (r if r.find("```") == -1 else r[: r.find("```")])
            for r in resp
        ]
        for resp, doc in zip(resps, docs)
    ]

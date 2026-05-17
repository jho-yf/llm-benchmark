"""Pre-download all benchmark datasets for offline use in Docker."""
import json
import sys
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset
from huggingface_hub import snapshot_download


_DATASETS = [
    ("openai/gsm8k", False),
    ("openai/openai_humaneval", False),
    ("cais/mmlu", True),
    ("ceval/ceval-exam", True),
    ("Xnhyacinth/LongBench", True),
]


def main():
    project_dir = Path(__file__).parent.parent
    datasets_cache = project_dir / "datasets"
    hf_cache = project_dir / "hf_cache"
    hf_cache.mkdir(exist_ok=True)

    print(f"Downloading datasets to: {datasets_cache}")
    print(f"Caching HF hub repo snapshots to: {hf_cache}")

    for repo_id, needs_config in _DATASETS:
        print(f"\n=== {repo_id} ===")

        # 1. Cache dataset repo snapshot (loading scripts, metadata) for offline use
        print(f"  Snapshot...", end=" ", flush=True)
        try:
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                cache_dir=str(hf_cache),
            )
            print("OK")
        except Exception as e:
            print(f"WARN: {e}")

        # 2. Load datasets to cache arrow files
        try:
            if needs_config:
                configs = get_dataset_config_names(repo_id)
                print(f"  {len(configs)} configs: {configs[:5]}{'...' if len(configs) > 5 else ''}")
                for i, cfg in enumerate(configs):
                    print(f"  [{i+1}/{len(configs)}] {cfg}...", end=" ", flush=True)
                    load_dataset(repo_id, cfg, trust_remote_code=True)
                    print("OK")
            else:
                load_dataset(repo_id, trust_remote_code=True)
                print("  OK")
        except Exception as e:
            print(f"  WARN: {e}", file=sys.stderr)

    # 3. Also cache lm-eval built-in task dataset repos that are not in _DATASETS
    extra_repos = [
        "openai/gsm8k",
    ]
    for repo_id in extra_repos:
        if repo_id in [r[0] for r in _DATASETS]:
            continue
        print(f"\n=== {repo_id} (extra) ===")
        try:
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                cache_dir=str(hf_cache),
            )
            print("  OK")
        except Exception as e:
            print(f"  WARN: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()

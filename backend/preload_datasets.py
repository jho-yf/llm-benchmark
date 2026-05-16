"""Pre-download all benchmark datasets for offline use in Docker."""
import json
import sys
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset


# Explicit dataset list: (repo_id, needs_config)
_DATASETS = [
    ("openai/gsm8k", False),
    ("openai/openai_humaneval", False),
    ("cais/mmlu", True),
    ("ceval/ceval-exam", True),
    ("Xnhyacinth/LongBench", True),
]


def main():
    datasets_cache = Path(__file__).parent.parent / "datasets"
    print(f"Downloading datasets to: {datasets_cache}")

    for repo_id, needs_config in _DATASETS:
        print(f"\n=== {repo_id} ===")
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

    print("\nDone.")


if __name__ == "__main__":
    main()

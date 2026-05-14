"""Pre-download all benchmark datasets for offline use in Docker."""
import json
import sys
from pathlib import Path

from lm_eval.tasks import TaskManager


def main():
    presets_dir = Path(__file__).parent / "presets"
    all_tasks = []

    for f in sorted(presets_dir.glob("*.json")):
        preset = json.loads(f.read_text())
        tasks = preset["config"]["tasks"]
        if isinstance(tasks, list):
            all_tasks.extend(tasks)
        else:
            all_tasks.append(tasks)

    all_tasks = list(dict.fromkeys(all_tasks))
    print(f"Pre-downloading datasets for tasks: {all_tasks}")

    tm = TaskManager(include_path=None)
    for task_name in all_tasks:
        print(f"  Loading task: {task_name}")
        try:
            task_dict = tm.load_task_or_group(task_name)
            if isinstance(task_dict, dict):
                for name, task_obj in task_dict.items():
                    if hasattr(task_obj, "download"):
                        task_obj.download()
                    elif hasattr(task_obj, "dataset"):
                        _ = task_obj.dataset
            print(f"    OK: {task_name}")
        except Exception as e:
            print(f"    WARN: {task_name} - {e}", file=sys.stderr)

    print("Done.")


if __name__ == "__main__":
    main()

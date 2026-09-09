"""Smoke test for prompt builders."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from prompts import build_classification_prompt, build_summary_prompt


def main() -> None:
    classification = build_classification_prompt(
        "What is the India airport limit?",
        "airport_policy.txt: INR 2,000 per trip",
    )
    summary = build_summary_prompt(
        "airport_policy.txt",
        "India airport trips are limited to INR 2,000 per trip.",
    )
    assert "What is the India airport limit?" in classification
    assert "airport_policy.txt" in classification
    assert "Return valid JSON only" in classification
    assert '"key_rules"' in summary
    print("Prompt test passed: classification and summary templates")


if __name__ == "__main__":
    main()
"""
CLI entry point for running the evaluation harness.
Invoked via: python -m app.eval.cli --mode ... --verifier ... --out ...
or via: python manage.py eval --mode ...
"""

import os
import sys
import json
import argparse

from app.eval.loader import load_dataset
from app.eval.runner import EvalRunner, format_report_table


def main():
    parser = argparse.ArgumentParser(description="Inkguard Policy Evaluation Harness")
    parser.add_argument(
        "--mode",
        choices=["rules_only", "mock", "cached", "live"],
        default="rules_only",
        help="Evaluation execution mode",
    )
    parser.add_argument(
        "--verifier",
        choices=["on", "off"],
        default="off",
        help="Toggle secondary LLM verifier pass",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to output evaluation JSON report",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of documents to evaluate",
    )
    parser.add_argument(
        "--match-verdict",
        action="store_true",
        help="Require claim verdict match for true positives",
    )

    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=None,
        help="Filter AI claim/tone findings below confidence threshold (default: config CLAIM_CONFIDENCE_THRESHOLD)",
    )

    args = parser.parse_args()

    docs = load_dataset()
    verifier_enabled = args.verifier.lower() == "on"

    runner = EvalRunner(
        mode=args.mode,
        verifier_enabled=verifier_enabled,
        claim_confidence_threshold=args.confidence_threshold,
    )
    report = runner.evaluate(
        docs,
        limit=args.limit,
        require_verdict_match=args.match_verdict,
    )

    print(format_report_table(report, args.mode, verifier_enabled))

    if args.out:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nWrote evaluation report to {args.out}")


if __name__ == "__main__":
    main()

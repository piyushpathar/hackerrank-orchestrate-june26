#!/usr/bin/env python3
"""Main pipeline entrypoint to process claims and produce output.csv."""

from __future__ import annotations

import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Add the parent directory of this script (which is "code/") to python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from claimverify.cache import ResponseCache
from claimverify.config import load_config
from claimverify.data import load_claims, load_evidence_requirements, load_user_history
from claimverify.pipeline import process_claim, ClaimResult
from claimverify.providers import AnthropicProvider, HeuristicProvider, OpenAIProvider
from claimverify.schema import OUTPUT_COLUMNS


def print_summary(results: list[ClaimResult], elapsed: float) -> None:
    total = len(results)
    errors = sum(1 for r in results if r.error is not None)
    cached = sum(1 for r in results if r.cached)
    tokens_in = sum(r.input_tokens for r in results)
    tokens_out = sum(r.output_tokens for r in results)
    images_sent = sum(r.images_sent for r in results)

    # Cost calculation based on model pricing (from config)
    config = load_config()
    pricing = config.pricing
    # pricing input/output are per million tokens
    cost_in = (tokens_in / 1_000_000) * pricing.get("input", 0.0)
    cost_out = (tokens_out / 1_000_000) * pricing.get("output", 0.0)
    total_cost = cost_in + cost_out

    print("=" * 60)
    print("CLAIMVERIFY EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total claims processed: {total}")
    print(f"Successful processes:  {total - errors}")
    print(f"Errors encountered:    {errors}")
    print(f"Cache hit rate:        {cached / total * 100:.1f}% ({cached}/{total})")
    print(f"Total time elapsed:    {elapsed:.2f} seconds")
    print(f"Average latency:       {elapsed / max(total, 1):.2f} seconds/claim")
    print(f"Images sent:           {images_sent}")
    print(f"Total tokens used:     {tokens_in + tokens_out} (In: {tokens_in}, Out: {tokens_out})")
    print(f"Estimated API Cost:    ${total_cost:.4f} (Model: {config.model})")
    print("=" * 60)


def main() -> None:
    config = load_config()
    print(f"Config Loaded: provider={config.provider}, model={config.model}, max_workers={config.max_workers}, cache={config.use_cache}")

    # Initialize paths
    repo_root = Path(__file__).resolve().parents[1]
    dataset_dir = repo_root / "dataset"
    input_csv = dataset_dir / "claims.csv"
    output_csv = dataset_dir / "output.csv"

    # Override input if arguments are passed
    if len(sys.argv) > 1:
        input_csv = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2:
        output_csv = Path(sys.argv[2]).resolve()

    print(f"Processing input file: {input_csv}")
    print(f"Saving output to:      {output_csv}")

    # Load resources
    try:
        history_index = load_user_history()
        requirements = load_evidence_requirements()
        claims = load_claims(input_csv, has_labels=False)
    except Exception as exc:
        print(f"Error loading datasets: {exc}")
        sys.exit(1)

    print(f"Loaded {len(claims)} claims, {len(history_index)} user history entries, {len(requirements)} evidence requirements.")

    # Initialize cache & provider
    cache = ResponseCache(config.cache_dir, enabled=config.use_cache)
    if config.provider == "anthropic":
        provider: Any = AnthropicProvider(
            model=config.model,
            timeout=config.request_timeout,
            max_tokens=config.max_output_tokens,
        )
    elif config.provider == "openai":
        provider = OpenAIProvider(
            model=config.model,
            timeout=config.request_timeout,
            max_tokens=config.max_output_tokens,
        )
    else:
        provider = HeuristicProvider(model=config.model)

    start_time = time.time()
    results: list[ClaimResult] = []

    # Process concurrently using ThreadPoolExecutor
    print(f"Running processing pipeline with {config.max_workers} workers...")
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        # Submit each claim exactly once; map future -> claim for ordering/errors.
        futures = {
            executor.submit(
                process_claim,
                claim,
                provider,
                config,
                cache,
                requirements,
                history_index,
            ): claim
            for claim in claims
        }

        # Gather results as they complete (re-ordered to input order below).
        for future in as_completed(futures):
            claim = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                # Handle unexpected exceptions in thread
                print(f"Unhandled thread exception for user {claim.user_id}: {exc}")

    elapsed = time.time() - start_time

    # Sort results to match original claims order
    # Let's map claims to their index to keep order
    claim_order = {id(c): i for i, c in enumerate(claims)}
    results.sort(key=lambda r: claim_order[id(r.claim)])

    # Write output CSV
    try:
        with output_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            for res in results:
                # Build complete output row
                row = {
                    "user_id": res.claim.user_id,
                    "image_paths": res.claim.image_paths,
                    "user_claim": res.claim.user_claim,
                    "claim_object": res.claim.claim_object,
                    "evidence_standard_met": "true" if res.prediction.evidence_standard_met else "false",
                    "evidence_standard_met_reason": res.prediction.evidence_standard_met_reason,
                    "risk_flags": res.prediction.risk_flags,
                    "issue_type": res.prediction.issue_type,
                    "object_part": res.prediction.object_part,
                    "claim_status": res.prediction.claim_status,
                    "claim_status_justification": res.prediction.claim_status_justification,
                    "supporting_image_ids": res.prediction.supporting_image_ids,
                    "valid_image": "true" if res.prediction.valid_image else "false",
                    "severity": res.prediction.severity,
                }
                writer.writerow(row)
        print(f"Output successfully written to {output_csv}")
    except Exception as exc:
        print(f"Error writing output file: {exc}")
        sys.exit(1)

    print_summary(results, elapsed)


if __name__ == "__main__":
    main()

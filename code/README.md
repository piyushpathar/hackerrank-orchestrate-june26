# ClaimVerify — Multi-Modal Evidence Review

ClaimVerify decides whether submitted images **support**, **contradict**, or provide
**not enough information** for a damage claim about a `car`, `laptop`, or `package`.
Images are treated as the primary source of truth; the conversation defines what to
check; user history only adds risk context and never overrides clear visual evidence.

## Layout

```
code/
├── main.py                 # Batch entrypoint: claims.csv -> output.csv
├── requirements.txt        # Python dependencies
├── evaluation/
│   └── main.py             # Runs on sample_claims.csv, writes evaluation/evaluation_report.md
└── claimverify/
    ├── config.py           # Env-driven config + provider auto-selection + pricing
    ├── data.py             # Loads claims, user_history, evidence_requirements
    ├── images.py           # Image load, media-type detect, downscale (WebP), SHA-256 hash
    ├── prompts.py          # System + user prompt construction (allowed-value constrained)
    ├── providers.py        # Anthropic, OpenAI, and Heuristic providers
    ├── pipeline.py         # Per-claim orchestration: cache -> model (retry) -> normalize
    ├── signals.py          # Deterministic prompt-injection + history risk signals
    ├── schema.py           # Output columns, allowed values, normalization
    └── cache.py            # Content-addressed disk cache (SHA-256 of model+prompt+images)
```

## Requirements

- Python 3.10+
- `pip install -r requirements.txt` (optional — the default heuristic provider
  runs on the standard library alone)

## Running

From the repository root (the parent of `code/`):

```bash
# Generate predictions for dataset/claims.csv -> dataset/output.csv
python3 code/main.py

# Or pass explicit input/output paths
python3 code/main.py dataset/claims.csv output.csv

# Run the evaluation on the labeled sample set; writes evaluation/evaluation_report.md
python3 code/evaluation/main.py
```

## Providers

The provider is selected automatically, or forced via `CLAIMVERIFY_PROVIDER`:

| Provider    | Trigger                                   | Notes |
|-------------|-------------------------------------------|-------|
| `anthropic` | `ANTHROPIC_API_KEY` set                   | Claude vision (default model `claude-3-5-sonnet-latest`) |
| `openai`    | `OPENAI_API_KEY` set                      | GPT-4o vision (default model `gpt-4o`) |
| `heuristic` | no API key (default fallback)             | Deterministic, offline, zero-cost rules — used to run without credentials |

## Configuration (environment variables)

| Variable                   | Default                      | Description |
|----------------------------|------------------------------|-------------|
| `CLAIMVERIFY_PROVIDER`     | auto                         | `anthropic` \| `openai` \| `heuristic` |
| `CLAIMVERIFY_MODEL`        | per provider                 | Override model name |
| `CLAIMVERIFY_WORKERS`      | `4`                          | Thread-pool size (throttles RPM) |
| `CLAIMVERIFY_MAX_RETRIES`  | `4`                          | Retries with exponential backoff |
| `CLAIMVERIFY_TIMEOUT`      | `60`                         | Per-request timeout (seconds) |
| `CLAIMVERIFY_MAX_TOKENS`   | `1024`                       | Max output tokens |
| `CLAIMVERIFY_CACHE_DIR`    | `code/.cache`                | Response cache directory |
| `CLAIMVERIFY_NO_CACHE`     | unset                        | Set to disable the response cache |
| `CLAIMVERIFY_IMAGE_MAX_DIM`| `1024`                       | Downscale images above this dimension |

## How a claim is processed

1. Load the claim, its user history, and object-relevant evidence requirements.
2. Load + downscale images, compute SHA-256 content hashes.
3. Build a constrained prompt listing allowed values for the claim object.
4. Check the content-addressed cache (model + prompt + image hashes); on a hit,
   skip the model call entirely.
5. On a miss, call the vision model with retry/backoff; on hard failure, degrade
   gracefully to a `not_enough_information` / `manual_review_required` row.
6. Post-process deterministically: merge user-history risk flags, flag embedded
   prompt-injection text as `text_instruction_present`, and coerce every field to
   the exact allowed schema before writing `output.csv`.

## Output

`output.csv` contains exactly these columns, in order:

```
user_id, image_paths, user_claim, claim_object, evidence_standard_met,
evidence_standard_met_reason, risk_flags, issue_type, object_part, claim_status,
claim_status_justification, supporting_image_ids, valid_image, severity
```

## Cost / latency notes

See `evaluation/evaluation_report.md` for model-call counts, token usage, projected
cost, latency, and the caching / batching / retry strategy.

<div align="center">

<img src="docs/images/pastecb-img-0.svg" alt="PasteCB" width="96" height="96" />

# PasteCB — Smart macOS Clipboard for Agents

[![macOS](https://img.shields.io/badge/macOS-26%2B-000000?style=flat-square&logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![Swift](https://img.shields.io/badge/Swift-5.0-F05138?style=flat-square&logo=swift&logoColor=white)](https://swift.org)
[![GitHub Release](https://img.shields.io/github/v/release/macosfy/pastecb-macos?style=flat-square&logo=github&label=release)](https://github.com/macosfy/pastecb-macos/releases)
[![License](https://img.shields.io/badge/license-Proprietary-9E9E9E?style=flat-square)](https://macosfy.com)

</div>

PasteCB is a smart clipboard for **macOS**, optimized for working with agents. It cuts vision token usage by **29% to 59%** on every image you copy.

**Download:** [Latest build (.zip)](https://github.com/macosfy/PasteCB/releases/latest)

---

## Evals

```text
Model: gpt-4o

Eval    Variant   Pixels       Size  Prompt  Total  Saved    File
------  --------  ---------  ------  ------  -----  -------  -------------------------------
eval-0  original  1244x808   62.1 KB    1134   1135  -        img-eval-0-1244x808.png
eval-0  PasteCB   700x455   104.1 KB     454    455  +59.96%  img-eval-0-pastecb-700x455.png
eval-1  original  1538x324   69.7 KB     794    795  -        img-eval-1-1538x324.png
eval-1  PasteCB   1000x211   85.5 KB     454    455  +42.82%  img-eval-1-pastecb-1000x211.png
eval-2  original  2172x1236 167.8 KB    1134   1135  -        img-eval-2-2172x1236.png
eval-2  PasteCB   1000x569  126.0 KB     794    795  +29.98%  img-eval-2-pastecb-1000x569.png
```

Average prompt-token savings across the 3 evals: **+44.25%**.

---

## Run the evals

Run `pastecb_vision_token_eval.py` to reproduce the evals locally.

### Setup

```bash
cd evals
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# edit .env and set OPENAI_API_KEY
```

### Run

```bash
python pastecb_vision_token_eval.py
```

### Environment


| Variable              | Required | Default  | Notes                                    |
| --------------------- | -------- | -------- | ---------------------------------------- |
| `OPENAI_API_KEY`      | yes      | —        | Loaded from `evals/.env`.                |
| `OPENAI_VISION_MODEL` | no       | `gpt-4o` | Any vision-capable chat model. CLI wins. |


The script uses `max_tokens=8` so totals stay dominated by **prompt / image** tokenization. Exact vision math is provider-specific; the `usage` field returned per request is what gets billed.

---

<div align="center">

© 2026 macosfy. All rights reserved.

</div>

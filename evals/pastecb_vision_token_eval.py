#!/usr/bin/env python3
"""
PasteCB vision token eval.

Sends a fixed probe prompt plus each fixture image to an OpenAI vision-capable
chat model and prints a single clean table with the API usage values
(prompt_tokens, total_tokens) for the original and the PasteCB-resized variant,
plus the relative prompt-token saving per row.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import struct
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

EVAL_DIR = Path(__file__).resolve().parent
FIXTURES = EVAL_DIR / "fixtures"

PAIR_FIXTURES: list[tuple[str, str]] = [
    ("img-eval-0-1244x808.png", "img-eval-0-pastecb-700x455.png"),
    ("img-eval-1-1538x324.png", "img-eval-1-pastecb-1000x211.png"),
    ("img-eval-2-2172x1236.png", "img-eval-2-pastecb-1000x569.png"),
]

PROBE_PROMPT = (
    "Reply with exactly the single digit 0. Do not describe the image. "
    "This is a token measurement probe."
)


def load_env() -> None:
    load_dotenv(EVAL_DIR / ".env")


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG or too short: {path.name}")
    if data[12:16] != b"IHDR":
        raise ValueError(f"IHDR chunk missing: {path.name}")
    w, h = struct.unpack(">II", data[16:24])
    return int(w), int(h)


def encode_image_data_url(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if not mime:
        mime = "application/octet-stream"
    raw = path.read_bytes()
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def measure(client: OpenAI, model: str, image_path: Path) -> dict:
    if not image_path.is_file():
        raise FileNotFoundError(f"File not found: {image_path}")

    url = encode_image_data_url(image_path)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROBE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": url, "detail": "auto"},
                    },
                ],
            }
        ],
        max_tokens=8,
        temperature=0,
    )
    u = resp.usage
    w, h = png_dimensions(image_path)
    return {
        "file": image_path.name,
        "bytes": image_path.stat().st_size,
        "pixels": f"{w}x{h}",
        "prompt_tokens": u.prompt_tokens,
        "total_tokens": u.total_tokens,
    }


def kb(n: int) -> str:
    return f"{n / 1024:.1f} KB"


def trunc_pct(value: float, decimals: int = 2) -> str:
    factor = 10 ** decimals
    truncated = int(value * factor) / factor
    sign = "+" if truncated >= 0 else "-"
    return f"{sign}{abs(truncated):.{decimals}f}%"


def render_table(model: str, rows: list[dict]) -> str:
    headers = ["Eval", "Variant", "Pixels", "Size", "Prompt", "Total", "Saved", "File"]
    body: list[list[str]] = []
    for r in rows:
        label = f"eval-{r['index'] - 1}"
        o, c = r["original"], r["compressed"]
        saved = r["saved_pct"]
        body.append([label, "original", o["pixels"], kb(o["bytes"]), str(o["prompt_tokens"]), str(o["total_tokens"]), "-", o["file"]])
        body.append([
            label,
            "pastecb",
            c["pixels"],
            kb(c["bytes"]),
            str(c["prompt_tokens"]),
            str(c["total_tokens"]),
            trunc_pct(saved),
            c["file"],
        ])

    widths = [len(h) for h in headers]
    for row in body:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    aligns = ["left", "left", "left", "right", "right", "right", "right", "left"]

    def fmt_row(cells: list[str]) -> str:
        parts = []
        for cell, w, a in zip(cells, widths, aligns):
            parts.append(cell.rjust(w) if a == "right" else cell.ljust(w))
        return "  ".join(parts)

    lines = [
        f"Model: {model}",
        "",
        fmt_row(headers),
        "  ".join("-" * w for w in widths),
    ]
    lines.extend(fmt_row(row) for row in body)
    return "\n".join(lines)


def collect(client: OpenAI, model: str) -> list[dict]:
    rows: list[dict] = []
    for idx, (orig_name, comp_name) in enumerate(PAIR_FIXTURES, start=1):
        orig = measure(client, model, FIXTURES / orig_name)
        comp = measure(client, model, FIXTURES / comp_name)
        o_pt = orig["prompt_tokens"]
        c_pt = comp["prompt_tokens"]
        saved_pct = ((o_pt - c_pt) / o_pt * 100) if o_pt else 0.0
        rows.append(
            {
                "index": idx,
                "original": orig,
                "compressed": comp,
                "saved_pct": saved_pct,
            }
        )
    return rows


def main() -> int:
    load_env()

    parser = argparse.ArgumentParser(
        description="PasteCB eval: compare vision prompt tokens for fixed fixture pairs.",
    )
    parser.add_argument("--model", help="Override OPENAI_VISION_MODEL")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print(
            "Missing OPENAI_API_KEY. Copy .env.example to .env in this folder and set your key.",
            file=sys.stderr,
        )
        return 1

    model = (args.model or os.environ.get("OPENAI_VISION_MODEL", "gpt-4o")).strip()
    client = OpenAI(api_key=api_key)

    try:
        rows = collect(client, model)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"API error: {e}", file=sys.stderr)
        return 1

    print(render_table(model, rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

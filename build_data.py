#!/usr/bin/env python3
"""Parse anchor_price_list.pdf → data/price_list.json (CLI wrapper around parser.py)."""

import json
import os

import parser

PDF_PATH = os.path.join(os.path.dirname(__file__), "anchor_price_list.pdf")
OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "price_list.json")


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    data = parser.parse_pdf(PDF_PATH)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

    total_chars = sum(len(p["raw_text"]) for p in data["pages"])
    print(f"Wrote {len(data['pages'])} pages ({total_chars:,} chars) to {OUT_PATH}")
    print(f"Edition: {data['store']['notes']}")


if __name__ == "__main__":
    main()

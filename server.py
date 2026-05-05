#!/usr/bin/env python3
"""Anchor Electronics MCP server — exposes the price list as searchable tools."""

import json
import os

from mcp.server.fastmcp import FastMCP

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "price_list.json")
with open(_DATA_PATH) as _f:
    _DATA = json.load(_f)

_port = int(os.getenv("PORT", "8080"))

mcp = FastMCP(
    "Anchor Electronics Price List",
    instructions=(
        "You have access to the January 2026 price list for Anchor Electronics, "
        "a component store in Santa Clara, CA. Use these tools to look up part numbers, "
        "prices, availability, and store information so you can help customers build shopping lists."
    ),
    host="0.0.0.0",
    port=_port,
)


@mcp.tool()
def get_store_info() -> str:
    """Return Anchor Electronics store details: address, phone, hours, and website."""
    s = _DATA["store"]
    return (
        f"Store:   {s['name']}\n"
        f"Address: {s['address']}\n"
        f"Phone:   {s['phone']}\n"
        f"Hours:   {s['hours']}\n"
        f"Website: {s['website']}\n"
        f"Notes:   {s['notes']}"
    )


@mcp.tool()
def list_categories() -> str:
    """List all product categories in the price list, one per line."""
    lines = [
        f"Page {p['page_number']}: {p['categories']}"
        for p in _DATA["pages"]
        if p["page_number"] > 1
    ]
    return "\n".join(lines)


@mcp.tool()
def search_products(query: str) -> str:
    """
    Search the price list for a part number, component type, or keyword.

    Returns matching lines with their page and category context.
    Prices may appear as per-unit costs or as 'X for $Y' bundles.
    Quantity pricing is common: columns are typically 1 / 25 / 50 / 100 / 250 / 1K.

    Examples: "MMBT3904", "10K resistor", "zener 5.1V", "74HC", "blue LED 0603"
    """
    q = query.lower().strip()
    if not q:
        return "Please provide a search query."

    results = []
    for page in _DATA["pages"]:
        if page["page_number"] == 1:
            continue
        matching = [
            line
            for line in page["raw_text"].splitlines()
            if q in line.lower() and line.strip()
        ]
        if matching:
            header = f"[Page {page['page_number']} — {page['categories']}]"
            results.append(header + "\n" + "\n".join(matching[:30]))

    if not results:
        return f"No entries found matching '{query}'. Try a broader term or use list_categories()."
    return "\n\n".join(results)


@mcp.tool()
def get_category_content(keyword: str) -> str:
    """
    Return the full price list text for one or more pages that match a category keyword.

    Pass a word from list_categories() output, e.g. 'capacitor', 'diode', 'transistor',
    'resistor', 'LED', 'socket', 'connector', 'switch', 'crystal', 'trimpot'.

    Returns raw text including all part numbers, specs, and prices for that section.
    Up to 3 matching pages are returned.
    """
    kw = keyword.lower().strip()
    matches = [
        p for p in _DATA["pages"]
        if kw in p["categories"].lower() and p["page_number"] > 1
    ]
    if not matches:
        return (
            f"No category matching '{keyword}'. "
            "Use list_categories() to see available categories."
        )
    parts = []
    for p in matches[:3]:
        parts.append(
            f"[Page {p['page_number']} — {p['categories']}]\n{p['raw_text']}"
        )
    return "\n\n".join(parts)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

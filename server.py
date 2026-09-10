#!/usr/bin/env python3
"""Anchor Electronics MCP server — exposes the price list as searchable tools."""

import asyncio
import contextlib
import json
import logging
import os
import re

import httpx
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

import parser

logger = logging.getLogger("anchor-mcp")
logging.basicConfig(level=logging.INFO)

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "price_list.json")
with open(_DATA_PATH) as _f:
    _DATA = json.load(_f)

# Anchor's own, stable price-list URL (found via their site nav: "Inventory" / "Price list").
_FETCH_URL = "https://anchor-electronics.com/price-list.pdf?x99187"
_REFRESH_INTERVAL_SECONDS = 12 * 60 * 60
_STARTUP_FETCH_TIMEOUT_SECONDS = 15

_port = int(os.getenv("PORT", "8080"))

mcp = FastMCP(
    "Anchor Electronics Price List",
    instructions=(
        f"You have access to the {_DATA['store']['edition']} price list for Anchor Electronics, "
        "a component store in Santa Clara, CA. Use these tools to look up part numbers, "
        "prices, availability, and store information so you can help customers build shopping lists."
    ),
    host="0.0.0.0",
    port=_port,
    streamable_http_path="/",
)

# Family prefixes customers commonly type as part of a full part number
# (e.g. "CD4543", "74LS00"). The catalog's densest pages sometimes render a
# part's numeric suffix without its family prefix attached (a PDF-extraction
# artifact — see parser.py), so a literal search for the full part number can
# miss a part that's genuinely in stock under its bare number. Stripping a
# known prefix and also searching the bare remainder works around that
# without depending on perfect text extraction. Longer/more-specific
# prefixes are listed first so e.g. "74HCT00" strips to "00", not "HCT00".
_FAMILY_PREFIXES = [
    "74HCT", "74ALS", "74LS", "74HC", "74S", "74C", "74F", "74",
    "CD", "MC", "SN", "LM", "NE", "TL",
]


def _alt_queries(query):
    upper = query.strip().upper()
    alts = []
    for prefix in _FAMILY_PREFIXES:
        if upper.startswith(prefix):
            remainder = query.strip()[len(prefix):]
            # Require a reasonably specific numeric remainder (this catalog's
            # standalone CD40xx/45xx-style part numbers are 4+ digits) so we
            # don't fall back to a near-universal 2-digit substring like "00"
            # for a query like "74LS00" (which is already a complete,
            # directly-searchable token on its own).
            if re.fullmatch(r"\d{4,6}", remainder):
                alts.append(remainder)
    return alts


async def _fetch_latest():
    """Download and parse the live price list. Raises on any failure."""
    async with httpx.AsyncClient(timeout=_STARTUP_FETCH_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = await client.get(_FETCH_URL)
        response.raise_for_status()
        pdf_bytes = response.content

    data = await asyncio.to_thread(parser.parse_pdf, pdf_bytes)

    total_chars = sum(len(p["raw_text"]) for p in data["pages"])
    if len(data["pages"]) < 20 or total_chars < 50_000:
        raise ValueError(
            f"fetched price list failed sanity check: {len(data['pages'])} pages, "
            f"{total_chars} chars"
        )
    return data


async def _refresh_once():
    global _DATA
    try:
        _DATA = await _fetch_latest()
        logger.info("refreshed price list: %s", _DATA["store"]["notes"])
    except Exception:
        logger.warning("price list refresh failed; keeping last known-good data", exc_info=True)


async def _refresh_loop():
    while True:
        await asyncio.sleep(_REFRESH_INTERVAL_SECONDS)
        await _refresh_once()


async def _on_startup():
    await _refresh_once()
    asyncio.create_task(_refresh_loop())


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
    if not query.strip():
        return "Please provide a search query."

    queries = [query.lower().strip()] + [q.lower() for q in _alt_queries(query)]

    results = []
    for page in _DATA["pages"]:
        if page["page_number"] == 1:
            continue
        seen = set()
        matching = []
        for line in page["raw_text"].splitlines():
            if not line.strip() or line in seen:
                continue
            line_lower = line.lower()
            if any(q in line_lower for q in queries):
                matching.append(line)
                seen.add(line)
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


def create_app():
    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://claude.ai"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # FastMCP already installs its own lifespan (running the streamable-http
    # session manager) via app.router.lifespan_context; wrap it rather than
    # replace it so both run.
    original_lifespan = app.router.lifespan_context

    @contextlib.asynccontextmanager
    async def lifespan(app):
        await _on_startup()
        async with original_lifespan(app):
            yield

    app.router.lifespan_context = lifespan
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="0.0.0.0", port=_port)

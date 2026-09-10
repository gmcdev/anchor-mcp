#!/usr/bin/env python3
"""Anchor Electronics price-list PDF -> structured data.

Shared between build_data.py (CLI, regenerates the bundled data/price_list.json
from a local PDF) and server.py (runtime: parses a freshly fetched PDF from
Anchor's site).

Uses pypdf's linear text extraction, which handles the large majority of this
catalog's pages cleanly. A handful of dense, multi-column logic-IC pages (with
several unrelated part-family tables packed side by side) don't extract
cleanly under pypdf *or* any generic layout-aware library tried against this
document — reconstructing those correctly would need a hand-built column
schema specific to those pages, which is out of scope here. Search-side
handling for that (see server.py's prefix-tolerant search_products) is what
makes full part-number lookups work regardless of that extraction limitation.
"""

import io
import re

import pypdf

# The edition label the catalog itself prints on its cover, e.g. "May 2026-C".
EDITION_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September"
    r"|October|November|December)\s+\d{4}(?:-[A-Z])?\b"
)

# Human-readable label for each page (1-indexed)
PAGE_CATEGORIES = {
    1:  "Index / Cover",
    2:  "SMT Resistors (5% and 1%), SMT Trimpots, SMT Resistor Arrays, SMT Power Resistors",
    3:  "SMT Capacitors — Ceramic, Tantalum, Aluminum Electrolytic",
    4:  "SMT Diodes (Signal, Zener, Schottky, TVS, Bridge), SMT LEDs",
    5:  "SMT Inductors, SMT Power Inductors, SMT Ferrite Beads, SMT Switches",
    6:  "SMT Transistors (BJT, MOSFET, JFET, Darlington), SMD Connectors, SMT Fuses, SMT Prototyping Boards",
    7:  "SMT Logic ICs (74-series single gate), SMT Crystals, SMT Opto Isolators, SMT Voltage Regulators, SMT Test Clips",
    8:  "Thru-Hole ICs — TTL 74/74S/74LS/74HC/74HCT Logic, Thru-Hole Voltage Regulators",
    9:  "Thru-Hole ICs — Op-Amps, Comparators, Timers, Analog, Thru-Hole Test Clips",
    10: "Thru-Hole ICs — Z80/6800/8000/6500 Series, SRAM, DRAM, EEPROM, UART, Disk Controllers, IC Sockets",
    11: "Thru-Hole LEDs, Opto Isolators, Photo Cells, Photo Sensors (Gap Detectors), Crystals, Oscillators",
    12: "Thru-Hole Capacitors — Electrolytic, Film, Ceramic Disc",
    13: "Thru-Hole Capacitors (continued), Thru-Hole Ferrite, Thru-Hole Inductors",
    14: "Thru-Hole Resistors (1/4W, 1/2W, 1W, Carbon, Metal Film)",
    15: "Trimpots (Multi-turn, Single-turn), Slide Pots, Panel Mount Pots, Resistor Networks, Power Resistors, Digital Pot",
    16: "Thru-Hole Transistors (NPN, PNP, MOSFET, Darlington, RF)",
    17: "Thru-Hole Transistors (continued), Bridge Rectifiers, Thru-Hole Diodes (Signal, Zener, Schottky, Rectifier)",
    18: "Test Leads, BNC Connectors, Molex Connectors, Crimp Lugs, E-Z Hooks, USB Adapters",
    19: "D-Sub Connectors, Headers, Flat Cable, Edgeboard Connectors, VME Connectors, Shorting Plugs, Gender Changers, HDMI Cables",
    20: "Switches (Toggle, Pushbutton, Slide, Rotary), Fuses, Cable Ties, Heat Shrink, Relays, Line Cords",
    21: "Soldering Supplies (Solder, Flux, Tips, Stations), Desoldering Tools, Wire-Wrapping Supplies",
    22: "Heat Sinks, Fans, Power Supplies, Transformers, Variac, Calipers, Wall Adapters, Terminal Blocks",
    23: "Chemicals (Cleaners, Lubricants, Adhesives), Tape (Kapton, Electrical, Copper Foil)",
    24: "Arduino / Microcontroller Accessories, Breadboards, Batteries, Enclosures, PCBs, Test Points, Robotics, Bumpers",
    25: "Bargain Board (Clearance / Surplus Items)",
    26: "Store Policy, Protocol Analyzers, Embedded Test Equipment, Host Adapters, I2C Products, Store Map",
}

STORE_BASE = {
    "name": "Anchor Electronics",
    "address": "2040 Walsh Ave., Santa Clara, CA 95050",
    "phone": "(408) 727-3693",
    "website": "https://www.anchor-electronics.com",
    "hours": "Monday through Friday, 7:30 AM – 4:00 PM",
}


def parse_pdf(source):
    """Parse an Anchor Electronics price-list PDF into the price-list data dict.

    `source` may be a file path, a file-like object, or raw bytes.
    """
    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)
    reader = pypdf.PdfReader(source)
    pages = []
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        text = page.extract_text() or ""
        text = "\n".join(
            line for line in text.splitlines()
            if "www.anchor-electronics.com" not in line
        ).strip()
        pages.append({
            "page_number": page_num,
            "categories": PAGE_CATEGORIES.get(page_num, f"Page {page_num}"),
            "raw_text": text,
        })

    cover_text = pages[0]["raw_text"] if pages else ""
    edition_match = EDITION_RE.search(cover_text)
    edition = edition_match.group(0) if edition_match else "unknown edition"

    store = dict(STORE_BASE)
    store["edition"] = edition
    store["notes"] = f"{edition} price list. Online-only items include: tools, wire, chemicals."
    return {"store": store, "pages": pages}

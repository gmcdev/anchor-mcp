#!/usr/bin/env python3
"""Parse anchor_price_list.pdf → data/price_list.json"""

import json
import os
import pypdf

PDF_PATH = os.path.join(os.path.dirname(__file__), "anchor_price_list.pdf")
OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "price_list.json")

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

STORE = {
    "name": "Anchor Electronics",
    "address": "2040 Walsh Ave., Santa Clara, CA 95050",
    "phone": "(408) 727-3693",
    "website": "https://www.anchor-electronics.com",
    "hours": "Monday through Friday, 7:30 AM – 4:00 PM",
    "notes": "January 2026 price list. Online-only items include: tools, wire, chemicals.",
}


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    reader = pypdf.PdfReader(PDF_PATH)
    pages = []
    for i, page in enumerate(reader.pages):
        page_num = i + 1
        text = page.extract_text() or ""
        # Remove the footer line that repeats on every page
        text = "\n".join(
            line for line in text.splitlines()
            if "www.anchor-electronics.com" not in line
        ).strip()
        pages.append({
            "page_number": page_num,
            "categories": PAGE_CATEGORIES.get(page_num, f"Page {page_num}"),
            "raw_text": text,
        })

    data = {"store": STORE, "pages": pages}
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

    total_chars = sum(len(p["raw_text"]) for p in pages)
    print(f"Wrote {len(pages)} pages ({total_chars:,} chars) to {OUT_PATH}")


if __name__ == "__main__":
    main()

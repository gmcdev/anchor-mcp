# Anchor Electronics MCP

An MCP server exposing the [Anchor Electronics](https://www.anchor-electronics.com) component price list, so customers can use Claude to search for parts and build shopping lists.

Anchor Electronics is a walk-in electronics component store at 2040 Walsh Ave., Santa Clara, CA 95050. They stock a deep inventory of SMT and through-hole components: resistors, capacitors, diodes, transistors, ICs, connectors, inductors, LEDs, crystals, sockets, potentiometers, soldering supplies, and much more. Hours: Monday–Friday, 7:30 AM–4:00 PM.

The price list is current as of **January 2026**.

---

## Tools

| Tool | Description |
|------|-------------|
| `get_store_info` | Store name, address, phone, hours, and website |
| `list_categories` | All product categories across the 26-page price list |
| `search_products` | Search by part number, component type, or keyword |
| `get_category_content` | Full price list text for a given category |

---

## Install

### Claude.ai (Pro / Max)

1. Go to **claude.ai** → profile → **Settings** → **Integrations**
2. Click **Add Integration**
3. Enter the URL: `https://anchor-mcp-5atekw3vma-uw.a.run.app/mcp`
4. Name it **Anchor Electronics**

### Claude Code (CLI)

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "anchor-electronics": {
      "type": "http",
      "url": "https://anchor-mcp-5atekw3vma-uw.a.run.app/mcp"
    }
  }
}
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "anchor-electronics": {
      "type": "http",
      "url": "https://anchor-mcp-5atekw3vma-uw.a.run.app/mcp"
    }
  }
}
```

---

## Development

### Prerequisites

- Python 3.12+
- [`mcp[cli]`](https://pypi.org/project/mcp/) >= 1.27.0

### Setup

```bash
pip install -r requirements.txt
```

### Re-parse the price list

If Anchor Electronics publishes an updated PDF:

```bash
# Replace anchor_price_list.pdf with the new file, then:
python build_data.py
```

This regenerates `data/price_list.json`.

### Run locally

```bash
python server.py
# MCP endpoint: http://localhost:8080/mcp
```

### Deploy to Cloud Run

```bash
# First time: enable APIs and link billing
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com \
  --project=anchor-electronics-mcp

# Deploy
./deploy.sh
```

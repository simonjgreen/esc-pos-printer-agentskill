---
name: print
description: Print text, receipts, barcodes, QR codes, or a test page to an ESC/POS thermal printer over IP
argument-hint: <text or "demo"> [--host IP] [--port PORT]
allowed-tools: [Bash, Read, Write]
version: 1.0.0
---

# /print Command

Print to an ESC/POS thermal printer over IP.

## Arguments

The user invoked this with: $ARGUMENTS

## Parsing Arguments

1. If arguments contain `--host` or `--port`, extract those values. Otherwise use defaults: host=192.168.1.251, port=9100.
2. The remaining text (after removing --host/--port flags) is the print content.

## Behavior by Input

### `/print demo`
Print the full test/demo page:
```json
{
  "printer": {"host": "192.168.1.251", "port": 9100},
  "jobs": [{"type": "demo"}]
}
```

### `/print <simple text>`
Wrap in a text job with cut:
```json
{
  "printer": {"host": "192.168.1.251", "port": 9100},
  "jobs": [
    {"type": "text", "content": "<the text>", "size": "normal"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

### `/print receipt <description>`
Interpret the description and build a receipt with appropriate header, items, separator, total, and cut. Use your judgment to structure the receipt from the description.

### `/print qr <data>`
```json
{
  "printer": {"host": "192.168.1.251", "port": 9100},
  "jobs": [
    {"type": "qr", "data": "<the data>", "size": 6},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

### `/print barcode <data>`
```json
{
  "printer": {"host": "192.168.1.251", "port": 9100},
  "jobs": [
    {"type": "barcode", "data": "<the data>", "format": "CODE128"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

## Execution

Determine the plugin directory from context. Ensure the venv exists:

```bash
if [ ! -d "PLUGIN_DIR/scripts/.venv" ]; then
    bash PLUGIN_DIR/scripts/setup.sh
fi
```

Then pipe the JSON to the script:

```bash
echo '<json>' | PLUGIN_DIR/scripts/.venv/bin/python PLUGIN_DIR/scripts/escpos_print.py
```

Report success or the error message from the JSON response.

---
name: print
description: Print text, receipts, barcodes, QR codes, or a test page to an ESC/POS thermal printer over IP, USB, or serial
argument-hint: <text or "demo"> [--host IP] [--port PORT] [--usb VENDOR:PRODUCT] [--serial /dev/ttyUSB0]
allowed-tools: [Bash, Read, Write]
version: 1.0.0
metadata: {"openclaw": {"requires": {"bins": ["python3"]}}}
---

# /print Command

Print to an ESC/POS thermal printer over IP, USB, or serial.

## Arguments

The user invoked this with: $ARGUMENTS

## Parsing Arguments

1. Extract printer connection flags if present:
   - `--host IP` and `--port PORT` → network printer
   - `--usb VENDOR_ID:PRODUCT_ID` → USB printer (decimal IDs separated by colon)
   - `--serial /dev/ttyUSB0` and optional `--baud RATE` → serial printer
   - No flags → default network printer at 192.168.1.251:9100
2. The remaining text (after removing flags) is the print content.

## Printer Config by Flags

**Network (default):**
```json
{"printer": {"type": "network", "host": "192.168.1.251", "port": 9100}}
```

**USB:**
```json
{"printer": {"type": "usb", "vendor_id": 1046, "product_id": 20497}}
```

**Serial:**
```json
{"printer": {"type": "serial", "port": "/dev/ttyUSB0", "baudrate": 9600}}
```

## Behavior by Input

### `/print demo`
Print the full test/demo page:
```json
{"jobs": [{"type": "demo"}]}
```

### `/print <simple text>`
Wrap in a text job with cut:
```json
{"jobs": [
  {"type": "text", "content": "<the text>", "size": "normal"},
  {"type": "feed", "lines": 3},
  {"type": "cut"}
]}
```

### `/print receipt <description>`
Interpret the description and build a receipt with appropriate header, items, separator, total, and cut. Use your judgment to structure the receipt from the description.

### `/print qr <data>`
```json
{"jobs": [
  {"type": "qr", "data": "<the data>", "size": 6},
  {"type": "feed", "lines": 3},
  {"type": "cut"}
]}
```

### `/print barcode <data>`
```json
{"jobs": [
  {"type": "barcode", "data": "<the data>", "format": "CODE128"},
  {"type": "feed", "lines": 3},
  {"type": "cut"}
]}
```

## Execution

Resolve the plugin directory:
- **Claude Code:** `${CLAUDE_PLUGIN_ROOT}`
- **OpenClaw:** `{baseDir}/..`
- **Other:** The repo/plugin directory path

Ensure the venv exists, then pipe JSON to the script:

```bash
PLUGIN_DIR="<resolved plugin root>"
if [ ! -d "$PLUGIN_DIR/scripts/.venv" ]; then
    bash "$PLUGIN_DIR/scripts/setup.sh"
fi
echo '<json>' | "$PLUGIN_DIR/scripts/.venv/bin/python" "$PLUGIN_DIR/scripts/escpos_print.py"
```

Report success or the error message from the JSON response.

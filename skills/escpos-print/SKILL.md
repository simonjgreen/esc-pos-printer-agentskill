---
name: escpos-print
description: Use when the user asks to print something, generate a receipt, produce physical output, print a label, test a printer, or send output to a thermal printer. Handles ESC/POS printing over IP, USB, or serial with support for text, barcodes, QR codes, images, and receipt layouts.
version: 1.0.0
allowed-tools: [Bash, Read, Write]
metadata: {"openclaw": {"requires": {"bins": ["python3"]}}}
---

# ESC/POS Printer

Print to ESC/POS thermal printers over IP, USB, or serial. Supports text formatting, barcodes, QR codes, images (with smart dithering), and receipt-style layouts.

## Setup

Before first use, ensure the Python venv exists. The plugin root is the directory containing `scripts/` and `skills/`.

- **Claude Code:** `${CLAUDE_PLUGIN_ROOT}` resolves the plugin root
- **OpenClaw:** `{baseDir}/..` from a skill folder resolves to plugin root
- **Other tools:** Resolve from the repo/plugin directory path

```bash
PLUGIN_DIR="<resolved plugin root>"
if [ ! -d "$PLUGIN_DIR/scripts/.venv" ]; then
    bash "$PLUGIN_DIR/scripts/setup.sh"
fi
```

## How to Print

Construct a JSON object and pipe it to the Python script:

```bash
echo '<json>' | "$PLUGIN_DIR/scripts/.venv/bin/python" "$PLUGIN_DIR/scripts/escpos_print.py"
```

## Printer Configuration

The `"printer"` object selects the connection type.

### Network (IP)
```json
{"printer": {"type": "network", "host": "192.168.1.251", "port": 9100}}
```
- `type`: "network" (default if omitted)
- `host`: IP address (required)
- `port`: TCP port (default: 9100)

### USB
```json
{"printer": {"type": "usb", "vendor_id": 1046, "product_id": 20497}}
```
- `vendor_id`: USB vendor ID (required, decimal integer)
- `product_id`: USB product ID (required, decimal integer)
- `in_ep`: Input endpoint (default: 0x82)
- `out_ep`: Output endpoint (default: 0x01)

To find vendor/product IDs: `lsusb` on Linux, `system_profiler SPUSBDataType` on macOS.

### Serial
```json
{"printer": {"type": "serial", "port": "/dev/ttyUSB0", "baudrate": 9600}}
```
- `port`: Device path (required) — e.g., `/dev/ttyUSB0`, `/dev/ttyACM0`, `COM3`
- `baudrate`: Baud rate (default: 9600)

## JSON Format

```json
{
  "printer": { "type": "network", "host": "192.168.1.251", "port": 9100 },
  "columns": 48,
  "jobs": [ ... ]
}
```

- `columns`: Character width. 48 for 80mm printers (default), 32 for 58mm printers.

## Job Types

### Text
```json
{"type": "text", "content": "Hello", "bold": false, "underline": false, "align": "left", "size": "normal", "font": "a"}
```
- `align`: "left", "center", "right"
- `size`: "normal", "large" (2x), "xlarge" (4x)
- `font`: "a" (standard), "b" (condensed)

### Separator
```json
{"type": "separator", "char": "-"}
```
Fills the full column width with the character.

### Columns (two-column row)
```json
{"type": "columns", "left": "Item Name", "right": "$5.00", "bold": false}
```
Left-aligned left text, right-aligned right text, padded to column width.

### Barcode
```json
{"type": "barcode", "data": "123456789012", "format": "CODE128", "align": "center"}
```
Formats: EAN13, UPC-A, CODE39, CODE128, ITF, CODABAR.

### QR Code
```json
{"type": "qr", "data": "https://example.com", "size": 6, "error_correction": "M"}
```
- `size`: 1-16 (module size)
- `error_correction`: L, M, Q, H

### Image
```json
{"type": "image", "path": "/tmp/image.png", "width": 384, "dither": "stucki"}
```
Supports PNG, JPG, BMP. Width in pixels (height scales proportionally). Max printable width is typically 384px for 80mm printers.

- `dither`: Dithering method for converting to 1-bit. Choose based on content:
  - `"stucki"` (default) — sharp, high detail. Best for photos and complex images.
  - `"ordered"` — halftone pattern. Good for graphics, illustrations, gradients.
  - `"enhanced"` — contrast/sharpness boost + Floyd-Steinberg. Good for low-contrast or washed-out images.
  - `"atkinson"` — lighter, higher contrast. Good for logos, icons, line art with some shading.
  - `"floyd-steinberg"` — classic error diffusion. General purpose, slightly softer than Stucki.
  - `"threshold"` — hard black/white cutoff, no dithering. Best for already-monochrome images, text, simple logos.

### Feed
```json
{"type": "feed", "lines": 3}
```

### Cut
```json
{"type": "cut", "partial": false}
```

### Demo (test page)
```json
{"type": "demo"}
```
Prints a full capability test showing all job types.

## Output

The script returns JSON on stdout:
- Success: `{"success": true}`
- Error: `{"success": false, "error": "description"}`

## Examples

**Network printer — simple text:**
```json
{
  "printer": {"host": "192.168.1.251", "port": 9100},
  "jobs": [
    {"type": "text", "content": "Hello World!", "align": "center", "size": "large"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

**USB printer — receipt:**
```json
{
  "printer": {"type": "usb", "vendor_id": 1046, "product_id": 20497},
  "columns": 48,
  "jobs": [
    {"type": "text", "content": "ACME STORE", "align": "center", "size": "large", "bold": true},
    {"type": "text", "content": "123 Main St", "align": "center"},
    {"type": "separator"},
    {"type": "columns", "left": "Coffee", "right": "$4.50"},
    {"type": "columns", "left": "Muffin", "right": "$3.25"},
    {"type": "separator", "char": "="},
    {"type": "columns", "left": "TOTAL", "right": "$7.75", "bold": true},
    {"type": "feed", "lines": 1},
    {"type": "qr", "data": "https://receipt.example.com/abc123", "size": 6},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

**Serial printer — label:**
```json
{
  "printer": {"type": "serial", "port": "/dev/ttyUSB0", "baudrate": 115200},
  "columns": 32,
  "jobs": [
    {"type": "text", "content": "SHELF LABEL", "align": "center", "bold": true},
    {"type": "barcode", "data": "SKU12345", "format": "CODE128"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

## Error Handling

If the script fails, report the error message to the user. Common issues:
- Connection refused: printer off or wrong IP/port
- Timeout: printer unreachable on network
- USB device not found: wrong vendor/product ID or no permissions (`sudo` or udev rule needed)
- Serial port error: wrong device path or port in use
- File not found: image path doesn't exist

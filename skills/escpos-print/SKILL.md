---
name: escpos-print
description: Use when the user asks to print something, generate a receipt, produce physical output, print a label, test a printer, or send output to a thermal printer. Handles ESC/POS printing over IP with support for text, barcodes, QR codes, images, and receipt layouts.
version: 1.0.0
allowed-tools: [Bash, Read, Write]
---

# ESC/POS IP Printer

Print to ESC/POS thermal printers over IP. Supports text formatting, barcodes, QR codes, images, and receipt-style layouts.

## Setup

Before first use, ensure the venv exists. Determine PLUGIN_DIR as the root of this plugin (parent of `skills/`).

```bash
if [ ! -d "PLUGIN_DIR/scripts/.venv" ]; then
    bash PLUGIN_DIR/scripts/setup.sh
fi
```

## How to Print

Construct a JSON object and pipe it to the Python script:

```bash
echo '<json>' | PLUGIN_DIR/scripts/.venv/bin/python PLUGIN_DIR/scripts/escpos_print.py
```

### Default Printer

- **Host:** 192.168.1.251
- **Port:** 9100

### JSON Format

```json
{
  "printer": { "host": "192.168.1.251", "port": 9100 },
  "columns": 48,
  "jobs": [ ... ]
}
```

- `columns`: Character width. 48 for 80mm printers (default), 32 for 58mm printers.

### Job Types

#### Text
```json
{"type": "text", "content": "Hello", "bold": false, "underline": false, "align": "left", "size": "normal", "font": "a"}
```
- `align`: "left", "center", "right"
- `size`: "normal", "large" (2x), "xlarge" (4x)
- `font`: "a" (standard), "b" (condensed)

#### Separator
```json
{"type": "separator", "char": "-"}
```
Fills the full column width with the character.

#### Columns (two-column row)
```json
{"type": "columns", "left": "Item Name", "right": "$5.00", "bold": false}
```
Left-aligned left text, right-aligned right text, padded to column width.

#### Barcode
```json
{"type": "barcode", "data": "123456789012", "format": "CODE128", "align": "center"}
```
Formats: EAN13, UPC-A, CODE39, CODE128, ITF, CODABAR.

#### QR Code
```json
{"type": "qr", "data": "https://example.com", "size": 6, "error_correction": "M"}
```
- `size`: 1-16 (module size)
- `error_correction`: L, M, Q, H

#### Image
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

#### Feed
```json
{"type": "feed", "lines": 3}
```

#### Cut
```json
{"type": "cut", "partial": false}
```

#### Demo (test page)
```json
{"type": "demo"}
```
Prints a full capability test showing all job types.

## Output

The script returns JSON on stdout:
- Success: `{"success": true}`
- Error: `{"success": false, "error": "description"}`

## Examples

**Simple text:**
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

**Receipt:**
```json
{
  "printer": {"host": "192.168.1.251", "port": 9100},
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

## Error Handling

If the script fails, report the error message to the user. Common issues:
- Connection refused: printer off or wrong IP
- Timeout: printer unreachable on network
- File not found: image path doesn't exist

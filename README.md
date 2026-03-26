# ESC/POS Printer Skill

An AI agent skill for printing to ESC/POS thermal printers over **IP**, **USB**, or **serial**. Works with Claude Code, OpenClaw, Cursor, and any AI coding tool that can run shell commands.

Supports text formatting, barcodes, QR codes, images (with 6 dithering methods), and receipt-style column layouts.

## Quick Start

```bash
# 1. Install dependencies
bash scripts/setup.sh

# 2. Print something
echo '{"printer": {"host": "192.168.1.251"}, "jobs": [{"type": "text", "content": "Hello!"}, {"type": "cut"}]}' \
  | scripts/.venv/bin/python scripts/escpos_print.py
```

## Platform Setup

### Claude Code
Install as a plugin — the `.claude-plugin/` directory is auto-detected. Skills appear as `/print` command and auto-invoked `escpos-print`.

### OpenClaw
Install as a plugin — `openclaw.plugin.json` is auto-detected. Requires `python3` on PATH.

### Cursor / Other Tools
Point your agent at this directory and tell it to read `skills/escpos-print/SKILL.md` for full instructions. The core interface is just JSON piped to a Python script.

## Printer Configuration

### Network (IP)
```json
{"printer": {"type": "network", "host": "192.168.1.251", "port": 9100}}
```

### USB
```json
{"printer": {"type": "usb", "vendor_id": 1046, "product_id": 20497}}
```
Find IDs with `lsusb` (Linux) or `system_profiler SPUSBDataType` (macOS).

### Serial
```json
{"printer": {"type": "serial", "port": "/dev/ttyUSB0", "baudrate": 9600}}
```

The `type` field defaults to `"network"` if omitted.

## JSON Interface

Pipe a JSON object to `scripts/escpos_print.py` via stdin:

```json
{
  "printer": { "type": "network", "host": "192.168.1.251", "port": 9100 },
  "columns": 48,
  "jobs": [
    {"type": "text", "content": "Hello", "bold": true, "align": "center"},
    {"type": "cut"}
  ]
}
```

- `columns`: Character width — 48 for 80mm printers (default), 32 for 58mm.
- `jobs`: Array of job objects (see below).

Returns `{"success": true}` or `{"success": false, "error": "message"}` on stdout.

## Job Types

| Type | Key Options |
|------|-------------|
| `text` | `content`, `bold`, `underline`, `align` (left/center/right), `size` (normal/large/xlarge), `font` (a/b) |
| `separator` | `char` (default: "-") — fills column width |
| `columns` | `left`, `right`, `bold` — two-column receipt row |
| `barcode` | `data`, `format` (CODE128/EAN13/UPC-A/CODE39/ITF/CODABAR), `align` |
| `qr` | `data`, `size` (1-16), `error_correction` (L/M/Q/H) |
| `image` | `path`, `width` (pixels), `dither` (see below) |
| `feed` | `lines` (default: 1) |
| `cut` | `partial` (bool) |
| `demo` | No options — prints a full capability test page |

## Image Dithering

The `dither` option on image jobs controls how colour/greyscale images are converted to 1-bit for the thermal printer:

| Method | Best For |
|--------|----------|
| `stucki` (default) | Photos and complex images — sharp, high detail |
| `ordered` | Graphics, illustrations, gradients — halftone pattern |
| `enhanced` | Low-contrast or washed-out images — boosted contrast + Floyd-Steinberg |
| `atkinson` | Logos, icons, line art with shading — lighter, higher contrast |
| `floyd-steinberg` | General purpose — classic error diffusion, slightly softer |
| `threshold` | Already-monochrome images, text, simple logos — hard black/white cutoff |

## Examples

**Receipt:**
```json
{
  "printer": {"host": "192.168.1.251"},
  "columns": 48,
  "jobs": [
    {"type": "text", "content": "ACME STORE", "align": "center", "size": "large", "bold": true},
    {"type": "separator"},
    {"type": "columns", "left": "Coffee", "right": "$4.50"},
    {"type": "columns", "left": "Muffin", "right": "$3.25"},
    {"type": "separator", "char": "="},
    {"type": "columns", "left": "TOTAL", "right": "$7.75", "bold": true},
    {"type": "qr", "data": "https://receipt.example.com/abc123"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

**Photo print:**
```json
{
  "printer": {"host": "192.168.1.251"},
  "jobs": [
    {"type": "image", "path": "/tmp/photo.jpg", "width": 384, "dither": "stucki"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

**Demo/test page:**
```json
{
  "printer": {"host": "192.168.1.251"},
  "jobs": [{"type": "demo"}]
}
```

## Dependencies

- Python 3.10+
- `python-escpos` (printer communication)
- `Pillow` (image processing)

All installed automatically by `scripts/setup.sh` into a local venv at `scripts/.venv/`.

## License

MIT

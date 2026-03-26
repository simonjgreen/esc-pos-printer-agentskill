# ESC/POS IP Printer Skill — Design Spec

## Overview

A Claude Code plugin that enables agents to print to ESC/POS thermal printers over IP. Provides both a model-invoked skill (Claude uses autonomously when printing is relevant) and a user-invoked `/print` slash command. Uses `python-escpos` via a Python helper script for full feature support including text formatting, barcodes, QR codes, images, and receipt-style layouts.

## Plugin Structure

```
ESC-POS-IP-Printer-Skill/
  .claude-plugin/
    plugin.json
  skills/
    escpos-print/
      SKILL.md              # Model-invoked skill (autonomous)
    print/
      SKILL.md              # User-invoked /print command
  scripts/
    escpos_print.py         # Python script — all ESC/POS communication
    requirements.txt        # python-escpos + Pillow
    setup.sh                # Creates venv, installs deps
```

## Python Script Interface

### Invocation

```bash
echo '<json>' | /path/to/venv/bin/python /path/to/escpos_print.py
```

### Input Format (JSON on stdin)

```json
{
  "printer": { "host": "192.168.1.251", "port": 9100 },
  "columns": 48,
  "jobs": [
    { "type": "text", "content": "Hello", "bold": true, "align": "center", "size": "large" },
    { "type": "separator" },
    { "type": "columns", "left": "Item", "right": "$5.00" },
    { "type": "barcode", "data": "123456789012", "format": "EAN13" },
    { "type": "qr", "data": "https://example.com", "size": 6 },
    { "type": "image", "path": "/tmp/logo.png", "width": 200 },
    { "type": "feed", "lines": 3 },
    { "type": "cut" }
  ]
}
```

### Top-Level Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `printer.host` | yes | — | Printer IP address |
| `printer.port` | no | 9100 | Printer TCP port |
| `columns` | no | 48 | Column width (chars). 48 for 80mm, 32 for 58mm |
| `jobs` | yes | — | Array of print job items |

### Job Types

#### `text`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `content` | string | required | Text to print |
| `bold` | bool | false | Bold text |
| `underline` | bool | false | Underlined text |
| `align` | string | "left" | "left", "center", or "right" |
| `size` | string | "normal" | "normal", "large" (2x), "xlarge" (4x) |
| `font` | string | "a" | "a" (standard) or "b" (condensed) |

#### `separator`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `char` | string | "-" | Character to repeat across column width |

#### `columns`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `left` | string | required | Left-aligned text |
| `right` | string | required | Right-aligned text |
| `bold` | bool | false | Bold text |

Pads space between left and right to fill column width.

#### `barcode`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `data` | string | required | Barcode data |
| `format` | string | "CODE128" | EAN13, UPC-A, CODE39, CODE128, ITF, CODABAR |
| `align` | string | "center" | Alignment |

#### `qr`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `data` | string | required | QR code data |
| `size` | int | 6 | Module size (1-16) |
| `error_correction` | string | "M" | L, M, Q, or H |

#### `image`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `path` | string | required | Path to image file (PNG, JPG, BMP) |
| `width` | int | auto | Target width in pixels (height scales proportionally) |

#### `feed`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `lines` | int | 1 | Number of blank lines |

#### `cut`
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `partial` | bool | false | Partial cut (true) or full cut (false) |

#### `demo`
No options. Prints a full capability test page:
1. Large centered header: "ESC/POS PRINTER TEST"
2. Normal text line
3. Bold text line
4. Underline text line
5. Font B text line
6. Separator
7. Multi-column receipt rows (3-4 items with prices)
8. Separator with "=" character
9. Column total row in bold
10. Barcode (CODE128, "TESTPRINT123")
11. QR code linking to a test URL
12. Small programmatically-generated test image (checkerboard pattern)
13. Feed 4 lines + full cut

### Output Format (JSON on stdout)

Success:
```json
{"success": true}
```

Error:
```json
{"success": false, "error": "Connection refused: 192.168.1.251:9100"}
```

### Error Handling

- TCP connection timeout: 5 seconds
- Script catches all exceptions and returns JSON error
- Non-zero exit code on failure

## Skills

### Model-Invoked Skill (`escpos-print`)

**Trigger conditions:** User asks to print something, generate a receipt, produce physical output, print a label, or test a printer.

**Behavior:** Claude constructs the appropriate JSON job array based on context, pipes it to the Python script via Bash, and reports success/failure.

### User-Invoked Command (`/print`)

**Usage examples:**
- `/print Hello World` — prints plain text
- `/print demo` — prints full test page
- `/print receipt ...` — Claude interprets and formats as receipt

**Behavior:** Parses arguments, constructs job JSON, executes. For simple text, wraps in a text job + cut. For "demo", sends a demo job. For complex requests, Claude builds the full job array.

## Setup

`setup.sh` creates a Python venv in `scripts/.venv/` and installs dependencies. The skills call `setup.sh` if the venv doesn't exist before first use.

## Default Printer

Both skills default to `192.168.1.251:9100`. Override via:
- JSON: `"printer": {"host": "x.x.x.x", "port": 9100}`
- `/print` arguments: `/print --host 10.0.0.1 --port 9100 Hello`

## Testing

Print the demo page to `192.168.1.251:9100` to validate all capabilities work end-to-end.

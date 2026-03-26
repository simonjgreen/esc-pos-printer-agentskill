# ESC/POS Printer — AI Agent Skill

Give any AI agent the ability to print to ESC/POS thermal receipt printers over **IP**, **USB**, or **serial**.

Built as a cross-platform agent skill with first-class support for **Claude Code**, **OpenClaw**, and any other AI tool that can run shell commands (Cursor, Windsurf, Cline, etc.). One repo, multiple front doors.

## Platform Support

| Platform | Install Method | Discovery |
|----------|---------------|-----------|
| **Claude Code** | `/plugin simonjgreen/esc-pos-printer-agentskill` | Auto-detected via `.claude-plugin/marketplace.json` |
| **OpenClaw** | `clawhub install escpos-print` | Published to ClawHub via `scripts/publish-clawhub.sh` |
| **Cursor / Windsurf / Cline** | Clone repo, point agent at `skills/escpos-print/SKILL.md` | Agent reads the skill markdown directly |
| **Any tool with shell access** | Clone repo, run `bash scripts/setup.sh` | JSON-in, JSON-out via stdin/stdout |

### Claude Code

```
/plugin simonjgreen/esc-pos-printer-agentskill
```

Installs both skills:
- **`escpos-print`** — model-invoked, Claude uses automatically when printing is relevant
- **`/print`** — user-invoked slash command (e.g., `/print demo`, `/print receipt ...`)

### OpenClaw

```bash
clawhub install escpos-print
```

Or install locally:
```bash
openclaw plugins install ./path/to/esc-pos-printer-agentskill
```

The `openclaw.plugin.json` manifest and `metadata.openclaw.requires` frontmatter handle dependency checking (`python3` must be on PATH).

### Generic (any agent)

```bash
git clone https://github.com/simonjgreen/esc-pos-printer-agentskill.git
cd esc-pos-printer-agentskill
bash scripts/setup.sh
```

Then tell your agent: *"Read `skills/escpos-print/SKILL.md` for printing instructions."*

The core interface is deliberately simple — JSON on stdin, JSON on stdout, called via a single Python script. Any agent that can run a shell command can use it.

## Quick Start

```bash
# Setup (one-time)
bash scripts/setup.sh

# Print "Hello World"
echo '{"printer": {"host": "192.168.1.251"}, "jobs": [{"type": "text", "content": "Hello!"}, {"type": "cut"}]}' \
  | scripts/.venv/bin/python scripts/escpos_print.py

# Print a full demo/test page
echo '{"printer": {"host": "192.168.1.251"}, "jobs": [{"type": "demo"}]}' \
  | scripts/.venv/bin/python scripts/escpos_print.py
```

## Printer Connections

### Network (IP)
```json
{"printer": {"type": "network", "host": "192.168.1.251", "port": 9100}}
```

### USB
```json
{"printer": {"type": "usb", "vendor_id": 1046, "product_id": 20497}}
```
Find IDs: `lsusb` (Linux), `system_profiler SPUSBDataType` (macOS).

### Serial
```json
{"printer": {"type": "serial", "port": "/dev/ttyUSB0", "baudrate": 9600}}
```

The `type` field defaults to `"network"` if omitted.

## JSON Interface

Pipe a JSON object to `scripts/escpos_print.py` via stdin:

```json
{
  "printer": {"host": "192.168.1.251"},
  "columns": 48,
  "jobs": [
    {"type": "text", "content": "Hello", "bold": true, "align": "center"},
    {"type": "cut"}
  ]
}
```

- `columns`: Character width — 48 for 80mm printers (default), 32 for 58mm.
- Returns `{"success": true}` or `{"success": false, "error": "message"}` on stdout.

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
| `demo` | No options — prints full capability test page |

## Image Dithering

Six dithering methods for converting images to 1-bit thermal output. The agent can choose based on content type:

| Method | Best For |
|--------|----------|
| `stucki` (default) | Photos and complex images — sharp, high detail |
| `ordered` | Graphics, illustrations, gradients — halftone pattern |
| `enhanced` | Low-contrast or washed-out images — boosted contrast + Floyd-Steinberg |
| `atkinson` | Logos, icons, line art with shading — lighter, higher contrast |
| `floyd-steinberg` | General purpose — classic error diffusion, slightly softer |
| `threshold` | Already-monochrome images, text, simple logos — hard black/white cutoff |

All dithering is pure Python (no numpy) to keep the dependency footprint minimal.

## Examples

**Receipt:**
```json
{
  "printer": {"host": "192.168.1.251"},
  "columns": 48,
  "jobs": [
    {"type": "text", "content": "ACME STORE", "align": "center", "size": "large", "bold": true},
    {"type": "text", "content": "123 Main St", "align": "center"},
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

**Photo over USB:**
```json
{
  "printer": {"type": "usb", "vendor_id": 1046, "product_id": 20497},
  "jobs": [
    {"type": "image", "path": "/tmp/photo.jpg", "width": 384, "dither": "stucki"},
    {"type": "feed", "lines": 3},
    {"type": "cut"}
  ]
}
```

**Label over serial:**
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

## Architecture

```
esc-pos-printer-agentskill/
  .claude-plugin/
    plugin.json              # Claude Code plugin metadata
    marketplace.json         # Claude Code marketplace discovery
  openclaw.plugin.json       # OpenClaw plugin manifest
  skills/
    escpos-print/SKILL.md    # Model-invoked skill (auto-triggered)
    print/SKILL.md           # User-invoked /print command
  scripts/
    escpos_print.py          # Core — JSON stdin, ESC/POS out
    setup.sh                 # One-command venv + dependency install
    publish-clawhub.sh       # Publish skills to OpenClaw's ClawHub
    requirements.txt         # python-escpos + Pillow
  tests/
    test_escpos_print.py     # 22 unit tests
```

The skills are thin instruction layers that tell the agent how to construct JSON and call the Python script. The script handles all printer communication, formatting, and image processing. This separation means the same core works identically regardless of which agent platform invokes it.

## Publishing

**ClawHub (OpenClaw):**
```bash
clawhub login
bash scripts/publish-clawhub.sh 1.0.0
```

**Claude Code:** Already discoverable via the GitHub repo as a marketplace.

## Dependencies

- Python 3.10+
- `python-escpos` (printer communication)
- `Pillow` (image processing)

All installed automatically by `scripts/setup.sh` into a local venv at `scripts/.venv/`. No global installs, no numpy, no heavy deps.

## License

MIT

# ESC/POS IP Printer Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin that lets agents print to ESC/POS thermal printers over IP, with full support for text, barcodes, QR codes, images, and receipt layouts.

**Architecture:** A Python helper script (`escpos_print.py`) receives JSON on stdin describing print jobs and sends ESC/POS commands to the printer via TCP. Two SKILL.md files expose this — one model-invoked (autonomous) and one user-invoked (`/print` command). A `setup.sh` script bootstraps a venv with dependencies.

**Tech Stack:** Python 3.12, python-escpos, Pillow, Claude Code plugin system (SKILL.md format)

---

## File Structure

```
ESC-POS-IP-Printer-Skill/
  .claude-plugin/
    plugin.json                 # Plugin metadata
  skills/
    escpos-print/
      SKILL.md                  # Model-invoked skill
    print/
      SKILL.md                  # User-invoked /print command
  scripts/
    escpos_print.py             # Main Python script
    requirements.txt            # python-escpos, Pillow
    setup.sh                    # Venv bootstrap
  tests/
    test_escpos_print.py        # Unit tests for the Python script
```

---

### Task 1: Plugin Scaffold and Setup Script

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `scripts/requirements.txt`
- Create: `scripts/setup.sh`

- [ ] **Step 1: Create plugin.json**

```json
{
  "name": "escpos-ip-printer",
  "description": "Print to ESC/POS thermal printers over IP — text, barcodes, QR codes, images, and receipt layouts",
  "author": {
    "name": "Simon",
    "email": ""
  },
  "version": "1.0.0"
}
```

Write to `.claude-plugin/plugin.json`.

- [ ] **Step 2: Create requirements.txt**

```
python-escpos>=3.0
Pillow>=10.0
```

Write to `scripts/requirements.txt`.

- [ ] **Step 3: Create setup.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
echo "Setup complete."
```

Write to `scripts/setup.sh`, then `chmod +x scripts/setup.sh`.

- [ ] **Step 4: Run setup.sh to create venv**

Run: `cd /home/simon/Documents/ESC-POS-IP-Printer-Skill && bash scripts/setup.sh`
Expected: "Setup complete." with venv created at `scripts/.venv/`.

- [ ] **Step 5: Verify python-escpos installed**

Run: `scripts/.venv/bin/python -c "from escpos.printer import Network; print('OK')"`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git init
git add .claude-plugin/plugin.json scripts/requirements.txt scripts/setup.sh
git commit -m "feat: plugin scaffold and setup script"
```

---

### Task 2: Core Python Script — Text Printing

**Files:**
- Create: `scripts/escpos_print.py`
- Create: `tests/test_escpos_print.py`

- [ ] **Step 1: Write failing test for text job processing**

```python
# tests/test_escpos_print.py
import json
import sys
import os
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from escpos_print import process_jobs


class MockPrinter:
    """Mock that records ESC/POS method calls."""
    def __init__(self):
        self.calls = []

    def set(self, **kwargs):
        self.calls.append(('set', kwargs))

    def text(self, txt):
        self.calls.append(('text', txt))

    def cut(self):
        self.calls.append(('cut',))

    def close(self):
        self.calls.append(('close',))


def test_text_job_basic():
    printer = MockPrinter()
    jobs = [{"type": "text", "content": "Hello World"}]
    process_jobs(printer, jobs, columns=48)

    # Should reset formatting, then print text with newline
    set_calls = [c for c in printer.calls if c[0] == 'set']
    text_calls = [c for c in printer.calls if c[0] == 'text']
    assert len(text_calls) == 1
    assert text_calls[0][1] == "Hello World\n"


def test_text_job_bold_center():
    printer = MockPrinter()
    jobs = [{"type": "text", "content": "Title", "bold": True, "align": "center"}]
    process_jobs(printer, jobs, columns=48)

    set_calls = [c for c in printer.calls if c[0] == 'set']
    assert any(c[1].get('bold') == True for c in set_calls)
    assert any(c[1].get('align') == 'center' for c in set_calls)


def test_text_job_large_size():
    printer = MockPrinter()
    jobs = [{"type": "text", "content": "Big", "size": "large"}]
    process_jobs(printer, jobs, columns=48)

    set_calls = [c for c in printer.calls if c[0] == 'set']
    # large = double width + double height
    assert any(c[1].get('double_width') == True and c[1].get('double_height') == True for c in set_calls)
```

Write to `tests/test_escpos_print.py`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'escpos_print'`

- [ ] **Step 3: Write escpos_print.py with text support**

```python
#!/usr/bin/env python3
"""ESC/POS printer helper — receives JSON on stdin, sends to printer over IP."""

import json
import sys
from escpos.printer import Network


SIZE_MAP = {
    "normal": {"double_width": False, "double_height": False},
    "large": {"double_width": True, "double_height": True},
    "xlarge": {"double_width": True, "double_height": True},  # handled with text_type
}


def process_jobs(printer, jobs, columns=48):
    """Process a list of print jobs on the given printer."""
    for job in jobs:
        job_type = job.get("type")
        if job_type == "text":
            _handle_text(printer, job, columns)
        elif job_type == "cut":
            printer.cut()


def _handle_text(printer, job, columns):
    """Handle a text print job."""
    content = job.get("content", "")
    bold = job.get("bold", False)
    underline = job.get("underline", False)
    align = job.get("align", "left")
    size = job.get("size", "normal")
    font = job.get("font", "a")

    size_opts = SIZE_MAP.get(size, SIZE_MAP["normal"])

    printer.set(
        align=align,
        bold=bold,
        underline=1 if underline else 0,
        font=font,
        double_width=size_opts["double_width"],
        double_height=size_opts["double_height"],
    )
    printer.text(content + "\n")

    # Reset formatting after each job
    printer.set(
        align="left",
        bold=False,
        underline=0,
        font="a",
        double_width=False,
        double_height=False,
    )


def main():
    """Main entry point — read JSON from stdin, print to network printer."""
    try:
        data = json.load(sys.stdin)
        host = data["printer"]["host"]
        port = data["printer"].get("port", 9100)
        columns = data.get("columns", 48)
        jobs = data.get("jobs", [])

        printer = Network(host, port, timeout=5)
        process_jobs(printer, jobs, columns)
        printer.close()

        print(json.dumps({"success": True}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

Write to `scripts/escpos_print.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/escpos_print.py tests/test_escpos_print.py
git commit -m "feat: core print script with text job support"
```

---

### Task 3: Separator and Columns Jobs

**Files:**
- Modify: `scripts/escpos_print.py`
- Modify: `tests/test_escpos_print.py`

- [ ] **Step 1: Write failing tests for separator and columns**

Append to `tests/test_escpos_print.py`:

```python
def test_separator_default():
    printer = MockPrinter()
    jobs = [{"type": "separator"}]
    process_jobs(printer, jobs, columns=48)

    text_calls = [c for c in printer.calls if c[0] == 'text']
    assert len(text_calls) == 1
    assert text_calls[0][1] == "-" * 48 + "\n"


def test_separator_custom_char():
    printer = MockPrinter()
    jobs = [{"type": "separator", "char": "="}]
    process_jobs(printer, jobs, columns=48)

    text_calls = [c for c in printer.calls if c[0] == 'text']
    assert text_calls[0][1] == "=" * 48 + "\n"


def test_columns_job():
    printer = MockPrinter()
    jobs = [{"type": "columns", "left": "Item", "right": "$5.00"}]
    process_jobs(printer, jobs, columns=48)

    text_calls = [c for c in printer.calls if c[0] == 'text']
    assert len(text_calls) == 1
    line = text_calls[0][1]
    assert line.startswith("Item")
    assert line.rstrip("\n").endswith("$5.00")
    assert len(line.rstrip("\n")) == 48


def test_columns_job_32_cols():
    printer = MockPrinter()
    jobs = [{"type": "columns", "left": "Tax", "right": "$1.00"}]
    process_jobs(printer, jobs, columns=32)

    text_calls = [c for c in printer.calls if c[0] == 'text']
    line = text_calls[0][1]
    assert len(line.rstrip("\n")) == 32
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: 4 new tests FAIL (unknown type, no handler)

- [ ] **Step 3: Add separator and columns handlers to escpos_print.py**

Add to `process_jobs` dispatch:

```python
        elif job_type == "separator":
            _handle_separator(printer, job, columns)
        elif job_type == "columns":
            _handle_columns(printer, job, columns)
```

Add handler functions:

```python
def _handle_separator(printer, job, columns):
    """Print a horizontal separator line."""
    char = job.get("char", "-")
    printer.text(char * columns + "\n")


def _handle_columns(printer, job, columns):
    """Print a two-column row (left-aligned + right-aligned)."""
    left = job.get("left", "")
    right = job.get("right", "")
    bold = job.get("bold", False)

    if bold:
        printer.set(bold=True)

    padding = columns - len(left) - len(right)
    if padding < 1:
        padding = 1
    line = left + " " * padding + right
    printer.text(line + "\n")

    if bold:
        printer.set(bold=False)
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/escpos_print.py tests/test_escpos_print.py
git commit -m "feat: separator and columns job types"
```

---

### Task 4: Barcode and QR Code Jobs

**Files:**
- Modify: `scripts/escpos_print.py`
- Modify: `tests/test_escpos_print.py`

- [ ] **Step 1: Write failing tests for barcode and QR**

Append to `tests/test_escpos_print.py`:

```python
class MockPrinterFull(MockPrinter):
    """Extended mock with barcode/qr/image methods."""
    def barcode(self, data, bc_type, **kwargs):
        self.calls.append(('barcode', data, bc_type, kwargs))

    def qr(self, data, **kwargs):
        self.calls.append(('qr', data, kwargs))

    def image(self, img, **kwargs):
        self.calls.append(('image', img, kwargs))

    def ln(self, count=1):
        self.calls.append(('ln', count))


def test_barcode_job():
    printer = MockPrinterFull()
    jobs = [{"type": "barcode", "data": "123456789012", "format": "EAN13"}]
    process_jobs(printer, jobs, columns=48)

    bc_calls = [c for c in printer.calls if c[0] == 'barcode']
    assert len(bc_calls) == 1
    assert bc_calls[0][1] == "123456789012"
    assert bc_calls[0][2] == "EAN13"


def test_barcode_default_format():
    printer = MockPrinterFull()
    jobs = [{"type": "barcode", "data": "TESTPRINT123"}]
    process_jobs(printer, jobs, columns=48)

    bc_calls = [c for c in printer.calls if c[0] == 'barcode']
    assert bc_calls[0][2] == "CODE128"


def test_qr_job():
    printer = MockPrinterFull()
    jobs = [{"type": "qr", "data": "https://example.com", "size": 8}]
    process_jobs(printer, jobs, columns=48)

    qr_calls = [c for c in printer.calls if c[0] == 'qr']
    assert len(qr_calls) == 1
    assert qr_calls[0][1] == "https://example.com"
    assert qr_calls[0][2].get('size') == 8


def test_qr_defaults():
    printer = MockPrinterFull()
    jobs = [{"type": "qr", "data": "test"}]
    process_jobs(printer, jobs, columns=48)

    qr_calls = [c for c in printer.calls if c[0] == 'qr']
    assert qr_calls[0][2].get('size') == 6
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: 4 new tests FAIL

- [ ] **Step 3: Add barcode and QR handlers**

Add to `process_jobs` dispatch:

```python
        elif job_type == "barcode":
            _handle_barcode(printer, job, columns)
        elif job_type == "qr":
            _handle_qr(printer, job)
```

Add handler functions:

```python
def _handle_barcode(printer, job, columns):
    """Print a barcode."""
    data = job.get("data", "")
    bc_format = job.get("format", "CODE128")
    align = job.get("align", "center")

    printer.set(align=align)
    printer.barcode(data, bc_format)
    printer.set(align="left")


def _handle_qr(printer, job):
    """Print a QR code."""
    data = job.get("data", "")
    size = job.get("size", 6)
    ec = job.get("error_correction", "M")

    ec_map = {"L": 0, "M": 1, "Q": 2, "H": 3}
    native_ec = ec_map.get(ec, 1)

    printer.qr(data, size=size, native=True, ec=native_ec)
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/escpos_print.py tests/test_escpos_print.py
git commit -m "feat: barcode and QR code job types"
```

---

### Task 5: Image and Feed Jobs

**Files:**
- Modify: `scripts/escpos_print.py`
- Modify: `tests/test_escpos_print.py`

- [ ] **Step 1: Write failing tests for image and feed**

Append to `tests/test_escpos_print.py`:

```python
import tempfile
from PIL import Image


def test_feed_job():
    printer = MockPrinterFull()
    jobs = [{"type": "feed", "lines": 3}]
    process_jobs(printer, jobs, columns=48)

    ln_calls = [c for c in printer.calls if c[0] == 'ln']
    assert len(ln_calls) == 1
    assert ln_calls[0][1] == 3


def test_feed_default():
    printer = MockPrinterFull()
    jobs = [{"type": "feed"}]
    process_jobs(printer, jobs, columns=48)

    ln_calls = [c for c in printer.calls if c[0] == 'ln']
    assert ln_calls[0][1] == 1


def test_image_job():
    printer = MockPrinterFull()

    # Create a small test image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (100, 50), color="white")
        img.save(f.name)
        tmp_path = f.name

    jobs = [{"type": "image", "path": tmp_path}]
    process_jobs(printer, jobs, columns=48)

    img_calls = [c for c in printer.calls if c[0] == 'image']
    assert len(img_calls) == 1

    os.unlink(tmp_path)


def test_image_job_with_width():
    printer = MockPrinterFull()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (400, 200), color="white")
        img.save(f.name)
        tmp_path = f.name

    jobs = [{"type": "image", "path": tmp_path, "width": 200}]
    process_jobs(printer, jobs, columns=48)

    img_calls = [c for c in printer.calls if c[0] == 'image']
    assert len(img_calls) == 1
    # The image passed to printer should be resized
    passed_img = img_calls[0][1]
    assert passed_img.width == 200

    os.unlink(tmp_path)
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: 4 new tests FAIL

- [ ] **Step 3: Add image and feed handlers**

Add to top of `escpos_print.py`:

```python
from PIL import Image as PILImage
```

Add to `process_jobs` dispatch:

```python
        elif job_type == "image":
            _handle_image(printer, job)
        elif job_type == "feed":
            _handle_feed(printer, job)
```

Add handler functions:

```python
def _handle_image(printer, job):
    """Print an image from a file path."""
    path = job.get("path", "")
    width = job.get("width")

    img = PILImage.open(path)
    if width:
        ratio = width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((width, new_height))

    printer.image(img)


def _handle_feed(printer, job):
    """Feed blank lines."""
    lines = job.get("lines", 1)
    printer.ln(lines)
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: All 15 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/escpos_print.py tests/test_escpos_print.py
git commit -m "feat: image and feed job types"
```

---

### Task 6: Demo Job

**Files:**
- Modify: `scripts/escpos_print.py`
- Modify: `tests/test_escpos_print.py`

- [ ] **Step 1: Write failing test for demo job**

Append to `tests/test_escpos_print.py`:

```python
def test_demo_job():
    printer = MockPrinterFull()
    jobs = [{"type": "demo"}]
    process_jobs(printer, jobs, columns=48)

    call_types = [c[0] for c in printer.calls]

    # Demo should produce: text, separator, columns, barcode, qr, image, ln, cut
    assert 'text' in call_types
    assert 'barcode' in call_types
    assert 'qr' in call_types
    assert 'image' in call_types
    assert 'cut' in call_types

    # Should have multiple text calls (header, styles, etc.)
    text_calls = [c for c in printer.calls if c[0] == 'text']
    assert len(text_calls) >= 8  # header + styles + separator + column rows + total
```

- [ ] **Step 2: Run test to verify it fails**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py::test_demo_job -v`
Expected: FAIL

- [ ] **Step 3: Add demo handler**

Add to `process_jobs` dispatch:

```python
        elif job_type == "demo":
            _handle_demo(printer, columns)
```

Add handler function:

```python
def _handle_demo(printer, columns):
    """Print a full capability demo/test page."""
    demo_jobs = [
        {"type": "text", "content": "ESC/POS PRINTER TEST", "align": "center", "size": "large", "bold": True},
        {"type": "text", "content": "Capability Demo Page", "align": "center"},
        {"type": "separator", "char": "="},
        {"type": "text", "content": "Normal text"},
        {"type": "text", "content": "Bold text", "bold": True},
        {"type": "text", "content": "Underline text", "underline": True},
        {"type": "text", "content": "Font B text", "font": "b"},
        {"type": "text", "content": "Right aligned", "align": "right"},
        {"type": "text", "content": "Center aligned", "align": "center"},
        {"type": "separator"},
        {"type": "text", "content": "RECEIPT DEMO", "align": "center", "bold": True},
        {"type": "separator"},
        {"type": "columns", "left": "Widget A", "right": "$9.99"},
        {"type": "columns", "left": "Widget B", "right": "$14.50"},
        {"type": "columns", "left": "Gizmo C", "right": "$3.25"},
        {"type": "columns", "left": "Doohickey D", "right": "$7.00"},
        {"type": "separator", "char": "="},
        {"type": "columns", "left": "TOTAL", "right": "$34.74", "bold": True},
        {"type": "feed", "lines": 1},
        {"type": "text", "content": "BARCODE TEST", "align": "center", "bold": True},
        {"type": "barcode", "data": "TESTPRINT123", "format": "CODE128"},
        {"type": "feed", "lines": 1},
        {"type": "text", "content": "QR CODE TEST", "align": "center", "bold": True},
        {"type": "qr", "data": "https://github.com/anthropics/claude-code", "size": 6},
        {"type": "feed", "lines": 1},
        {"type": "text", "content": "IMAGE TEST", "align": "center", "bold": True},
    ]

    # Process text/separator/columns/barcode/qr/feed jobs
    process_jobs(printer, demo_jobs, columns)

    # Generate and print a checkerboard test image
    checkerboard = _generate_test_image()
    printer.image(checkerboard)

    # Footer
    process_jobs(printer, [
        {"type": "feed", "lines": 1},
        {"type": "separator", "char": "="},
        {"type": "text", "content": "TEST COMPLETE", "align": "center", "bold": True},
        {"type": "text", "content": f"Column width: {columns}", "align": "center"},
        {"type": "feed", "lines": 4},
        {"type": "cut"},
    ], columns)


def _generate_test_image():
    """Generate a small checkerboard test pattern image."""
    width, height = 200, 50
    img = PILImage.new("1", (width, height), 1)  # 1-bit, white background
    pixels = img.load()
    block = 10
    for y in range(height):
        for x in range(width):
            if (x // block + y // block) % 2 == 0:
                pixels[x, y] = 0  # black
    return img
```

- [ ] **Step 4: Run tests to verify all pass**

Run: `scripts/.venv/bin/python -m pytest tests/test_escpos_print.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/escpos_print.py tests/test_escpos_print.py
git commit -m "feat: demo job type with full capability test page"
```

---

### Task 7: Model-Invoked Skill (escpos-print)

**Files:**
- Create: `skills/escpos-print/SKILL.md`

- [ ] **Step 1: Write the model-invoked skill**

```markdown
---
name: escpos-print
description: Use when the user asks to print something, generate a receipt, produce physical output, print a label, test a printer, or send output to a thermal printer. Handles ESC/POS printing over IP with support for text, barcodes, QR codes, images, and receipt layouts.
version: 1.0.0
allowed-tools: [Bash, Read, Write]
---

# ESC/POS IP Printer

Print to ESC/POS thermal printers over IP. Supports text formatting, barcodes, QR codes, images, and receipt-style layouts.

## Setup

Before first use, ensure the venv exists:

```bash
PLUGIN_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
```

Check if the venv exists. If not, run setup:

```bash
if [ ! -d "PLUGIN_DIR/scripts/.venv" ]; then
    bash PLUGIN_DIR/scripts/setup.sh
fi
```

Where `PLUGIN_DIR` is the directory containing this plugin (the parent of `skills/`). Determine this from the skill's own path context.

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
{"type": "image", "path": "/tmp/image.png", "width": 200}
```
Supports PNG, JPG, BMP. Width in pixels (height scales proportionally).

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
```

Write to `skills/escpos-print/SKILL.md`.

- [ ] **Step 2: Commit**

```bash
git add skills/escpos-print/SKILL.md
git commit -m "feat: model-invoked escpos-print skill"
```

---

### Task 8: User-Invoked /print Command

**Files:**
- Create: `skills/print/SKILL.md`

- [ ] **Step 1: Write the /print command skill**

```markdown
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
```

Write to `skills/print/SKILL.md`.

- [ ] **Step 2: Commit**

```bash
git add skills/print/SKILL.md
git commit -m "feat: user-invoked /print command"
```

---

### Task 9: End-to-End Test — Print Demo Page

**Files:** None created — this is a live printer test.

- [ ] **Step 1: Run the demo print to the real printer**

```bash
echo '{"printer": {"host": "192.168.1.251", "port": 9100}, "columns": 48, "jobs": [{"type": "demo"}]}' | /home/simon/Documents/ESC-POS-IP-Printer-Skill/scripts/.venv/bin/python /home/simon/Documents/ESC-POS-IP-Printer-Skill/scripts/escpos_print.py
```

Expected: `{"success": true}` and a full demo page prints on the thermal printer.

- [ ] **Step 2: Report results to user for physical verification**

Tell the user what was sent and ask them to confirm the physical printout looks correct.

- [ ] **Step 3: Final commit if any adjustments were needed**

```bash
git add -A
git commit -m "feat: ESC/POS IP printer skill v1.0.0"
```

#!/usr/bin/env python3
"""ESC/POS printer helper — receives JSON on stdin, sends to printer over IP."""

import json
import sys
from escpos.printer import Network
from PIL import Image as PILImage


# GS ! n — character size. n = (width_mult - 1) << 4 | (height_mult - 1)
SIZE_MAP = {
    "normal": 0x00,   # 1x1
    "large": 0x11,    # 2x2
    "xlarge": 0x33,   # 4x4
}


def _init_printer(printer):
    """Reset printer and set compact defaults."""
    printer._raw(b'\x1b\x40')       # ESC @ - initialize printer
    printer._raw(b'\x1b\x33\x18')   # ESC 3 24 - line spacing 24 dots
    printer._raw(b'\x1d\x21\x00')   # GS ! 0 - character size 1x1


def process_jobs(printer, jobs, columns=48):
    """Process a list of print jobs on the given printer."""
    for job in jobs:
        job_type = job.get("type")
        if job_type == "text":
            _handle_text(printer, job, columns)
        elif job_type == "separator":
            _handle_separator(printer, job, columns)
        elif job_type == "columns":
            _handle_columns(printer, job, columns)
        elif job_type == "barcode":
            _handle_barcode(printer, job, columns)
        elif job_type == "qr":
            _handle_qr(printer, job)
        elif job_type == "image":
            _handle_image(printer, job)
        elif job_type == "feed":
            _handle_feed(printer, job)
        elif job_type == "demo":
            _handle_demo(printer, columns)
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

    size_byte = SIZE_MAP.get(size, 0x00)

    printer.set(align=align, bold=bold, underline=1 if underline else 0, font=font)
    printer._raw(b'\x1d\x21' + bytes([size_byte]))  # GS ! n — character size
    printer.text(content + "\n")

    # Reset formatting
    printer.set(align="left", bold=False, underline=0, font="a")
    printer._raw(b'\x1d\x21\x00')  # GS ! 0 — back to 1x1


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


def _handle_barcode(printer, job, columns):
    """Print a barcode."""
    data = job.get("data", "")
    bc_format = job.get("format", "CODE128")
    align = job.get("align", "center")

    # CODE128 needs subset prefix for hardware rendering
    if bc_format == "CODE128" and not data.startswith("{"):
        data = "{B" + data

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
    img = PILImage.new("1", (width, height), 1)
    pixels = img.load()
    block = 10
    for y in range(height):
        for x in range(width):
            if (x // block + y // block) % 2 == 0:
                pixels[x, y] = 0
    return img


def main():
    """Main entry point — read JSON from stdin, print to network printer."""
    try:
        data = json.load(sys.stdin)
        host = data["printer"]["host"]
        port = data["printer"].get("port", 9100)
        columns = data.get("columns", 48)
        jobs = data.get("jobs", [])

        printer = Network(host, port, timeout=5)
        _init_printer(printer)
        process_jobs(printer, jobs, columns)
        printer.close()

        print(json.dumps({"success": True}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

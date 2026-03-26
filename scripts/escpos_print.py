#!/usr/bin/env python3
"""ESC/POS printer helper — receives JSON on stdin, sends to printer over IP."""

import json
import sys
from escpos.printer import Network
from PIL import Image as PILImage


SIZE_MAP = {
    "normal": {"double_width": False, "double_height": False},
    "large": {"double_width": True, "double_height": True},
    "xlarge": {"double_width": True, "double_height": True},
}


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

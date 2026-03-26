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
    assert any(c[1].get('double_width') == True and c[1].get('double_height') == True for c in set_calls)


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
    assert bc_calls[0][1] == "{BTESTPRINT123"  # CODE128 auto-prefixed with {B
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
    passed_img = img_calls[0][1]
    assert passed_img.width == 200

    os.unlink(tmp_path)


def test_demo_job():
    printer = MockPrinterFull()
    jobs = [{"type": "demo"}]
    process_jobs(printer, jobs, columns=48)

    call_types = [c[0] for c in printer.calls]

    assert 'text' in call_types
    assert 'barcode' in call_types
    assert 'qr' in call_types
    assert 'image' in call_types
    assert 'cut' in call_types

    text_calls = [c for c in printer.calls if c[0] == 'text']
    assert len(text_calls) >= 8

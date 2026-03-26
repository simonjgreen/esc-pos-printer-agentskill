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

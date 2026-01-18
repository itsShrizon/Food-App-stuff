"""
Receipt Parser Module - Backward Compatible Facade.

This module re-exports from the receipt_parser package for backward compatibility.
Actual implementation is in receipt_parser/ package.
"""

from receipt_parser import (
    parse_receipt_image,
    parse_receipt_from_base64,
    format_receipt_summary,
)

__all__ = [
    'parse_receipt_image',
    'parse_receipt_from_base64',
    'format_receipt_summary',
]

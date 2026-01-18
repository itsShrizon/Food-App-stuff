"""Receipt formatting functions."""

from typing import Any, Dict


def format_receipt_summary(receipt_data: Dict[str, Any]) -> str:
    """Format receipt data into a human-readable summary."""
    lines = []
    lines.append("=" * 60)
    lines.append("📄 RECEIPT SUMMARY")
    lines.append("=" * 60)
    
    if receipt_data.get("store_name"):
        lines.append(f"🏪 Store: {receipt_data['store_name']}")
    if receipt_data.get("date"):
        lines.append(f"📅 Date: {receipt_data['date']}")
    
    currency = receipt_data.get("currency", "$")
    
    lines.append("\n📦 ITEMS PURCHASED:")
    lines.append("-" * 60)
    
    for i, item in enumerate(receipt_data.get("items", []), 1):
        name = item.get("name", "Unknown")
        quantity = item.get("quantity", "1 unit")
        price = item.get("price", "0.00")
        lines.append(f"{i}. {name}")
        lines.append(f"   Quantity: {quantity} | Price: {currency}{price}")
    
    if receipt_data.get("total"):
        lines.append("-" * 60)
        lines.append(f"💰 TOTAL: {currency}{receipt_data['total']}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)

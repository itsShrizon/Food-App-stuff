"""Interactive receipt parser demo script."""

import json
from pathlib import Path

from receipt_parser import parse_receipt_image, format_receipt_summary


def display_receipt_items(receipt_data):
    """Display receipt items in a table format."""
    print("\n" + "="*70)
    print("FOOD ITEMS EXTRACTED")
    print("="*70)
    
    if not receipt_data.get('items'):
        print("\nNo food items found on this receipt.")
        return
    
    # Header
    print(f"\n{'#':<4} {'Item Name':<30} {'Quantity':<15} {'Price':>10}")
    print("-"*70)
    
    # Items
    currency = receipt_data.get('currency', '$')
    for i, item in enumerate(receipt_data['items'], 1):
        name = item.get('name', 'Unknown')[:28]
        quantity = item.get('quantity', 'N/A')[:13]
        price = item.get('price', '0.00')
        
        print(f"{i:<4} {name:<30} {quantity:<15} {currency}{price:>9}")
    
    # Total
    if receipt_data.get('total'):
        print("-"*70)
        print(f"{'TOTAL':<50} {currency}{receipt_data['total']:>14}")
    
    print("="*70)


def save_to_json(receipt_data, output_file):
    """Save receipt data to JSON file."""
    try:
        with open(output_file, 'w') as f:
            json.dump(receipt_data, f, indent=2)
        print(f"\nData saved to: {output_file}")
    except Exception as e:
        print(f"\nError saving file: {e}")


def display_statistics(receipt_data):
    """Display statistics about the receipt."""
    items = receipt_data.get('items', [])
    
    if not items:
        return
    
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    # Count items
    total_items = len(items)
    print(f"\n   Total Items: {total_items}")
    
    # Calculate average price
    try:
        prices = [float(item.get('price', '0')) for item in items]
        avg_price = sum(prices) / len(prices) if prices else 0
        print(f"   Average Price: ${avg_price:.2f}")
        
        if prices:
            print(f"   Most Expensive: ${max(prices):.2f}")
            print(f"   Least Expensive: ${min(prices):.2f}")
    except:
        pass
    
    # Store info
    if receipt_data.get('store_name'):
        print(f"   Store: {receipt_data['store_name']}")
    
    if receipt_data.get('date'):
        print(f"   Date: {receipt_data['date']}")
    
    print("="*70)


def main():
    """Main function to run receipt parser demo."""
    print("\n" + "="*70)
    print("RECEIPT PARSER - Gemini Vision AI")
    print("="*70)
    print("\nExtract food items, quantities, and prices from receipt images\n")
    
    # Get image path from user
    image_path = input("Enter receipt image path: ").strip()
    
    if not image_path:
        print("No path provided.")
        return
    
    # Remove quotes if present
    image_path = image_path.strip('"\'')
    
    # Check if file exists
    if not Path(image_path).exists():
        print(f"\nError: File not found: {image_path}")
        return
    
    # Process the receipt
    print("\n" + "="*70)
    print(f"PROCESSING RECEIPT: {Path(image_path).name}")
    print("="*70)
    print("\nAnalyzing image with Gemini AI...\n")
    
    try:
        # Parse receipt
        receipt_data = parse_receipt_image(image_path)
        
        # Display formatted summary
        print(format_receipt_summary(receipt_data))
        
        # Display items table
        display_receipt_items(receipt_data)
        
        # Display statistics
        display_statistics(receipt_data)
        
        # Ask if user wants to save
        print("\n" + "="*70)
        save_choice = input("Save to JSON file? (y/n): ").strip().lower()
        if save_choice == 'y':
            default_name = Path(image_path).stem + "_data.json"
            filename = input(f"Filename [{default_name}]: ").strip() or default_name
            save_to_json(receipt_data, filename)
            print("\nProcessing complete!")
        else:
            print("\nProcessing complete!")
        
        print("="*70)
        
    except ValueError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError processing receipt: {e}")


if __name__ == "__main__":
    main()

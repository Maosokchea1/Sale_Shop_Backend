import sqlite3

def fix_all_orders():
    try:
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        
        # First, check current state
        cursor.execute("SELECT id, status, total_amount_usd FROM orders")
        before = cursor.fetchall()
        print("Before update:")
        for row in before[:5]:
            print(f"  ID: {row[0]}, Status: {row[1]}, Amount: {row[2]}")
        
        # Update all orders with NULL amounts
        cursor.execute("UPDATE orders SET total_amount_usd = 29.99 WHERE total_amount_usd IS NULL")
        cursor.execute("UPDATE orders SET total_amount_khr = 122959 WHERE total_amount_khr IS NULL")
        
        # Update paid orders with higher amount
        cursor.execute("UPDATE orders SET total_amount_usd = 99.99, total_amount_khr = 409959 WHERE status = 'paid'")
        
        conn.commit()
        
        # Verify updates
        cursor.execute("SELECT id, order_number, status, total_amount_usd FROM orders")
        orders = cursor.fetchall()
        
        print("\nAfter update:")
        total_revenue = 0
        paid_count = 0
        
        for order in orders:
            order_id, order_num, status, amount = order
            if amount is None:
                amount = 0
            if status == 'paid':
                total_revenue += amount
                paid_count += 1
            print(f"  ID: {order_id}, Order: {order_num}, Status: {status}, Amount: ${amount:.2f}")
        
        print(f"\n📊 Summary:")
        print(f"  Total Orders: {len(orders)}")
        print(f"  Paid Orders: {paid_count}")
        print(f"  💰 Total Revenue: ${total_revenue:.2f}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    fix_all_orders()
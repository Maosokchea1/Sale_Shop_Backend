import sqlite3

def fix_orders():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    try:
        # Update pending orders
        cursor.execute("UPDATE orders SET total_amount_usd = 29.99 WHERE total_amount_usd IS NULL AND status = 'pending'")
        cursor.execute("UPDATE orders SET total_amount_khr = 122959 WHERE total_amount_khr IS NULL AND status = 'pending'")
        
        # Update paid orders
        cursor.execute("UPDATE orders SET total_amount_usd = 49.99, total_amount_khr = 204959 WHERE status = 'paid' AND total_amount_usd IS NULL")
        
        conn.commit()
        print("Orders updated successfully")
        
        # Verify
        cursor.execute("SELECT id, order_number, status, total_amount_usd FROM orders")
        orders = cursor.fetchall()
        
        print("\nUpdated orders:")
        total_revenue = 0
        for order in orders:
            amount = order[3] if order[3] else 0
            status = order[2]
            if status == 'paid':
                total_revenue += amount
            print(f"  ID: {order[0]}, Number: {order[1]}, Status: {status}, Amount: ${amount}")
        
        print(f"\nTotal Revenue from paid orders: ${total_revenue}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_orders()
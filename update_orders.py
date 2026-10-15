import sqlite3

conn = sqlite3.connect('ecommerce.db')
cursor = conn.cursor()

# Update pending orders
cursor.execute("UPDATE orders SET total_amount_usd = 29.99 WHERE total_amount_usd IS NULL AND status = 'pending'")
cursor.execute("UPDATE orders SET total_amount_khr = 122959 WHERE total_amount_khr IS NULL AND status = 'pending'")

# Update paid orders
cursor.execute("UPDATE orders SET total_amount_usd = 49.99, total_amount_khr = 204959 WHERE status = 'paid' AND total_amount_usd IS NULL")

conn.commit()

print(f"Updated {cursor.rowcount} orders")

# Verify
cursor.execute("SELECT id, order_number, status, total_amount_usd FROM orders")
orders = cursor.fetchall()

print("\nOrders in database:")
for order in orders:
    amount = order[3] if order[3] else 0
    status = order[2]
    print(f"  ID: {order[0]}, Number: {order[1]}, Status: {status}, Amount: ${amount}")

conn.close()
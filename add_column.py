import sqlite3

def add_transaction_id_column():
    try:
        conn = sqlite3.connect('ecommerce.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'transaction_id' not in columns:
            print("Adding transaction_id column to orders table...")
            cursor.execute("ALTER TABLE orders ADD COLUMN transaction_id TEXT")
            print("Column added successfully!")
        else:
            print("transaction_id column already exists")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    add_transaction_id_column()
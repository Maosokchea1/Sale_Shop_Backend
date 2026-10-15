# add_product_images_table.py
from database import engine
import models

def add_product_images_table():
    # Create the new table
    models.ProductImage.__table__.create(bind=engine, checkfirst=True)
    print("✅ Product images table created successfully!")

if __name__ == "__main__":
    add_product_images_table()
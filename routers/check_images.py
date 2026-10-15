from database import SessionLocal
import models

def check_product_images():
    db = SessionLocal()
    products = db.query(models.Product).all()
    
    if not products:
        print("No products found in database!")
    else:
        print(f"Found {len(products)} products:\n")
        for product in products:
            print(f"ID: {product.id}")
            print(f"Title: {product.title}")
            print(f"Image URL: {product.image_url if product.image_url else 'No image set'}")
            print("-" * 50)
    
    db.close()

if __name__ == "__main__":
    check_product_images()
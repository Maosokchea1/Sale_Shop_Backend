from database import SessionLocal
import models

def update_product_images():
    db = SessionLocal()
    products = db.query(models.Product).all()
    
    # Default product image
    default_image = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400"
    
    updated_count = 0
    for product in products:
        if not product.image_url or product.image_url == "":
            product.image_url = default_image
            updated_count += 1
            print(f"Updated image for: {product.title}")
    
    db.commit()
    db.close()
    print(f"\n✅ Updated {updated_count} products with default images!")

if __name__ == "__main__":
    update_product_images()
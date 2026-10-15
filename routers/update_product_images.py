from database import SessionLocal
import models

def update_product_images():
    db = SessionLocal()
    products = db.query(models.Product).all()
    
    # Default images for different product types
    default_images = {
        "shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
        "jacket": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=400",
        "shoe": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400",
        "dress": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400",
        "hat": "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=400",
    }
    
    updated_count = 0
    for product in products:
        if not product.image_url:
            # Assign default image based on title
            title_lower = product.title.lower()
            image_url = None
            
            if "shirt" in title_lower or "t-shirt" in title_lower:
                image_url = default_images["shirt"]
            elif "jacket" in title_lower:
                image_url = default_images["jacket"]
            elif "sneaker" in title_lower or "shoe" in title_lower:
                image_url = default_images["shoe"]
            elif "dress" in title_lower:
                image_url = default_images["dress"]
            elif "beanie" in title_lower or "hat" in title_lower:
                image_url = default_images["hat"]
            else:
                # Use a generic product image
                image_url = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"
            
            product.image_url = image_url
            updated_count += 1
            print(f"Updated image for: {product.title}")
    
    db.commit()
    db.close()
    print(f"\n✅ Updated {updated_count} products with default images!")

if __name__ == "__main__":
    update_product_images()
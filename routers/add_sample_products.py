from database import SessionLocal
import models

def add_sample_products():
    db = SessionLocal()
    
    # First, check if categories exist
    categories = db.query(models.Category).all()
    if not categories:
        print("No categories found! Please add categories first.")
        print("You can add categories through the admin panel.")
        db.close()
        return
    
    # Sample images from Unsplash (free stock photos)
    sample_products = [
        {
            "title": "Classic White T-Shirt",
            "category_id": categories[0].id if categories else 1,
            "description": "100% cotton comfortable t-shirt. Perfect for everyday wear.",
            "original_price_usd": 29.99,
            "discount_price_usd": 19.99,
            "original_price_khr": 123000,
            "discount_price_khr": 82000,
            "stock_quantity": 100,
            "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
            "options": {"Size": ["S", "M", "L", "XL"], "Color": ["White", "Black"]}
        },
        {
            "title": "Black Denim Jacket",
            "category_id": categories[0].id if categories else 1,
            "description": "Stylish denim jacket for all seasons. Made with premium quality denim.",
            "original_price_usd": 89.99,
            "discount_price_usd": 69.99,
            "original_price_khr": 369000,
            "discount_price_khr": 287000,
            "stock_quantity": 50,
            "image_url": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=400",
            "options": {"Size": ["S", "M", "L", "XL"]}
        },
        {
            "title": "Casual Sneakers",
            "category_id": categories[0].id if categories else 1,
            "description": "Comfortable everyday sneakers. Perfect for walking and casual outings.",
            "original_price_usd": 59.99,
            "discount_price_usd": 49.99,
            "original_price_khr": 246000,
            "discount_price_khr": 205000,
            "stock_quantity": 75,
            "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400",
            "options": {"Size": ["38", "39", "40", "41", "42"], "Color": ["White", "Black"]}
        },
        {
            "title": "Summer Dress",
            "category_id": categories[0].id if categories else 1,
            "description": "Light and breezy summer dress. Perfect for beach and casual outings.",
            "original_price_usd": 49.99,
            "discount_price_usd": 39.99,
            "original_price_khr": 205000,
            "discount_price_khr": 164000,
            "stock_quantity": 60,
            "image_url": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400",
            "options": {"Size": ["XS", "S", "M", "L"], "Color": ["Blue", "Pink", "Yellow"]}
        },
        {
            "title": "Wool Beanie",
            "category_id": categories[0].id if categories else 1,
            "description": "Warm wool beanie for cold weather. One size fits most.",
            "original_price_usd": 19.99,
            "discount_price_usd": 14.99,
            "original_price_khr": 82000,
            "discount_price_khr": 61500,
            "stock_quantity": 150,
            "image_url": "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=400",
            "options": {"Color": ["Black", "Gray", "Navy"]}
        }
    ]
    
    added_count = 0
    for product_data in sample_products:
        # Check if product already exists
        existing = db.query(models.Product).filter(models.Product.title == product_data["title"]).first()
        if existing:
            print(f"Product '{product_data['title']}' already exists, skipping...")
            continue
            
        product = models.Product(**product_data)
        db.add(product)
        added_count += 1
        print(f"Added product: {product_data['title']}")
    
    db.commit()
    db.close()
    print(f"\n✅ Successfully added {added_count} sample products!")

if __name__ == "__main__":
    add_sample_products()
from database import SessionLocal
import models

def seed_categories():
    db = SessionLocal()
    
    default_categories = [
        {"name": "T-Shirts", "description": "Comfortable and stylish t-shirts for all occasions"},
        {"name": "Pants", "description": "Jeans, trousers, and casual pants"},
        {"name": "Dresses", "description": "Elegant dresses for every season"},
        {"name": "Jackets", "description": "Coats and jackets for cold weather"},
        {"name": "Accessories", "description": "Bags, belts, watches, and more"},
        {"name": "Shoes", "description": "Footwear for men and women"},
        {"name": "Sportswear", "description": "Activewear and sports clothing"},
    ]
    
    for cat_data in default_categories:
        existing = db.query(models.Category).filter(models.Category.name == cat_data["name"]).first()
        if not existing:
            category = models.Category(**cat_data)
            db.add(category)
            print(f"Added category: {cat_data['name']}")
    
    db.commit()
    db.close()
    print("Categories seeded successfully!")

if __name__ == "__main__":
    seed_categories()
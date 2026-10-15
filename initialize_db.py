from database import engine, Base
import models

def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    
    # Create default categories
    from database import SessionLocal
    db = SessionLocal()
    
    default_categories = [
        {"name": "T-Shirts", "description": "Comfortable and stylish t-shirts"},
        {"name": "Pants", "description": "Jeans, trousers, and more"},
        {"name": "Dresses", "description": "Elegant dresses for all occasions"},
        {"name": "Jackets", "description": "Coats and jackets for every season"},
        {"name": "Accessories", "description": "Bags, belts, and accessories"}
    ]
    
    for cat_data in default_categories:
        existing = db.query(models.Category).filter(models.Category.name == cat_data["name"]).first()
        if not existing:
            category = models.Category(**cat_data)
            db.add(category)
            print(f"Created category: {cat_data['name']}")
    
    db.commit()
    db.close()
    print("Database initialization complete!")

if __name__ == "__main__":
    init_database()
from database import SessionLocal
import models

def check_database():
    db = SessionLocal()
    
    # Check categories table
    categories = db.query(models.Category).all()
    print(f"Categories found: {len(categories)}")
    for cat in categories:
        print(f"  - ID: {cat.id}, Name: {cat.name}")
    
    # Check if category exists
    admin = db.query(models.User).filter(models.User.is_admin == True).first()
    if admin:
        print(f"Admin user: {admin.email}")
    else:
        print("No admin user found!")
    
    db.close()

if __name__ == "__main__":
    check_database()
from database import SessionLocal
from auth import get_password_hash
import models

def create_admin_user():
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(models.User).filter(models.User.is_admin == True).first()
    if not admin:
        admin_user = models.User(
            full_name="Administrator",
            email="admin@example.com",
            phone_number="+1234567890",
            hashed_password=get_password_hash("admin123"),
            is_admin=True,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully!")
        print("Email: admin@example.com")
        print("Password: admin123")
    else:
        print("Admin user already exists!")
    
    db.close()

if __name__ == "__main__":
    create_admin_user()
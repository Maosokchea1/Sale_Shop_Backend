from sqlalchemy.orm import Session
from sqlalchemy import and_
import models
import schemas
from datetime import datetime
import uuid

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    from auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    update_data = user_update.dict(exclude_unset=True)
    if 'password' in update_data and update_data['password']:
        from auth import get_password_hash
        update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

# Category CRUD
def get_category(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Category).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def update_category(db: Session, category_id: int, category_update: schemas.CategoryCreate):
    db_category = get_category(db, category_id)
    if not db_category:
        return None
    for field, value in category_update.dict().items():
        setattr(db_category, field, value)
    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int):
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
        return True
    return False

# Product CRUD
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: int = None):
    query = db.query(models.Product)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False

def get_low_stock_products(db: Session, threshold: int = 10):
    return db.query(models.Product).filter(models.Product.stock_quantity <= threshold).all()

def get_high_stock_products(db: Session, threshold: int = 100):
    return db.query(models.Product).filter(models.Product.stock_quantity >= threshold).all()

# Order CRUD
def generate_order_number():
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

# In crud.py, update the create_order function:

def create_order(db: Session, order: schemas.OrderCreate, user_id: int):
    order_number = generate_order_number()
    total_usd = 0
    total_khr = 0
    order_items = []
    
    for item in order.items:
        product = get_product(db, item.product_id)
        if not product:
            raise ValueError(f"Product {item.product_id} not found")
        
        # Check stock but DON'T decrease yet
        if product.stock_quantity < item.quantity:
            raise ValueError(f"Insufficient stock for {product.title}")
        
        price_usd = product.discount_price_usd or product.original_price_usd
        price_khr = product.discount_price_khr or product.original_price_khr
        
        total_usd += price_usd * item.quantity
        total_khr += price_khr * item.quantity
        
        order_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price_usd": price_usd,
            "price_khr": price_khr,
            "selected_options": item.selected_options
        })
        
        # REMOVE THIS LINE - Don't decrease stock here
        # product.stock_quantity -= item.quantity
    
    db_order = models.Order(
        user_id=user_id,
        order_number=order_number,
        total_amount_usd=total_usd,
        total_amount_khr=total_khr,
        shipping_address=order.shipping_address,
        payment_method=order.payment_method,
        status="pending"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Add order items
    for item_data in order_items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    
    return db_order

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Order).filter(models.Order.user_id == user_id).offset(skip).limit(limit).all()

def get_all_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()

def update_order_status(db: Session, order_id: int, status: str):
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order

# Payment CRUD
def create_payment(db: Session, payment_data: dict):
    db_payment = models.Payment(**payment_data)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment(db: Session, payment_id: int):
    return db.query(models.Payment).filter(models.Payment.id == payment_id).first()

def get_payment_by_transaction(db: Session, transaction_id: str):
    return db.query(models.Payment).filter(models.Payment.transaction_id == transaction_id).first()

def get_all_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Payment).offset(skip).limit(limit).all()

def update_payment_status(db: Session, payment_id: int, status: str, payment_details: dict = None):
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        return None
    db_payment.status = status
    if payment_details:
        db_payment.payment_details = payment_details
    db.commit()
    db.refresh(db_payment)
    return db_payment

# Banner CRUD
# Banner CRUD
def get_banners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Banner).filter(models.Banner.is_active == True).order_by(models.Banner.order).offset(skip).limit(limit).all()

def get_all_banners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Banner).offset(skip).limit(limit).all()

def create_banner(db: Session, banner: schemas.BannerCreate):
    db_banner = models.Banner(**banner.dict())
    db.add(db_banner)
    db.commit()
    db.refresh(db_banner)
    return db_banner

def update_banner(db: Session, banner_id: int, banner_update: schemas.BannerUpdate):
    db_banner = db.query(models.Banner).filter(models.Banner.id == banner_id).first()
    if not db_banner:
        return None
    update_data = banner_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_banner, field, value)
    db.commit()
    db.refresh(db_banner)
    return db_banner

def delete_banner(db: Session, banner_id: int):
    db_banner = db.query(models.Banner).filter(models.Banner.id == banner_id).first()
    if db_banner:
        db.delete(db_banner)
        db.commit()
        return True
    return False

# Brand CRUD
def get_brands(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Brand).filter(models.Brand.is_active == True).offset(skip).limit(limit).all()

def get_all_brands(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Brand).offset(skip).limit(limit).all()

def create_brand(db: Session, brand: schemas.BrandCreate):
    db_brand = models.Brand(**brand.dict())
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand

def update_brand(db: Session, brand_id: int, brand_update: schemas.BrandCreate):
    db_brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if not db_brand:
        return None
    for field, value in brand_update.dict().items():
        setattr(db_brand, field, value)
    db.commit()
    db.refresh(db_brand)
    return db_brand

def delete_brand(db: Session, brand_id: int):
    db_brand = db.query(models.Brand).filter(models.Brand.id == brand_id).first()
    if db_brand:
        db.delete(db_brand)
        db.commit()
        return True
    return False

# Dashboard Stats
def get_dashboard_stats(db: Session):
    total_users = db.query(models.User).count()
    total_orders = db.query(models.Order).count()
    total_products = db.query(models.Product).count()
    
    # Calculate total revenue from completed orders
    completed_orders = db.query(models.Order).filter(models.Order.status == "delivered").all()
    total_revenue_usd = sum(order.total_amount_usd for order in completed_orders)
    total_revenue_khr = sum(order.total_amount_khr for order in completed_orders)
    
    low_stock = get_low_stock_products(db, 10)
    high_stock = get_high_stock_products(db, 100)
    recent_orders = get_all_orders(db, 0, 10)
    
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_revenue_usd": total_revenue_usd,
        "total_revenue_khr": total_revenue_khr,
        "low_stock_products": low_stock,
        "high_stock_products": high_stock,
        "recent_orders": recent_orders
    }
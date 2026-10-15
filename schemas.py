from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Product Schemas
class ProductOption(BaseModel):
    label: str
    values: List[str]

class ProductBase(BaseModel):
    title: str
    category_id: int
    description: Optional[str] = None
    original_price_usd: float
    discount_price_usd: Optional[float] = None
    original_price_khr: float
    discount_price_khr: Optional[float] = None
    stock_quantity: int = 0
    promocode: Optional[str] = None
    image_url: Optional[str] = None
    options: Optional[Dict[str, Any]] = {}
    
# Add these schemas
class ProductImageBase(BaseModel):
    image_url: str
    display_order: int = 0

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageResponse(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Update ProductResponse to include images
class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    category: Optional[CategoryResponse] = None
    images: List[ProductImageResponse] = []
    
    class Config:
        from_attributes = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    original_price_usd: Optional[float] = None
    discount_price_usd: Optional[float] = None
    original_price_khr: Optional[float] = None
    discount_price_khr: Optional[float] = None
    stock_quantity: Optional[int] = None
    promocode: Optional[str] = None
    image_url: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

# Order Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    selected_options: Optional[Dict[str, Any]] = {}

class OrderCreate(BaseModel):
    items: List[OrderItemBase]
    shipping_address: str
    payment_method: str

class OrderItemResponse(OrderItemBase):
    id: int
    price_usd: float
    price_khr: float
    product: Optional[ProductResponse] = None
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    order_number: str
    total_amount_usd: float
    total_amount_khr: float
    status: str
    payment_method: Optional[str] = None
    shipping_address: Optional[str] = None
    created_at: datetime
    items: List[OrderItemResponse]
    
    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str

# Payment Schemas
class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    transaction_id: str
    amount_usd: float
    amount_khr: float
    currency: str
    status: str
    payment_method: Optional[str] = None
    payment_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Banner Schemas
class BannerBase(BaseModel):
    title: str
    text: Optional[str] = None
    image_url: str
    link_url: Optional[str] = None
    order: int = 0

class BannerCreate(BannerBase):
    pass

class BannerResponse(BannerBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class BannerUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

# Brand Schemas
class BrandBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: str
    link_url: Optional[str] = None

class BrandCreate(BrandBase):
    pass

class BrandResponse(BrandBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Telegram Config Schema
class TelegramConfigCreate(BaseModel):
    bot_token: str
    chat_id: str

class TelegramConfigResponse(TelegramConfigCreate):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard Stats
class DashboardStats(BaseModel):
    total_users: int
    total_orders: int
    total_products: int
    total_revenue_usd: float
    total_revenue_khr: float
    low_stock_products: List[ProductResponse]
    high_stock_products: List[ProductResponse]
    recent_orders: List[OrderResponse]
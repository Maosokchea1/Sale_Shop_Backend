from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil
from datetime import datetime
from database import get_db
import schemas
import crud
from auth import get_current_admin
import models

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("/")
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all products"""
    products = crud.get_products(db, skip=skip, limit=limit, category_id=category_id)
    
    # Add images to each product
    result = []
    for product in products:
        images = db.query(models.ProductImage).filter(
            models.ProductImage.product_id == product.id
        ).order_by(models.ProductImage.display_order).all()
        
        product_dict = {
            "id": product.id,
            "title": product.title,
            "category_id": product.category_id,
            "category": product.category,
            "description": product.description,
            "original_price_usd": product.original_price_usd,
            "discount_price_usd": product.discount_price_usd,
            "original_price_khr": product.original_price_khr,
            "discount_price_khr": product.discount_price_khr,
            "stock_quantity": product.stock_quantity,
            "promocode": product.promocode,
            "image_url": product.image_url,
            "options": product.options,
            "created_at": product.created_at,
            "images": [
                {
                    "id": img.id,
                    "image_url": img.image_url,
                    "display_order": img.display_order
                } for img in images
            ]
        }
        result.append(product_dict)
    
    return result

@router.get("/low-stock")
def get_low_stock_products(
    threshold: int = Query(10, ge=0),
    db: Session = Depends(get_db)
):
    """Get low stock products"""
    return crud.get_low_stock_products(db, threshold)

@router.get("/high-stock")
def get_high_stock_products(
    threshold: int = Query(100, ge=0),
    db: Session = Depends(get_db)
):
    """Get high stock products"""
    return crud.get_high_stock_products(db, threshold)

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Load additional images
    images = db.query(models.ProductImage).filter(
        models.ProductImage.product_id == product_id
    ).order_by(models.ProductImage.display_order).all()
    
    # Convert to dict and add images
    result = {
        "id": product.id,
        "title": product.title,
        "category_id": product.category_id,
        "description": product.description,
        "original_price_usd": product.original_price_usd,
        "discount_price_usd": product.discount_price_usd,
        "original_price_khr": product.original_price_khr,
        "discount_price_khr": product.discount_price_khr,
        "stock_quantity": product.stock_quantity,
        "promocode": product.promocode,
        "image_url": product.image_url,
        "options": product.options,
        "created_at": product.created_at,
        "images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "display_order": img.display_order,
                "created_at": img.created_at
            } for img in images
        ]
    }
    
    return result

@router.post("/upload-image")
async def upload_product_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_admin)
):
    """Upload single product image (main/featured)"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Validate file size (max 5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max size: 5MB")
        
        # Create upload directory if not exists
        upload_dir = "uploads/products"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{timestamp}_{unique_id}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return full URL
        file_url = f"http://localhost:8000/uploads/products/{filename}"
        print(f"✅ Image uploaded: {file_url}")
        
        return {"image_url": file_url, "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.post("/upload-multiple-images")
async def upload_multiple_product_images(
    files: List[UploadFile] = File(...),
    current_user = Depends(get_current_admin)
):
    """Upload multiple product images at once"""
    try:
        uploaded_images = []
        upload_dir = "uploads/products"
        os.makedirs(upload_dir, exist_ok=True)
        
        for idx, file in enumerate(files):
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]
            if file.content_type not in allowed_types:
                continue
            
            # Validate file size
            contents = await file.read()
            if len(contents) > 5 * 1024 * 1024:
                continue
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            filename = f"{timestamp}_{unique_id}_{idx}.{file_extension}"
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Return full URL
            file_url = f"http://localhost:8000/uploads/products/{filename}"
            uploaded_images.append({
                "image_url": file_url, 
                "filename": filename,
                "display_order": len(uploaded_images)
            })
        
        return {"images": uploaded_images, "success": True, "count": len(uploaded_images)}
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{product_id}/add-image")
def add_product_image(
    product_id: int,
    image_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Add image to product"""
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get current max display order
    max_order = db.query(models.ProductImage).filter(
        models.ProductImage.product_id == product_id
    ).count()
    
    new_image = models.ProductImage(
        product_id=product_id,
        image_url=image_data.get("image_url"),
        display_order=image_data.get("display_order", max_order)
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)
    
    return {
        "id": new_image.id, 
        "image_url": new_image.image_url, 
        "display_order": new_image.display_order
    }

@router.delete("/{product_id}/images/{image_id}")
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete product image"""
    image = db.query(models.ProductImage).filter(
        models.ProductImage.id == image_id,
        models.ProductImage.product_id == product_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    db.delete(image)
    db.commit()
    return {"message": "Image deleted successfully"}

@router.get("/{product_id}/images")
def get_product_images(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get all images for a product"""
    images = db.query(models.ProductImage).filter(
        models.ProductImage.product_id == product_id
    ).order_by(models.ProductImage.display_order).all()
    
    return [
        {
            "id": img.id,
            "image_url": img.image_url,
            "display_order": img.display_order,
            "created_at": img.created_at
        } for img in images
    ]

@router.put("/{product_id}/images/reorder")
def reorder_product_images(
    product_id: int,
    image_ids: List[int],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Reorder product images"""
    for index, image_id in enumerate(image_ids):
        db.query(models.ProductImage).filter(
            models.ProductImage.id == image_id,
            models.ProductImage.product_id == product_id
        ).update({"display_order": index})
    
    db.commit()
    return {"message": "Images reordered successfully"}

@router.post("/", response_model=schemas.ProductResponse)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create product (admin only)"""
    # Verify category exists
    category = crud.get_category(db, product.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return crud.create_product(db, product)

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update product (admin only)"""
    updated_product = crud.update_product(db, product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete product (admin only)"""
    # Also delete associated images
    db.query(models.ProductImage).filter(
        models.ProductImage.product_id == product_id
    ).delete()
    
    success = crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}
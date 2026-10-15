from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
import schemas
import crud
from auth import get_current_admin

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("/")
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all categories for frontend"""
    return crud.get_categories(db, skip=skip, limit=limit)

@router.get("/all")
def get_all_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all categories with product count for admin"""
    from models import Category, Product
    
    # Get categories with product count
    categories = db.query(
        Category,
        func.count(Product.id).label('product_count')
    ).outerjoin(Product, Category.id == Product.category_id).group_by(Category.id).offset(skip).limit(limit).all()
    
    result = []
    for category, product_count in categories:
        category_dict = {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "created_at": category.created_at,
            "product_count": product_count
        }
        result.append(category_dict)
    
    return result

@router.get("/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/", response_model=schemas.CategoryResponse)
def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create category (admin only)"""
    existing = db.query(crud.models.Category).filter(crud.models.Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    return crud.create_category(db, category)

@router.put("/{category_id}", response_model=schemas.CategoryResponse)
def update_category(
    category_id: int,
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update category (admin only)"""
    updated_category = crud.update_category(db, category_id, category)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated_category

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete category (admin only)"""
    success = crud.delete_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}
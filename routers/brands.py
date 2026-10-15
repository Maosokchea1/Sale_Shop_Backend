from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
import uuid
from database import get_db
import schemas
import crud
from auth import get_current_admin

router = APIRouter(prefix="/api/brands", tags=["Brands"])

@router.get("/")
def get_active_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get active brands for frontend"""
    return crud.get_brands(db, skip=skip, limit=limit)

@router.get("/all")
def get_all_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all brands for admin"""
    return crud.get_all_brands(db, skip=skip, limit=limit)

@router.post("/upload-image")
async def upload_brand_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_admin)
):
    """Upload brand logo image"""
    try:
        print(f"Received file: {file.filename}, Content-Type: {file.content_type}")
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp", "image/svg+xml"]
        if file.content_type not in allowed_types:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid file type. Allowed: {', '.join(allowed_types)}"}
            )
        
        # Create upload directory if not exists
        upload_dir = "uploads/brands"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        # Get file extension from original filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        filename = f"{timestamp}_{unique_id}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Read and save file
        contents = await file.read()
        
        # Validate file size (max 5MB)
        if len(contents) > 5 * 1024 * 1024:
            return JSONResponse(
                status_code=400,
                content={"detail": "File too large. Max size 5MB"}
            )
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return URL
        file_url = f"http://localhost:8000/uploads/brands/{filename}"
        print(f"✅ Brand logo uploaded successfully: {file_url}")
        
        return JSONResponse(
            status_code=200,
            content={"image_url": file_url, "filename": filename}
        )
        
    except Exception as e:
        print(f"❌ Error uploading brand logo: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to upload image: {str(e)}"}
        )

@router.post("/", response_model=schemas.BrandResponse)
def create_brand(
    brand: schemas.BrandCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create brand (admin only)"""
    # Check if brand already exists
    existing = db.query(crud.models.Brand).filter(
        crud.models.Brand.name == brand.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Brand already exists")
    
    return crud.create_brand(db, brand)

@router.put("/{brand_id}", response_model=schemas.BrandResponse)
def update_brand(
    brand_id: int,
    brand: schemas.BrandCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update brand (admin only)"""
    updated_brand = crud.update_brand(db, brand_id, brand)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated_brand

@router.delete("/{brand_id}")
def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete brand (admin only)"""
    success = crud.delete_brand(db, brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"message": "Brand deleted successfully"}
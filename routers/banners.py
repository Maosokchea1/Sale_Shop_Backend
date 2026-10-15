from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime
from database import get_db
import schemas
import crud
from auth import get_current_admin

router = APIRouter(prefix="/api/banners", tags=["Banners"])

@router.get("/")
def get_active_banners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get active banners for frontend"""
    return crud.get_banners(db, skip=skip, limit=limit)

@router.get("/all")
def get_all_banners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all banners for admin"""
    return crud.get_all_banners(db, skip=skip, limit=limit)

@router.post("/upload-image")
async def upload_banner_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_admin)
):
    """Upload banner image (admin only)"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Create upload directory
        upload_dir = "uploads/banners"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        filename = f"{timestamp}_{unique_id}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return full URL
        file_url = f"http://localhost:8000/uploads/banners/{filename}"
        print(f"✅ Banner image uploaded: {file_url}")
        
        return {"image_url": file_url, "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Banner upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.post("/", response_model=schemas.BannerResponse)
def create_banner(
    banner: schemas.BannerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create banner (admin only)"""
    try:
        return crud.create_banner(db, banner)
    except Exception as e:
        print(f"❌ Error creating banner: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{banner_id}", response_model=schemas.BannerResponse)
def update_banner(
    banner_id: int,
    banner: schemas.BannerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update banner (admin only)"""
    try:
        updated_banner = crud.update_banner(db, banner_id, banner)
        if not updated_banner:
            raise HTTPException(status_code=404, detail="Banner not found")
        return updated_banner
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating banner: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{banner_id}")
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete banner (admin only)"""
    try:
        success = crud.delete_banner(db, banner_id)
        if not success:
            raise HTTPException(status_code=404, detail="Banner not found")
        return {"message": "Banner deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting banner: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
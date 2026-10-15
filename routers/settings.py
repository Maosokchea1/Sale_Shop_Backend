from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models
import schemas
from auth import get_current_admin, get_current_user

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("/admin-info")
def get_admin_info(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get admin information"""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at
    }

@router.get("/telegram-config", response_model=schemas.TelegramConfigResponse)
def get_telegram_config(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get Telegram bot configuration (admin only)"""
    config = db.query(models.TelegramConfig).filter(models.TelegramConfig.is_active == True).first()
    if not config:
        raise HTTPException(status_code=404, detail="Telegram config not found")
    return config

@router.post("/telegram-config", response_model=schemas.TelegramConfigResponse)
def create_telegram_config(
    config: schemas.TelegramConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create Telegram bot configuration (admin only)"""
    # Deactivate existing configs
    db.query(models.TelegramConfig).update({"is_active": False})
    
    db_config = models.TelegramConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.put("/telegram-config/{config_id}", response_model=schemas.TelegramConfigResponse)
def update_telegram_config(
    config_id: int,
    config: schemas.TelegramConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update Telegram bot configuration (admin only)"""
    db_config = db.query(models.TelegramConfig).filter(models.TelegramConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Telegram config not found")
    
    for field, value in config.dict().items():
        setattr(db_config, field, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/exchange-rate")
def get_exchange_rate(
    db: Session = Depends(get_db)
):
    """Get USD to KHR exchange rate"""
    # You can store this in settings table
    setting = db.query(models.Setting).filter(models.Setting.key == "exchange_rate").first()
    if setting:
        return {"usd_to_khr": float(setting.value)}
    return {"usd_to_khr": 4100.00}  # Default rate
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import schemas
import crud
from auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.post("/", response_model=schemas.OrderResponse)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new order"""
    try:
        new_order = crud.create_order(db, order, current_user.id)
        
        # NO Telegram notification for new orders
        # Only send notification on payment success
        
        return new_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.OrderResponse])
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's orders"""
    if current_user.is_admin:
        return crud.get_all_orders(db, skip=skip, limit=limit)
    return crud.get_user_orders(db, current_user.id, skip=skip, limit=limit)

@router.get("/my-orders", response_model=List[schemas.OrderResponse])
def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's orders"""
    return crud.get_user_orders(db, current_user.id, skip=skip, limit=limit)

@router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get order by ID"""
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if user owns this order or is admin
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return order

@router.put("/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update order status (admin only)"""
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    updated_order = crud.update_order_status(db, order_id, status_update.status)
    
    # Optional: Send notification for status update if needed
    # But NOT sending for now
    
    return updated_order
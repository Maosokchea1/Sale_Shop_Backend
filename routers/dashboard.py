from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import schemas
import crud
from auth import get_current_admin
from typing import List

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get dashboard statistics (admin only)"""
    try:
        # Get all stats
        total_users = db.query(crud.models.User).count()
        total_orders = db.query(crud.models.Order).count()
        total_products = db.query(crud.models.Product).count()
        
        # Calculate total revenue from paid orders
        paid_orders = db.query(crud.models.Order).filter(
            crud.models.Order.status == 'paid'
        ).all()
        
        total_revenue_usd = 0
        for order in paid_orders:
            if order.total_amount_usd:
                total_revenue_usd += order.total_amount_usd
        
        # Get low stock products
        low_stock_products = db.query(crud.models.Product).filter(
            crud.models.Product.stock_quantity <= 10
        ).limit(10).all()
        
        # Get high stock products
        high_stock_products = db.query(crud.models.Product).filter(
            crud.models.Product.stock_quantity >= 100
        ).limit(10).all()
        
        # Get recent orders - ONLY those with valid items
        from sqlalchemy import func
        recent_orders = db.query(crud.models.Order).filter(
            crud.models.Order.id.in_(
                db.query(crud.models.OrderItem.order_id).filter(
                    crud.models.OrderItem.product_id.isnot(None)
                )
            )
        ).order_by(crud.models.Order.created_at.desc()).limit(10).all()
        
        # Convert to response format
        from schemas import ProductResponse, OrderResponse
        
        return {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_products": total_products,
            "total_revenue_usd": total_revenue_usd,
            "total_revenue_khr": total_revenue_usd * 4100,
            "low_stock_products": [ProductResponse.model_validate(p) for p in low_stock_products],
            "high_stock_products": [ProductResponse.model_validate(p) for p in high_stock_products],
            "recent_orders": [OrderResponse.model_validate(o) for o in recent_orders]
        }
    except Exception as e:
        print(f"Error in dashboard stats: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return partial data instead of failing
        return {
            "total_users": db.query(crud.models.User).count(),
            "total_orders": db.query(crud.models.Order).count(),
            "total_products": db.query(crud.models.Product).count(),
            "total_revenue_usd": 0,
            "total_revenue_khr": 0,
            "low_stock_products": [],
            "high_stock_products": [],
            "recent_orders": []
        }
        
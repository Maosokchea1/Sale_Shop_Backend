from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import pytz
from database import get_db
import schemas
import crud
from auth import get_current_user, get_current_admin
from khqr_payment import create_khqr_payment, verify_khqr_transaction, verify_webhook_signature
import uuid
import json
import telegram_bot
import os

# Cambodia Timezone (UTC+7)
CAMBODIA_TZ = pytz.timezone('Asia/Phnom_Penh')

def get_cambodia_time():
    """Get current time in Cambodia timezone"""
    return datetime.now(CAMBODIA_TZ)

router = APIRouter(prefix="/api/payments", tags=["Payments"])

@router.post("/create-khqr/{order_id}")
async def create_khqr_payment_session(
    order_id: int,
    success_url: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create KHQR payment session for an order"""
    try:
        print(f"🔄 Creating KHQR payment for order {order_id} at {get_cambodia_time()}")
        
        # Get order
        order = crud.get_order(db, order_id)
        if not order:
            print(f"❌ Order {order_id} not found")
            raise HTTPException(status_code=404, detail="Order not found")
        
        print(f"✅ Order found: {order.order_number}, Total: ${order.total_amount_usd}")
        
        # Check if user owns this order
        if order.user_id != current_user.id and not current_user.is_admin:
            print(f"❌ Access denied for user {current_user.id}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if order already paid
        if order.status == "paid":
            print(f"❌ Order already paid")
            raise HTTPException(status_code=400, detail="Order already paid")
        
        # Check if order has items
        if not order.items or len(order.items) == 0:
            print(f"❌ Order has no items")
            raise HTTPException(status_code=400, detail="Order has no items")
        
        # Check amount
        if order.total_amount_usd <= 0:
            print(f"❌ Invalid amount: ${order.total_amount_usd}")
            raise HTTPException(status_code=400, detail="Invalid order amount")
        
        # Generate transaction ID with Cambodia timestamp
        timestamp = get_cambodia_time().strftime("%Y%m%d%H%M%S")
        transaction_id = f"TXN-{timestamp}-{uuid.uuid4().hex[:8].upper()}"
        print(f"📝 Generated transaction ID: {transaction_id}")
        
        # Check if payment already exists for this order
        existing_payment = db.query(crud.models.Payment).filter(
            crud.models.Payment.order_id == order_id
        ).first()
        
        if existing_payment:
            print(f"⚠️ Payment already exists for order {order_id}")
            payment = existing_payment
        else:
            # Create payment record with Cambodia time
            payment_data = {
                "order_id": order_id,
                "transaction_id": transaction_id,
                "amount_usd": float(order.total_amount_usd),
                "amount_khr": float(order.total_amount_khr),
                "currency": "USD",
                "status": "pending",
                "payment_method": "khqr",
                "created_at": get_cambodia_time()
            }
            payment = crud.create_payment(db, payment_data)
            print(f"✅ Payment record created with ID: {payment.id} at {get_cambodia_time()}")
        
        # Create KHQR payment session
        try:
            payment_session = await create_khqr_payment(
                transaction_id=payment.transaction_id,
                amount_usd=float(order.total_amount_usd),
                success_url=success_url,
                remark=f"Payment for order {order.order_number}"
            )
            print(f"✅ KHQR payment session created at {get_cambodia_time()}")
        except Exception as e:
            print(f"❌ KHQR payment creation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "payment_id": payment.id,
                "transaction_id": payment.transaction_id,
                "fallback_url": f"/payment-success?order_id={order_id}&transaction_id={payment.transaction_id}"
            }
        
        return {
            "success": True,
            "payment_id": payment.id,
            "transaction_id": payment.transaction_id,
            "order_id": order.id,
            "order_number": order.order_number,
            "amount": order.total_amount_usd,
            "payment_url": payment_session.get("payment_url"),
            "params": payment_session.get("params", {}),
            "full_url": payment_session.get("full_url", ""),
            "cambodia_time": get_cambodia_time().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating KHQR payment: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")

@router.post("/webhook/khqr")
async def khqr_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle KHQR payment webhook with Cambodia timezone"""
    try:
        body = await request.json()
        print(f"📨 Webhook received at {get_cambodia_time()}: {json.dumps(body, indent=2)}")
        
        # Get transaction ID
        transaction_id = body.get("transaction_id")
        if not transaction_id:
            print("❌ No transaction_id in webhook")
            return {"status": "error", "message": "No transaction_id"}
        
        # Find payment by transaction ID
        payment = crud.get_payment_by_transaction(db, transaction_id)
        if not payment:
            print(f"❌ Payment not found for transaction: {transaction_id}")
            return {"status": "error", "message": "Payment not found"}
        
        # Check payment status from webhook
        payment_status = body.get("status", "").lower()
        
        # Only process successful payments
        if payment_status != "success":
            print(f"⏳ Ignoring non-success payment: {payment_status}")
            return {"status": "ignored", "message": f"Payment status: {payment_status}"}
        
        # Check if already processed
        if payment.status == "success":
            print(f"✅ Payment {transaction_id} already marked as success")
            return {"status": "success", "message": "Already processed"}
        
        # Update payment status to success with Cambodia time
        payment.status = "success"
        payment.payment_details = body
        db.commit()
        print(f"✅ Payment {transaction_id} marked as success at {get_cambodia_time()}")
        
        # Update order status
        order = crud.get_order(db, payment.order_id)
        if order and order.status == "pending":
            order.status = "paid"
            db.commit()
            print(f"✅ Order {order.order_number} marked as paid at {get_cambodia_time()}")
            
            # Send Telegram notification for successful payment
            background_tasks.add_task(telegram_bot.notify_payment_success, db, order, payment)
        
        return {
            "status": "success", 
            "message": "Payment processed successfully",
            "cambodia_time": get_cambodia_time().isoformat()
        }
    
    except Exception as e:
        print(f"❌ Webhook error at {get_cambodia_time()}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@router.get("/verify/{transaction_id}")
async def verify_payment(
    transaction_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Verify payment status with Cambodia timezone"""
    try:
        print(f"🔍 Verifying payment for transaction: {transaction_id} at {get_cambodia_time()}")
        
        # Find payment
        payment = crud.get_payment_by_transaction(db, transaction_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # If already success
        if payment.status == "success":
            order = crud.get_order(db, payment.order_id)
            return {
                "payment_id": payment.id,
                "status": payment.status,
                "order_status": order.status if order else "unknown",
                "verified": True,
                "cambodia_time": get_cambodia_time().isoformat()
            }
        
        # Verify with KHQR API
        verification = await verify_khqr_transaction(transaction_id)
        
        # Only update if verified as success
        if verification.get("verified", False):
            payment.status = "success"
            db.commit()
            
            order = crud.get_order(db, payment.order_id)
            if order and order.status == "pending":
                order.status = "paid"
                db.commit()
                print(f"✅ Order {order.order_number} marked as paid at {get_cambodia_time()}")
                
                # Send Telegram notification
                background_tasks.add_task(telegram_bot.notify_payment_success, db, order, payment)
            
            return {
                "payment_id": payment.id,
                "status": "success",
                "order_status": order.status if order else "paid",
                "verified": True,
                "cambodia_time": get_cambodia_time().isoformat()
            }
        
        return {
            "payment_id": payment.id,
            "status": payment.status,
            "verified": False,
            "cambodia_time": get_cambodia_time().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error verifying payment at {get_cambodia_time()}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/order-status/{order_id}")
async def get_order_payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get order and payment status with Cambodia timezone"""
    try:
        order = crud.get_order(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Check ownership
        if order.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Find payment
        payment = db.query(crud.models.Payment).filter(
            crud.models.Payment.order_id == order_id
        ).first()
        
        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "order_status": order.status,
            "payment_status": payment.status if payment else "pending",
            "total_amount": order.total_amount_usd,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "cambodia_time": get_cambodia_time().isoformat()
        }
    except Exception as e:
        print(f"❌ Error getting order status at {get_cambodia_time()}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.PaymentResponse])
def get_all_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get all payments with Cambodia timezone (admin only)"""
    payments = crud.get_all_payments(db, skip=skip, limit=limit)
    
    # Add Cambodia time to response
    result = []
    for payment in payments:
        payment_dict = {
            "id": payment.id,
            "order_id": payment.order_id,
            "transaction_id": payment.transaction_id,
            "amount_usd": payment.amount_usd,
            "amount_khr": payment.amount_khr,
            "currency": payment.currency,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "payment_details": payment.payment_details,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "cambodia_time": get_cambodia_time().isoformat()
        }
        result.append(payment_dict)
    
    return result
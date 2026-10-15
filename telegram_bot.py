import requests
from sqlalchemy.orm import Session
import models
from datetime import datetime

def send_telegram_notification(bot_token: str, chat_id: str, message: str):
    """ផ្ញើការជូនដំណឹងតាម Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ ការជូនដំណឹង Telegram បានផ្ញើដោយជោគជ័យ")
            return response.json()
        else:
            print(f"❌ ការជូនដំណឹង Telegram បរាជ័យ: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ កំហុសការជូនដំណឹង Telegram: {str(e)}")
        return None

def format_success_payment_message(order, payment):
    """ធ្វើទ្រង់ទ្រាយសារទូទាត់ជោគជ័យសម្រាប់ Telegram"""
    message = f"""
💚 <b>ការទូទាត់ជោគជ័យ!</b> 💚

━━━━━━━━━━━━━━━━━━━━
✅ <b>ការបញ្ជាទិញបានបញ្ជាក់</b>
━━━━━━━━━━━━━━━━━━━━
<b>លេខបញ្ជាទិញ:</b> <code>{order.order_number}</code>
<b>លេខប្រតិបត្តិការ:</b> <code>{payment.transaction_id}</code>
<b>កាលបរិច្ឆេទទូទាត់:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
<b>វិធីទូទាត់:</b> KHQR

━━━━━━━━━━━━━━━━━━━━
👤 <b>ព័ត៌មានអតិថិជន</b>
━━━━━━━━━━━━━━━━━━━━
<b>ឈ្មោះ:</b> {order.user.full_name}
<b>អ៊ីមែល:</b> {order.user.email}
<b>ទូរស័ព្ទ:</b> {order.user.phone_number or 'មិនមាន'}

━━━━━━━━━━━━━━━━━━━━
📦 <b>ព័ត៌មានលម្អិតការបញ្ជាទិញ</b>
━━━━━━━━━━━━━━━━━━━━
"""
    
    # បន្ថែមទំនិញ
    for item in order.items:
        product_title = item.product.title if item.product else f"ផលិតផល #{item.product_id}"
        price = item.price_usd
        subtotal = price * item.quantity
        
        message += f"""
<b>• {product_title}</b>
   ចំនួន: {item.quantity} × ${price:.2f} = <b>${subtotal:.2f}</b>"""
        
        if item.selected_options:
            options_str = ", ".join([f"{k}: {v}" for k, v in item.selected_options.items()])
            message += f"\n   ជម្រើស: {options_str}"
    
    message += f"""

━━━━━━━━━━━━━━━━━━━━
💰 <b>សង្ខេបការទូទាត់</b>
━━━━━━━━━━━━━━━━━━━━
<b>សរុបរង:</b> ${order.total_amount_usd:.2f}
<b>ថ្លៃដឹកជញ្ជូន:</b> $0.00
<b>ពន្ធ:</b> រួមបញ្ចូល
<b>សរុបបានបង់:</b> <b>${order.total_amount_usd:.2f}</b>

━━━━━━━━━━━━━━━━━━━━
📍 <b>អាសយដ្ឋានដឹកជញ្ជូន</b>
━━━━━━━━━━━━━━━━━━━━
{order.shipping_address}

━━━━━━━━━━━━━━━━━━━━
✨ <b>ការទូទាត់ត្រូវបានផ្ទៀងផ្ទាត់ដោយជោគជ័យ!</b>
🚚 <i>ការបញ្ជាទិញរបស់អ្នកនឹងត្រូវបានដំណើរការក្នុងរយៈពេល 24 ម៉ោង។</i>
💚 <i>សូមអរគុណសម្រាប់ការទិញទំនិញ!</i>
"""
    
    return message

def notify_payment_success(db: Session, order, payment):
    """ផ្ញើការជូនដំណឹងតែសម្រាប់ការទូទាត់ជោគជ័យប៉ុណ្ណោះ"""
    try:
        # ទទួលបានការកំណត់ Telegram ដែលសកម្ម
        tg_config = db.query(models.TelegramConfig).filter(
            models.TelegramConfig.is_active == True
        ).first()
        
        if not tg_config:
            print("⚠️ រកមិនឃើញការកំណត់ Telegram ដែលសកម្ម - រំលងការជូនដំណឹង")
            return False
        
        # ផ្ញើតែពេលការទូទាត់ជោគជ័យប៉ុណ្ណោះ
        if payment.status != "success" and order.status != "paid":
            print(f"⏳ ការទូទាត់មិនទាន់ជោគជ័យនៅឡើយទេ - រំលងការជូនដំណឹង")
            return False
        
        print(f"📤 កំពុងផ្ញើការជូនដំណឹងជោគជ័យសម្រាប់ការបញ្ជាទិញ {order.order_number}")
        
        # ធ្វើទ្រង់ទ្រាយសារជោគជ័យ
        message = format_success_payment_message(order, payment)
        
        # ផ្ញើការជូនដំណឹង
        result = send_telegram_notification(tg_config.bot_token, tg_config.chat_id, message)
        
        if result:
            print(f"✅ ការជូនដំណឹងទូទាត់ជោគជ័យបានផ្ញើសម្រាប់ការបញ្ជាទិញ {order.order_number}")
            return True
        else:
            print(f"❌ បរាជ័យក្នុងការផ្ញើការជូនដំណឹងទូទាត់សម្រាប់ការបញ្ជាទិញ {order.order_number}")
            return False
            
    except Exception as e:
        print(f"❌ កំហុសក្នុងការផ្ញើការជូនដំណឹងទូទាត់: {str(e)}")
        return False
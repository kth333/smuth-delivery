import pytz
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
import views.messages as messages

SGT = pytz.timezone("Asia/Singapore")

def get_order_keyboard(bot_username: str, order_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🚴 Claim This Order", url=f"https://t.me/{bot_username}?start=claim_{order_id}")],
        [InlineKeyboardButton("📝 Place an Order", url=f"https://t.me/{bot_username}?start=order")]
    ]
    return InlineKeyboardMarkup(keyboard)

def format_order_time(order) -> str:
    return (
        f"{order.earliest_pickup_time.astimezone(SGT).strftime('%A, %m-%d %I:%M%p')} - "
        f"{order.latest_pickup_time.astimezone(SGT).strftime('%I:%M%p')}"
    )

def format_order_message(order, claim_status: str) -> str:
    return messages.NEW_ORDER.format(
        order_id=escape_markdown(str(order.id), version=2),
        order_text=escape_markdown(order.order_text, version=2),
        order_location=escape_markdown(order.location, version=2),
        order_time=escape_markdown(format_order_time(order), version=2),
        order_details=escape_markdown(order.details, version=2),
        delivery_fee=escape_markdown(order.delivery_fee, version=2),
        claim_status=escape_markdown(claim_status, version=2)
    )

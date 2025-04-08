import os
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from models.order_model import Order
from models.database import session_local, SGT
from utils.utils import get_main_menu
from views import messages

async def view_orders(update: Update, context: CallbackContext):
    """
    Handles the /vieworders command to show available orders.
    """
    message = update.message if update.message else update.callback_query.message
    now = datetime.now(SGT)
    session = session_local()
    orders = session.query(Order).filter(
        Order.claimed == False,
        Order.expired == False,
        Order.latest_pickup_time > now
    ).order_by(Order.earliest_pickup_time.asc()).all()
    session.close()

    if orders:
        order_list = []
        for o in orders:
            time_str = (
                f"{o.earliest_pickup_time.astimezone(SGT).strftime('%A, %m-%d %I:%M%p')} - "
                f"{o.latest_pickup_time.astimezone(SGT).strftime('%I:%M%p')}"
            )
            order_text = (
                f"📌 *Order ID:* {escape_markdown(str(o.id), version=2)}\n"
                f"🍽 *Meal:* {escape_markdown(o.order_text, version=2)}\n"
                f"📍 *Location:* {escape_markdown(o.location, version=2)}\n"
                f"⏳ *Time:* {escape_markdown(time_str, version=2)}\n"
                f"ℹ️ *Details:* {escape_markdown(o.details, version=2)}\n"
                f"💸 *Delivery Fee:* ${escape_markdown(o.delivery_fee, version=2)}\n"
            )
            order_list.append(order_text)

        for i in range(0, len(order_list), 10):
            chunk = "\n".join(order_list[i:i+10])
            await message.reply_text(
                f"Available Orders:\n\n{chunk}",
                parse_mode="MarkdownV2",
                reply_markup=get_main_menu()
            )
    else:
        await message.reply_text(
            messages.NO_ORDERS_AVAILABLE,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
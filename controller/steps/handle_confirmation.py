from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_orders, user_states
from models.database import SGT

async def handle_confirmation_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Retrieve order data for the user
    order_data = user_orders.get(user_id)
    if not order_data:
        await update.message.reply_text(
            "No order data found. Please start your order again.",
            reply_markup=get_main_menu()
        )
        return

    # Format the pickup time range
    earliest_time = order_data['earliest_dt'].astimezone(SGT).strftime('%A %m-%d %I:%M%p')
    latest_time = order_data['latest_dt'].astimezone(SGT).strftime('%m-%d %I:%M%p')
    order_time_str = f"{earliest_time} - {latest_time}"

    # Build the order summary using the ORDER_SUMMARY message from views/messages.py
    order_summary = messages.ORDER_SUMMARY.format(
        order_text=escape_markdown(order_data.get('meal', ''), version=2),
        order_location=escape_markdown(order_data.get('location', ''), version=2),
        order_time=escape_markdown(order_time_str, version=2),
        order_details=escape_markdown(order_data.get('details', ''), version=2),
        delivery_fee=escape_markdown(order_data.get('delivery_fee', ''), version=2)
    )

    # Create inline buttons for confirming or canceling the order
    keyboard = [
        [InlineKeyboardButton("Confirm Order", callback_data=f"confirm_order_{user_id}")],
        [InlineKeyboardButton("Cancel Order", callback_data=f"cancel_order_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(order_summary, parse_mode="MarkdownV2", reply_markup=reply_markup)
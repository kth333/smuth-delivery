from telegram import Update
from telegram.ext import CallbackContext
from datetime import datetime, timedelta
from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_states, user_orders
from controllers.time_validation import validate_strict_time_format
from models.database import SGT

async def handle_earliest_time_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    earliest_dt = validate_strict_time_format(text)
    if not earliest_dt:
        await update.message.reply_text(
            "Invalid time format. Please use MM-DD HH:MMam/pm.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return False
    now = datetime.now(SGT)
    if earliest_dt < now or earliest_dt > now + timedelta(days=7):
        await update.message.reply_text(
            "Earliest pickup time must be in the future and within the next 7 days.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return False
    user_orders.setdefault(user_id, {})['earliest_dt'] = earliest_dt
    user_orders[user_id]['earliest_input'] = text
    user_states[user_id]['state'] = 'awaiting_order_latest_time'
    await update.message.reply_text(
        messages.ORDER_INSTRUCTIONS_LATEST_TIME,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    return True
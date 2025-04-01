from telegram import Update
from telegram.ext import CallbackContext
from datetime import timedelta
from utils.utils import get_main_menu, get_cancel_keyboard
from views import messages
from controllers.order_state import user_states, user_orders
from controllers.time_validation import validate_strict_time_format

async def handle_latest_time_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    latest_dt = validate_strict_time_format(text)
    if not latest_dt:
        await update.message.reply_text(
            "Invalid time format. Please use MM-DD HH:MMam/pm.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return False
    earliest_dt = user_orders[user_id]['earliest_dt']
    if latest_dt <= earliest_dt or latest_dt - earliest_dt > timedelta(hours=3):
        await update.message.reply_text(
            "Latest pickup time must be after the earliest time and within 3 hours.",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard(user_id)
        )
        return False
    user_orders[user_id]['latest_dt'] = latest_dt
    user_orders[user_id]['latest_input'] = text
    user_states[user_id]['state'] = 'awaiting_order_details'
    await update.message.reply_text(
        messages.ORDER_INSTRUCTIONS_DETAILS,
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(user_id)
    )
    return True
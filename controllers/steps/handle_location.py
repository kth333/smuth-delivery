from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_states, user_orders

async def handle_location_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text or len(text) > 100:
        await update.message.reply_text(
            messages.ORDER_TOO_LONG.format(max_length=100, order_length=len(text)),
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return False
    user_orders.setdefault(user_id, {})['location'] = text
    user_states[user_id]['state'] = 'awaiting_order_earliest_time'
    await update.message.reply_text(
        messages.ORDER_INSTRUCTIONS_EARLIEST_TIME,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    return True

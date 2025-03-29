from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_states, user_orders

async def handle_meal_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text or len(text) > 100:
        await update.message.reply_text(
            messages.ORDER_TOO_LONG.format(max_length=100, order_length=len(text)),
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return False
    user_orders.setdefault(user_id, {})['meal'] = text
    user_states[user_id]['state'] = 'awaiting_order_location'
    await update.message.reply_text(
        messages.ORDER_INSTRUCTIONS_LOCATION,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    return True
from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_cancel_keyboard
from views import messages
from controllers.order_state import user_states, user_orders

async def handle_details_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if not text or len(text) > 500:
        await update.message.reply_text(
            messages.ORDER_DETAILS_TOO_LONG.format(max_length=500, order_length=len(text)),
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard(user_id)
        )
        return False
    user_orders.setdefault(user_id, {})['details'] = text
    user_states[user_id]['state'] = 'awaiting_order_delivery_fee'
    await update.message.reply_text(
        messages.ORDER_INSTRUCTIONS_FEE,
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(user_id)
    )
    return True
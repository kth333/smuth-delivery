from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu
from controllers.order_state import user_states, user_orders

async def handle_fee_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    try:
        fee_amount = float(text)
        if fee_amount < 1.0:
            await update.message.reply_text(
                "Delivery fee must be at least $1.00.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return False
    except ValueError:
        await update.message.reply_text(
            "Please enter a valid number for the delivery fee.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        return False
    user_orders.setdefault(user_id, {})['delivery_fee'] = text
    user_states[user_id]['state'] = 'awaiting_order_confirmation'
    return True
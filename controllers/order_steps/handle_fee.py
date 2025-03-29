from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_cancel_keyboard
from controllers.order_state import user_states, user_orders
from views import messages 

async def handle_fee_input(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if len(text) > 4:
        await update.message.reply_text(
            messages.ORDER_DETAILS_TOO_LONG.format(max_length=4, order_length=len(text)),
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard(user_id)
        )
        return
    try:
        fee_amount = float(text)
        if fee_amount < 1.0:
            await update.message.reply_text(
                "💸 Delivery fee must be at least *$1.00*. Please enter a higher amount.",
                parse_mode="Markdown",
            )
            return False
        if fee_amount > 5.0:
            await update.message.reply_text(
                "Stop the cap",
                parse_mode="Markdown",
                reply_markup=get_cancel_keyboard(user_id)
            )
            return False
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a *valid number* for the delivery fee. Example: `1.50`",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard(user_id)
        )
        return False
    user_orders.setdefault(user_id, {})['delivery_fee'] = text
    user_states[user_id]['state'] = 'awaiting_order_confirmation'
    return True
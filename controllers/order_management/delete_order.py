from telegram import Update
from telegram.ext import CallbackContext
from models.order_model import Order
from models.database import session_local
from utils.utils import get_main_menu
from controllers.order_state import user_states
from views import messages

async def delete_order(update: Update, context: CallbackContext):
    """
    Handles deletion of an order that has not yet been claimed.
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    order_id = user_states.get(user_id, {}).get("selected_order")
    if not order_id:
        await message.reply_text("No order selected. Please try again.", reply_markup=get_main_menu())
        return

    session = session_local()
    order = session.query(Order).filter_by(id=order_id).first()
    if order:
        if order.claimed:
            await message.reply_text(
                "This order has been claimed. Please contact the runner to cancel your order.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            session.close()
            return
        
        user_states[user_id]["state"] = "deleting_order"
        await message.reply_text("Please reply with YES to confirm order deletion or NO to abort.")
    else:
        await message.reply_text(
            "Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
            parse_mode="Markdown"
        )
    session.close()
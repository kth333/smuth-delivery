from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown
from models.order_model import Order
from models.database import session_local
from utils.utils import get_main_menu
from controllers.order_state import user_states
from views import messages

async def handle_my_orders(update: Update, context: CallbackContext):
    """
    Lists orders placed by the current user.
    """
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    message = update.message if update.message else update.callback_query.message
    session = session_local()
    orders = session.query(Order).filter_by(user_id=user_id, expired=False).all()
    session.close()
    
    if orders:
        order_list = [
            f"Order ID: {escape_markdown(str(o.id), version=2)}\nMeal: {escape_markdown(o.order_text, version=2)}\n"
            for o in orders
        ]
        for i in range(0, len(order_list), 10):
            chunk = "\n".join(order_list[i:i+10])
            await message.reply_text(
                f"My Orders:\n\n{chunk}",
                parse_mode="MarkdownV2"
            )
        keyboard = [[InlineKeyboardButton("Back", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        user_states[user_id] = {"state": "selecting_order_id"}
        await message.reply_text("Please enter the Order ID you want to cancel", reply_markup=reply_markup)
    else:
        await message.reply_text(
            "You do not have any orders right now. Please place an order using /order.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
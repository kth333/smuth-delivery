import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown
from models.order_model import Order
from models.database import session_local
from utils.utils import get_main_menu
from views.order_view import get_order_keyboard
from controllers.order_state import user_states

async def handle_deletion(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    order_id = user_states[user_id].get('selected_order')
    with session_local() as session:
        order = session.query(Order).filter_by(id=order_id).first()
    if order:
        response = update.message.text.strip().lower()
        if response == 'yes':
            order.expired = True
            with session_local() as session:
                session.add(order)
                session.commit()
            await message.reply_text(
                "Your order has been successfully canceled.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            bot_username = context.bot.username
            reply_markup = get_order_keyboard(bot_username, order.id)
            if order.channel_message_id:
                try:
                    cancel_msg = f"Order ID: {escape_markdown(str(order.id), version=2)}\nThis order has been canceled by the user."
                    await context.bot.edit_message_text(
                        chat_id=os.getenv("CHANNEL_ID"),
                        message_id=order.channel_message_id,
                        text=cancel_msg,
                        parse_mode="MarkdownV2",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logging.warning(f"Failed to edit deleted order message: {e}")
        elif response == 'no':
            await message.reply_text(
                "Order deletion canceled.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
    else:
        await message.reply_text(
            "Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
            parse_mode="Markdown"
        )
    user_states.pop(user_id, None)
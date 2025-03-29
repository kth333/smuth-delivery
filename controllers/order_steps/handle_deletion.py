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
    response = message.text.strip().lower()
    order_id = user_states[user_id].get('selected_order')

    with session_local() as session:
        order = session.query(Order).filter_by(id=order_id).first()

        if not order:
            await message.reply_text(
                "Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
                parse_mode="Markdown"
            )
            user_states.pop(user_id, None)
            return

        if response == 'yes':
            order.expired = True
            session.commit()

            bot_username = context.bot.username
            escaped_order_id = escape_markdown(str(order.id), version=2)
            await message.reply_text(
                "✅ Your order has been successfully canceled",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

            if order.channel_message_id:
                try:
                    cancel_msg = f"📌 *Order ID:* {escaped_order_id}\n🗑 *This order has been canceled by the user\\.*"
                    await context.bot.edit_message_text(
                        chat_id=os.getenv("CHANNEL_ID"),
                        message_id=order.channel_message_id,
                        text=cancel_msg,
                        parse_mode="MarkdownV2"
                    )
                except Exception as e:
                    logging.warning(f"Failed to edit deleted order message: {e}")

        elif response == 'no':
            await message.reply_text(
                "❌ Order deletion canceled",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

    user_states.pop(user_id, None)
import os
import logging
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from models.database import session_local, SGT
from views.order_view import get_order_keyboard, format_order_time, format_order_message
from views import messages
from utils.utils import get_main_menu
from controllers.order_state import user_states

async def perform_claim(session, order, order_id: int, update, context):
    """
    Performs the actual claim logic:
      - Updates the order in the DB,
      - Notifies the claimer,
      - Notifies the orderer,
      - Edits the channel message.
    Assumes all validations (order exists, not claimed, active claims check, etc.) have already passed.
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    user_handle = update.effective_user.username

    # Update the order record
    order.claimed = True
    order.runner_id = user_id
    order.runner_handle = user_handle
    order.order_claimed_time = datetime.now(SGT)
    session.commit()

    claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
    orderer_id = order.user_id

    # Notify the claimer
    await message.reply_text(
        messages.CLAIM_SUCCESS_MESSAGE.format(
            order_id=escape_markdown(str(order_id), version=2),
            order_text=escape_markdown(order.order_text, version=2),
            order_location=escape_markdown(order.location, version=2),
            order_time=escape_markdown(format_order_time(order), version=2),
            order_details=escape_markdown(order.details, version=2),
            delivery_fee=escape_markdown(order.delivery_fee, version=2),
            orderer_handle=escape_markdown(order.user_handle, version=2) if order.user_handle else "Unknown"
        ),
        parse_mode="MarkdownV2",
        reply_markup=get_main_menu()
    )

    # Notify the orderer if possible
    if orderer_id:
        try:
            await context.bot.send_message(
                chat_id=orderer_id,
                text=messages.ORDER_CLAIMED_NOTIFICATION.format(
                    order_id=escape_markdown(str(order_id), version=2),
                    order_text=escape_markdown(order.order_text, version=2),
                    order_location=escape_markdown(order.location, version=2),
                    order_time=escape_markdown(format_order_time(order), version=2),
                    order_details=escape_markdown(order.details, version=2),
                    delivery_fee=escape_markdown(order.delivery_fee, version=2),
                    claimed_by=escape_markdown(claimed_by, version=2)
                ),
                parse_mode="MarkdownV2",
                reply_markup=get_main_menu()
            )
        except Exception as e:
            logging.warning(f"Failed to notify orderer {orderer_id}: {e}")

    # Update the channel post with the new claim status
    bot_username = context.bot.username
    reply_markup = get_order_keyboard(bot_username, order.id)
    edited_text = format_order_message(order, "Claim Status: 🛵 This order has been claimed.")
    await context.bot.edit_message_text(
        chat_id=os.getenv("CHANNEL_ID"),
        message_id=order.channel_message_id,
        text=edited_text,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup
    )

    # Clear state
    user_states.pop(user_id, None)
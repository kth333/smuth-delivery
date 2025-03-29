import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from models.order_model import Order
from models.database import session_local, SGT
from utils.utils import get_main_menu
from controllers.order_state import user_states
from views import messages
from views.order_view import get_order_keyboard, format_order_message, format_order_time

async def cancel_claim(update: Update, context: CallbackContext):
    """
    Cancels the user's claim on an order, notifies the orderer that the claim was canceled,
    and updates the channel message to show that the order is available to claim.
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    order_id = user_states.get(user_id, {}).get("selected_order")
    if not order_id:
        await message.reply_text("No claim selected. Please try again.", reply_markup=get_main_menu())
        return

    session = session_local()
    order = session.query(Order).filter_by(id=order_id, runner_id=user_id, claimed=True).first()
    if order:
        now = datetime.now(SGT)
        if order.latest_pickup_time < now:
            await message.reply_text(
                "You cannot cancel this claim because the pickup time has already passed.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            user_states.pop(user_id, None)
            session.close()
            return

        # Update the order to mark it as not claimed.
        order.claimed = False
        order.runner_id = None
        order.runner_handle = None
        order.order_claimed_time = None
        session.add(order)
        session.commit()

        # Notify the runner (user canceling the claim)
        await message.reply_text(
            f"You have canceled your claim on Order ID {order_id}.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

        # Notify the orderer that their order's claim was canceled.
        orderer_id = order.user_id
        try:
            await context.bot.send_message(
                chat_id=orderer_id,
                text=f"Sorry, your order (ID: {order_id}) has had its claim canceled by the runner.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Failed to notify orderer {orderer_id}: {e}")

        # Update the channel message to reflect that the order is now available.
        bot_username = context.bot.username
        reply_markup = get_order_keyboard(bot_username, order.id)
        edited_text = format_order_message(order, "Claim Status: ✅ This order is available to claim.")
        try:
            await context.bot.edit_message_text(
                chat_id=os.getenv("CHANNEL_ID"),
                message_id=order.channel_message_id,
                text=edited_text,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.warning(f"Failed to update channel message for order {order_id}: {e}")
    else:
        await message.reply_text(
            "No valid claim found to cancel.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    user_states.pop(user_id, None)
    session.close()
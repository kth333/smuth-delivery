import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from models.order_model import Order
from models.database import session_local, SGT
from views.order_view import get_order_keyboard, format_order_time, format_order_message
from views import messages
from utils.utils import get_main_menu
from controllers.order_state import user_states

async def handle_claim(update: Update, context: CallbackContext):
    """
    Handles the /claim command. If an order ID is provided, processes it;
    otherwise, prompts the user to enter an order ID.
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    order_id = context.user_data.pop("claim_order_id", None)
    if order_id:
        await process_claim_order_by_id(update, context, user_id, order_id)
    elif context.args and len(context.args) > 0:
        order_id = context.args[0]
        await process_claim_order_by_id(update, context, user_id, order_id)
    else:
        user_states[user_id] = {"state": "awaiting_order_id"}
        await message.reply_text(
            messages.ORDER_ID_REQUEST,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

async def process_claim_order_by_id(update: Update, context: CallbackContext, user_id: int, order_id: str):
    """
    Processes an order claim given an order ID.
    """
    message = update.message if update.message else update.callback_query.message
    try:
        order_id = int(order_id)
    except ValueError:
        await message.reply_text(
            messages.INVALID_ORDER_ID,
            reply_markup=get_main_menu()
        )
        return

    with session_local() as session:
        order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
        if not order:
            await message.reply_text(
                messages.CLAIM_FAILED.format(order_id=order_id),
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return
        if order.user_id == user_id:
            await message.reply_text(
                "You cannot claim your own order.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return
        active_claims = session.query(Order).filter_by(runner_id=user_id, claimed=True, expired=False).count()
        if active_claims >= 2:
            await message.reply_text(
                "You have already claimed 2 active orders. Please cancel one before claiming a new one.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return

        # Process claim.
        order.claimed = True
        order.runner_id = user_id
        user_handle = update.effective_user.username
        order.runner_handle = user_handle
        order.order_claimed_time = datetime.now(SGT)
        session.commit()

        claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
        orderer_id = order.user_id

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
                    parse_mode="MarkdownV2"
                )
            except Exception as e:
                logging.warning(f"Failed to notify orderer {orderer_id}: {e}")

        bot_username = context.bot.username
        reply_markup = get_order_keyboard(bot_username, order.id)
        edited_text = format_order_message(order, "Claim Status: This order has been claimed.")
        await context.bot.edit_message_text(
            chat_id=os.getenv("CHANNEL_ID"),
            message_id=order.channel_message_id,
            text=edited_text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
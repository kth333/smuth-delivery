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
from controllers.claim_steps.perform_claim import perform_claim

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
        # if order.user_id == user_id:
        #     await message.reply_text(
        #         "⚠️ You cannot claim your own order.",
        #         parse_mode="Markdown",
        #         reply_markup=get_main_menu()
        #     )
        #     return
        # active_claims = session.query(Order).filter_by(runner_id=user_id, claimed=True, expired=False).count()
        # if active_claims >= 2:
        #     await message.reply_text(
        #         "🚫 You have already claimed 2 active orders. Please cancel one before claiming a new one.",
        #         parse_mode="Markdown",
        #         reply_markup=get_main_menu()
        #     )
        #     return

        # Now that all checks pass, call the helper to perform the claim.
        await perform_claim(session, order, order_id, update, context)
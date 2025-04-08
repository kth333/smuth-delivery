import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from models.order_model import Order
from models.database import session_local, SGT
from controllers.order_state import user_states
from utils.utils import get_main_menu
from views import messages

async def start(update: Update, context: CallbackContext):
    """
    Handles the /start command. If a claim argument is provided (e.g. "claim_123"),
    it retrieves the order and sends a confirmation prompt. Otherwise, it shows
    the welcome text.
    """
    user_id = update.effective_user.id
    args = context.args if context.args else []
    message = update.message if update.message else update.callback_query.message

    keyboard = [[InlineKeyboardButton("Back", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if args and args[0].startswith("claim_"):
        order_id = args[0].split("_")[1]
        session = session_local()
        order = session.query(Order).filter_by(id=order_id, claimed=False).first()
        session.close()

        if order:
            user_states[user_id] = {"state": "awaiting_claim_confirmation", "order_id": int(order_id)}
            order_time = escape_markdown(
                f"{order.earliest_pickup_time.astimezone(SGT).strftime('%A, %m-%d %I:%M%p')} - "
                f"{order.latest_pickup_time.astimezone(SGT).strftime('%I:%M%p')}",
                version=2
            )
            await message.reply_text(
                messages.CLAIM_CONFIRMATION.format(
                    order_id=escape_markdown(str(order_id), version=2),
                    order_text=escape_markdown(order.order_text, version=2),
                    order_location=escape_markdown(order.location, version=2),
                    order_time=order_time,
                    order_details=escape_markdown(order.details, version=2),
                    delivery_fee=escape_markdown(order.delivery_fee, version=2)
                ),
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )
        else:
            await message.reply_text(
                messages.CLAIM_FAILED.format(order_id=order_id),
                reply_markup=get_main_menu()
            )
    else:
        await message.reply_text(
            messages.WELCOME_TEXT,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

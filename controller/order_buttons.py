import os
from telegram import Update
from telegram.ext import CallbackContext
from controllers.order_conversation import handle_conversation, handle_order, handle_my_orders, handle_my_claims
from controllers.order_claim import handle_claim
from controllers.order_state import user_states, user_orders
from utils.utils import get_main_menu
from views.order_view import get_order_keyboard, format_order_message, format_order_time
from views import messages
from models.order_model import Order
from models.database import session_local, SGT
from telegram.helpers import escape_markdown
from datetime import datetime

async def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    callback_data = query.data

    if callback_data.startswith("confirm_order_"):
        new_order = Order(
            order_text=user_orders[user_id]['meal'],
            location=user_orders[user_id]['location'],
            earliest_pickup_time=user_orders[user_id]['earliest_dt'],
            latest_pickup_time=user_orders[user_id]['latest_dt'],
            details=user_orders[user_id]['details'],
            delivery_fee=user_orders[user_id]['delivery_fee'],
            user_id=user_id,
            user_handle=query.from_user.username,
            order_placed_time=datetime.now(SGT)
        )
        with session_local() as session:
            session.add(new_order)
            session.commit()
            bot_username = context.bot.username
            reply_markup = get_order_keyboard(bot_username, new_order.id)
            sent_message = await context.bot.send_message(
                chat_id=os.getenv("CHANNEL_ID"),
                text=messages.ORDER_PLACED.format(
                    order_id=escape_markdown(str(new_order.id), version=2),
                    order_text=escape_markdown(new_order.order_text, version=2),
                    order_location=escape_markdown(new_order.location, version=2),
                    order_time=escape_markdown(format_order_time(new_order), version=2),
                    order_details=escape_markdown(new_order.details, version=2),
                    delivery_fee=escape_markdown(new_order.delivery_fee, version=2)
                ),
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )
            new_order.channel_message_id = sent_message.message_id
            session.commit()
        del user_states[user_id]
        del user_orders[user_id]
        await query.message.edit_text(
            messages.ORDER_PLACED.format(
                order_id=escape_markdown(str(new_order.id), version=2),
                order_text=escape_markdown(new_order.order_text, version=2),
                order_location=escape_markdown(new_order.location, version=2),
                order_time=escape_markdown(format_order_time(new_order), version=2),
                order_details=escape_markdown(new_order.details, version=2),
                delivery_fee=escape_markdown(new_order.delivery_fee, version=2)
            ),
            parse_mode="MarkdownV2",
            reply_markup=get_main_menu()
        )
    elif callback_data.startswith("cancel_order_"):
        del user_states[user_id]
        del user_orders[user_id]
        await query.message.edit_text(
            "Your order has been canceled. To place a new order, please use the menu.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    elif callback_data == 'start':
        await handle_order(update, context)
    elif callback_data == 'order':
        await handle_order(update, context)
    elif callback_data == 'vieworders':
        await handle_my_orders(update, context)
    elif callback_data == 'claim':
        await handle_claim(update, context)
    elif callback_data == 'myorders':
        await handle_my_orders(update, context)
    elif callback_data == 'myclaims':
        await handle_my_claims(update, context)
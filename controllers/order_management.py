import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from models.order_model import Order
from models.database import session_local, SGT
from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_states

async def view_orders(update: Update, context: CallbackContext):
    """
    Handles the /vieworders command to show available orders.
    """
    message = update.message if update.message else update.callback_query.message
    now = datetime.now(SGT)
    session = session_local()
    orders = session.query(Order).filter(
        Order.claimed == False,
        Order.latest_pickup_time > now
    ).order_by(Order.earliest_pickup_time.asc()).all()
    session.close()

    if orders:
        order_list = []
        for o in orders:
            time_str = (
                f"{o.earliest_pickup_time.astimezone(SGT).strftime('%A %m-%d %I:%M%p')} - "
                f"{o.latest_pickup_time.astimezone(SGT).strftime('%A %m-%d %I:%M%p')}"
            )
            order_text = (
                f"Order ID: {escape_markdown(str(o.id), version=2)}\n"
                f"Meal: {escape_markdown(o.order_text, version=2)}\n"
                f"Location: {escape_markdown(o.location, version=2)}\n"
                f"Time: {escape_markdown(time_str, version=2)}\n"
                f"Details: {escape_markdown(o.details, version=2)}\n"
                f"Delivery Fee: {escape_markdown(o.delivery_fee, version=2)}\n"
            )
            order_list.append(order_text)

        for i in range(0, len(order_list), 10):
            chunk = "\n".join(order_list[i:i+10])
            await message.reply_text(
                f"Available Orders:\n\n{chunk}",
                parse_mode="MarkdownV2",
                reply_markup=get_main_menu()
            )
    else:
        await message.reply_text(
            messages.NO_ORDERS_AVAILABLE,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

async def handle_my_orders(update: Update, context: CallbackContext):
    """
    Lists orders placed by the current user.
    """
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    message = update.message if update.message else update.callback_query.message
    session = session_local()
    orders = session.query(Order).filter_by(user_id=user_id).all()
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
    else:
        await message.reply_text(
            "You do not have any orders right now. Please place an order using /order.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    
    keyboard = [[InlineKeyboardButton("Back", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_states[user_id] = {"state": "selecting_order_id"}
    await message.reply_text("Please enter the Order ID", reply_markup=reply_markup)

async def handle_my_claims(update: Update, context: CallbackContext):
    """
    Lists orders that the current user has claimed.
    """
    user_id = update.effective_user.id if update.message else update.callback_query.from_user.id
    message = update.message if update.message else update.callback_query.message
    session = session_local()
    orders = session.query(Order).filter_by(runner_id=user_id, claimed=True, expired=False).all()
    session.close()

    if orders:
        order_list = [
            f"Order ID: {escape_markdown(str(o.id), version=2)}\nMeal: {escape_markdown(o.order_text, version=2)}\n"
            for o in orders
        ]
        for i in range(0, len(order_list), 10):
            chunk = "\n".join(order_list[i:i+10])
            await message.reply_text(
                f"My Claims:\n\n{chunk}",
                parse_mode="MarkdownV2"
            )
    else:
        await message.reply_text(
            "You haven't claimed any orders yet. Check /vieworders for available orders.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    
    keyboard = [[InlineKeyboardButton("Back", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_states[user_id] = {"state": "selecting_claimed_order"}
    await message.reply_text("Please enter the Order ID you want to cancel claim for:", reply_markup=reply_markup)

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
                "This order has been claimed. Please contact the runner to delete your order.",
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

async def cancel_claim(update: Update, context: CallbackContext):
    """
    Cancels the user's claim on an order.
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
        order.claimed = False
        order.runner_id = None
        order.runner_handle = None
        order.order_claimed_time = None
        session.add(order)
        session.commit()
        await message.reply_text(
            f"You have canceled your claim on Order ID {order_id}.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await message.reply_text(
            "No valid claim found to cancel.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    user_states.pop(user_id, None)
    session.close()
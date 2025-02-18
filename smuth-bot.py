from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    user = Column(String, nullable=False)
    claimed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

user_states = {}

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("Place Order", callback_data='order')],
        [InlineKeyboardButton("View Orders", callback_data='vieworders')],
        [InlineKeyboardButton("Claim Order", callback_data='claim')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to Smuth Delivery! Use the buttons below to interact.", reply_markup=get_main_menu())
    await view_orders(update, context)

async def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'order':
        await handle_order(update, context)
    elif query.data == 'vieworders':
        await view_orders(update, context)
    elif query.data == 'claim':
        await handle_claim(update, context)
    elif query.data == 'help':
        await help_command(update, context)

async def handle_order(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_order'
    await update.effective_message.reply_text("Please type your order now, including your preferred menu, delivery time, and location.", 
    reply_markup=get_main_menu())

async def handle_claim(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_claim'
    await update.effective_message.reply_text("Please type the order ID you want to claim.", reply_markup=get_main_menu())

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        return
    session = session_local()
    state = user_states.pop(user_id)
    if state == 'awaiting_order':
        new_order = Order(order_text=update.message.text, user=update.message.from_user.username)
        session.add(new_order)
        session.commit()
        await update.message.reply_text(f'Order received (ID: {new_order.id}): "{new_order.order_text}"', reply_markup=get_main_menu())
    elif state == 'awaiting_claim':
        try:
            order_id = int(update.message.text)
            order = session.query(Order).filter_by(id=order_id, claimed=False).first()
            if order:
                order.claimed = True
                session.commit()
                await update.message.reply_text(f'Order {order_id} claimed by @{update.message.from_user.username}.', reply_markup=get_main_menu())
            else:
                await update.message.reply_text("Order not found or already claimed.", reply_markup=get_main_menu())
        except ValueError:
            await update.message.reply_text("Invalid order ID.", reply_markup=get_main_menu())
    session.close()

async def view_orders(update: Update, context: CallbackContext):
    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    if orders:
        message = "Available Orders:\n" + "\n".join([f'ID: {o.id} - {o.order_text} (User: @{o.user})' for o in orders])
    else:
        message = "No orders to be claimed right now!"
    await update.callback_query.message.reply_text(message, reply_markup=get_main_menu())
    session.close()

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Start the bot\n"
        "/order - Place an order\n"
        "/vieworders - View all available orders\n"
        "/claim - Claim an order\n"
        "/help - Show this help message"
    )
    await update.effective_message.reply_text(help_text, reply_markup=get_main_menu())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", handle_order))
    app.add_handler(CommandHandler("vieworders", view_orders))
    app.add_handler(CommandHandler("claim", handle_claim))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.run_polling()

if __name__ == '__main__':
    main()

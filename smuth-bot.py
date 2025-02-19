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

# To track user interaction states
user_states = {}

# Function to generate the main menu keyboard
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("Place Order", callback_data='order')],
        [InlineKeyboardButton("View Orders", callback_data='vieworders')],
        [InlineKeyboardButton("Claim Order", callback_data='claim')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Handles the /start command and displays the main menu
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to Smuth Delivery! Use the buttons below to interact.", reply_markup=get_main_menu())
    await view_orders(update, context)

async def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    actions = {
        'order': handle_order,
        'vieworders': view_orders,
        'claim': handle_claim,
        'help': help_command
    }
    await actions[query.data](update, context)

# Handles the /order command and asks for the order
async def handle_order(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_order'
    await update.effective_message.reply_text("Please type your order now, including your preferred menu, delivery time, and location.", reply_markup=get_main_menu())

# Handles the /claimm command and asks for the order ID to claim
async def handle_claim(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_claim'
    await update.effective_message.reply_text("Please type the order ID you want to claim.", reply_markup=get_main_menu())

# Handles incoming text messages based on user states
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        await update.message.reply_text("Need help? Type /help or click on the 'Help' below", reply_markup=get_main_menu())
        return
    
    session = session_local()
    state = user_states.pop(user_id)
    
    if state == 'awaiting_order':
        new_order = Order(order_text=update.message.text, user=update.message.from_user.username or 'UnknownUser')
        session.add(new_order)
        session.commit()
        await update.message.reply_text(f'Order received (ID: {new_order.id}): "{new_order.order_text}"', reply_markup=get_main_menu())
    
    elif state == 'awaiting_claim':
        try:
            order_id = int(update.message.text)
            order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
            
            if order:
                order.claimed = True
                session.commit()
                await update.message.reply_text(f'Order {order_id} claimed by @{update.message.from_user.username or "UnknownUser"}.', reply_markup=get_main_menu())
            else:
                await update.message.reply_text("Order not found or already claimed.", reply_markup=get_main_menu())
        except ValueError:
            await update.message.reply_text("Invalid order ID.", reply_markup=get_main_menu())
    
    session.close()

# Displays available orders that haven't been claimed yet
async def view_orders(update: Update, context: CallbackContext):
    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    session.close()
    
    if orders:
        message = "Available Orders:\n" + "\n".join([f'ID: {o.id} - {o.order_text} (User: @{o.user})' for o in orders])
    else:
        message = "No orders to be claimed right now!"    
    if update.callback_query:
        await update.callback_query.message.reply_text(message, reply_markup=get_main_menu())
    else:
        await update.message.reply_text(message, reply_markup=get_main_menu())

# Handles the /help command to provide users with available commands
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Start the bot\n"
        "/order - Place an order\n"
        "/vieworders - View all available orders\n"
        "/claim - Claim an order\n"
        "/help - Show this help message"
    )
    await update.effective_message.reply_text(help_text, reply_markup=get_main_menu())

# Entry point of the bot, initializes handlers and starts polling
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
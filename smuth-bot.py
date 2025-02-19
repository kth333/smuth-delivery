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
    args = context.args if context.args else []  # Ensure args is always a list

    if args and args[0].startswith("claim_"):
        try:
            order_id = int(args[0].split("_")[1])  # Extract order ID

            session = session_local()
            order = session.query(Order).filter_by(id=order_id, claimed=False).first()
            session.close()

            if order:
                order_details = f"Order ID: {order.id}\nDetails: {order.order_text}"
                user_states[update.effective_user.id] = 'awaiting_claim'
                await update.message.reply_text(
                    f"You're about to claim the following order:\n\n{order_details}\n\nPlease confirm by sending the order ID.",
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text("Sorry, this order has already been claimed or does not exist.", reply_markup=get_main_menu())

        except (IndexError, ValueError):  # Handle invalid claim IDs
            await update.message.reply_text("Invalid order claim request.", reply_markup=get_main_menu())

    else:
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

CHANNEL_ID = os.getenv("CHANNEL_ID")

# Handles the /claim command and asks for the order ID to claim
async def handle_claim(update: Update, context: CallbackContext):
    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    session.close()

    if not orders:
        await update.message.reply_text("No available orders to claim at the moment.", reply_markup=get_main_menu())
        return

    order_list = "\n".join([f"ID: {o.id} - {o.order_text}" for o in orders])

    # Limit to 10 orders per message (to avoid exceeding Telegram's limits)
    order_chunks = [order_list[i:i+10] for i in range(0, len(order_list), 10)]
    
    for chunk in order_chunks:
        await update.message.reply_text(f"Available Orders to Claim:\n{chunk}\n\nPlease type the Order ID you want to claim.")

    user_states[update.effective_user.id] = 'awaiting_claim'

# Handles incoming text messages based on user states
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        await update.message.reply_text("Need help? Type /help or click on the 'Help' below", reply_markup=get_main_menu())
        return

    session = session_local()
    state = user_states.pop(user_id)

    try:
        if state == 'awaiting_order':
            new_order = Order(order_text=update.message.text, user=update.message.from_user.username or 'UnknownUser')
            session.add(new_order)
            session.commit()

            await update.message.reply_text(
                f"Order received (ID: {new_order.id})",
                reply_markup=get_main_menu()
            )

            bot_username = context.bot.username
            keyboard = [[InlineKeyboardButton("Claim This Order", url=f"https://t.me/{bot_username}?start=claim_{new_order.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = f"New order placed.\nOrder ID: {new_order.id}\nDetails: {new_order.order_text}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message, reply_markup=reply_markup)

        elif state == 'awaiting_claim':
            try:
                order_id = int(update.message.text)
                order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

                if order:
                    order.claimed = True
                    session.commit()

                    user_handle = update.message.from_user.username
                    claimed_by = f"@{user_handle}" if user_handle else "an unknown user"

                    await update.message.reply_text(
                        f"Order {order_id} has been claimed.\n\nDetails: {order.order_text}",
                        reply_markup=get_main_menu()
                    )

                    message = f"Order {order_id} has been claimed by {claimed_by}.\n\nDetails: {order.order_text}"
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=message)

                else:
                    await update.message.reply_text("Order not found or already claimed.", reply_markup=get_main_menu())

            except ValueError:
                await update.message.reply_text("Invalid order ID.", reply_markup=get_main_menu())

    except Exception as e:
        await update.message.reply_text("An error occurred. Please try again later.")
        print(f"Error: {e}")

    finally:
        session.close()

# Displays available orders that haven't been claimed yet
async def view_orders(update: Update, context: CallbackContext):
    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    session.close()

    if not orders:
        message = "No orders to be claimed right now!"
    else:
        chunks = []
        order_texts = [f'ID: {o.id} - {o.order_text}' for o in orders]

        # Send orders in multiple messages if they exceed 20 entries (avoiding Telegram's message limit)
        for i in range(0, len(order_texts), 20):
            chunks.append("\n".join(order_texts[i:i+20]))

        for chunk in chunks:
            await update.message.reply_text(f"Available Orders:\n{chunk}", reply_markup=get_main_menu())

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
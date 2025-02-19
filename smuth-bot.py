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

# Maximum allowed characters for an order
MAX_ORDER_LENGTH = 500

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    claimed = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=False)  # Store Telegram numeric ID
    user_handle = Column(String, nullable=True)  # Store Telegram username

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
            order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
            session.close()

            if order:
                order_details = f"Order ID: {order.id}\nDetails: {order.order_text}"
                # Save the order ID for confirmation in user states
                user_states[update.effective_user.id] = {'state': 'awaiting_confirmation', 'order_id': order.id}
                print(f"User {update.effective_user.id} is in 'awaiting_confirmation' state. Order ID: {order.id}")
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
    user_states[update.effective_user.id] = {'state': 'awaiting_order'}
    print(f"User {update.effective_user.id} is in 'awaiting_order' state.")
    await update.effective_message.reply_text("Please type your order now, including your preferred menu, delivery time, and location.", reply_markup=get_main_menu())

CHANNEL_ID = os.getenv("CHANNEL_ID")

# Handles the /claim command and asks for the order ID to claim
async def handle_claim(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    print(f"User {user_id} is interacting with the claim flow.")

    # If it's a /claim command (text-based)
    if update.message:
        # If there are arguments provided (e.g., /claim <order_id>)
        if context.args:
            try:
                order_id = int(context.args[0])  # Extract order ID from command args
                session = session_local()
                try:
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

                    if order:
                        order.claimed = True
                        session.commit()

                        user_handle = update.message.from_user.username
                        claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                        orderer_id = order.user_id

                        if user_id in user_states:
                            del user_states[user_id]

                        # Notify the claimer
                        message = f"Order {order_id} has been claimed successfully. We have notified the orderer with your telegram handle.\nDetails: {order.order_text}"
                        await update.message.reply_text(message, reply_markup=get_main_menu())

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=f"Your order (ID: {order_id}) has been claimed by {claimed_by}.\n\nDetails: {order.order_text}"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        # Send a message to the channel
                        bot_username = context.bot.username
                        keyboard = [
                        [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        channel_message = f"Order {order_id} has been claimed.\n\nDetails: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_message, reply_markup=reply_markup)

                    else:
                        message = "This order is either already claimed or doesn't exist."
                        await update.message.reply_text(message, reply_markup=get_main_menu())
                finally:
                    session.close()

            except ValueError:
                message = "Invalid order ID. Please enter a valid number."
                await update.message.reply_text(message, reply_markup=get_main_menu())

        else:
            # If no ID is provided, prompt the user to enter the order ID they want to claim
            user_states[user_id] = {'state': 'awaiting_order_id'}
            await update.message.reply_text(
                "Please enter the Order ID you want to claim:",
                reply_markup=get_main_menu()
            )

    # If it's an inline button press (callback query)
    elif update.callback_query:
        query_data = update.callback_query.data

        # If the user clicked the "Claim Order" button (without order ID)
        if query_data == "claim":
            user_states[user_id] = {'state': 'awaiting_order_id'}
            await update.callback_query.message.reply_text(
                "Please enter the Order ID you want to claim:",
                reply_markup=get_main_menu()
            )
            await update.callback_query.answer()  # Acknowledge the callback query

        # If the user clicked the "Claim This Order" button (with order ID)
        elif query_data.startswith("claim_"):
            try:
                order_id = int(query_data.split("_")[1])  # Extract order ID from the callback data
                session = session_local()
                try:
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

                    if order:
                        order.claimed = True
                        session.commit()

                        user_handle = update.callback_query.from_user.username
                        claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                        orderer_id = order.user_id

                        if user_id in user_states:
                            del user_states[user_id]

                        # Notify the claimer
                        message = f"Order {order_id} has been claimed successfully. We have notified the orderer with your telegram handle.\nDetails: {order.order_text}"
                        await update.callback_query.message.reply_text(message, reply_markup=get_main_menu())

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=f"Your order (ID: {order_id}) has been claimed by {claimed_by}.\n\nDetails: {order.order_text}"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        # Send a message to the channel
                        bot_username = context.bot.username
                        keyboard = [
                        [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        channel_message = f"Order {order_id} has been claimed.\n\nDetails: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_message, reply_markup=reply_markup)

                    else:
                        message = "This order is either already claimed or doesn't exist."
                        await update.callback_query.message.reply_text(message, reply_markup=get_main_menu())

                finally:
                    session.close()

            except (ValueError, IndexError):
                message = "Invalid order ID."
                await update.callback_query.message.reply_text(message, reply_markup=get_main_menu())
            await update.callback_query.answer()  # Acknowledge the callback query

# Handles incoming text messages based on user states
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    print(f"User {user_id} is sending a message. Current state: {user_states.get(user_id)}")

    # Check if the user has an active state (awaiting confirmation or awaiting claim)
    if user_id not in user_states:
        await update.message.reply_text("Need help? Type /help or click on the 'Help' below", reply_markup=get_main_menu())
        return

    state_data = user_states.get(user_id)
    if not state_data:
        await update.message.reply_text("Something went wrong. Please try again later.", reply_markup=get_main_menu())
        return

    state = state_data['state']
    session = session_local()

    try:
        if state == 'awaiting_order':
            # User is typing an order
            order_text = update.message.text
            print(f"User {user_id} typed the order: {order_text}")  # Debug print for order text

            # Check if the order exceeds the maximum length
            if len(order_text) > MAX_ORDER_LENGTH:
                await update.message.reply_text(
                    f"Your order is too long. Please limit your order to {MAX_ORDER_LENGTH} characters. Your order was {len(order_text)} characters long.",
                    reply_markup=get_main_menu()
                )
                return  # Stop processing this message if it's too long

            # Save the order if it's within the character limit
            new_order = Order(order_text=order_text, user_id=update.message.from_user.id, user_handle=update.message.from_user.username)
            session.add(new_order)
            session.commit()

            if user_id in user_states:
                del user_states[user_id]

            await update.message.reply_text(
                f"Order received (ID: {new_order.id})",
                reply_markup=get_main_menu()
            )

            bot_username = context.bot.username
            keyboard = [
                [InlineKeyboardButton("Claim This Order", url=f"https://t.me/{bot_username}?start=claim_{new_order.id}")],
                [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = f"New order placed.\nOrder ID: {new_order.id}\nDetails: {new_order.order_text}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message, reply_markup=reply_markup)

        elif state == 'awaiting_confirmation':
            # Check if the order ID matches the one the user is trying to claim
            try:
                order_id = int(update.message.text)  # The user types the order ID
                stored_order_id = state_data['order_id']

                if order_id == stored_order_id:
                    # Proceed with the claim
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
                    if order:
                        order.claimed = True
                        session.commit()

                        user_handle = update.message.from_user.username
                        claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                        orderer_id = order.user_id

                        if user_id in user_states:
                            del user_states[user_id]

                        # Notify the claimer
                        message = f"Order {order_id} has been claimed successfully. We have notified the orderer with your telegram handle.\nDetails: {order.order_text}"
                        await update.message.reply_text(message, reply_markup=get_main_menu())

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=f"Your order (ID: {order_id}) has been claimed by {claimed_by}.\n\nDetails: {order.order_text}"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        bot_username = context.bot.username
                        keyboard = [
                        [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        # Send a message to the channel
                        channel_message = f"Order {order_id} has been claimed.\n\nDetails: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_message, reply_markup=reply_markup)

                    else:
                        await update.message.reply_text("This order is no longer available or has been claimed.", reply_markup=get_main_menu())
                else:
                    await update.message.reply_text("The order ID does not match the one you were asked to confirm. Please try again.", reply_markup=get_main_menu())

            except ValueError:
                await update.message.reply_text("Invalid order ID. Please enter a valid number.", reply_markup=get_main_menu())

        elif state == 'awaiting_order_id':
            # Check if the user is entering the order ID for claiming
            try:
                order_id = int(update.message.text)  # The user types the order ID
                try:
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

                    if order:
                        order.claimed = True
                        session.commit()

                        user_handle = update.message.from_user.username
                        claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                        orderer_id = order.user_id

                        if user_id in user_states:
                            del user_states[user_id]

                        # Notify the claimer
                        message = f"Order {order_id} has been claimed successfully. We have notified the orderer with your telegram handle.\nDetails: {order.order_text}"
                        await update.message.reply_text(message, reply_markup=get_main_menu())

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=f"Your order (ID: {order_id}) has been claimed by {claimed_by}.\n\nDetails: {order.order_text}"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        bot_username = context.bot.username
                        keyboard = [
                        [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        # Send a message to the channel
                        message = f"Order {order_id} has been claimed.\n\nDetails: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=message, reply_markup=reply_markup)

                    else:
                        message = "This order is either already claimed or doesn't exist."
                        await update.message.reply_text(message, reply_markup=get_main_menu())

                finally:
                    session.close()

            except ValueError:
                message = "Invalid order ID. Please enter a valid number."
                await update.message.reply_text(message, reply_markup=get_main_menu())

    except Exception as e:
        await update.message.reply_text("An error occurred. Please try again later.")
        print(f"Error: {e}")  # Debugging logs

    finally:
        session.close()

# Displays available orders that haven't been claimed yet
async def view_orders(update: Update, context: CallbackContext):
    # Determine if it's a message (command) or a callback query (button press)
    if update.message:
        # Handle /vieworders command
        user_message = update.message
    elif update.callback_query:
        # Handle inline button press
        user_message = update.callback_query.message
        await update.callback_query.answer()  # Acknowledge the callback query
    
    # Query the database to get available orders
    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    session.close()

    # Initialize the message variable
    if orders:
        chunks = []
        order_texts = [f'ID: {o.id} - {o.order_text}' for o in orders]

        # Send orders in multiple messages if they exceed 20 entries (avoiding Telegram's message limit)
        for i in range(0, len(order_texts), 20):
            chunks.append("\n".join(order_texts[i:i+20]))

        # Send each chunk to the user
        for chunk in chunks:
            await user_message.reply_text(f"Available Orders:\n{chunk}", reply_markup=get_main_menu())
    else:
        await user_message.reply_text("No orders to be claimed right now!", reply_markup=get_main_menu())

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
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
    """Handles the /start command and provides detailed onboarding instructions."""
    user_id = update.effective_user.id
    args = context.args if context.args else []  # Ensure args is always a list

    if args and args[0].startswith("claim_"):
        try:
            order_id = int(args[0].split("_")[1])  # Extract order ID

            session = session_local()
            order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
            session.close()

            if order:
                order_details = f"🍱 *Order ID:* {order.id}\n📌 *Details:* {order.order_text}"
                # Save the order ID for confirmation in user states
                user_states[user_id] = {'state': 'awaiting_confirmation', 'order_id': order.id}
                await update.message.reply_text(
                    f"*You're about to claim an order!*\n\n{order_details}\n\n"
                    "✅ Please confirm by *sending the order ID* below.",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
            else:
                if user_id in user_states:
                    del user_states[user_id]
                await update.message.reply_text(
                    "⚠️ Sorry, this order has already been claimed or does not exist.",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )

        except (IndexError, ValueError):  # Handle invalid claim IDs
            if user_id in user_states:
                del user_states[user_id]
            await update.message.reply_text(
                "❌ *Invalid order claim request.* Please check the order ID and try again.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

    else:
        welcome_text = (
            "👋 *Welcome to SmuthDelivery!* 🚀\n\n"
            "🎓 Designed by SMU students for SMU students, SmuthDelivery connects busy students with food runners to get meals efficiently! 🍛🥡\n\n"
            "🛠️ *How It Works:*\n"
            "1️⃣ *Order Food:* Use /order to place an order with your meal, pickup location, and time.\n"
            "2️⃣ *Claim Orders:* If you're heading to a food vendor, check /vieworders and claim available orders.\n"
            "3️⃣ *Earn Extra Income:* Deliver food for fellow students and get paid!\n"
            "4️⃣ *Pickup & Enjoy:* Get notified when your order is ready at the pickup point.\n\n"
            "💡 *Quick Commands:*\n"
            "📌 /order - Place an order\n"
            "📌 /vieworders - See available food orders\n"
            "📌 /claim or /claim <order id> - Claim an order as a runner\n"
            "📌 /help - Get assistance\n\n"
            "🔥 Start by placing an order using */order* now!"
        )

        await update.message.reply_text(
            welcome_text, parse_mode="Markdown", reply_markup=get_main_menu()
        )


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
    """Handles the /order command with step-by-step order placement instructions."""
    
    user_id = update.effective_user.id
    user_states[user_id] = {'state': 'awaiting_order'}
    print(f"User {user_id} is in 'awaiting_order' state.")

    order_instructions = (
        "📝 *Placing an Order*\n\n"
        "📌 *Please enter your order details in the following format:*\n"
        "🍽 *Meal:* Menu number 1 at King Kong Curry\n"
        "📍 *Pickup Location:* SCIS 1 SR 3-1\n"
        "⏳ *Pickup Time:* Around 1.30 PM\n\n"
        "✅ Example: *Menu number 1 at King Kong Curry, SCIS 1 SR 3-1, Around 1.30 PM*\n\n"
        "🚀 *Your order will be listed for food runners to claim!*"
    )

    await update.effective_message.reply_text(
        order_instructions, parse_mode="Markdown", reply_markup=get_main_menu()
    )

CHANNEL_ID = os.getenv("CHANNEL_ID")

# Handles the /claim command and asks for the order ID to claim
async def handle_claim(update: Update, context: CallbackContext):
    """Handles order claiming and provides clear user instructions."""
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
                        claim_success_message = (
                            f"✅ *Order {order_id} Successfully Claimed!*\n\n"
                            "📌 *Order Details:*\n"
                            f"🍽 *Meal:* {order.order_text}\n"
                            "🚀 *Next Steps:*\n"
                            "1️⃣ Buy the meal from the vendor.\n"
                            "2️⃣ Confirm purchase via the bot.\n"
                            "3️⃣ Deliver to the pickup location.\n"
                            "4️⃣ Receive your payment!\n\n"
                            "💡 Stay updated with your claimed orders for smooth transactions!"
                        )

                        await update.message.reply_text(claim_success_message, parse_mode="Markdown", reply_markup=get_main_menu())

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=(
                                        f"📢 *Your Order Has Been Claimed!*\n\n"
                                        f"📌 *Order ID:* {order_id}\n"
                                        f"🍽 *Details:* {order.order_text}\n"
                                        f"🚴 Claimed by: {claimed_by}\n\n"
                                        "📍 *Stay tuned for updates on delivery!*"
                                    ),
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        # Send a message to the channel
                        bot_username = context.bot.username
                        keyboard = [
                            [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        channel_message = f"📢 Order {order_id} has been claimed!\n\n🍽 Details: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_message, reply_markup=reply_markup)

                    else:
                        if user_id in user_states:
                            del user_states[user_id]
                        await update.message.reply_text(
                            "⚠️ This order has already been claimed or does not exist.", 
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )
                finally:
                    session.close()

            except ValueError:
                if user_id in user_states:
                    del user_states[user_id]
                await update.message.reply_text(
                    "❌ Invalid Order ID. Please enter a valid number.", 
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )

        else:
            # If no ID is provided, prompt the user to enter the order ID they want to claim
            user_states[user_id] = {'state': 'awaiting_order_id'}
            await update.message.reply_text(
                "🔍 Please enter the *Order ID* you want to claim:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

    # If it's an inline button press (callback query)
    elif update.callback_query:
        query_data = update.callback_query.data

        # If the user clicked the "Claim Order" button (without order ID)
        if query_data == "claim":
            user_states[user_id] = {'state': 'awaiting_order_id'}
            await update.callback_query.message.reply_text(
                "🔍 Please enter the *Order ID* you want to claim:",
                parse_mode="Markdown",
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
                        claim_success_message = (
                            f"✅ *Order {order_id} Successfully Claimed!*\n\n"
                            "📌 *Order Details:*\n"
                            f"🍽 *Meal:* {order.order_text}\n"
                            "🚀 *Next Steps:*\n"
                            "1️⃣ Buy the meal from the vendor.\n"
                            "2️⃣ Confirm purchase via the bot.\n"
                            "3️⃣ Deliver to the pickup location.\n"
                            "4️⃣ Receive your payment!\n\n"
                            "💡 Stay updated with your claimed orders for smooth transactions!"
                        )

                        await update.callback_query.message.reply_text(claim_success_message, parse_mode="Markdown", reply_markup=get_main_menu())

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=(
                                        f"📢 *Your Order Has Been Claimed!*\n\n"
                                        f"📌 *Order ID:* {order_id}\n"
                                        f"🍽 *Details:* {order.order_text}\n"
                                        f"🚴 Claimed by: {claimed_by}\n\n"
                                        "📍 *Stay tuned for updates on delivery!*"
                                    ),
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        # Send a message to the channel
                        bot_username = context.bot.username
                        keyboard = [
                            [InlineKeyboardButton("Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        channel_message = f"📢 Order {order_id} has been claimed!\n\n🍽 Details: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_message, reply_markup=reply_markup)

                    else:
                        if user_id in user_states:
                            del user_states[user_id]
                        await update.callback_query.message.reply_text(
                            "⚠️ This order has already been claimed or does not exist.", 
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )

                finally:
                    session.close()

            except (ValueError, IndexError):
                if user_id in user_states:
                    del user_states[user_id]
                await update.callback_query.message.reply_text(
                    "❌ Invalid Order ID. Please enter a valid number.", 
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
            await update.callback_query.answer()  # Acknowledge the callback query

# Handles incoming text messages based on user states
async def handle_message(update: Update, context: CallbackContext):
    """Processes user messages based on their current state (ordering, claiming, etc.)."""
    user_id = update.message.from_user.id
    print(f"User {user_id} is sending a message. Current state: {user_states.get(user_id)}")

    # Check if the user has an active state (awaiting order, confirmation, dispute, etc.)
    if user_id not in user_states:
        await update.message.reply_text(
            "❓ Need help? Type /help or click on 'Help' below.",
            reply_markup=get_main_menu()
        )
        return

    state_data = user_states.get(user_id)
    if not state_data:
        await update.message.reply_text(
            "⚠️ Something went wrong. Please try again later.",
            reply_markup=get_main_menu()
        )
        return

    state = state_data['state']
    session = session_local()

    try:
        if state == 'awaiting_order':
            # User is typing an order
            order_text = update.message.text.strip()
            print(f"User {user_id} typed the order: {order_text}")  # Debugging

            # Validate order length
            if len(order_text) > MAX_ORDER_LENGTH:
                await update.message.reply_text(
                    f"⚠️ Your order is too long! Please limit your order to {MAX_ORDER_LENGTH} characters.\n\n"
                    f"📝 *Your order length:* {len(order_text)} characters.",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
                return

            # Save the order
            new_order = Order(order_text=order_text, user_id=user_id, user_handle=update.message.from_user.username)
            session.add(new_order)
            session.commit()

            del user_states[user_id]  # Clear state after order placement

            # Confirm order placement
            await update.message.reply_text(
                f"✅ *Order Placed Successfully!*\n\n"
                f"📌 *Order ID:* {new_order.id}\n"
                f"🍽 *Details:* {order_text}\n\n"
                "⚡ Your order has been listed! A food runner will claim it soon.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

            # Notify food runners in the channel
            bot_username = context.bot.username
            keyboard = [
                [InlineKeyboardButton("🚴 Claim This Order", url=f"https://t.me/{bot_username}?start=claim_{new_order.id}")],
                [InlineKeyboardButton("📝 Place an Order", url=f"https://t.me/{bot_username}?start=order")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = f"📢 New Order Available\n\n📌 Order ID: {new_order.id}\n🍽 Details: {new_order.order_text}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message, reply_markup=reply_markup)

        elif state == 'awaiting_confirmation':
            # User is confirming an order claim
            try:
                order_id = int(update.message.text.strip())  # The user types the order ID
                stored_order_id = state_data['order_id']

                if order_id == stored_order_id:
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
                    if order:
                        order.claimed = True
                        session.commit()

                        user_handle = update.message.from_user.username
                        claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                        orderer_id = order.user_id

                        del user_states[user_id]  # Clear state after claiming

                        # Notify the claimer
                        await update.message.reply_text(
                            f"✅ *Order {order_id} Successfully Claimed!*\n\n"
                            "🚀 *Next Steps:*\n"
                            "1️⃣ Buy the meal from the vendor.\n"
                            "2️⃣ Confirm purchase via the bot.\n"
                            "3️⃣ Deliver to the pickup location.\n"
                            "4️⃣ Receive your payment!\n\n"
                            "💡 Stay updated with your claimed orders for a smooth experience.",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )

                        # Notify the orderer
                        if orderer_id:
                            try:
                                await context.bot.send_message(
                                    chat_id=orderer_id,
                                    text=(
                                        f"📢 *Your Order Has Been Claimed!*\n\n"
                                        f"📌 *Order ID:* {order_id}\n"
                                        f"🍽 *Details:* {order.order_text}\n"
                                        f"🚴 Claimed by: {claimed_by}\n\n"
                                        "📍 *Stay tuned for updates on delivery!*"
                                    ),
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                print(f"Failed to notify orderer @{orderer_id}: {e}")

                        # Notify the channel
                        bot_username = context.bot.username
                        keyboard = [
                            [InlineKeyboardButton("📝 Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)

                        channel_message = f"📢 Order {order_id} has been claimed!\n\n🍽 Details: {order.order_text}"
                        await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_message, reply_markup=reply_markup)

                    else:
                        del user_states[user_id]
                        await update.message.reply_text(
                            "⚠️ This order is no longer available or has been claimed.",
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )
                else:
                    del user_states[user_id]
                    await update.message.reply_text(
                        "❌ The order ID does not match the one you were asked to confirm. Please try again.",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

            except ValueError:
                del user_states[user_id]
                await update.message.reply_text(
                    "❌ Invalid Order ID. Please enter a valid number.",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )

        elif state == 'awaiting_order_id':
            # User is entering an order ID to claim
            try:
                order_id = int(update.message.text.strip())

                order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()
                if order:
                    order.claimed = True
                    session.commit()

                    user_handle = update.message.from_user.username
                    claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                    orderer_id = order.user_id

                    del user_states[user_id]  # Clear state

                    # Notify the claimer
                    await update.message.reply_text(
                        f"✅ *Order {order_id} Successfully Claimed!*\n\n"
                        "🚀 *Next Steps:*\n"
                        "1️⃣ Buy the meal from the vendor.\n"
                        "2️⃣ Confirm purchase via the bot.\n"
                        "3️⃣ Deliver to the pickup location.\n"
                        "4️⃣ Receive your payment!\n\n"
                        "💡 Stay updated with your claimed orders for smooth transactions.",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

                    # Notify the orderer
                    if orderer_id:
                        try:
                            await context.bot.send_message(
                                chat_id=orderer_id,
                                text=(
                                    f"📢 *Your Order Has Been Claimed!*\n\n"
                                    f"📌 *Order ID:* {order_id}\n"
                                    f"🍽 *Details:* {order.order_text}\n"
                                    f"🚴 Claimed by: {claimed_by}\n\n"
                                    "📍 *Stay tuned for updates on delivery!*"
                                ),
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"Failed to notify orderer @{orderer_id}: {e}")

                else:
                    del user_states[user_id]
                    await update.message.reply_text(
                        "⚠️ This order is either already claimed or doesn't exist.",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

            except ValueError:
                del user_states[user_id]
                await update.message.reply_text(
                    "❌ Invalid Order ID. Please enter a valid number.",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )

    except Exception as e:
        await update.message.reply_text("⚠️ An error occurred. Please try again later.")
        print(f"Error: {e}")  # Debugging logs

    finally:
        session.close()

# Displays available orders that haven't been claimed yet
async def view_orders(update: Update, context: CallbackContext):
    """Handles viewing available orders and ensures proper formatting."""
    
    # Determine if it's a message (command) or a callback query (button press)
    if update.message:
        user_message = update.message  # Handle /vieworders command
    elif update.callback_query:
        user_message = update.callback_query.message  # Handle inline button press
        await update.callback_query.answer()  # Acknowledge the callback query
    
    # Query the database to get available orders
    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    session.close()

    if orders:
        order_list = [
            f"📌 *Order ID:* {o.id}\n🍽 *Meal:* {o.order_text}\n" for o in orders
        ]

        # Break orders into multiple messages if too long (avoid Telegram message limit)
        for i in range(0, len(order_list), 10):  # Send 10 orders per message
            chunk = "\n".join(order_list[i:i + 10])
            await user_message.reply_text(
                f"🔍 *Available Orders:*\n\n{chunk}",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

    else:
        await user_message.reply_text(
            "⏳ *No orders available right now!*\n\n"
            "💡 Check back later or place an order using /order.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

# Handles the /help command to provide users with available commands
# Handles the /help command to provide users with available commands
async def help_command(update: Update, context: CallbackContext):
    """Displays available commands and a short guide for new users."""

    help_text = (
        "💡 *SmuthDelivery Bot Guide*\n\n"
        "📌 *How It Works:*\n"
        "1️⃣ *Order Food:* Use `/order` to place an order with meal details and pickup location.\n"
        "2️⃣ *View Available Orders:* Use `/vieworders` to check pending orders.\n"
        "3️⃣ *Claim Orders:* If you're heading to a food vendor, use `/claim <order_id>` to pick up an order.\n"
        "4️⃣ *Payment:* Complete your payment securely using `/pay`.\n"
        "5️⃣ *Dispute Issues:* If you face problems with an order, use `/dispute <order_id> <issue>`.\n\n"
        "📌 *Available Commands:*\n"
        "🔹 /start - Start the bot and view the main menu\n"
        "🔹 /order - Place a food order\n"
        "🔹 /vieworders - See all available orders\n"
        "🔹 /claim or /claim <order_id> - Claim an order for delivery\n"
        "🔹 /help - View this help message\n\n"
        "💡 *Tip:* Try placing an order using `/order` now!"
    )

    await update.effective_message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_menu())

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
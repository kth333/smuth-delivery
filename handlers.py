from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database import Order, session_local  # Importing Order model and session to interact with the database
from utils import get_main_menu  # Importing the helper function for generating the keyboard
import messages  # Importing the messages from messages.py
import os

CHANNEL_ID = os.getenv("CHANNEL_ID")
MAX_ORDER_LENGTH = 500

# Global variable to track user states
user_states = {}

async def start(update: Update, context: CallbackContext):
    """Handles the /start command and provides onboarding instructions."""
    user_id = update.effective_user.id
    args = context.args if context.args else []  # Ensure args is always a list

    message = update.message if update.message else update.callback_query.message

    if args and args[0].startswith("claim_"):
        order_id = args[0].split("_")[1]  # Extract order ID from "claim_<order_id>"
        
        # Store the order ID in user state and set to awaiting confirmation
        user_states[user_id] = {'state': 'awaiting_confirmation', 'order_id': int(order_id)}

        await message.reply_text(
            messages.CLAIM_CONFIRMATION.format(order_id=order_id),  # Apply .format()
            parse_mode="Markdown"
        )

    else:
        await message.reply_text(
            messages.WELCOME_TEXT, parse_mode="Markdown", reply_markup=get_main_menu()
        )

async def handle_order(update: Update, context: CallbackContext):
    """Handles the /order command and asks the user for their order details."""
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message

    user_states[user_id] = {'state': 'awaiting_order'}  # Set the state to 'awaiting_order'

    await message.reply_text(
        messages.ORDER_INSTRUCTIONS, parse_mode="Markdown", reply_markup=get_main_menu()
    )

async def handle_claim(update: Update, context: CallbackContext):
    """Handles the /claim command and allows the user to claim an order."""
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message

    # Check if the order_id was passed via /start?start=claim_<order_id>
    order_id = context.user_data.pop("claim_order_id", None)  # Pop to avoid persistent claims

    if order_id:
        await process_claim_order_by_id(update, context, user_id, order_id)

    # Handle manual `/claim <order_id>` command
    elif context.args and len(context.args) > 0:
        order_id = context.args[0]  # Extract order ID from command
        await process_claim_order_by_id(update, context, user_id, order_id)

    # If no order ID provided, ask the user to enter one
    else:
        user_states[user_id] = {'state': 'awaiting_order_id'}
        await message.reply_text(
            messages.ORDER_ID_REQUEST, parse_mode="Markdown", reply_markup=get_main_menu()
        )

async def process_claim_order_by_id(update: Update, context: CallbackContext, user_id: int, order_id: str):
    """Processes the claim request by order ID."""
    message = update.message if update.message else update.callback_query.message

    try:
        order_id = int(order_id)
        session = session_local()
        order = session.query(Order).filter_by(id=order_id, claimed=False).first()

        if order:
            order.claimed = True
            session.commit()
            await message.reply_text(messages.CLAIM_SUCCESS_MESSAGE.format(order_id=order_id, order_text=order.order_text), reply_markup=get_main_menu())
        else:
            await message.reply_text(messages.CLAIM_FAILED.format(order_id=order_id), reply_markup=get_main_menu())
        session.close()
    except ValueError:
        await message.reply_text(messages.INVALID_ORDER_ID, reply_markup=get_main_menu())

async def view_orders(update: Update, context: CallbackContext):
    """Handles the /vieworders command to show available orders."""
    message = update.message if update.message else update.callback_query.message

    session = session_local()
    orders = session.query(Order).filter_by(claimed=False).all()
    session.close()

    if orders:
        order_list = [f"📌 *Order ID:* {o.id}\n🍽 *Meal:* {o.order_text}\n" for o in orders]
        for i in range(0, len(order_list), 10):  # Send 10 orders per message
            chunk = "\n".join(order_list[i:i + 10])
            await message.reply_text(
                f"🔍 *Available Orders:*\n\n{chunk}",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
    else:
        await message.reply_text(
            messages.NO_ORDERS_AVAILABLE,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

async def handle_message(update: Update, context: CallbackContext):
    """Handles incoming messages based on user state (awaiting order, confirmation, etc.)."""
    user_id = update.message.from_user.id
    if user_id not in user_states:
        await update.message.reply_text(
            "❓ Need help? Type /help or click on 'Help' below.",
            reply_markup=get_main_menu()
        )
        return

    state_data = user_states[user_id]
    if not state_data:
        await update.message.reply_text(
            messages.GENERAL_ERROR,
            reply_markup=get_main_menu()
        )
        return

    state = state_data['state']
    session = session_local()

    try:
        if state == 'awaiting_order':
            # User is typing an order
            order_text = update.message.text.strip()

            # Validate order length
            if len(order_text) > MAX_ORDER_LENGTH:
                await update.message.reply_text(
                    messages.ORDER_TOO_LONG.format(max_length=MAX_ORDER_LENGTH, order_length=len(order_text)),
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
                return

            # Save the order to the database
            new_order = Order(order_text=order_text, user_id=user_id, user_handle=update.message.from_user.username)
            session.add(new_order)
            session.commit()

            del user_states[user_id]  # Clear state after order placement

            # Confirm order placement
            await update.message.reply_text(
                messages.ORDER_PLACED.format(order_id=new_order.id, order_text=order_text),
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
            
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=messages.NEW_ORDER.format(order_id=new_order.id, order_text=order_text),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )


        elif state == 'awaiting_confirmation':
            # User is confirming an order claim
            order_id = int(update.message.text.strip())  # The user types the order ID
            stored_order_id = state_data['order_id']

            if order_id == stored_order_id:
                order = session.query(Order).filter_by(id=order_id, claimed=False).first()
                if order:
                    order.claimed = True
                    session.commit()

                    user_handle = update.message.from_user.username
                    claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                    orderer_id = order.user_id

                    del user_states[user_id]  # Clear state after claiming

                    # Notify the claimer
                    await update.message.reply_text(
                        messages.CLAIM_SUCCESS_MESSAGE.format(order_id=order_id, order_text=order.order_text),
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

                    # Notify the orderer
                    if orderer_id:
                        try:
                            await context.bot.send_message(
                                chat_id=orderer_id,
                                text=messages.ORDER_CLAIMED_NOTIFICATION.format(
                                    order_id=order_id,
                                    order_text=order.order_text,
                                    claimed_by=claimed_by
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

                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=messages.NEW_CLAIM.format(order_id=order_id, order_text=order.order_text),
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )

                else:
                    del user_states[user_id]
                    await update.message.reply_text(
                        messages.CLAIM_FAILED,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
            else:
                del user_states[user_id]
                await update.message.reply_text(
                    messages.INVALID_ORDER_ID,
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
                        messages.CLAIM_SUCCESS_MESSAGE.format(order_id=order_id, order_text=order.order_text),
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

                    # Notify the orderer
                    if orderer_id:
                        try:
                            await context.bot.send_message(
                                chat_id=orderer_id,
                                text=messages.ORDER_CLAIMED_NOTIFICATION.format(
                                    order_id=order_id,
                                    order_text=order.order_text,
                                    claimed_by=claimed_by
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

                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=messages.NEW_CLAIM.format(order_id=order_id, order_text=order.order_text),
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )

                else:
                    del user_states[user_id]
                    await update.message.reply_text(
                        messages.CLAIM_FAILED,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

            except ValueError:
                del user_states[user_id]
                await update.message.reply_text(
                    messages.INVALID_ORDER_ID,
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )

    except Exception as e:
        await update.message.reply_text(messages.GENERAL_ERROR)
        print(f"Error: {e}")  # Debugging logs

    finally:
        session.close()

async def help_command(update: Update, context: CallbackContext):
    """Handles the /help command and provides users with available commands."""
    message = update.message if update.message else update.callback_query.message

    help_text = (
        "💡 *SmuthDelivery Bot Guide*\n\n"
        "📌 *How It Works:*\n"
        "1️⃣ *Order Food:* Use `/order` to place an order with meal details and pickup location.\n"
        "2️⃣ *View Available Orders:* Use `/vieworders` to check pending orders.\n"
        "3️⃣ *Claim Orders:* If you're heading to a food vendor, use `/claim <order_id>` to pick up an order.\n"
        "📌 *Available Commands:*\n"
        "🔹 /start - Start the bot and view the main menu\n"
        "🔹 /order - Place a food order\n"
        "🔹 /vieworders - See all available orders\n"
        "🔹 /claim or /claim <order_id> - Claim an order for delivery\n"
        "🔹 /help - View this help message\n\n"
        "💡 *Tip:* Try placing an order using `/order` now!"
    )

    await message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_menu())

async def handle_button(update: Update, context: CallbackContext):
    """Handles button presses from InlineKeyboardMarkup."""
    query = update.callback_query  # Get the button press event
    await query.answer()  # Acknowledge the button press

    actions = {
        'order': handle_order,
        'vieworders': view_orders,
        'claim': handle_claim,
        'help': help_command
    }

    if query.data in actions:
        await actions[query.data](update, context)
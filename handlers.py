from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown
from database import Order, session_local  # Importing Order model and session to interact with the database
from utils import get_main_menu  # Importing the helper function for generating the keyboard
import messages  # Importing the messages from messages.py
from payment import *
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
            
            user_handle = update.message.from_user.username
            claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
            orderer_id = order.user_id   
            
            # Notify the claimer
            await update.message.reply_text(
                messages.CLAIM_SUCCESS_MESSAGE.format(order_id=order_id, order_text=order.order_text, orderer_handle=order.user_handle),
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            
            orderer_id = order.user_id
            
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
    user_id = update.effective_user.id if update.effective_user else update.message.from_user.id
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

    try:
        with session_local() as session:  # Use context manager to auto-close session

            if state == 'awaiting_order':
                # User is typing an order
                order_text = update.message.text.strip()

                # Validate order input
                if not order_text:
                    await update.message.reply_text(
                        messages.INVALID_ORDER_TEXT,  # Message for empty orders
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
                    return

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
                try:
                    order_id = int(update.message.text.strip())  # The user types the order ID
                    stored_order_id = state_data['order_id']

                    if order_id != stored_order_id:
                        del user_states[user_id]
                        await update.message.reply_text(
                            messages.INVALID_ORDER_ID,
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )
                        return

                    # Lock and fetch the order for update
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

                    if not order:  # Order is either non-existent or already claimed
                        del user_states[user_id]
                        await update.message.reply_text(
                            messages.CLAIM_FAILED.format(order_id=order_id),
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )
                        return

                    # Claim the order
                    order.claimed = True
                    session.commit()

                    user_handle = update.message.from_user.username
                    claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                    orderer_id = order.user_id

                    del user_states[user_id]  # Clear state after claiming

                    # Notify the claimer
                    await update.message.reply_text(
                        messages.CLAIM_SUCCESS_MESSAGE.format(order_id=order_id, order_text=order.order_text, orderer_handle=order.user_handle),
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

                except ValueError:
                    del user_states[user_id]
                    await update.message.reply_text(
                        messages.INVALID_ORDER_ID,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )

            elif state == 'awaiting_order_id':
                try:
                    order_id = int(update.message.text.strip())

                    # Lock and fetch the order for update
                    order = session.query(Order).filter_by(id=order_id, claimed=False).with_for_update().first()

                    if not order:  # Order does not exist or is already claimed
                        del user_states[user_id]
                        await update.message.reply_text(
                            messages.CLAIM_FAILED.format(order_id=order_id),
                            parse_mode="Markdown",
                            reply_markup=get_main_menu()
                        )
                        return

                    # Claim the order
                    order.claimed = True
                    session.commit()

                    user_handle = update.message.from_user.username
                    claimed_by = f"@{user_handle}" if user_handle else "an unknown user"
                    orderer_id = order.user_id

                    del user_states[user_id]  # Clear state

                    # Notify the claimer
                    await update.message.reply_text(
                        messages.CLAIM_SUCCESS_MESSAGE.format(order_id=order_id, order_text=order.order_text, orderer_handle=order.user_handle),
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

                except ValueError:
                    del user_states[user_id]
                    await update.message.reply_text(
                        messages.INVALID_ORDER_ID,
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
            elif state == 'selecting_order_id':
                user_message = update.message.text.strip()
            
                session = session_local()
                order = session.query(Order).filter_by(id=user_message, user_id=user_id).first()
                session.close()
            
                keyboard = [
                    [InlineKeyboardButton("Complete Order", callback_data='delete_order')], # Not finished yet
                    [InlineKeyboardButton("Make Payment", callback_data='handle_payment')],
                    [InlineKeyboardButton("Edit Order", callback_data='edit_order')],
                    [InlineKeyboardButton("Delete Order", callback_data='delete_order')],
                    [InlineKeyboardButton("Back", callback_data='start')]
                ]
            
                reply_markup = InlineKeyboardMarkup(keyboard)
                if order: 
                    await update.message.reply_text(
                        f"✅ *Order Selected:* {order.order_text}\n\n"
                        "Please choose an option:", reply_markup=reply_markup)
                
                    user_states[user_id] = {'selected_order': order.id}  # Store selected order ID
                else: 
                    await update.message.reply_text(
                        "❌ Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
                        parse_mode="Markdown"
                    )
            elif state == 'awaiting_payment_amount':
                amount = update.message.text
                if amount.isdigit():
                    await update.message.reply_text(
                        f"💳 *Would you like to proceed with payment?*\n"
                        "Reply with *YES* to continue or *CANCEL* to abort.",
                        parse_mode="Markdown"
                    )
                    user_states[user_id]['state'] = 'awaiting_payment_confirmation'
                    user_states[user_id]['amount'] = amount
                else:
                    await update.message.reply_text(
                        "❌ Please enter a valid number",
                        parse_mode="Markdown"
                    )
            elif state == 'awaiting_payment_confirmation':
                # Handle the final confirmation for payment
                user_message = update.message.text
                if user_message.lower() == "yes":
                    await update.message.reply_text(
                        "💳 Your payment is being processed. Thank you for your order!",
                        parse_mode="Markdown"
                    )
                    amount = user_states.get(user_id)['amount']
                    await send_payment_link(update, context, amount)
                    del user_states[user_id]  # Clear user state after confirmation
                elif user_message.lower() == "cancel":
                    await update.message.reply_text(
                        "❌ Payment has been canceled.",
                        parse_mode="Markdown"
                    )
                    del user_states[user_id]  # Clear user data after cancelation
                else:
                    await update.message.reply_text(
                        "❌ Invalid response. Please reply with *YES* to confirm payment or *CANCEL* to abort.",
                        parse_mode="Markdown"
                   )
            elif state == 'editing_order':
             
                new_order_text = update.message.text
                order_id = user_states.get(user_id)['selected_order']

                session = session_local()
                order = session.query(Order).filter_by(id=order_id).first()
            
                order.order_text = new_order_text
                session.commit()
                session.close()
            
                del user_states[user_id]
            
                await update.message.reply_text(
                    "Your Order has been updated",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )

                # Notify food runners in the channel
                bot_username = context.bot.username
                keyboard = [
                    [InlineKeyboardButton("🚴 Claim This Order", url=f"https://t.me/{bot_username}?start=claim_{order_id}")],
                    [InlineKeyboardButton("📝 Place an Order", url=f"https://t.me/{bot_username}?start=order")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=messages.EDITED_ORDER.format(order_id=order_id, order_text=new_order_text),
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

            elif state == 'deleting_order':
                user_message = update.message.text
                order_id = user_states.get(user_id)['selected_order']

                session = session_local()
                order = session.query(Order).filter_by(id=order_id).first()

                if user_message.lower() == 'yes':
                    session.delete(order)
                    session.commit()

                    await update.message.reply_text(
                        "Your Order has been successfully deleted",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
                elif user_message.lower() == 'no':
                    await update.message.reply_text(
                        "Failed to delete your order",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu()
                    )
            
                session.close()

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")  # Log the actual error
        print(f"[DEBUG] User ID: {user_id}, User State: {user_states.get(user_id, 'No state found')}")
        import traceback
        print(traceback.format_exc())  # Print full traceback for debugging
        await update.message.reply_text(messages.GENERAL_ERROR)

admin_handle = os.getenv("TELEGRAM_ADMIN_HANDLE")

async def help_command(update: Update, context: CallbackContext):
    """Handles the /help command and provides users with instructions on how to order, deliver, and contact admins."""

    message = update.effective_message

    help_text = (
        "💡 *SmuthDelivery Bot Guide* 🚀\n\n"
        "📌 *How It Works:*\n"
        "1️⃣ *Place an Order:* To place an order, use the bot to enter the details of your meal, pickup location, and preferred pickup time.\n"
        "2️⃣ *Claim an Order \(Food Runner\):* If you're a food runner, check available orders and use the bot to claim one to pick up from a vendor.\n"
        "3️⃣ *Delivering Food:* After claiming an order, pick up the food from the vendor and deliver it to the user’s specified location.\n"
        "4️⃣ *Communicate via Telegram Chat:* Once you've claimed an order, communicate with the orderer via Telegram chat to finalize details.\n\n"
        
        "🔹 This bot is still in very early development. Features are not perfect.\n"
        f"🔹 If you have any issues or need help, contact {admin_handle} for help.\n\n"
        
        "📢 *Stay Updated:* Subscribe to our channel for real\-time updates on new orders: [Smuth Delivery]\(https://t.me/smuth\_delivery\)"
    )

    # Escape the periods (.) for MarkdownV2
    help_text = help_text.replace('.', '\\.')

    # Send the message with MarkdownV2 formatting
    await message.reply_text(help_text, parse_mode="MarkdownV2", reply_markup=get_main_menu())

async def handle_my_orders(update: Update, context: CallbackContext):
    # Check if the update is from a callback query or a message
    if update.callback_query and update.callback_query.from_user:
        # Callback query update (button pressed)
        user_id = update.callback_query.from_user.id
    elif update.message and update.message.from_user:
        # Message update (user sends a message)
        user_id = update.message.from_user.id
    
    message = update.message or update.callback_query.message
    
    # Determine if it's a message (command) or a callback query (button press)
    if update.message:
        user_message = update.message  # Handle /vieworders command
    elif update.callback_query:
        user_message = update.callback_query.message  # Handle inline button press
        await update.callback_query.answer()  # Acknowledge the callback query
    
    session = session_local()
    orders = session.query(Order).filter_by(user_id=user_id).all()
    session.close()
    
    if orders:
        order_list = [
            f"📌 *Order ID:* {o.id}\n🍽 *Meal:* {o.order_text}\n" for o in orders
        ]

        # Break orders into multiple messages if too long (avoid Telegram message limit)
        for i in range(0, len(order_list), 10):  # Send 10 orders per message
            chunk = "\n".join(order_list[i:i + 10])
            await user_message.reply_text(
                f"🔍 *My Orders:*\n\n{chunk}\n\n ",
                parse_mode="Markdown",
            )
    else:
        await user_message.reply_text(
            "⏳ You do not have any orders right now!*\n\n"
            "💡 Please place an order using /order.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    
    keyboard = [
        [InlineKeyboardButton("Back", callback_data='start')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_states[user_id] = {'state': 'selecting_order_id'}
    
    await message.reply_text("Please enter the Order ID", reply_markup=reply_markup)

async def handle_payment(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    # Determine if it's a message (command) or a callback query (button press)
    if update.message:
        user_message = update.message  # Handle /vieworders command
    elif update.callback_query:
        user_message = update.callback_query.message  # Handle inline button press
        await update.callback_query.answer()  # Acknowledge the callback query
    
    # Query the database to get available orders
    session = session_local()
    orders = session.query(Order).filter_by(user_id=user_id).all()
    session.close()
    
    if orders:
        order_list = [
            f"📌 *Order ID:* {o.id}\n🍽 *Meal:* {o.order_text}\n" for o in orders
        ]

        # Break orders into multiple messages if too long (avoid Telegram message limit)
        for i in range(0, len(order_list), 10):  # Send 10 orders per message
            chunk = "\n".join(order_list[i:i + 10])
            await user_message.reply_text(
                f"🔍 *My Orders:*\n\n{chunk}\n\n ",
                parse_mode="Markdown",
            )
        user_states[user_id] = {'state': 'selecting_order_id'}
    else:
        await user_message.reply_text(
            "⏳ You do not have any orders right now!*\n\n"
            "💡 Please place an order using /order.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
async def edit_order(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
    
    order_id = user_states.get(user_id)['selected_order']
    session = session_local()
    print(f"Searching for order with ID: {order_id}")
    order = session.query(Order).filter_by(id=order_id).first()
    
    if order:
        if order.claimed:
            await message.reply_text(
                f"This order has been claimed.\n"
                "Please contact the runner directly to change your order.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return
        
        user_states[user_id]['state'] = 'editing_order'
        
        await message.reply_text("Please enter your new order: ")
        
    else:
        await message.reply_text(
            "❌ Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
            parse_mode="Markdown"
        )
    session.close()
    
async def delete_order(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
    
    order_id = user_states.get(user_id)['selected_order']
    session = session_local()
    print(f"Searching for order with ID: {order_id}")
    order = session.query(Order).filter_by(id=order_id).first()
    
    if order:
        if order.claimed:
            await message.reply_text(
                f"This order has been claimed.\n"
                "Please contact the runner directly to delete your order.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            return
        
        user_states[user_id]['state'] = 'deleting_order'
        
        await message.reply_text("Please reply with *YES* to confirm order deletion or *NO* to abort.")
        
    else:
        await message.reply_text(
            "❌ Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
            parse_mode="Markdown"
        )
    session.close()

async def handle_button(update: Update, context: CallbackContext):
    """Handles button presses from InlineKeyboardMarkup."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if query.data == 'handle_payment':
        user_states[user_id]['state'] = 'awaiting_payment_amount'
        await query.message.reply_text("Please enter your payment amount")
    else:
        actions = {
            'start': start,
            'order': handle_order,
            'vieworders': view_orders,
            'claim': handle_claim,
            'myorders': handle_my_orders,
            'help': help_command,
            'edit_order': edit_order,
            'delete_order': delete_order,
        }

    if query.data in actions:
        await actions[query.data](update, context)
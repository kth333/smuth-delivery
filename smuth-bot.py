from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMedia
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import os
import psycopg2
import requests
import asyncio
import json
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import base64

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Sequence
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv('DATABASE_URL')
CLIENT_ID = os.getenv("OCBC_CLIENT_ID")
CLIENT_SECRET = os.getenv("OCBC_CLIENT_SECRET")
PHONE_NUMBER = os.getenv("OCBC_PHONE_NUMBER")
PAYNOW_QR_API = os.getenv("PAYNOW_QR_API")
PAYNOW_API = os.getenv("PAYNOW_API")

# Connect to your PostgreSQL database
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Open the SQL file and execute its contents
with open('database/setup.sql', 'r') as file:
    cursor.execute(file.read())

# Commit changes and close the connection
conn.commit()
cursor.close()
conn.close()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    try:
        return SessionLocal()
    except Exception as e:
        print(f"Error creating session: {e}")
        return None

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    order_text = Column(String, nullable=False)
    user = Column(String, nullable=False)
    claimed = Column(Boolean, default=False)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    order_id = Column(Integer, nullable=False)
    user = Column(String, nullable=False)  # Telegram username
    amount = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, completed, failed
    reference_id = Column(String, nullable=True)  # PayNow transaction ID

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
    reply_markup = get_main_menu())

async def handle_claim(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_claim'
    await update.effective_message.reply_text("Please type the order ID you want to claim.",
    reply_markup = get_main_menu())

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
        
        session.refresh(new_order)
        order_id = new_order.id
        
        amount = 10
        reference_id = await request_payment(user_id, order_id, amount, context)
        print(f'Printing reference id : "{reference_id}"')

        
        if reference_id:
            await update.message.reply_text(
                f'Order received (ID: {new_order.id}): "{new_order.order_text}"\n\n'
                f"Please complete your payment of ${amount} using PayNow. \n\n"
                f"Reference ID: {reference_id}\n\n"
                "We will notify you once your payment is confirmed.",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "Failed to initiate payment request. Please try again.",
                reply_markup=get_main_menu()
            )
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

async def request_payment(user, order_id, amount, context: CallbackContext):
    """Request payment from a user via PayNow API."""
    
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        "Authorization": "Bearer " + ACCESS_TOKEN
    }
    
    payload = {
        "ProxyType": "MSISDN",
        "ProxyValue": "+6599999999",
        "Amount": amount,
        "ReferenceText": "Testing123",
        "QRCodeSize": 100,
        "ExpiryDate": "20250222",
    }
    
    response = requests.post(PAYNOW_QR_API, headers=headers, json=payload)
    
    print(response.status_code)
    print(response.text)
    if response.status_code == 200:
        transaction_data = response.json()
        reference_id = transaction_data.get("ReferenceText")
        print('Checking reference id')
        print(reference_id)
        qr_code_url = transaction_data.get("Results")["QRCodeData"]  # Hypothetical QR code URL
        print('Checking QRCodeData')
        print(qr_code_url)
        
        # if is_qr_code_url_valid(qr_code_url):
        #     print("QR code URL is valid.")
        # else:
        #     print("QR code URL is not valid.")
        
        # Store transaction details in DB
        session = session_local()
        new_transaction = Transaction(
            order_id=order_id, user=user, amount=amount, reference_id=reference_id, status="pending"
        )
        session.add(new_transaction)
        session.commit()
        session.close()
        
        image_data = base64.b64decode(qr_code_url)
                
        image = Image.open(BytesIO(image_data))  # Convert the image data into a PIL Image object

        # Now send the QR code (or reference ID) to the user via Telegram
        await send_qr_code_to_user(user, image, context)
        
        await send_reference_id_to_user(user, reference_id)
        
        return reference_id
    else:
        return None
    
async def send_qr_code_to_user(user, image, context: CallbackContext):
    """Send the PayNow QR code to the user."""
    # Convert image to a file-like object
    bio = BytesIO()
    image.save(bio, format="PNG")
    bio.seek(0)
    
    
    # Send the QR code as an image to the user
    await context.bot.send_photo(
        chat_id=user,
        photo=bio,
        caption="Scan this QR code to complete your payment via PayNow."
    )
    
def is_qr_code_url_valid(qr_code_url):
    """Check if the PayNow QR code URL is valid by making a GET request."""
    try:
        # Send a GET request to the QR code URL
        response = requests.get(qr_code_url, stream=True)

        # Check if the status code is 200 (OK) and the content type is an image
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            return True
        else:
            print(f"Invalid QR code URL. Status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Error fetching QR code URL: {e}")
        return False

async def send_reference_id_to_user(user, reference_id):
    """Send the payment reference ID to the user."""
    await context.bot.send_message(
        chat_id=user,
        text=f"Use this reference ID to complete your payment: {reference_id}.",
    )

    
async def check_pending_payments():
    """Periodically checks the payment status of pending orders."""
    while True:
        session = session_local()

        if not session:
            print("Error creating session. Retrying in 60 seconds.")
            await asyncio.sleep(60)  # Retry after 60 seconds if session creation fails
            continue

        try:
            # Query the pending orders
            pending_orders = session.query(Order).filter_by(claimed=False).all()

            for order in pending_orders:
                # Check payment status for each order
                payment_status = await check_payment_status(order.id)  # Assuming this is a coroutine

                if payment_status == "COMPLETED":
                    # Mark order as claimed
                    order.claimed = True
                    session.commit()

                    # Notify the user that payment was successful
                    await context.bot.send_message(
                        chat_id=order.user,
                        text=f"Payment received for Order {order.id}! Your order is now being processed.",
                        reply_markup=get_main_menu()
                    )
        except Exception as e:
            print(f"Error while checking pending payments: {e}")
        finally:
            # Close session after all operations
            session.close()

        # Wait for 60 seconds before checking again
        await asyncio.sleep(60)
    
async def check_payment_status(order_id):
    """Check the payment status from OCBC PayNow API"""
    url = "https://api.ocbc.com/paynow/status"
    headers = {"Authorization": f"Bearer {CLIENT_ID}:{CLIENT_SECRET}"}
    payload = {"order_id": order_id}

    response = requests.get(url, headers=headers, params=payload)

    if response.status_code == 200:
        data = response.json()
        return data.get("status")  # Example: "PENDING" or "COMPLETED"
    return "FAILED"

async def send_payment(user, amount):
    """Send payment to a user via PayNow."""
    PAYNOW_TRANSFER_API = "https://api.ocbc.com/paynow/transfer"
    CLIENT_ID = os.getenv("OCBC_CLIENT_ID")
    CLIENT_SECRET = os.getenv("OCBC_CLIENT_SECRET")

    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "amount": amount,
        "sender_name": "Smuth Delivery",
        "recipient_paynow": user,  # User's PayNow ID (Phone/UEN)
    }

    response = requests.post(PAYNOW_TRANSFER_API, json=payload)
    return response.status_code == 200

async def process_claim(update: Update, context: CallbackContext, order_id):
    session = session_local()
    order = session.query(Order).filter_by(id=order_id, claimed=False).first()

    if order:
        amount = 5  # Example: Fixed amount per delivery
        if await send_payment(order.user, amount):
            order.claimed = True
            session.commit()
            await update.message.reply_text(
                f'Order {order_id} claimed. You received ${amount} via PayNow.',
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "Payment failed. Please try again later.",
                reply_markup=get_main_menu()
            )
    else:
        await update.message.reply_text("Order not found or already claimed.", reply_markup=get_main_menu())

    session.close()

async def view_orders(update: Update, context: CallbackContext):
    # Ensure we're dealing with a callback query
    if update.callback_query:
        callback_query = update.callback_query
        # Process the callback query if it has a valid message
        if callback_query.message:
            session = session_local()
            orders = session.query(Order).filter_by(claimed=False).all()
            if orders:
                message = "Available Orders:\n" + "\n".join([f'ID: {o.id} - {o.order_text} (User: @{o.user})' for o in orders])
            else:
                message = "No orders to be claimed right now!"
            await callback_query.message.reply_text(message, reply_markup=get_main_menu())
            session.close()
        else:
            # Handle the case where callback query does not contain a message
            print("Callback query does not have a message.")
    else:
        # Handle the case where it's a message update (not a callback query)
        if update.message:
            session = session_local()
            orders = session.query(Order).filter_by(claimed=False).all()
            if orders:
                message = "Available Orders:\n" + "\n".join([f'ID: {o.id} - {o.order_text} (User: @{o.user})' for o in orders])
            else:
                message = "No orders to be claimed right now!"
            await update.message.reply_text(message, reply_markup=get_main_menu())
            session.close()
        else:
            print("Neither callback_query nor message found in the update.")


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
    
    # Run periodic payment check in the background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.create_task(check_pending_payments()) 
    
    app.run_polling()

if __name__ == '__main__':
    main()

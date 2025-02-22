import os
from dotenv import load_dotenv
import stripe 
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import *

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_checkout_session(amount: int, currency: str, user_id): 
    success_url = f"https://t.me/your_bot?start=payment_success_{user_id}"  # Unique for the user
    cancel_url = f"https://t.me/your_bot?start=payment_cancel_{user_id}"
    
    checkout_session = stripe.checkout.Session.create(
        payment_method_types = ['paynow'],
        line_items=[{
            'price_data': {
                'currency': currency,
                'product_data': {
                    'name': 'SMUth-Bot Payment',
                },
                'unit_amount': amount, # Amount in cents
            },
            'quantity': 1,
        }],
        mode = 'payment',
        success_url = success_url,
        cancel_url = cancel_url,
    )
    return checkout_session.url

async def send_payment_link(update, context, amount):
    currency = 'sgd'
    user_id = update.message.from_user.id
    
    checkout_url = create_checkout_session(amount, currency, user_id)
    
    keyboard = [[InlineKeyboardButton("Pay Now", url=checkout_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click below to pay:", reply_markup=reply_markup)
    
async def handle_payment(update, context):
    from smuth_bot import get_main_menu
    my_user_id = update.message.from_user.id
    
    # Determine if it's a message (command) or a callback query (button press)
    if update.message:
        user_message = update.message  # Handle /vieworders command
    elif update.callback_query:
        user_message = update.callback_query.message  # Handle inline button press
        await update.callback_query.answer()  # Acknowledge the callback query
    
    # Query the database to get available orders
    session = session_local()
    orders = session.query(Order).filter_by(user_id=my_user_id).all()
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
            
        context.user_data["state"] = "SELECT_ORDER"
        

    else:
        await user_message.reply_text(
            "⏳ You do not have any orders right now!*\n\n"
            "💡 Please place an order using /order.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
async def select_order(update, context):
    if context.user_data.get("state") == "SELECT_ORDER":
        user_message = update.message.text.strip()  # Capture the user's input
        my_user_id = update.message.from_user.id

        # Logic to check if the order ID is valid
        session = session_local()
        order = session.query(Order).filter_by(id=user_message, user_id=my_user_id).first()
        session.close()

        # Check the user's current state
        if order:
            await update.message.reply_text(
                f"✅ *Order Selected:* {order.order_text}\n\n"
                "Please enter the amount below (SGD)",
                parse_mode="Markdown"
            )
            context.user_data["selected_order"] = order.id  # Store selected order ID
            context.user_data["state"] = "PAYMENT_AMOUNT"  # Transition to payment state

        else:
            await update.message.reply_text(
                "❌ Invalid Order ID. Please enter a valid Order ID or type /cancel to exit.",
                parse_mode="Markdown"
            )
    elif context.user_data.get("state") == "PAYMENT_AMOUNT":
        amount = update.message.text
        if amount.isdigit():
            await update.message.reply_text(
                f"💳 *Would you like to proceed with payment?*\n"
                "Reply with *YES* to continue or *CANCEL* to abort.",
                parse_mode="Markdown"
            )
            context.user_data["amount"] = amount
            context.user_data["state"] = "PAYMENT_CONFIRMATION"
        else:
            await update.message.reply_text(
                "❌ Please enter a valid number",
                parse_mode="Markdown"
            )
    elif context.user_data.get("state") == "PAYMENT_CONFIRMATION":
        # Handle the final confirmation for payment
        user_message = update.message.text
        if user_message.lower() == "yes":
            await update.message.reply_text(
                "💳 Your payment is being processed. Thank you for your order!",
                parse_mode="Markdown"
            )
            await send_payment_link(update, context, context.user_data.get("amount"))
            context.user_data.clear()  # Clear user data after cancelation
        elif user_message.lower() == "cancel":
            await update.message.reply_text(
                "❌ Payment has been canceled.",
                parse_mode="Markdown"
            )
            context.user_data.clear()  # Clear user data after cancelation
        else:
            await update.message.reply_text(
                "❌ Invalid response. Please reply with *YES* to confirm payment or *CANCEL* to abort.",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "❌ Invalid state. Please type /pay to start the payment process.",
            parse_mode="Markdown"
        )
        
@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, 'endpoint_secret'
        )
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_successful_payment(session)
            
        return '', 200
    except ValueError as e:
        # Invalid payload
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return '', 400
    
def handle_successful_payment(session):
    print(f"Payment successful: {session}")
    
    transfer_funds_to_user(session['payment_intent'])
    
def transfer_funds_to_user(payment_intent_id):
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    
    payout = stripe.Payout.create(
        amount = payment_intent.amount_received,
        currency = 'sgd',
        destination = ''
    )
    return payout

if __name__ == '__main__':
    app.run(port=5000)
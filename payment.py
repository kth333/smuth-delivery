import os
import re
from dotenv import load_dotenv
import stripe 
from flask import Flask, request, jsonify
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import *
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import messages

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

endpoint_secret = os.getenv('WEBHOOK_SECRET')

def create_checkout_session(amount: int, currency: str, user_id, order_id): 
    success_url = f"https://t.me/smuth_delivery?start=payment_success_{user_id}"  # Unique for the user
    cancel_url = f"https://t.me/smuth_delivery?start=payment_cancel_{user_id}"
    
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
        payment_intent_data={
            'metadata': {
                'user_id': user_id,  # User Id
                'order_id': order_id, # Order Id
            },
        },
        mode = 'payment',
        success_url = success_url,
        cancel_url = cancel_url,
    )
    return checkout_session.url

async def send_payment_link(update, context, amount, order_id):
    currency = 'sgd'
    user_id = update.message.from_user.id
    
    checkout_url = create_checkout_session(amount, currency, user_id, order_id)
    
    keyboard = [[InlineKeyboardButton("Pay Now", url=checkout_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click below to pay:", reply_markup=reply_markup)
        
def validate_and_convert_amount(amount: str) -> (bool, int):
    """
    Validates and converts the input amount to cents.
    
    Args:
    - amount: The input amount in string format (can include '$' or decimal).
    
    Returns:
    - (valid: bool, cents: int): A tuple where `valid` indicates if the amount is valid
      and `cents` is the amount in cents (if valid, otherwise -1).
    """
    
    # Remove the dollar sign if it exists
    amount = amount.replace('$', '').strip()
    
    # Check if the amount matches the pattern: integer or float with up to 2 decimal places
    if re.match(r"^\d+(\.\d{1,2})?$", amount):
        # Convert the amount to a float and then to cents
        try:
            # Use Decimal for precise floating-point arithmetic
            amount_decimal = Decimal(amount)
        
        # Check if the value is positive and at least 1 dollar (i.e., >= 1.00)
            if amount_decimal >= Decimal('1.00'):
            # Convert to cents
                amount_decimal = amount_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                amount_cents = int(amount_decimal * 100)
                return True, amount_cents
        except InvalidOperation:
            pass
    
    return False, -1

async def handle_payment_intent_succeeded(payment_intent, order_id, telegram_bot):
    amount = Decimal(payment_intent['amount'] / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    print(f"Payment for Order ID {order_id} succeeded. Amount: {amount}")
    
    
    session = session_local()
    order = session.query(Order).filter_by(id=order_id).first()
    
    order.payment_amount = amount
    runner_id = order.runner_id
    orderer_id = order.user_id
    session.commit()
    session.close()
    
    await notify_successful_payment(order_id, orderer_id, runner_id, amount, telegram_bot)
    
    
async def notify_successful_payment(order_id, orderer_id, runner_id, amount, telegram_bot):
    # Notify the orderer about the successful payment
    if orderer_id: 
        try:
            await telegram_bot.send_message(
                chat_id=orderer_id,
                text=messages.SUCCESSFUL_PAYMENT_NOTIFICATION.format(
                    order_id=order_id,
                    amount=amount
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to notify orderer @{orderer_id}: {e}")
    else:
        print(f"Orderer ID not found for Order ID {order_id}. Cannot notify.")

    # Notify the runner about the successful payment
    if runner_id:
        try:
            await telegram_bot.send_message(
                chat_id=runner_id,
                text=messages.SUCCESSFUL_PAYMENT_NOTIFICATION.format(
                    order_id=order_id,
                    amount=amount
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to notify runner @{runner_id}: {e}")
    else:
        print(f"Runner ID not found for Order ID {order_id}. Cannot notify.")
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
        
# @app.route('/webhook', methods=['POST'])
# def stripe_webhook():
#     payload = request.get_data(as_text=True)
#     sig_header = request.headers.get('Stripe-Signature')
    
#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, 'endpoint_secret'
#         )
        
#         if event['type'] == 'checkout.session.completed':
#             session = event['data']['object']
#             handle_successful_payment(session)
            
#         return '', 200
#     except ValueError as e:
#         # Invalid payload
#         return '', 400
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         return '', 400
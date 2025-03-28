import os
import json
import stripe
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
from handlers import handle_message, start, handle_order, view_orders, handle_claim, help_command, handle_button, handle_my_orders
from database import *
from payment import handle_payment_intent_succeeded
from flask import Flask, request, jsonify
import threading

flask_app = Flask(__name__)

telegram_bot = None

# Load environment variables
load_dotenv()

# Load the bot token
TOKEN = os.getenv('TELEGRAM_TOKEN')
endpoint_secret = os.getenv('WEBHOOK_SECRET')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@flask_app.route('/', methods=['GET', 'POST'])
def index():
    return "Welcome to the Smuth Delivery bot!"

@flask_app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    global telegram_bot
    event = None
    payload = request.get_data(as_text=True)
    
    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)
    if endpoint_secret:
        # Only verify the event if there is an endpoint secret defined
        # Otherwise use the basic event deserialized with json
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return jsonify(success=False)
    
    if event and event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        order_id = payment_intent['metadata']['order_id']
        print('Payment for {} succeeded'.format(payment_intent['amount']))
        asyncio.run(handle_payment_intent_succeeded(payment_intent, order_id, telegram_bot))
    else:
        # Unexpected event type
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

def start_flask():
    flask_app.run(host='0.0.0.0', port=5001, use_reloader=False, debug=True)  # Run Flask on a different port (e.g., 5001)

def start_telegram_bot():
    global telegram_bot
    app = Application.builder().token(TOKEN).build()
    telegram_bot = app.bot

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", handle_order))
    app.add_handler(CommandHandler("vieworders", view_orders))
    app.add_handler(CommandHandler("claim", handle_claim))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myorders", handle_my_orders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Callback Query Handler (buttons)
    app.add_handler(CallbackQueryHandler(handle_button))

    # Start polling
    app.run_polling()
    
def main():
    # Run Flask and Telegram bot in separate threads to avoid blocking each other
    threading.Thread(target=start_flask, daemon=True).start()
    start_telegram_bot()

if __name__ == '__main__':
    main()
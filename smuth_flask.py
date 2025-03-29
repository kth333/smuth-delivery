import os
import stripe
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from payment import handle_payment_intent_succeeded
from payout import update_onboarding_status
from smuth_bot import telegram_bot

# Load environment variables
load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)

endpoint_secret_payment = os.getenv('WEBHOOK_SECRET_PAYMENT')
endpoint_secret_payout = os.getenv('WEBHOOK_SECRET_PAYOUT')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@flask_app.route('/', methods=['GET', 'POST'])
def index():
    return "Welcome to the Smuth Delivery bot!"

@flask_app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    event = None
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('stripe-signature')
    
    try:
        try:
        # Attempt to verify the event using the payment secret
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret_payment
            )
            print("Event verified using payment secret.")
        except stripe.error.SignatureVerificationError:
            # If verification fails, try the payout secret
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret_payout
            )
            print("Event verified using payout secret.")
    except stripe.error.SignatureVerificationError as e:
        print(f"⚠️ Webhook signature verification failed: {e}")
        return jsonify(success=False)
    except Exception as e:
        print(f"⚠️ Webhook error: {e}")
        return jsonify(success=False)
    
    if event and event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']  # contains a stripe.PaymentIntent
        order_id = payment_intent['metadata']['order_id']
        print('Payment for {} succeeded'.format(payment_intent['amount']))
        asyncio.run(handle_payment_intent_succeeded(payment_intent, order_id, telegram_bot))
        
    elif event['type'] == 'account.updated':
        account = event['data']['object']
        update_onboarding_status(account)
        
    else:
        # Unexpected event type
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

if __name__ == '__main__':
    # Start Flask app
    flask_app.run(host='0.0.0.0', port=5001, debug=True)
import os
import stripe
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the Stripe API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Telegram Bot API token and chat ID
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = "1434893335"  # Updated with your Telegram ID

def send_telegram_message(message):
    """Send a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")

def test_create_account_link():
    # Replace with a valid Stripe account ID for testing
    stripe_account_id = "acct_1R7aEeP3nOZUUnhI"

    try:
        # Retrieve account details for debugging
        account = stripe.Account.retrieve(stripe_account_id)
        print("Account Details:")
        print(f"ID: {account['id']}")
        print(f"Requirements: {account['requirements']}")
        print(f"Capabilities: {account['capabilities']}")

        # Create an account link for onboarding
        account_link = stripe.AccountLink.create(
            account=stripe_account_id,
            refresh_url="https://example.com/refresh",  # URL to retry onboarding
            return_url="https://example.com/return",  # URL to redirect to after completing onboarding
            type="account_onboarding",  # Specify that this link is for onboarding
        )
        print("Generated Account Link:", account_link.url)

        # Send the link to Telegram
        send_telegram_message(f"Here is your Stripe onboarding link: {account_link.url}")
    except stripe.error.StripeError as e:
        print(f"Error creating account link: {e}")
        send_telegram_message("Failed to generate Stripe onboarding link. Please check the logs.")

if __name__ == "__main__":
    test_create_account_link()

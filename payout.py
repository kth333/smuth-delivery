import os
from dotenv import load_dotenv
import stripe 
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from database import *

load_dotenv()

user_states = {}

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')

async def create_stripe_account(user_email):
    try:
        account = stripe.Account.create(
            type = 'express',
            country = "SG",
            email = user_email,
            business_type = "individual",
            business_profile = {
                'mcc': '5812',
                'name': 'Smuth Delivery Runner',
                'product_description': 'Deliver Food'
            },
            capabilities = {
                'card_payments': {'requested': True},
                "transfers": {"requested": True}
                },
        )
        return account
    except stripe.error.StripeError as e:
        print(f"Error creatng Stripe account: {e}")
        return None

async def create_account_link(stripe_account_id):
    try:
        # Retrieve account details for debugging
        account = stripe.Account.retrieve(stripe_account_id)
        print("Account Details:")
        print(f"ID: {account['id']}")
        print(f"Requirements: {account['requirements']}")
        print(f"Capabilities: {account['capabilities']}")
        
        # Create an account link for Standard account onboarding
        account_link = stripe.AccountLink.create(
            account=stripe_account_id,
            refresh_url="https://example.com/refresh",  # URL to retry onboarding
            return_url="https://example.com/return",  # URL to redirect to after completing onboarding
            type="account_onboarding", # Specify that this link is for onboarding
            collection_options={"fields" : "currently_due"},
        )
        print("Generated Account Link:", account_link.url)
        return account_link.url
    except stripe.error.StripeError as e:
        print(f"Error creating account link: {e}")
        return None
        
async def start_stripe_account_creation(update, context):
    """Start the payment process and ask for the user's email."""
    user_states[update.message.from_user.id] = 'waiting_for_email'  # Set the user's state to waiting for email
    
    await update.message.reply_text("Please provide your email to create a Stripe account.")

async def get_email(update, context):
    """Process the user's email input and create the Stripe account."""
    user_id = update.message.from_user.id
    
    if user_states.get(user_id) == 'waiting_for_email':
        user_email = update.message.text  # Get the user's email
        account = await create_stripe_account(user_email)  # Create Stripe account
        
        if account:
            account_link = await create_account_link(account['id'])
            if account_link: 
                send_telegram_message(f"Here is your Stripe onboarding link: {account_link}", user_id)
                
                newStripeAccount = StripeAccount(
                    telegram_id = user_id,
                    stripe_account_id = account['id']
                )
                
                session = session_local()
                session.add(newStripeAccount)
                session.commit()
                
            else:
                await update.message.reply_text("There was an error generating your onboarding link.")
        else:
            await update.message.reply_text("There was an error creating your Stripe account.")
        
        # After handling, clear the user's state
        user_states[user_id] = 'done'
    else:
        await update.message.reply_text("I am not sure what you want to do. Please start with /pay to create your Stripe account.")

    
async def transfer_funds(runner_id, amount):
    session = session_local()
    
    stripe_account_id = session.query(StripeAccount).filter_by(telegram_id=runner_id).first().stripe_account_id
    session.close()
    
    transfer = await transfer_to_user(stripe_account_id, amount)
    
    if transfer:
        payout = await payout_to_user(stripe_account_id, amount)
    
        if payout:
            send_telegram_message(f"Successfully transferred ${amount} to your Stripe account: {payout['id']}", runner_id)
        else:
            send_telegram_message(f"Failed to transfer funds to your Stripe account. Please contact the admins for help", runner_id)
        return
    else:
        send_telegram_message(f"Failed to transfer funds to your Stripe account. Please contact the admins for help", runner_id)
        return  

async def transfer_to_user(stripe_account_id, amount):
    try:
        transfer = stripe.Transfer.create(
            amount = int(amount * 100), # amount in cents
            currency = 'sgd',
            destination = stripe_account_id,
            description = "Transfer to connected account for payout"
        )
        return transfer
    except stripe.error.StripeError as e:
        print(f"Error transferring funds: {e}")
        return None

async def payout_to_user(stripe_account_id, amount):
    try:
        payout = stripe.Payout.create(
            amount = int(amount * 100), # amount in cents
            currency = 'sgd',
            stripe_account = stripe_account_id,
        )
        return payout
    except stripe.error.StripeError as e:
        print(f"Error transferring funds: {e}")
        return None
        
def send_telegram_message(message, user_id):
    """Send a message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message,
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")
        
def update_onboarding_status(account):
    session = session_local()
    """Update the database on the onboarding status of the Stripe account."""
    stripe_account = session.query(StripeAccount).filter_by(stripe_account_id=account['id']).first()
    stripe_account.charges_enabled = account["charges_enabled"]
    stripe_account.payouts_enabled = account["payouts_enabled"]
    user_id = stripe_account.telegram_id
    
    session.commit()
    """Update the onboarding status of the Stripe account."""
    if account["charges_enabled"] and account["payouts_enabled"]:
        send_telegram_message(f"Account {account['id']} onboarding completed and is now fully enabled.", user_id)
    # else:
        # send_telegram_message(f"Account {account['id']} is not fully enabled yet.", user_id)
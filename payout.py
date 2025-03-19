import os
from dotenv import load_dotenv
import stripe 
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from database import *

load_dotenv()

app = Flask(__name__)

user_states = {}

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

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
        # Create an account link for Standard account onboarding
        account_link = stripe.AccountLink.create(
            account=stripe_account_id,
            refresh_url="https://example.com/success",  # URL to retry onboarding
            return_url="https://t.me/smuth_delivery",  # URL to redirect to after completing onboarding
            type="account_onboarding",  # Specify that this link is for onboarding
        )
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
                await update.message.reply_text(f"Account created successfully. Please complete your onboarding here: {account_link}")
                
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

    
async def transfer_funds(update, context):
    stripe_account_id = "acct_1QvDWP07K9AaD6uW"
    amount = 100
    
    payout = transfer_to_user(stripe_account_id, amount)
    
    if payout:
        await update.message.reply_text(f"Funds transferred successfully. Payout ID: {payout.id}")
    else:
        await update.message.reply_text("There was an error transferring funds.")

async def transfer_to_user(stripe_account_id, amount_in_cents):
    try:
        payout = stripe.Payout.create(
            amount = amount_in_cents,
            currency = 'sgd',
            stripe_account = stripe_account_id
        )
        return payout
    except stripe.error.StripeError as e:
        print(f"Error transferring funds: {e}")
        return None
        
from telegram import Update
from telegram.ext import CallbackContext
from controllers.order_state import user_states

async def handle_report_user_reason(update: Update, context: CallbackContext, order_id, reported_user_id):
    """
    Handles the report user reason.
    Prompts the user for report type (User/Bugs)
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    user_states[user_id]['state'] = 'reporting_user_details'
    
    await message.reply_text(
        "Please input the reason for reporting this user:",
    )
    
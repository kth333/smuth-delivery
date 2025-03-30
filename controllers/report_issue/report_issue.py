from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from controllers.order_state import user_states

async def handle_report(update: Update, context: CallbackContext):
    """
    Handles the report issue command.
    Prompts the user for report type (User/Bugs)
    """
    user_id = update.effective_user.id
    message = update.message if update.message else update.callback_query.message
    user_states[user_id] = 'report_issue'
    
    keyboard = [
        [InlineKeyboardButton("User", callback_data='report_user')],
        [InlineKeyboardButton("Bugs", callback_data='report_bug')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        "Please select the issue you want to report :",
        reply_markup=reply_markup
    )
    
    
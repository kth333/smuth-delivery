from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu
from views import messages

async def help_command(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    await message.reply_text(messages.HELP_TEXT, parse_mode="MarkdownV2", reply_markup=get_main_menu())
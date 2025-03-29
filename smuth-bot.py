import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from controllers.order_conversation import handle_order, handle_message, handle_my_orders, handle_my_claims
from controllers.order_claim import handle_claim
from controllers.help_command import help_command
from tasks.expire_orders import expire_old_orders

# Load environment variables
load_dotenv()

# Load the bot token
TOKEN = os.getenv('TELEGRAM_TOKEN')
# Initialize Bot
bot = Bot(token=TOKEN)

def main():
    app = Application.builder().token(TOKEN).build()

    # Register command handlers.
    app.add_handler(CommandHandler("start", handle_order))
    app.add_handler(CommandHandler("order", handle_order))
    app.add_handler(CommandHandler("vieworders", handle_my_orders))
    app.add_handler(CommandHandler("claim", handle_claim))
    app.add_handler(CommandHandler("myorders", handle_my_orders))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, OrderController.handle_message))
    app.add_handler(CallbackQueryHandler(OrderController.handle_button))

    # Set up the scheduler to run the expire_old_orders task every 5 minutes.
    scheduler = AsyncIOScheduler()
    scheduler.add_job(expire_old_orders, 'interval', minutes=5, args=[bot])
    scheduler.start()

    # Start polling
    app.run_polling()

if __name__ == '__main__':
    main()

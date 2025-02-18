from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
orders = []
user_states = {}

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("Place Order", callback_data='order')],
        [InlineKeyboardButton("View Orders", callback_data='vieworders')],
        [InlineKeyboardButton("Claim Order", callback_data='claim')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to Smuth Delivery! Use the buttons below to interact.", reply_markup=get_main_menu())
    await view_orders(update, context)

async def handle_button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'order':
        await handle_order(update, context)
    elif query.data == 'vieworders':
        await view_orders(update, context)
    elif query.data == 'claim':
        await handle_claim(update, context)
    elif query.data == 'help':
        await help_command(update, context)

async def handle_order(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_order'
    await update.effective_message.reply_text(
    "Please type your order now, including your preferred menu, delivery time, and location.", 
    reply_markup=get_main_menu())

async def handle_claim(update: Update, context: CallbackContext):
    user_states[update.effective_user.id] = 'awaiting_claim'
    await update.effective_message.reply_text("Please type the order ID you want to claim.", reply_markup=get_main_menu())

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        return
    state = user_states.pop(user_id)
    if state == 'awaiting_order':
        order_text = update.message.text
        order_id = len(orders) + 1
        orders.append({'id': order_id, 'order': order_text, 'user': update.message.from_user.username, 'user_id': user_id, 'claimed': False})
        await update.message.reply_text(
            f'Order received (ID: {order_id}): "{order_text}"\n'
            f'Placed by @{update.message.from_user.username} (ID: {user_id}).\n'
            'Anyone available can use /claim {order_id} to deliver.',
            reply_markup=get_main_menu())
    elif state == 'awaiting_claim':
        try:
            order_id = int(update.message.text)
            for order in orders:
                if order['id'] == order_id and not order['claimed']:
                    order['claimed'] = True
                    await update.message.reply_text(f'Order {order_id} claimed by @{update.message.from_user.username}.', reply_markup=get_main_menu())
                    return
            await update.message.reply_text("Order not found or already claimed.", reply_markup=get_main_menu())
        except ValueError:
            await update.message.reply_text("Invalid order ID.", reply_markup=get_main_menu())

async def view_orders(update: Update, context: CallbackContext):
    available_orders = [f'ID: {o["id"]} - {o["order"]} (User: @{o["user"]}, ID: {o["user_id"]})' for o in orders if not o['claimed']]
    await update.effective_message.reply_text("Available Orders:\n" + ("\n".join(available_orders) if available_orders else "No available orders."), reply_markup=get_main_menu())

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Start the bot\n"
        "/order - Place an order\n"
        "/vieworders - View all available orders\n"
        "/claim - Claim an order\n"
        "/help - Show this help message"
    )
    await update.effective_message.reply_text(help_text, reply_markup=get_main_menu())

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", handle_order))
    app.add_handler(CommandHandler("vieworders", view_orders))
    app.add_handler(CommandHandler("claim", handle_claim))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.run_polling()

if __name__ == '__main__':
    main()

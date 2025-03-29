from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu
from views import messages
from controllers.order_state import user_states
from controllers.steps.handle_meal import handle_meal_input
from controllers.steps.handle_location import handle_location_input
from controllers.steps.handle_earliest_time import handle_earliest_time_input
from controllers.steps.handle_latest_time import handle_latest_time_input
from controllers.steps.handle_details import handle_details_input
from controllers.steps.handle_fee import handle_fee_input
from controllers.steps.handle_confirmation import handle_confirmation_input
from controllers.steps.handle_deletion import handle_deletion

async def start_order(update: Update, context: CallbackContext):
    """
    Initiates the order placement conversation (triggered by /order).
    """
    user_id = update.effective_user.id
    user_states[user_id] = {"state": "awaiting_order_meal"}
    message = update.message if update.message else update.callback_query.message
    await message.reply_text(
        messages.ORDER_INSTRUCTIONS_MEAL,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

async def handle_conversation(update: Update, context: CallbackContext):
    """
    Dispatcher for the order placement conversation.
    
    Checks the current conversation state (stored in user_states)
    and calls the appropriate step handler.
    """
    user_id = update.effective_user.id

    if user_id not in user_states:
        await update.message.reply_text("Need help? Type /help or use the menu below.")
        return

    current_state = user_states[user_id].get("state")
    
    if current_state == "awaiting_order_meal":
        await handle_meal_input(update, context)
    elif current_state == "awaiting_order_location":
        await handle_location_input(update, context)
    elif current_state == "awaiting_order_earliest_time":
        await handle_earliest_time_input(update, context)
    elif current_state == "awaiting_order_latest_time":
        await handle_latest_time_input(update, context)
    elif current_state == "awaiting_order_details":
        await handle_details_input(update, context)
    elif current_state == "awaiting_order_delivery_fee":
        if await handle_fee_input(update, context):
            await handle_confirmation_input(update, context)
    elif current_state == "deleting_order":
        await handle_deletion(update, context)
    else:
        await update.message.reply_text(
            "Unknown state. Please try again or type /help.",
            reply_markup=get_main_menu()
        )
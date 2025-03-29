from telegram import Update
from telegram.ext import CallbackContext
from utils.utils import get_main_menu, get_cancel_keyboard
from views import messages
from controllers.order_state import user_states

from controllers.order_steps.handle_meal import handle_meal_input
from controllers.order_steps.handle_location import handle_location_input
from controllers.order_steps.handle_earliest_time import handle_earliest_time_input
from controllers.order_steps.handle_latest_time import handle_latest_time_input
from controllers.order_steps.handle_details import handle_details_input
from controllers.order_steps.handle_fee import handle_fee_input
from controllers.order_steps.handle_confirmation import handle_confirmation_input
from controllers.order_steps.handle_deletion import handle_deletion
from controllers.order_management.handle_select_claimed_order import handle_selecting_claimed_order
from controllers.order_management.delete_order import delete_order
from controllers.order_management.cancel_claim import cancel_claim
from controllers.claim_steps.handle_confirmation import handle_claim_confirmation
from controllers.claim_steps.handle_claim import process_claim_order_by_id

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
        reply_markup=get_cancel_keyboard(user_id)
    )

async def handle_conversation(update: Update, context: CallbackContext):
    """
    Dispatcher for the order placement conversation and other user interactions.
    Routes the message based on current user state.
    """
    user_id = update.effective_user.id

    if user_id not in user_states:
        await update.message.reply_text(
            "Need help? Type /help or use the menu below.",
            reply_markup=get_main_menu()
        )
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
    elif current_state == "awaiting_order_id":
        try:
            order_id = int(update.message.text.strip())
            await process_claim_order_by_id(update, context, user_id, order_id)
        except ValueError:
            await update.message.reply_text(
                messages.INVALID_ORDER_ID,
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
    elif current_state == "awaiting_claim_confirmation":
        await handle_claim_confirmation(update, context)
    elif current_state == "selecting_order_id":
        try:
            order_id = int(update.message.text.strip())
            user_states[user_id]["selected_order"] = order_id
            await delete_order(update, context)
        except ValueError:
            await update.message.reply_text(
                "Invalid Order ID. Please enter a number.",
                reply_markup=get_main_menu()
            )
    elif current_state == "selecting_claimed_order":
        await handle_selecting_claimed_order(update, context)
    elif current_state == "canceling_claim":
        user_response = update.message.text.strip().lower()
        if user_response == "yes":
            await cancel_claim(update, context)
        elif user_response == "no":
            await update.message.reply_text(
                "Claim cancellation aborted.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
            user_states.pop(user_id, None)
        else:
            await update.message.reply_text(
                "Invalid response. Please reply with YES to confirm cancellation or NO to abort.",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "Need help? Type /help or use the menu below.",
            reply_markup=get_main_menu()
        )
        user_states.pop(user_id, None)
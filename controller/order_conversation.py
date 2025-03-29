from telegram import Update
from telegram.ext import CallbackContext

from controllers.order_state import user_states
from controllers.steps.handle_meal import handle_meal_input
from controllers.steps.handle_location import handle_location_input
from controllers.steps.handle_earliest_time import handle_earliest_time_input
from controllers.steps.handle_latest_time import handle_latest_time_input
from controllers.steps.handle_details import handle_details_input
from controllers.steps.handle_fee import handle_fee_input
from controllers.steps.handle_confirmation import handle_confirmation_input
from controllers.steps.handle_deletion import handle_deletion

async def handle_conversation(update: Update, context: CallbackContext):
    """
    Dispatcher for the order placement conversation.
    
    This function examines the user's current state (stored in the shared
    `user_states` dictionary) and delegates the incoming update to the appropriate
    step handler.
    """
    user_id = update.effective_user.id

    # If no state exists, prompt the user to start over.
    if user_id not in user_states:
        await update.message.reply_text("Need help? Type /help or use the menu below.")
        return

    current_state = user_states[user_id].get('state')
    
    if current_state == 'awaiting_order_meal':
        await handle_meal_input(update, context)
    elif current_state == 'awaiting_order_location':
        await handle_location_input(update, context)
    elif current_state == 'awaiting_order_earliest_time':
        await handle_earliest_time_input(update, context)
    elif current_state == 'awaiting_order_latest_time':
        await handle_latest_time_input(update, context)
    elif current_state == 'awaiting_order_details':
        await handle_details_input(update, context)
    elif current_state == 'awaiting_order_delivery_fee':
        # handle_fee_input should update the state to 'awaiting_order_confirmation' on success.
        if await handle_fee_input(update, context):
            # Optionally, you can directly call confirmation here if not triggered by a button.
            # For example, uncomment the following line if you wish:
            # await handle_confirmation_input(update, context)
            pass
    elif current_state == 'awaiting_order_confirmation':
        await handle_confirmation_input(update, context)
    elif current_state == 'deleting_order':
        await handle_deletion(update, context)
    else:
        await update.message.reply_text(
            "Unknown state. Please try again or type /help.", 
            reply_markup=None
        )
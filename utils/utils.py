from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Generates the main menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Place Order", callback_data='order')],
        [InlineKeyboardButton("Available Orders", callback_data='vieworders')],
        [InlineKeyboardButton("Claim Order", callback_data='claim')],
        [InlineKeyboardButton("View and Cancel Orders", callback_data='myorders')],
        [InlineKeyboardButton("View and Cancel Claims", callback_data='myclaims')],
        [InlineKeyboardButton("Report Issue", callback_data='report_issue')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ])

def get_cancel_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Cancel Order", callback_data=f"cancel_order_{user_id}")]
    ])
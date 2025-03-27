from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    """Generates the main menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Place Order", callback_data='order')],
        [InlineKeyboardButton("View Orders", callback_data='vieworders')],
        [InlineKeyboardButton("Claim Order", callback_data='claim')],
        [InlineKeyboardButton("My Orders (cancel your order here)", callback_data='myorders')],
        [InlineKeyboardButton("My Claims (cancel your claim here)", callback_data='myclaims')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ])
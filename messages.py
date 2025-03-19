# General Welcome
WELCOME_TEXT = (
    "👋 *Welcome to SmuthDelivery!* 🚀\n\n"
    "🎓 Before you start, please use the help command to learn how it works!\n\n"

    "💡 *Quick Commands:*\n"
    "📌 /order - Place an order\n"
    "📌 /vieworders - See available food orders\n"
    "📌 /claim or /claim <order id> - Claim an order as a runner\n"
    "📌 /help - Get assistance\n\n"

    "*Please ensure your Telegram chat is open to new contacts so that orderers/runners can communicate with you!*"
)

# Order placement instructions
ORDER_INSTRUCTIONS_MEAL = (
    "📝 *Placing an Order* We will ask for delivery location, time, additional info and delivery fee next.\n\n"
    "📌 Step 1. Please enter your meal:\n"
    "✅ Example: *Menu number 1 at King Kong Curry*"
)

ORDER_INSTRUCTIONS_LOCATION = (
    "📝 *Placing an Order*\n\n"
    "📌 Step 2. Please enter the *location* you want your food to be delivered to:\n"
    "✅ Example: *SCIS 1 SR 3-1*"
)

ORDER_INSTRUCTIONS_TIME = (
    "📝 *Placing an Order*\n\n"
    "📌 Step 3. Please enter the *date/time* you want to receive your order:\n"
    "✅ Example: *Today, around 1.30 PM*"
)

ORDER_INSTRUCTIONS_DETAILS = (
    "📝 *Placing an Order*\n\n"
    "📌 Step 4. Please enter any *additional info* (enter \"none\" if not applicable):\n"
    "✅ Example: *Extra cutlery please*"
)

ORDER_INSTRUCTIONS_FEE = (
    "📝 *Placing an Order*\n\n"
    "📌 Step 5. Please enter the *delivery fee* you're offering to the runners:\n"
    "✅ Example: *Offering $2 for delivery!*"
)

# Claim success notification
CLAIM_SUCCESS_MESSAGE = (
    "✅ *Order {order_id} Successfully Claimed!*\n\n"
    "👤 *Orderer's Telegram Handle:* @{orderer_handle}\n\n"
    "📌 *Order Info:*\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
    "🚀 *Next Steps:*\n"
    "1️⃣ Buy the meal from the vendor.\n"
    "2️⃣ Confirm purchase via the bot.\n"
    "3️⃣ Deliver to the delivery location.\n"
    "4️⃣ Receive your payment!\n\n"
    "💡 Stay updated with your claimed orders for smooth transactions!"
)

# Order claimed notification for the orderer
ORDER_CLAIMED_NOTIFICATION = (
    "📢 *Your Order Has Been Claimed!*\n\n"
    "📌 *Order ID:* {order_id}\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
    "🚴 Claimed by: {claimed_by}\n\n"
    "📍 *Stay tuned for updates on delivery!*"
)

# Order ID request prompt
ORDER_ID_REQUEST = "🔍 Please enter the *Order ID* you want to claim:"

# Invalid order ID message
INVALID_ORDER_ID = "❌ Invalid Order ID. Please enter a valid number."

# Order length error
ORDER_TOO_LONG = (
    "⚠️ Your message is too long! Please limit it to {max_length} characters.\n\n"
    "📝 *Your message length:* {order_length} characters."
)

ORDER_DETAILS_TOO_LONG = (
    "⚠️ Your message is too long! Please limit it to {max_length} characters.\n\n"
    "📝 *Your message length:* {order_length} characters."
)

ORDER_SUMMARY = """*Order Summary*:
🍽 *Meal:* {order_text}
📍 *Location:* {order_location}
⏳ *Time:* {order_time}
ℹ️ *Details:* {order_details}
💸 *Delivery Fee:* {delivery_fee}

Would you like to confirm this order?
"""

# Order placement confirmation
ORDER_PLACED = (
    "✅ *Order Placed Successfully!*\n\n"
    "📌 *Order ID:* {order_id}\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
    "⚡ Your order has been listed! A food runner will claim it soon."
)

# New order notification in channel
NEW_ORDER = (
    "📢 New Order Available\n\n📌 Order ID: {order_id}\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
)

NEW_CLAIM = (
    "📢 Order {order_id} has been claimed!\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
)

EDITED_ORDER = (
    "📢 Order ID: {order_id} has been edited.\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
)

# No available orders message
NO_ORDERS_AVAILABLE = (
    "⏳ *No orders available right now!*\n\n"
    "💡 Check back later or place an order using /order."
)

# Claim failed or already claimed order message
CLAIM_FAILED = "⚠️ Order {order_id} has already been claimed or does not exist."

# Claim invalid order ID message
CLAIM_INVALID = "❌ *Invalid order claim request.* Please check the order ID and try again."

# General error message
GENERAL_ERROR = "⚠️ Something went wrong. Please try again later."

CLAIM_CONFIRMATION = (
    "✅ You are about to claim *Order ID: {order_id}*.\n\n"
    "🍽 *Meal:* {order_text}\n"
    "📍 *Location:* {order_location}\n"
    "⏳ *Date/Time:* {order_time}\n"
    "ℹ️ *Details:* {order_details}\n"
    "💸 *Delivery Fee Offered:* {delivery_fee}\n\n" 
    "Please confirm by sending the *Order ID* again.\n\n"
    "To cancel, press the *Back* button below."
)
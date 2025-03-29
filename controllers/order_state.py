# controllers/order_state.py

# Global dictionaries to store user state and temporary order data.
user_states = {}  # e.g. { user_id: { 'state': 'awaiting_order_meal', ... } }
user_orders = {}  # e.g. { user_id: { 'meal': ..., 'location': ..., etc. } }
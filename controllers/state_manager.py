from controllers.order_state import user_states

def update_state(user_id: int, new_state: str):
    if user_id in user_states:
        user_states[user_id]['state'] = new_state
    else:
        user_states[user_id] = {'state': new_state}
import re
import pytz
from datetime import datetime
from models.database import SGT

def validate_strict_time_format(user_input: str) -> datetime | None:
    pattern = r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\s+([0-1]?[0-9]):([0-5][0-9])(am|pm)$'
    if not re.match(pattern, user_input.strip().lower()):
        return None
    try:
        year = datetime.now(SGT).year
        full_input = f"{year}-{user_input.strip()}"
        dt = datetime.strptime(full_input, "%Y-%m-%d %I:%M%p")
        dt = SGT.localize(dt)
        return dt
    except Exception:
        return None
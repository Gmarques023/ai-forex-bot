import time
from datetime import datetime

def wait_until_next_interval():
    now = datetime.now()
    current_minute = now.minute
    wait_time = 0
    if current_minute % 15 != 0:
        next_interval_minute = (current_minute // 15 + 1) * 15
        if next_interval_minute == 60:
            next_interval_minute = 0
            next_interval_hour = (now.hour + 1) % 24
            next_interval_time = now.replace(hour=next_interval_hour, minute=next_interval_minute, second=0, microsecond=0)
        else:
            next_interval_time = now.replace(minute=next_interval_minute, second=0, microsecond=0)
        wait_time = (next_interval_time - now).total_seconds()
    time.sleep(wait_time)

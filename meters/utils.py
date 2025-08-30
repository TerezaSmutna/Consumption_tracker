# meters/utils.py
import datetime
from django.utils import timezone


def get_current_month_range(now=None):
    """
    Return a tuple (month_start, next_month) for the current calendar month.
    - month_start: aware datetime at the first day of the current month at 00:00:00
    - next_month: aware datetime at the first day of the next month at 00:00:00

    If `now` is provided, it must be an aware datetime. If not provided,
    timezone.now() is used.
    """
    if now is None:
        now = timezone.now()
    # Normalize to the first day of the current month at midnight
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Move to first day of the next month using the safe 28+4 rule
    next_month = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return month_start, next_month

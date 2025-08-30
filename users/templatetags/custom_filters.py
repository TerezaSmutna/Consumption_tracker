from datetime import datetime, timedelta

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma as django_intcomma

register = template.Library()


@register.filter(name='multiply')
def multiply(value, arg):
    return value * arg


@register.filter(name='has_group')
def has_group(user, group_name):
    """Check if user belongs to a specific group."""
    return user.groups.filter(name=group_name).exists()


@register.filter
def endswith(value, arg):
    """Checks if a string ends with a particular substring."""
    return str(value).endswith(str(arg))


@register.filter
def timedelta_to_minutes(value):
    return value.total_seconds() / 60


@register.filter
def calc_average(value, total):
    """Calculate the average value of a number."""
    if value is None or total is None:
        return None

    try:
        value = int(value)
        total = int(total)
    except (TypeError, ValueError):
        return None

    if total == 0:
        return 0

    return round(value / total, 1)


@register.filter(is_safe=False)
def convert_seconds(value):
    try:
        value = int(value)
        days, remainder = divmod(value, 86400)  # 86400 seconds in a day
        hours, remainder = divmod(remainder, 3600)  # 3600 seconds in an hour
        minutes, seconds = divmod(remainder, 60)  # 60 seconds in a minute

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except (ValueError, TypeError):
        return ""


@register.filter
def format_large_number(value):
    return django_intcomma(value)


@register.filter
def intspace(value):
    if value is None:
        return None

    try:
        value = int(value)
    except (TypeError, ValueError):
        return value

    return '{:,.0f}'.format(value).replace(",", " ")


@register.filter(name='range')
def int_to_range(value):
    return range(value)


@register.filter(name='paginate')
def paginate(current_page, max_pages=5):
    """
    Generate a range of page numbers for pagination.

    Given the current page number (value) and the maximum number of pages to display (max_pages),
    this function returns a range object containing the page numbers to be displayed.

    Args:
        current_page (int): The current page number.
        max_pages (int, optional): The maximum number of pages to display. Defaults to 5.

    Returns:
        range: A range object containing the page numbers to be displayed.
    """
    start = max(1, current_page - max_pages + 1)
    return range(start, current_page + 1)


@register.filter
def has_type(result):
    """Check if the result value is in the list of types."""
    return result in ('Clear', 'SPAM', 'SPAM-TAGGED', 'SPAM-QUARANTINED', 'SPAM-REJECTED', 'SPAM-DELETED')


@register.filter
def get_item_insensitive(dictionary, key):
    """Get an item from a dictionary, case-insensitive."""
    return dictionary.get(key.upper()) or dictionary.get(key.lower())


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(is_safe=False)
def convert_bytes(value, decimal_places=2):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']  # define the units and their sizes in bytes
    size = 1024.0  # define the size of each unit in bytes

    try:
        for unit in units:
            if value < size:
                return f"{value:.{decimal_places}f} {unit}"   # return the value in the appropriate unit with the specified number of decimal places
            value /= size  # if the current unit is too small, divide by the size and try the next unit

        return f"{value:.{decimal_places}f} {units[-1]}"  # return the value in petabytes with the specified number of decimal places
    except (ValueError, TypeError):
        return ""


@register.filter
def is_active(value, urls):
    return any(url in value for url in urls)


@register.filter
def unix_to_datetime(value):
    try:
        return datetime.fromtimestamp(int(value))
    except (ValueError, TypeError):
        return ""


@register.filter(is_safe=False)
def divide(value, arg):
    """Divide the value by the arg."""
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ""


@register.filter(name='zip')
def zip_iterables(value, arg):
    """Zip value iterable with arg iterable"""
    try:
        return zip(value, arg)
    except (ValueError, TypeError):
        return ""


@register.filter(name='get')
def get_element_by_index(sequence, i):
    try:
        return sequence[i]
    except IndexError:
        return ''


@register.filter
def add_hours(dt, hours):
    return dt + timedelta(hours=int(hours))
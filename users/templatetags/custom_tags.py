import re
from math import ceil

from django import template
from django.template.defaultfilters import floatformat, truncatechars

register = template.Library()


@register.filter(name='add_css')
def add_css(field, css):
    return field.as_widget(attrs={"class": css})


@register.simple_tag
def format_state_threshold(state, threshold):
    if (state is None) or (not threshold):
        return 'N/A'
    else:
        return f'{state} / {threshold}'


@register.simple_tag(takes_context=True)
def update_query_string(context, **kwargs):
    request = context['request']
    updated = request.GET.copy()

    for key, value in kwargs.items():
        updated[key] = value

    return updated.urlencode()


@register.simple_tag
def render_scanner(scanner, django_scanners_dict, truncate=None):
    scanner_value = scanner.scanner
    score_or_result = floatformat(scanner.score, -1) if scanner.score else scanner.result

    if scanner_value == "Clear" and scanner.score:
        output = f'Antispam: {score_or_result}'
    elif scanner_value == "Clear" and not scanner.score:
        output = '--'
    else:
        scanner_display = django_scanners_dict.get(scanner_value, scanner_value)
        output = f'{scanner_display}: {score_or_result}'

    if truncate:
        output = truncatechars(output, truncate)

    return output


@register.simple_tag
def clean_result(scanner, result):
    """Some cleaning from PHP: replace "EXE_files_are_not_al" with "EXE files" ???"""
    # Check if 'scanner' is 'Perlscan' and if 'result' starts with 3 uppercase letters
    if scanner == 'Perlscan' and re.match('^[A-Z]{3}', result):
        # If match found, append the match to matches list
        match = re.match('^[A-Z]{3}', result).group()

        # Concatenate the matched string with 'files'
        scanner_result = match + ' files'
    else:
        # Replace '_' with ' ' in 'result'
        scanner_result = result.replace('_', ' ')

    return scanner_result


@register.simple_tag
def calc_relative(value, total):
    """Calculate the relative value of a number."""
    if value is None or total is None:
        return None

    try:
        value = int(value)
        total = int(total)
    except (TypeError, ValueError):
        return None

    if total == 0:
        return 0

    return round(value / total * 100, 1)


@register.simple_tag
def get_scanner_switch_title(scanners_qs, group):
    if not scanners_qs:
        return "No available scanner in this category"
    else:
        scanners = ", ".join(scanner.name for scanner in scanners_qs)
        return f"Toggle {group} scanners: {scanners}"


@register.simple_tag
def search_pagination(current_page, total_pages, max_pages=5):
    if total_pages in {max_pages + 1, max_pages + 2}:
        return range(1, total_pages + 1)

    mid_pages = max_pages // 2
    # If the current page is less than max_pages.
    if current_page < max_pages:
        return range(1, min(total_pages + 1, max_pages + 1))
    # If the current page is near the end.
    elif current_page > total_pages - max_pages + 1:
        return range(max(1, total_pages - max_pages + 1), total_pages + 1)
    # If the current page is somewhere in the middle.
    else:
        return range(current_page - mid_pages, current_page + mid_pages + 1)

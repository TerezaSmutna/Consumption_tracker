# evidence_spotreby/formats/cs/formats.py

# Default date/time formats for Czech locale.
# These control how Django formats values when using {% localize %},
# form fields, admin, etc.
# They DO NOT provide translated month/weekday names (that comes from gettext).

# Full date, e.g. "1. září 2025"
DATE_FORMAT = "j. F Y"

# Full date + time, e.g. "1. září 2025 14:30"
DATETIME_FORMAT = "j. F Y H:i"

# Time only, e.g. "14:30"
TIME_FORMAT = "H:i"

# Year + month, e.g. "září 2025"
YEAR_MONTH_FORMAT = "F Y"

# Month + day, e.g. "1. září"
MONTH_DAY_FORMAT = "j. F"

# Short formats (for inputs, admin widgets, etc.)
SHORT_DATE_FORMAT = "d.m.Y"
SHORT_DATETIME_FORMAT = "d.m.Y H:i"

# Separators
DECIMAL_SEPARATOR = ","
THOUSAND_SEPARATOR = "\xa0"  # non-breaking space, common in Czech
NUMBER_GROUPING = 3

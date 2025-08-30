Translation files live here.

How to extract/update messages and compile translations:

1) Create/Update message catalogs (example for Czech and English):
   python manage.py makemessages -l cs -l en

2) Edit the created files under locale\cs\LC_MESSAGES\django.po and locale\en\LC_MESSAGES\django.po

3) Compile catalogs:
   python manage.py compilemessages

Notes:
- Ensure you have gettext utilities installed (msgfmt, xgettext).
- Django's built-in strings (including admin) are translated automatically; you only need to translate your app's strings.
- Add {% load i18n %} in templates and wrap text in {% trans %} or {% blocktrans %}.
- In Python, wrap user-visible strings with gettext: from django.utils.translation import gettext as _

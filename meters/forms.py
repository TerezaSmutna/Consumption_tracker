# meters/forms.py
import datetime

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Reading, Meter, Room, MeterType
from .utils import get_current_month_range


class BootstrapModelForm(forms.ModelForm):
    """Base form which applies Bootstrap 'form-control' to all widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs.update({"class": f"{css_class} form-control".strip()})


class ReadingForm(BootstrapModelForm):
    def __init__(self, *args, meter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.meter = meter

    class Meta:
        model = Reading
        fields = ["value"]

    def clean(self):
        cleaned_data = super().clean()
        meter = getattr(self, "meter", None)
        # When editing an existing reading, don't block on duplicate check
        is_new = self.instance.pk is None
        if meter is not None and is_new:
            # Determine current month window in aware datetimes
            month_start, next_month = get_current_month_range()
            exists = Reading.objects.filter(
                meter=meter,
                timestamp__gte=month_start,
                timestamp__lt=next_month,
            ).exists()
            if exists:
                raise forms.ValidationError(_("A reading for this meter already exists for this month."))
        return cleaned_data


class MeterForm(BootstrapModelForm):
    class Meta:
        model = Meter
        fields = ["name", "type", "room"]


class RoomForm(BootstrapModelForm):
    class Meta:
        model = Room
        fields = ["name"]


class MeterTypeForm(BootstrapModelForm):
    class Meta:
        model = MeterType
        fields = ["name", "unit"]


class MonthRangeForm(forms.Form):
    start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month", "class": "form-control"}),
        label=_("Start month"),
        input_formats=["%Y-%m"],
    )
    end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "month", "class": "form-control"}),
        label=_("End month"),
        input_formats=["%Y-%m"],
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        print(f'start: {start}, end: {end}')

        if start:
            start = start.replace(day=1)
            cleaned_data["start"] = timezone.make_aware(datetime.datetime.combine(start, datetime.time.min))

        if end:
            # move to first day of next month
            next_month = (end.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            cleaned_data["end"] = timezone.make_aware(datetime.datetime.combine(next_month, datetime.time.min))

        if start and end and start > end:
            raise forms.ValidationError(_("Start month cannot be after end month."))

        return cleaned_data

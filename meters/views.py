# meters/views.py
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, CreateView, TemplateView, ListView, UpdateView, View
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
from django.conf import settings

from .forms import ReadingForm, MonthRangeForm
from .models import Meter, Reading, MeterType, Room
from .utils import get_current_month_range
from .services import get_overview_data, get_meter_type_data
from collections import defaultdict



class MeterListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Meter
    template_name = "meters/meter_list.html"
    context_object_name = "meters"
    paginate_by = 20
    permission_required = "meters.view_meter"
    

class BaseMeterPermissionView(PermissionRequiredMixin):
    permission_required = "meters.view_meter"
    
class OverviewView(BaseMeterPermissionView, View):
    def get(self, request, *args, **kwargs):
        first = MeterType.objects.order_by("id").first()

        if not first:
            return redirect("meter_list")

        # ALWAYS go to first meter type
        return redirect("meter_type_detail", pk=first.id)


class ReadingCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Reading
    form_class = ReadingForm
    template_name = "meters/reading_form.html"
    permission_required = "meters.add_reading"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get(self, request, *args, **kwargs):
        # If a reading exists for the current calendar month, redirect to edit view
        meter = get_object_or_404(Meter, slug=self.kwargs["slug"])
        month_start, next_month = get_current_month_range()
        exists = Reading.objects.filter(
            meter=meter,
            timestamp__gte=month_start,
            timestamp__lt=next_month,
        ).exists()
        if exists:
            return self.redirect_to_edit()
        return super().get(request, *args, **kwargs)

    def redirect_to_edit(self):
        return redirect(reverse_lazy("reading_edit", kwargs={"slug": self.kwargs["slug"]}))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        meter = get_object_or_404(Meter, slug=self.kwargs["slug"])
        kwargs["meter"] = meter
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meter = get_object_or_404(Meter, slug=self.kwargs["slug"])
        context["meter"] = meter
        return context

    def form_valid(self, form):
        meter = get_object_or_404(Meter, slug=self.kwargs["slug"])
        form.instance.meter = meter
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("reading_detail", kwargs={"slug": self.kwargs["slug"]})


class ReadingUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Reading
    form_class = ReadingForm
    template_name = "meters/reading_form.html"
    permission_required = "meters.change_reading"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        meter = get_object_or_404(Meter, slug=self.kwargs["slug"])
        month_start, next_month = get_current_month_range()
        return get_object_or_404(
            Reading,
            meter=meter,
            timestamp__gte=month_start,
            timestamp__lt=next_month,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["meter"] = self.get_object().meter if self.object is None else self.object.meter
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ensure meter is available for template
        context["meter"] = self.object.meter
        return context

    def get_success_url(self):
        return reverse_lazy("reading_detail", kwargs={"slug": self.kwargs["slug"]})


class ReadingDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Meter
    template_name = "meters/reading_detail.html"
    context_object_name = "meter"
    permission_required = "meters.view_reading"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = MonthRangeForm(self.request.GET or None)
        context["form"] = form

        meter = self.object

        # default range: last 12 months including current month
        month_start = timezone.now().date().replace(day=1)
        # start from the first day 12 months ago
        default_start = (month_start - datetime.timedelta(days=365)).replace(day=1)
        # end is exclusive: first day of the next month to include current month/today
        next_month = (month_start.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

        # defaults as aware datetimes
        start_dt = timezone.make_aware(datetime.datetime.combine(default_start, datetime.time.min))
        end_dt = timezone.make_aware(datetime.datetime.combine(next_month, datetime.time.min))

        if form.is_valid():
            if form.cleaned_data.get("start"):
                start_dt = form.cleaned_data["start"]  # already aware
            if form.cleaned_data.get("end"):
                end_dt = form.cleaned_data["end"]  # already aware

        qs = (
            Reading.objects.filter(
                meter=meter,
                timestamp__gte=start_dt,
                timestamp__lt=end_dt,
            )
            .annotate(month=TruncMonth("timestamp"))
            .values("month", "value")
             # .annotate(total=Sum("value"))
            .order_by("month")
        )

        monthly_data = list(qs)
        monthly_sum = sum(row["value"] for row in monthly_data if row["value"] is not None)

        context["monthly_data"] = monthly_data
        context["monthly_sum"] = monthly_sum
        return context


class ReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "meters/report.html"
    permission_required = "meters.view_reading"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # agregace spotřeby per meter, per month
        qs = (
            Reading.objects
            .annotate(month=TruncMonth("timestamp"))
            .values("meter__name", "meter__type__unit", "month")
            .annotate(total=Sum("value"))
            .order_by("meter__name", "month")
        )

        context["report"] = qs
        return context


class MeterTypeOverviewView(BaseMeterPermissionView, TemplateView):
    template_name = "overview/meter_type_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        meter_type = MeterType.objects.get(pk=self.kwargs["pk"])
        mode = self.request.GET.get("mode", "monthly")

        selected_years = self.request.GET.getlist("years")
        selected_years = [int(y) for y in selected_years if y.isdigit()]

        rooms = Room.objects.filter(
            meters__type=meter_type
        ).distinct()

        data = []

        all_years = set()
        all_months = set()

        for room in rooms:
            meters = room.meters.filter(type=meter_type)

            for meter in meters:
                readings = meter.readings.all()

                monthly_data = {}
                yearly_data = {}

                grouped_months = defaultdict(list)
                grouped_years = defaultdict(list)

                for r in readings:
                    year = r.timestamp.year
                    month = r.timestamp.month

                    grouped_months[(month, year)].append(r)
                    grouped_years[year].append(r)

                    all_years.add(year)
                    all_months.add((month, year))

                for key, values in grouped_months.items():
                    latest = max(values, key=lambda x: x.timestamp)
                    monthly_data[key] = latest.value

                for year, values in grouped_years.items():
                    latest = max(values, key=lambda x: x.timestamp)
                    yearly_data[year] = latest.value

                meter.monthly_data = monthly_data
                meter.yearly_data = yearly_data

            data.append({
                "room": room,
                "meters": meters
            })

        months = sorted(all_months, key=lambda x: (x[1], x[0]))
        years = sorted(all_years)

        if not selected_years and years:
            selected_years = [years[-1]]

        if selected_years:
            months = [m for m in months if m[1] in selected_years]
            years = [y for y in years if y in selected_years]

        context.update({
            "meter_type": meter_type,
            "data": data,
            "mode": mode,
            "months": months,
            "years": years,
            "all_years": sorted(all_years),
            "selected_years": selected_years,
        })

        return context
    

def link_callback(uri, rel):
    result = finders.find(uri.replace(settings.STATIC_URL, '', 1))
    if result:
        return result
    return uri

def meter_type_pdf(request, pk):
    meter_type = MeterType.objects.get(pk=pk)
    mode = request.GET.get("mode", "monthly")
    selected_years = request.GET.getlist("years")
    selected_years = [int(y) for y in selected_years if y.isdigit()]

    rooms = Room.objects.filter(meters__type=meter_type).distinct()
    data = []
    all_years = set()
    all_months = set()

    for room in rooms:
        meters = room.meters.filter(type=meter_type)
        for meter in meters:
            readings = meter.readings.all()
            monthly_data = {}
            yearly_data = {}
            grouped_months = defaultdict(list)
            grouped_years = defaultdict(list)

            for r in readings:
                year = r.timestamp.year
                month = r.timestamp.month
                grouped_months[(month, year)].append(r)
                grouped_years[year].append(r)
                all_years.add(year)
                all_months.add((month, year))

            for key, values in grouped_months.items():
                latest = max(values, key=lambda x: x.timestamp)
                monthly_data[key] = latest.value

            for year, values in grouped_years.items():
                latest = max(values, key=lambda x: x.timestamp)
                yearly_data[year] = latest.value

            meter.monthly_data = monthly_data
            meter.yearly_data = yearly_data

        data.append({"room": room, "meters": meters})

    months = sorted(all_months, key=lambda x: (x[1], x[0]))
    years = sorted(all_years)

    if not selected_years and years:
        selected_years = [years[-1]]
    if selected_years:
        months = [m for m in months if m[1] in selected_years]
        years = [y for y in years if y in selected_years]

    context = {
        "meter_type": meter_type,
        "data": data,
        "mode": mode,
        "months": months,
        "years": years,
        "selected_years": selected_years,
        "STATIC_URL": settings.STATIC_URL,
    }

    template = get_template("overview/overview_pdf.html")
    html = template.render(context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{meter_type.name}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response, encoding="UTF-8", link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse("Error generating PDF: <pre>" + html + "</pre>")
    return response

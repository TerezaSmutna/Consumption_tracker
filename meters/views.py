# meters/views.py
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, CreateView, TemplateView, ListView, UpdateView
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from .forms import ReadingForm, MonthRangeForm
from .models import Meter, Reading
from .utils import get_current_month_range
from .services import get_overview_data


class MeterListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Meter
    template_name = "meters/meter_list.html"
    context_object_name = "meters"
    paginate_by = 20
    permission_required = "meters.view_meter"
    
class OverviewView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Meter
    template_name = "overview/overview.html"
    context_object_name = "overview"
    paginate_by = 20
    permission_required = "meters.view_meter"


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


class OverviewView(TemplateView):
    template_name = "overview/overview.html"
    title = _("Overview")

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context["overview"] = get_overview_data()
        return context
    

def overview_export_pdf(request):
    overview = get_overview_data()

    template_path = 'overview/overview_pdf.html'
    context = {'overview': overview}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="overview.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
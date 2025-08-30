# meters/models.py
from cProfile import label

from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Room(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    def __str__(self):
        return self.name


class MeterType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    unit = models.CharField(max_length=20, verbose_name=_("Unit"))  # for example: "kWh", "KJ"

    class Meta:
        verbose_name = _("Meter type")
        verbose_name_plural = _("Meter types")

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Meter(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    type = models.ForeignKey(MeterType, on_delete=models.CASCADE, related_name="meters", verbose_name=_("Type"))
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="meters", verbose_name=_("Room"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name=_("Slug"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("Meter")
        verbose_name_plural = _("Meters")

    def save(self, *args, **kwargs):
        if not self.slug:  # auto-generate slug on first save
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Reading(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name="readings", verbose_name=_("Meter"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    value = models.DecimalField(verbose_name=_("Value"), max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = _("Reading")
        verbose_name_plural = _("Readings")

    def __str__(self):
        return f"{self.meter.name} - {self.timestamp.date()} - {self.value}"


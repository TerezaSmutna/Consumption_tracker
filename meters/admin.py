from django.contrib import admin
from .models import Room, MeterType, Meter, Reading


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(MeterType)
class MeterTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit")
    search_fields = ("name", "unit")


@admin.register(Meter)
class MeterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "room")
    list_filter = ("type", "room")
    search_fields = ("name",)
    autocomplete_fields = ("type", "room")


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("id", "meter", "value", "timestamp")
    list_filter = ("meter", "timestamp")
    search_fields = ("meter__name",)
    date_hierarchy = "timestamp"
    autocomplete_fields = ("meter",)

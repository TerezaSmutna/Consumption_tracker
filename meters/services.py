from .models import Meter, MeterType
from decimal import Decimal
from collections import defaultdict

def get_overview_data():
    overview_items = []

    meter_types = MeterType.objects.all()

    for meter_type in meter_types:
        meters = meter_type.meters.all()

        total = Decimal("0.00")

        for meter in meters:
            latest = meter.readings.order_by("-timestamp").first()

            if latest:
                total += latest.value

        overview_items.append(
            {
                "meter_type": meter_type.name,
                "unit": meter_type.unit,
                "total": total,
            }
        )

    return overview_items

def get_meter_type_data(meter_type_id, mode):
    meters = Meter.objects.filter(type_id=meter_type_id).select_related("room")

    result = defaultdict(lambda: {"meters": [], "columns": set()})

    for meter in meters:
        readings = meter.readings.all()

        grouped = {}

        for r in readings:
            if mode == "monthly":
                key = r.timestamp.strftime("%m/%y")
            else:
                key = r.timestamp.strftime("%Y")

            grouped[key] = r.value
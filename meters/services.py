from .models import MeterType
from decimal import Decimal

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
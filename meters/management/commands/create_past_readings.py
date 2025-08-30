from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from meters.models import Room, MeterType, Meter, Reading


class Command(BaseCommand):
    help = "Create monthly past readings for a meter (one per month)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--meter-name",
            type=str,
            default=None,
            help="Name of the meter to target. If omitted, uses the first meter or creates a demo one.",
        )
        parser.add_argument(
            "--months",
            type=int,
            default=20,
            help="How many months in the past to create (default: 20).",
        )
        parser.add_argument(
            "--value-start",
            type=str,
            default="100.00",
            help="Starting decimal value for the first created reading (default: 100.00).",
        )
        parser.add_argument(
            "--increment",
            type=str,
            default="1.00",
            help="Increment added each subsequent month (default: 1.00).",
        )
        parser.add_argument(
            "--include-current",
            action="store_true",
            help="Include the current month (by default current month is skipped).",
        )

    @staticmethod
    def month_anchor(dt):
        # first day of month at noon to avoid DST edge cases
        return dt.replace(day=1, hour=12, minute=0, second=0, microsecond=0)

    @staticmethod
    def add_months(dt, months):
        # dt assumed to be at day=1
        y = dt.year + (dt.month - 1 + months) // 12
        m = (dt.month - 1 + months) % 12 + 1
        return dt.replace(year=y, month=m)

    def handle(self, *args, **options):
        meter_name = options.get("meter_name")
        months = options.get("months")
        value_start_raw = options.get("value_start")
        increment_raw = options.get("increment")
        include_current = options.get("include_current")

        if months <= 0:
            raise CommandError("--months must be a positive integer")

        try:
            base_value = Decimal(value_start_raw)
            increment = Decimal(increment_raw)
        except (InvalidOperation, TypeError):
            raise CommandError("--value-start and --increment must be valid decimals, e.g., 100.00")

        # Select or create a meter
        meter = None
        if meter_name:
            try:
                meter = Meter.objects.get(name=meter_name)
            except Meter.DoesNotExist:
                raise CommandError(f"Meter with name '{meter_name}' does not exist.")
        else:
            meter = Meter.objects.first()
            if meter is None:
                room, _ = Room.objects.get_or_create(name="Default Room")
                mtype, _ = MeterType.objects.get_or_create(name="Electricity", unit="kWh")
                meter = Meter.objects.create(name="Demo Meter", type=mtype, room=room)
                self.stdout.write(self.style.WARNING(f"No meters found; created demo meter: {meter.name}"))

        now = timezone.now()
        start = self.month_anchor(now)

        # Build range: by default skip current month; create strictly in the past.
        # We'll iterate oldest->newest for deterministic values.
        created = 0
        checked = 0

        # If include_current: create months from (months-1) months ago up to current month (0)
        # Else: from months months ago up to 1 month ago.
        start_offset = months if not include_current else months - 1
        end_offset = 0 if include_current else 1

        for i in range(start_offset, end_offset - 1, -1):
            target_ts = self.add_months(start, -i)
            checked += 1

            exists = Reading.objects.filter(
                meter=meter,
                timestamp__year=target_ts.year,
                timestamp__month=target_ts.month,
            ).exists()
            if exists:
                continue

            # Determine value for this reading
            step_index = (start_offset - i)  # 0-based progression
            value = base_value + (increment * Decimal(step_index))

            r = Reading.objects.create(meter=meter, value=value)
            # Update timestamp with a direct update to bypass auto_now_add
            Reading.objects.filter(pk=r.pk).update(timestamp=target_ts)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Checked {checked} months, created {created} readings for meter '{meter.name}'."
            )
        )

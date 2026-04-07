
from . import __version__
from meters.models import MeterType


def version(request):
    return {'VERSION': __version__}


def meter_types(request):
    return {
        "meter_types": MeterType.objects.all()
    }

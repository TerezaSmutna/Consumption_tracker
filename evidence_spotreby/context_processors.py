
from . import __version__

def version(request):
    return {'VERSION': __version__}

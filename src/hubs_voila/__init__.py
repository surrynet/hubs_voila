from pkg_resources import get_distribution

try:
    __version__ = get_distribution(__name__).version
except Exception:
    __version__ = '1.0.2'

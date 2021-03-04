from importlib.metadata import version

PROJECT_NAME = "doni"

try:
    __version__ = version(__name__)
except:
    pass

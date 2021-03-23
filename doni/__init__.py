try:
    from importlib.metadata import version
except:
    # Python < 3.7
    from importlib_metadata import version

PROJECT_NAME = "doni"

try:
    __version__ = version(__name__)
except:
    pass

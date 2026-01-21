from importlib.metadata import PackageNotFoundError, version

from .base import DigitalTwin

try:
    __version__ = version("echoed")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["DigitalTwin", "__version__"]

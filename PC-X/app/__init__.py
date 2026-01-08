"""PC-X application package."""

from app.config import VERSION  # noqa: F401
from app.main import PCToolsModule  # noqa: F401

__all__ = ["PCToolsModule", "VERSION"]

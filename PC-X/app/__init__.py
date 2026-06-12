"""PC-X application package."""

from app.config import VERSION  # noqa: F401

__all__ = ["PCToolsModule", "VERSION"]


def __getattr__(name: str):
    """Lazily expose GUI objects without importing Qt during config access."""
    if name == "PCToolsModule":
        from app.main import PCToolsModule

        return PCToolsModule
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

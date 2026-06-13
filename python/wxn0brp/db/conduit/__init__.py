__all__ = ["Collection", "ValtheraConduit", "ValtheraConduitError", "ValtheraDb", "ensure_binary"]


def __getattr__(name: str):
    if name in {"Collection", "ValtheraConduit", "ValtheraConduitError", "ValtheraDb"}:
        from . import client

        return getattr(client, name)
    if name == "ensure_binary":
        from .install import ensure_binary

        return ensure_binary
    raise AttributeError(name)

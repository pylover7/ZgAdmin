from fastapi import APIRouter

from .email import emailProtectedRouter  # noqa: F401

settingsRouter = APIRouter()

__all__ = ["settingsRouter"]

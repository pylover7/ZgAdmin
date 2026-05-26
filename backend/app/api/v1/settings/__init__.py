from fastapi import APIRouter

from .email import emailProtectedRouter

settingsRouter = APIRouter()

__all__ = ["settingsRouter"]

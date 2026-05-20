from fastapi import APIRouter

from .general import generalPublicRouter, generalProtectedRouter

settingsRouter = APIRouter()

__all__ = ["settingsRouter"]

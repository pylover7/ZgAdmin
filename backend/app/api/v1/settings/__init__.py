from fastapi import APIRouter

from .general import generalPublicRouter, generalProtectedRouter
from .security import securityPublicRouter, securityProtectedRouter

settingsRouter = APIRouter()

__all__ = ["settingsRouter"]

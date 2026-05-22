from fastapi import APIRouter

from .general import generalProtectedRouter
from .security import securityProtectedRouter

settingsRouter = APIRouter()

__all__ = ["settingsRouter"]

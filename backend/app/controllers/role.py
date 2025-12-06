from uuid import UUID
from sqlmodel import Session

from app.core.crud import CRUDBase
from app.models import Role, RoleCreate, RoleUpdate
from app.controllers.menu import menuController
from app.controllers.api import apiController


class RoleController(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def __init__(self):
        super().__init__(Role)

    async def updateMenus(self, session: Session, id: UUID, menuIds: list[UUID]):
        role_obj = await self.get(session, id)
        if not role_obj:
            return None
        role_obj.menus.clear()
        for item in menuIds:
            menu_obj = await menuController.get(session, item)
            if not menu_obj:
                continue
            role_obj.menus.append(menu_obj)
        session.add(role_obj)
        session.commit()

    async def updateApis(self, session: Session, id: UUID, apiIds: list[UUID]):
        role_obj = await self.get(session, id)
        if not role_obj:
            return None
        role_obj.apis.clear()
        for item in apiIds:
            if "/" in str(item):
                continue
            api_obj = await apiController.get(session, item)
            if not api_obj:
                continue
            role_obj.apis.append(api_obj)
        session.add(role_obj)
        session.commit()


roleController = RoleController()

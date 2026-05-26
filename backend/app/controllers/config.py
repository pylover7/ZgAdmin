"""单行配置表统一控制器 — 所有全局配置表共享同一模式：
获取唯一行 / 更新字段 / 敏感字段脱敏"""
from typing import Type, TypeVar

from sqlmodel import Session, select, SQLModel

T = TypeVar("T", bound=SQLModel)
U = TypeVar("U", bound=SQLModel)


class ConfigController:
    """单行配置表控制器 — 不继承 CRUDBase，因为单行表的访问模式与多行 CRUD 完全不同"""

    def __init__(self, model: Type[T], update_model: Type[U]):
        self.model = model
        self.update_model = update_model

    def get(self, session: Session) -> T | None:
        """获取全局唯一配置行"""
        return session.exec(select(self.model)).first()

    def update(self, session: Session, data: U) -> T | None:
        """更新配置，敏感字段空值时保留原值"""
        config = self.get(session)
        if not config:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude={"id"})
        sensitive_fields = getattr(self.model, "SENSITIVE_FIELDS", [])

        # 敏感字段：空值不更新（保留原值）
        for field in sensitive_fields:
            if field in update_data and not update_data[field]:
                update_data.pop(field)

        for key, value in update_data.items():
            setattr(config, key, value)

        session.add(config)
        session.commit()
        session.refresh(config)
        return config

    def mask_sensitive(self, data: dict) -> dict:
        """对敏感字段返回空值"""
        sensitive_fields = getattr(self.model, "SENSITIVE_FIELDS", [])
        for field in sensitive_fields:
            if field in data:
                data[field] = ""
        return data


# ─── 实例 ────────────────────────────────────────────────────────────────

from app.models.config import SiteConfig, SiteConfigUpdate
from app.models.config import OAuthConfig, OAuthConfigUpdate
from app.models.config import EmailConfig, EmailConfigUpdate
from app.models.security import SecurityPolicy, SecurityPolicyUpdate

siteConfigController = ConfigController(SiteConfig, SiteConfigUpdate)
oauthConfigController = ConfigController(OAuthConfig, OAuthConfigUpdate)
emailConfigController = ConfigController(EmailConfig, EmailConfigUpdate)
securityPolicyController = ConfigController(SecurityPolicy, SecurityPolicyUpdate)

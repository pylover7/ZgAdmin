from datetime import datetime, timedelta, timezone
import urllib.parse
import secrets
import jwt
import httpx

from fastapi import HTTPException
from sqlmodel import select

from app.models.login import JWTPayload
from app.settings import settings
from app.core.database import DatabaseSession
from app.models.config import OAuthConfig
from app.models import User
from app.models.login import QQAccessToken, QQUserInfo
from app.settings.log import logger
from app.utils.password import get_password_hash


def create_access_token(*, data: JWTPayload) -> str:
    """
    创建访问令牌

    :param data: 数据
    :return: 令牌
    """
    payload = data.model_dump().copy()
    encoded_jwt = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> JWTPayload:
    """
    解码访问令牌

    :param token: 令牌
    :return: 数据
    """
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[
            settings.JWT_ALGORITHM])
    return JWTPayload(**payload)


async def get_qq_access_token(code: str) -> QQAccessToken:
    """使用授权码获取access_token"""
    with DatabaseSession() as session:
        oauth_config = session.exec(select(OAuthConfig)).first()

    app_id = (oauth_config.qq_app_id if oauth_config and oauth_config.qq_app_id else None) or settings.QQ_APP_ID
    app_key = (oauth_config.qq_app_key if oauth_config and oauth_config.qq_app_key else None) or settings.QQ_APP_KEY
    redirect_uri = (oauth_config.qq_redirect_uri if oauth_config and oauth_config.qq_redirect_uri else None) or settings.QQ_REDIRECT_URI

    # URL编码确保参数安全
    encoded_redirect_uri = urllib.parse.quote(redirect_uri, safe='')

    token_url = (
        f"https://graph.qq.com/oauth2.0/token?"
        f"grant_type=authorization_code&"
        f"client_id={app_id}&"
        f"client_secret={app_key}&"
        f"code={code}&"
        f"redirect_uri={encoded_redirect_uri}"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(token_url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="获取QQ access_token失败")

            # 解析返回的查询参数
            query_params = urllib.parse.parse_qs(response.text)

            # 验证必需参数
            access_token = query_params.get("access_token", [None])[0]
            openid = query_params.get("openid", [None])[0]
            expires_in = query_params.get("expires_in", ["0"])[0]

            if not access_token or not openid:
                raise HTTPException(status_code=400, detail="QQ API返回参数不完整")

            return QQAccessToken(
                access_token=access_token,
                expires_in=int(expires_in) if expires_in.isdigit() else 0,
                refresh_token=query_params.get("refresh_token", [None])[0] or "",
                openid=openid,
                scope=query_params.get("scope", [None])[0] or "",
                unionid=query_params.get("unionid", [None])[0]
            )
        except httpx.RequestError as e:
            logger.error(f"QQ API请求失败: {str(e)}")
            raise HTTPException(status_code=500, detail="QQ服务不可用") from e


async def get_qq_userinfo(access_token: str, openid: str) -> QQUserInfo:
    """获取QQ用户信息"""
    with DatabaseSession() as session:
        oauth_config = session.exec(select(OAuthConfig)).first()

    app_id = (oauth_config.qq_app_id if oauth_config and oauth_config.qq_app_id else None) or settings.QQ_APP_ID

    userinfo_url = (
        f"https://graph.qq.com/user/get_user_info?"
        f"access_token={access_token}&"
        f"oauth_consumer_key={app_id}&"
        f"openid={openid}"
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(userinfo_url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="获取QQ用户信息失败")

            user_data = response.json()

            if user_data.get("ret") != 0:
                error_msg = user_data.get('msg', '未知错误')
                logger.error(f"QQ用户信息API错误: {error_msg}")
                raise HTTPException(status_code=400, detail=f"QQ API错误: {error_msg}")

            # 获取头像，优先使用高清头像
            avatar = (
                user_data.get("figureurl_qq_2")
                or user_data.get("figureurl_qq_1")
                or ""
            )

            return QQUserInfo(
                openid=openid,
                nickname=user_data.get("nickname", "QQ用户"),
                avatar=avatar,
                unionid=None  # 需要额外API调用获取
            )
        except httpx.RequestError as e:
            logger.error(f"QQ用户信息API请求失败: {str(e)}")
            raise HTTPException(status_code=500, detail="QQ服务不可用") from e


async def find_or_create_qq_user(session, qq_userinfo: QQUserInfo) -> User:
    """查找或创建QQ用户"""
    try:
        # 首先通过openid查找用户
        statement = select(User).where(User.qq_openid == qq_userinfo.openid)
        user = session.exec(statement).first()

        if user:
            # 更新用户信息
            if qq_userinfo.nickname:
                user.qq_nickname = qq_userinfo.nickname
                user.nickname = qq_userinfo.nickname
            if qq_userinfo.avatar:
                user.qq_avatar = qq_userinfo.avatar
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

        # 如果用户不存在，创建新用户
        timestamp = str(int(datetime.now().timestamp()))
        new_user = User(
            username=f"qq_{qq_userinfo.openid[:8]}_{timestamp}",
            email=f"qq_{qq_userinfo.openid}@qq.local",  # 临时邮箱
            password=get_password_hash("qq_default_password"),  # 默认密码
            nickname=qq_userinfo.nickname or f"QQ用户_{qq_userinfo.openid[:8]}",
            qq_openid=qq_userinfo.openid,
            qq_nickname=qq_userinfo.nickname,
            qq_avatar=qq_userinfo.avatar,
            status=1,
            is_superuser=False
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        logger.info(f"成功创建QQ用户: {new_user.username}")
        return new_user

    except Exception as e:
        logger.error(f"创建或更新QQ用户失败: {str(e)}")
        session.rollback()
        raise HTTPException(status_code=500, detail="用户信息保存失败") from e


def create_oauth_state(purpose: str = "qq_login") -> str:
    """创建OAuth state令牌 — JWT签名防CSRF"""
    payload = {
        "purpose": purpose,
        "nonce": secrets.token_hex(16),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_oauth_state(state: str, purpose: str = "qq_login") -> bool:
    """验证OAuth state令牌"""
    try:
        payload = jwt.decode(
            state, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("purpose") == purpose
    except jwt.ExpiredSignatureError:
        logger.warning("OAuth state令牌已过期")
    except jwt.InvalidTokenError:
        logger.warning("OAuth state令牌无效")
    return False

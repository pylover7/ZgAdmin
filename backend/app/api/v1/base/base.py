import hashlib
import urllib.parse
from datetime import timedelta, datetime
from pathlib import Path
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Request, HTTPException, Query, Depends, Header
from fastapi.responses import FileResponse
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import jwt
from sqlalchemy.orm import selectinload, InstrumentedAttribute
from sqlalchemy import func
from sqlmodel import select, col, Session

from app.controllers.department import deptController
from app.controllers.user import userController
from app.settings.log import logger
from app.models.login import CredentialsSchema, JWTPayload, JWTOut, refreshTokenSchema, \
    JWTReOut, QQLoginSchema
from app.models.logs import LoginLog
from app.models.security import SecurityPolicy
from app.core.dependency import DependUser, DependRateLimit, SessionDep, get_db
from app.core.redis import get_redis
from app.models import Api, Menu, Role, User, UpdatePassword, UpdateProfile, UpdatePreferences
from app.models.file import File
from app.models.base import Fail, Success, FailAuth, SuccessExtra
from app.controllers.config import siteConfigController, oauthConfigController, securityPolicyController
from app.settings import settings
from app.utils import menuTree
from app.utils.captcha import generate_captcha, verify_captcha
from app.utils.jwtt import create_access_token, decode_access_token, \
    get_qq_access_token, get_qq_userinfo, find_or_create_qq_user, \
    create_oauth_state, verify_oauth_state
from app.utils.password import get_password_hash, verify_password
from app.utils.password_policy import validate_password_strength, check_password_history, update_password_history
from app.utils.signed_url import verify_signed_url

router = APIRouter()


@router.get("/captcha", summary="获取登录验证码")
async def get_captcha():
    """获取服务端图形验证码（公开接口，无需认证）"""
    redis = get_redis()
    captcha_key, captcha_image = await generate_captcha(redis)
    return Success(data={
        "captcha_key": captcha_key,
        "captcha_image": captcha_image,
    })


@router.get("/init", summary="获取前端初始化配置（公开）")
async def get_init_config(session: SessionDep):
    """一次性返回前端初始化所需的所有公开数据：站点信息、功能开关、安全配置"""
    # 站点信息
    site_config = siteConfigController.get(session)
    site = (await site_config.to_dict()) if site_config else {
        "site_name": "ZgAdmin",
        "site_desc": "一个开源的在线工具箱",
        "logo": "",
        "default_lang": "zh-CN",
        "copyright": "",
        "icp": "",
    }
    # 功能开关
    oauth_config = oauthConfigController.get(session)
    features = {
        "qq_login": settings.FEATURE_QQ_LOGIN and (
            bool(oauth_config.qq_app_id) if oauth_config else bool(settings.QQ_APP_ID)),
        "wechat_login": settings.FEATURE_WECHAT_LOGIN,
        "email": settings.FEATURE_EMAIL,
        "monitor_log": settings.FEATURE_MONITOR_LOG,
    }
    # 安全配置
    policy = securityPolicyController.get(session)
    security = {
        "captcha_enabled": policy.captcha_enabled if policy else True,
    }
    return Success(data={
        "site": site,
        "features": features,
        "security": security,
    })


@router.get("/health", summary="健康检查")
async def health_check():
    return {"status": "ok"}


@router.post("/accessToken", summary="获取token", dependencies=[DependRateLimit])
async def login_access_token(
        session: SessionDep, request: Request, credentials: CredentialsSchema):
    # 验证码校验
    policy = session.exec(select(SecurityPolicy)).first()
    captcha_enabled = policy.captcha_enabled if policy else True

    if captcha_enabled:
        if not credentials.captcha_key or not credentials.captcha_code:
            return Fail(msg="请输入验证码")
        redis = get_redis()
        captcha_valid = await verify_captcha(redis, credentials.captcha_key, credentials.captcha_code)
        if not captcha_valid:
            return Fail(msg="验证码错误或已过期")

    user: User | None = await userController.authenticate(
        session=session,
        credentials=credentials,
        request=request
    )
    if not user:
        return FailAuth(msg="用户名或密码错误！")
    await userController.update_last_login(session=session, pk=user.id)
    roles = [item.code for item in user.roles]
    try:
        depart = deptController.get_all_name(session, user)
    except Exception:
        logger.debug("获取部门名称失败")
        depart = ""
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now() + access_token_expires
    expire_refresh = datetime.now() + refresh_token_expires

    data = JWTOut(
        username=user.username,
        nickname=user.nickname or "",
        depart=depart,
        roles=roles,
        accessToken=create_access_token(
            data=JWTPayload(
                user_id=(str(user.id)),
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        refreshToken=create_access_token(
            data=JWTPayload(
                user_id=str(user.id),
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire_refresh,
            )
        ),
        expires=expire.strftime("%Y-%m-%d %H:%M:%S")  # expire.timestamp()
    )
    return Success(data=data.model_dump())


@router.post("/logout", summary="登出（将Token加入黑名单）")
async def logout(current_user: DependUser,
                 authorization: str = Header(..., description="token验证")):
    """将当前 Token 加入 Redis 黑名单，TTL = Token 剩余过期时间"""
    token = authorization.split(" ")[1]
    try:
        decode_data = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="登录已过期") from exc
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="无效的Token") from exc
    exp = decode_data.get("exp", 0)
    now = datetime.now().timestamp()
    remaining_ttl = int(exp - now)
    if remaining_ttl > 0:
        redis = get_redis()
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        key = f"token:blacklist:{token_hash}"
        await redis.set(key, "1", ex=remaining_ttl)
    await logger.operationInfo(user=current_user.username, msg="用户登出")
    return Success(msg="登出成功")


@router.post("/refreshToken", summary="刷新token", dependencies=[DependRateLimit])
async def refresh_token(refreshToken: refreshTokenSchema):
    try:
        payload = decode_access_token(refreshToken.refreshToken)
    except ExpiredSignatureError:
        return FailAuth(msg="refreshToken已过期")
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now() + access_token_expires
    expire_refresh = datetime.now() + refresh_token_expires

    data = JWTReOut(
        accessToken=create_access_token(
            data=JWTPayload(
                user_id=payload.user_id,
                username=payload.username,
                is_superuser=payload.is_superuser,
                exp=expire,
            )
        ),
        refreshToken=create_access_token(
            data=JWTPayload(
                user_id=payload.user_id,
                username=payload.username,
                is_superuser=payload.is_superuser,
                exp=expire_refresh,
            )
        ),
        expires=expire.strftime("%Y-%m-%d %H:%M:%S")  # expire.timestamp()
    )

    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息")
async def get_userinfo(session: SessionDep, current_user: DependUser):
    user_obj = await userController.get(session=session, pk=current_user.id)
    if not user_obj:
        return FailAuth(msg="用户不存在或已被删除！")
    data = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=data)


@router.get("/userMenu", summary="查看用户菜单")
async def get_user_menu(session: SessionDep, current_user: DependUser):
    statement = select(User).where(col(User.id) == current_user.id).options(selectinload(
        cast(InstrumentedAttribute, User.roles)).selectinload(cast(InstrumentedAttribute, Role.menus)))
    user_obj = session.exec(statement).first()
    if not user_obj:
        return FailAuth(msg="用户不存在或已被删除！")
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = list(session.exec(select(Menu)).all())
    else:
        for role_obj in user_obj.roles:
            menus.extend(role_obj.menus)
    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parentId is None:
            parent_menus.append(menu)
    res = []

    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        parent_menu_dict["meta"] = {}
        parent_menu_dict["meta"]["title"] = parent_menu_dict["title"]
        parent_menu_dict["meta"]["icon"] = parent_menu_dict["icon"]
        parent_menu_dict["meta"]["showLink"] = parent_menu_dict["showLink"]
        parent_menu_dict["meta"]["rank"] = parent_menu_dict["rank"]

        parent_menu_dict = await menuTree(parent_menu_dict, menus)
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userApi", summary="查看用户API")
async def get_user_api(session: SessionDep, current_user: DependUser):
    statement = select(User).where(col(User.id) == current_user.id).options(selectinload(
        cast(InstrumentedAttribute, User.roles)).selectinload(cast(InstrumentedAttribute, Role.apis)))
    user_obj = session.exec(statement).first()
    if not user_obj:
        return FailAuth(msg="用户不存在或已被删除！")
    if user_obj.is_superuser:
        statement = select(Api)
        result = session.exec(statement)
        api_objs = list(result.all())
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    apis = []
    for role_obj in user_obj.roles:
        apis.extend([api.method.lower() + api.path for api in role_obj.apis])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/updatePwd", summary="更新用户密码")
async def update_user_password(
        session: SessionDep,
        req_in: UpdatePassword,
        current_user: DependUser):
    user = await userController.get(session=session, pk=current_user.id)
    if not user:
        return FailAuth(msg="用户不存在或已被删除！")
    verified = verify_password(req_in.current_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")

    # 密码复杂度校验
    policy = session.exec(select(SecurityPolicy)).first()
    if policy:
        valid, msg = validate_password_strength(req_in.new_password, policy)
        if not valid:
            return Fail(msg=msg)

        # 历史密码校验
        history_count = policy.password_history_count if policy else 3
        if check_password_history(req_in.new_password, user.password_history, history_count):
            return Fail(msg=f"新密码不能与最近 {history_count} 次使用的密码相同")

    # 更新密码 & 历史记录
    old_hash = user.password
    user.password = get_password_hash(req_in.new_password)
    if policy and policy.password_history_count > 0:
        user.password_history = update_password_history(
            old_hash, user.password_history, policy.password_history_count
        )
    session.add(user)
    session.commit()
    return Success(msg="修改成功")


@router.post("/updateProfile", summary="更新用户资料")
async def update_user_profile(
        session: SessionDep,
        req_in: UpdateProfile,
        current_user: DependUser):
    user = await userController.get(session=session, pk=current_user.id)
    if not user:
        return FailAuth(msg="用户不存在或已被删除！")
    update_data = req_in.model_dump(exclude_unset=True)
    if not update_data:
        return Fail(msg="没有需要更新的字段")
    for key, value in update_data.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    data = await user.to_dict(exclude_fields=["password"])
    return Success(data=data, msg="更新成功")


@router.get("/preferences", summary="获取用户偏好设置")
async def get_user_preferences(
        session: SessionDep,
        current_user: DependUser):
    user = await userController.get(session=session, pk=current_user.id)
    if not user:
        return FailAuth(msg="用户不存在或已被删除！")
    prefs = user.preferences or {}
    default_prefs = {
        "notify_account": True,
        "notify_system": True,
        "notify_task": True,
    }
    default_prefs.update(prefs)
    return Success(data=default_prefs)


@router.post("/updatePreferences", summary="更新用户偏好设置")
async def update_user_preferences(
        session: SessionDep,
        req_in: UpdatePreferences,
        current_user: DependUser):
    user = await userController.get(session=session, pk=current_user.id)
    if not user:
        return FailAuth(msg="用户不存在或已被删除！")
    current_prefs = user.preferences or {}
    update_data = req_in.model_dump(exclude_unset=True)
    current_prefs.update(update_data)
    user.preferences = current_prefs
    session.add(user)
    session.commit()
    session.refresh(user)
    prefs = user.preferences or {}
    default_prefs = {
        "notify_account": True,
        "notify_system": True,
        "notify_task": True,
    }
    default_prefs.update(prefs)
    return Success(data=default_prefs, msg="更新成功")


@router.get("/loginLogs", summary="获取登录日志")
async def get_login_logs(
        session: SessionDep,
        current_user: DependUser,
        pageSize: int = Query(default=10, ge=1, le=100),
        currentPage: int = Query(default=1, ge=1)):
    user = await userController.get(session=session, pk=current_user.id)
    if not user:
        return FailAuth(msg="用户不存在或已被删除！")
    offset = (currentPage - 1) * pageSize
    count_stmt = select(func.count()).select_from(LoginLog).where(
        LoginLog.username == user.username
    )
    total = session.exec(count_stmt).one()
    stmt = select(LoginLog).where(
        LoginLog.username == user.username
    ).order_by(col(LoginLog.time).desc()).offset(offset).limit(pageSize)
    logs = session.exec(stmt).all()
    list_data = []
    for log in logs:
        item = await log.to_dict()
        item["summary"] = item.pop("behavior", "")
        item["operatingTime"] = item.pop("time", "")
        list_data.append(item)
    return SuccessExtra(data=list_data, total=total, currentPage=currentPage, pageSize=pageSize)


@router.get("/qq/auth-url", summary="获取QQ授权链接")
async def get_qq_auth_url(session: SessionDep):
    """获取QQ登录授权URL"""
    oauth_config = oauthConfigController.get(session)
    app_id = (oauth_config.qq_app_id if oauth_config and oauth_config.qq_app_id else None) or settings.QQ_APP_ID
    redirect_uri = (oauth_config.qq_redirect_uri if oauth_config and oauth_config.qq_redirect_uri else None) or settings.QQ_REDIRECT_URI
    qq_enabled = settings.FEATURE_QQ_LOGIN and (
        oauth_config.qq_enabled if oauth_config else False)

    if not qq_enabled:
        return Fail(msg="QQ登录未启用")

    if not app_id:
        return Fail(msg="QQ登录未配置")

    state = create_oauth_state()
    encoded_redirect_uri = urllib.parse.quote(redirect_uri, safe='')

    auth_url = (
        f"https://graph.qq.com/oauth2.0/authorize?"
        f"response_type=code&"
        f"client_id={app_id}&"
        f"redirect_uri={encoded_redirect_uri}&"
        f"state={state}&"
        f"scope=get_user_info"
    )

    return Success(data={
        "auth_url": auth_url,
        "state": state
    })


@router.post("/qq/login", summary="QQ登录", dependencies=[DependRateLimit])
async def qq_login(session: SessionDep, qq_login_data: QQLoginSchema):
    """处理QQ登录回调"""
    try:
        # 验证输入参数
        if not qq_login_data.code or not qq_login_data.state:
            return FailAuth(msg="授权参数不完整")

        # 验证state令牌（防CSRF）
        if not verify_oauth_state(qq_login_data.state):
            return FailAuth(msg="授权验证失败，请重新登录")

        # 1. 使用授权码获取access_token
        token_data = await get_qq_access_token(qq_login_data.code)

        # 2. 获取用户信息
        user_info = await get_qq_userinfo(token_data.access_token, token_data.openid)

        # 3. 查找或创建用户
        user = await find_or_create_qq_user(session, user_info)

        # 4. 生成JWT token
        roles = [item.code for item in user.roles]
        try:
            depart = deptController.get_all_name(session, user)
        except Exception as e:
            logger.debug(f"获取部门名称失败: {str(e)}")
            depart = ""

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now() + access_token_expires
        expire_refresh = datetime.now() + refresh_token_expires

        data = JWTOut(
            username=user.username,
            nickname=user.nickname or "",
            depart=depart,
            roles=roles,
            accessToken=create_access_token(
                data=JWTPayload(
                    user_id=str(user.id),
                    username=user.username,
                    is_superuser=user.is_superuser,
                    exp=expire,
                )
            ),
            refreshToken=create_access_token(
                data=JWTPayload(
                    user_id=str(user.id),
                    username=user.username,
                    is_superuser=user.is_superuser,
                    exp=expire_refresh,
                )
            ),
            expires=expire.strftime("%Y-%m-%d %H:%M:%S")
        )

        # 更新最后登录时间
        await userController.update_last_login(session=session, pk=user.id)

        return Success(data=data.model_dump())

    except HTTPException:
        # HTTP异常直接抛出，保持原有错误信息
        raise
    except Exception as e:
        logger.error(f"QQ登录失败: {str(e)}")
        return FailAuth(msg="QQ登录失败，请稍后重试")


@router.get("/file/download/{file_id}", summary="下载文件（签名URL）")
async def download_file(
    file_id: UUID,
    expires: int = Query(..., description="过期时间戳"),
    sign: str = Query(..., description="签名"),
    session: Session | None = Depends(get_db),
):
    if not verify_signed_url(file_id, expires, sign):
        return Fail(msg="签名无效或已过期")
    if not session:
        return Fail(msg="数据库连接失败")
    file_obj = session.get(File, file_id)
    if not file_obj:
        return Fail(msg="文件不存在")
    abs_path = Path(settings.STATIC_PATH) / file_obj.path
    if not abs_path.exists():
        return Fail(msg="文件已丢失")
    return FileResponse(
        path=str(abs_path),
        media_type=file_obj.mime_type,
        filename=file_obj.name,
    )

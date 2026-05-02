# import json
import urllib.parse
from datetime import timedelta, datetime
from uuid import UUID
# from uuid import uuid4

from fastapi import APIRouter, Request, HTTPException
# from fastapi.websockets import WebSocketState
from sqlmodel import select
from jwt.exceptions import ExpiredSignatureError
# from wechatpayv3 import WeChatPayType

from app.controllers.department import deptController
from app.controllers.user import userController
from app.settings.log import logger
from app.models.login import CredentialsSchema, JWTPayload, JWTOut, refreshTokenSchema, \
    JWTReOut, QQLoginSchema
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth, SessionDep
from app.models import Api, Menu, Role, User, UpdatePassword
from app.models.base import Fail, Success, FailAuth
from app.settings import settings
from app.settings.config import base_config
from app.utils import menuTree
from app.utils.jwtt import create_access_token, decode_access_token, \
    get_qq_access_token, get_qq_userinfo, find_or_create_qq_user
from app.utils.password import get_password_hash, verify_password
# from app.utils.pay import notify_url
# from app.utils.pay.wechat import wxpay

router = APIRouter()


@router.post("/accessToken", summary="获取token")
async def login_access_token(
        session: SessionDep, request: Request, credentials: CredentialsSchema):
    user: User | None = await userController.authenticate(
        session=session,
        credentials=credentials,
        request=request
    )
    if not user:
        return FailAuth(msg="用户名或密码错误！")
    await userController.update_last_login(session=session, id=user.id)
    roles = [item.code for item in user.roles]
    try:
        depart = deptController.get_all_name(session, user)
    except Exception as e:
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
        avatar=user.avatar or "",
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


@router.post("/refreshToken", summary="刷新token")
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


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo(session: SessionDep):
    user_id = CTX_USER_ID.get()
    user_obj = await userController.get(session=session, id=UUID(user_id))
    if not user_obj:
        return FailAuth(msg="用户不存在或已被删除！")
    data = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=data)


@router.get("/userMenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu(session: SessionDep):
    user_id = CTX_USER_ID.get()
    user_obj = await userController.get(session=session, id=UUID(user_id))
    if not user_obj:
        return FailAuth(msg="用户不存在或已被删除！")
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = list(session.exec(select(Menu)).all())
    else:
        role_objs: list[Role] = user_obj.roles
        for role_obj in role_objs:
            menu = role_obj.menus
            menus.extend(menu)
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


@router.get("/userApi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api(session: SessionDep):
    user_id = CTX_USER_ID.get()
    user_obj = await userController.get(session=session, id=UUID(user_id))
    if not user_obj:
        return FailAuth(msg="用户不存在或已被删除！")
    if user_obj.is_superuser:
        statement = select(Api)
        result = session.exec(statement)
        api_objs = list(result.all())
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/updatePwd", summary="更新用户密码", dependencies=[DependAuth])
async def update_user_password(session: SessionDep, req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await userController.get(session=session, id=UUID(user_id))
    if not user:
        return FailAuth(msg="用户不存在或已被删除！")
    verified = verify_password(req_in.current_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    session.add(user)
    session.commit()
    return Success(msg="修改成功")


@router.get("/qq/auth-url", summary="获取QQ授权链接")
async def get_qq_auth_url():
    """获取QQ登录授权URL"""
    # 优先读取运行时配置（管理后台设置），否则回退到 settings 默认值
    app_id = base_config.get_config("login", "qq_app_id") or settings.QQ_APP_ID
    redirect_uri = base_config.get_config("login", "qq_redirect_uri") or settings.QQ_REDIRECT_URI
    qq_enabled = base_config.get_config("login", "qq_enabled", fallback="false").lower() == "true"

    if not qq_enabled:
        from app.models.base import Fail
        return Fail(msg="QQ登录未启用")

    if not app_id:
        from app.models.base import Fail
        return Fail(msg="QQ登录未配置")

    state = "qq_login_" + str(datetime.now().timestamp())
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


@router.post("/qq/login", summary="QQ登录")
async def qq_login(session: SessionDep, qq_login: QQLoginSchema):
    """处理QQ登录回调"""
    try:
        # 验证输入参数
        if not qq_login.code or not qq_login.state:
            return FailAuth(msg="授权参数不完整")

        # 1. 使用授权码获取access_token
        token_data = await get_qq_access_token(qq_login.code)

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
            avatar=user.avatar or user.qq_avatar or "",
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
        await userController.update_last_login(session=session, id=user.id)

        return Success(data=data.model_dump())

    except HTTPException:
        # HTTP异常直接抛出，保持原有错误信息
        raise
    except Exception as e:
        logger.error(f"QQ登录失败: {str(e)}")
        return FailAuth(msg="QQ登录失败，请稍后重试")


# @router.post("/notify/{name}", summary="支付回调")
# async def notify(name: str, request: Request, session: SessionDep):
#     match name:
#         case "wechat":
#             result = wxpay.callback(headers=request.headers, body=await request.body())
#             if result and result.get('event_type') == 'TRANSACTION.SUCCESS':
#                 resource = result.get('resource')
#                 out_trade_no = resource.get('out_trade_no')
#                 # appid = resource.get('appid')
#                 # mchid = resource.get('mchid')
#                 # transaction_id = resource.get('transaction_id')
#                 # trade_type = resource.get('trade_type')
#                 # trade_state = resource.get('trade_state')
#                 # trade_state_desc = resource.get('trade_state_desc')
#                 # bank_type = resource.get('bank_type')
#                 # attach = resource.get('attach')
#                 # success_time = resource.get('success_time')
#                 # payer = resource.get('payer')
#                 # amount = resource.get('amount').get('total')
#                 await orderController.complete(session, out_trade_no)

#                 return Success(msg="支付成功")
#             else:
#                 return Fail(msg="支付失败")


# @router.websocket("/wechat", name="微信支付")
# async def wechat_pay(websocket: WebSocket, session: SessionDep):
#     await websocket.accept()
#     order_code = uuid4().__str__().replace("-", "")[:10] + "-" + now(3)
#     try:
#         while True:
#             data = await websocket.receive_json()
#             # 检查是否有新的消息
#             if data.get("type") == "heartbeat":
#                 logger.debug("心跳中...")
#                 continue
#             else:
#                 # 处理普通信息
#                 data["code"] = order_code
#                 obj_in = OrderCreate.model_validate(data)
#                 order_obj = await orderController.get(session, data["id"])
#                 if order_obj is None:
#                     order_obj = await orderController.create(session, obj_in)
#                     code_url, message = wxpay.pay(
#                         description=order_obj.goods.name,
#                         out_trade_no=order_code,
#                         amount={"total": order_obj.amount},
#                         pay_type=WeChatPayType.NATIVE,
#                         notify_url=notify_url("wechat"),
#                     )
#                     code_url = json.loads(message)["code_url"]
#                     result = await order_obj.to_dict()
#                     coupon = {"code": ""}
#                     result["coupon"] = coupon
#                 else:
#                     session.refresh(order_obj)
#                     result = await order_obj.to_dict()
#                     code_url = data["code_url"]
#                 result["code_url"] = code_url
#                 await websocket.send_json(result)

#     except Exception as e:
#         logger.debug(e)
#         if websocket.client_state == WebSocketState.DISCONNECTED:
#             logger.debug("客户端已断开连接")
#         else:
#             await websocket.close()

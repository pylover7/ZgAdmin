# 自定义配置

## 改项目名称

编辑 `.env`：

```bash
PROJECT_NAME=我的系统
```

也可以在「通用设置」页面修改站点名称，保存后立即生效。

## 改 Logo

方式一：在「通用设置」页面填写 Logo URL，保存即可。

方式二：替换 `frontend/public/` 下的图标文件，或修改 `frontend/src/layout/components/` 中的引用。

## 改管理员密码

编辑 `.env`：

```bash
FIRST_SUPERUSER=admin
FIRST_SUPERUSER_PASSWORD=my-new-password
```

删除数据库后重启生效：

```bash
rm backend/static/zgadmin.sqlite
./scripts/start.sh
```

> 已运行系统中修改密码，请使用「账户设置 → 账户安全 → 修改密码」。

## 改默认菜单

编辑 `backend/app/seed/data/menus.py`，修改或添加菜单树：

```python
DEFAULT_MENUS = [
    dict(
        menuType=0, title="我的菜单", name="my", path="/my",
        component="", rank=1, icon="ep:home-filled",
        children=[...],
    ),
]
```

删除数据库重启后生效。

## 关闭不需要的功能

编辑 `.env`：

```bash
FEATURE_QQ_LOGIN=False          # 关闭 QQ 登录
FEATURE_WECHAT_LOGIN=False      # 关闭微信登录
FEATURE_EMAIL=False             # 关闭邮件发送
FEATURE_MONITOR_LOG=True        # 保留操作日志
```

前端会自动查询 `/api/v1/base/features` 并根据返回值隐藏对应入口。

> 也可以在「登录设置」页面开关第三方登录，无需重启。

## 切换数据库

默认使用 SQLite（零配置）。切换到 PostgreSQL：

```bash
DB_SCHEME=postgresql
DB_SERVER=localhost
DB_PORT=5432
DB_PATH=mydb
DB_USER=myuser
DB_PASSWORD=mypassword
```

## 修改 JWT 过期时间

编辑 `.env`：

```bash
ACCESS_TOKEN_EXPIRE_MINUTES=120       # 访问令牌 2 小时
REFRESH_TOKEN_EXPIRE_MINUTES=43200    # 刷新令牌 30 天
```

## 安全策略配置

在「安全设置」页面可配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 最小密码长度 | 8 | 6–32 |
| 密码复杂度 | 大小写+数字 | 大写/小写/数字/特殊字符 |
| 密码历史检查 | 3 次 | 防止重复使用近期密码 |
| 最大登录尝试 | 5 次 | 超过后锁定账户 |
| 锁定时长 | 30 分钟 | 5–1440 分钟 |
| 登录验证码 | 开启 | 服务端生成验证码 |

详见 [安全设置](./security.md)。

## 文件上传配置

编辑 `.env`：

```bash
MAX_UPLOAD_SIZE=10485760  # 上传大小限制（字节），默认 10MB
```

允许的扩展名在 `backend/app/utils/file_upload.py` 中的 `ALLOWED_EXTENSIONS` 集合中配置。

详见 [文件管理](./file-manager.md)。

## 通用设置

在「通用设置」页面可配置：站点名称、描述、Logo、默认语言、邮件开关、版权信息、备案号。

详见 [系统设置](./settings.md)。

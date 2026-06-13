# ZgAdmin 后台管理系统 — 功能完善执行计划

- [ ] 数据库更改为 PostgreSQL
- [x] 首页监控保留半个小时数据就行了
- [x] 前端访问，终端的日志怎么不输出了
- [x] 更新脚本的实现
- [x] 部分国际化失败
- [x] 7 天免登录

分析得非常对喵~ 先确认一下当前各文件的最新状态，确保改动不冲突：

读取
.env.example
L1-End
读取
infrastructure.md
L1-End
现在整体脉络清楚了喵~ 总结一下改动计划：

[直接执行]
核心原则：.env 默认值面向裸机（localhost），docker-compose.yml 显式覆盖为 Docker 服务名

改动清单

# 文件 改动

1 backend/app/settings/__init__.py REDIS_URL 默认值 → "redis://localhost:6379/0"
2 backend/app/core/redis.py _create_redis 逻辑：local 模式自动降级 MemoryRedis，prod/staging 用默认值连真实 Redis
3 docker-compose.yml 新增 REDIS_URL=redis://redis:6379/0，覆盖默认的 localhost
4 .env.example REDIS_URL=redis://localhost:6379/0，注释更新
5 scripts/start.sh inject_dev_env 删 REDIS_URL 行；check_prod_env 删 REDIS_URL 检查块
6 .codebuddy/rules/infrastructure.md 更新 REDIS_URL 默认值说明
具体改动

1. backend/app/settings/__init__.py

python
复制
插入
新建文件
保存
应用

# 之前

REDIS_URL: str = ""  # 空=自动（dev用内存，prod需配置redis://host:port/db）

# 之后

REDIS_URL: str = "redis://localhost:6379/0"  # 裸机默认；docker-compose 中覆盖为 redis://redis:6379/0
2. backend/app/core/redis.py

python
复制
插入
新建文件
保存
应用

# 之前

def _create_redis() -> RedisClient:
    redis_url = getattr(settings, "REDIS_URL", "") or ""
    if redis_url:
        logger.info(f"Redis: 使用真实连接 ({redis_url.split['@'](-1)})")
        return RealRedis(redis_url)
    if settings.ENVIRONMENT == "local":
        logger.info("Redis: 使用内存适配器（开发模式）")
        return MemoryRedis()
    logger.warning("⚠ 生产环境未配置 REDIS_URL，降级使用内存适配器（多进程不可用）")
    return MemoryRedis()

# 之后

def _create_redis() -> RedisClient:
    redis_url = getattr(settings, "REDIS_URL", "") or ""

    # 开发模式：始终使用内存 Redis（避免本地未装 Redis 时启动失败）
    if settings.ENVIRONMENT == "local":
        logger.info("Redis: 使用内存适配器（开发模式）")
        return MemoryRedis()

    # 生产/预发布：使用 REDIS_URL 连接真实 Redis
    logger.info(f"Redis: 使用真实连接 ({redis_url.split('@')[-1]})")
    return RealRedis(redis_url)
3. docker-compose.yml — 新增 REDIS_URL 环境变量 + depends_on redis

yaml
复制
插入
新建文件
保存
应用
environment:

- ENVIRONMENT=production
- BACKEND_CORS_ORIGINS=<https://your-domain.com,https://admin.your-domain.com>
- SECRET_KEY=changethisxxx
- DB_SCHEME=postgresql
- DB_SERVER=postgres
- DB_PORT=5432
- DB_PATH=zgadmin
- DB_USER=zgadmin
- DB_PASSWORD=changethisxxx
- REDIS_URL=redis://redis:6379/0    # 新增
depends_on:
  postgres:
    condition: service_healthy
    required: true
  redis:                                # 新增
    condition: service_healthy
    required: true

4. .env.example

code
复制
插入
新建文件
保存
应用

# 之前

REDIS_URL=

# 之后

REDIS_URL=redis://localhost:6379/0  # 裸机默认；docker-compose 会覆盖为 redis://redis:6379/0
5. scripts/start.sh

inject_dev_env：删除 REDIS_URL 相关行（local 模式由_create_redis 自动降级）
check_prod_env：删除 REDIS_URL 检查块（第 93-106 行），默认值已就绪
6. .codebuddy/rules/infrastructure.md

code
复制
插入
新建文件
保存
应用
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址；docker-compose 中为 `redis://redis:6379/0` |
数据库那边
数据库默认值已经是裸机友好的：DB_SERVER=localhost、DB_SCHEME=sqlite，docker-compose 里覆盖为 DB_SERVER=postgres、DB_SCHEME=postgresql——已经是这个模式了，不需要改喵~

[深度交互]
现在所有基础设施默认值都是 裸机优先：

DB_SERVER=localhost + DB_SCHEME=sqlite → 裸机零配置即用
REDIS_URL=redis://localhost:6379/0 → 裸机装了 Redis 就能连
docker-compose 里统一覆盖为 Docker 服务名（postgres、redis）
确认没问题的话，切 craft mode 我来执行喵~

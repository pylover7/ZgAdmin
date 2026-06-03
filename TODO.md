# ZgAdmin 后台管理系统 — 功能完善执行计划

- [ ] 数据库更改为 PostgreSQL
- [ ] 前后端依赖的更新
- [ ] global-statement 是否应该重构而非忽略当前项目使用全局变量实现 Redis 单（_redis_instance）和监控状态（_prev_net、_prev_disk）。更 Pythonic 的做法是使用模块级单例或 functools.lru_cache。但这是重构范畴，不应混入本次工具迁移中。建议作为单独技术债项记录喵~

- [ ] 质疑 2：DTZ（时区）和 LOG（日志格式）为何不启用DTZ：本项目 utils/__init__.py 和controllers/user.py 多处使用 datetime.now() 无时区。启用后会产生大量修复需求，且 FastAPISQLModel 的时区处理模式需要团队统一约定，不适合在工具迁移 PR 中一并处理喵~LOG：本项目用 Loguru 而非 stdlib logging，LOG 规则会误报喵~

# 安全注意事项

- 生产环境必须修改 `SECRET_KEY` 和 `FIRST_SUPERUSER_PASSWORD`
- CORS 配置仅允许可信域名
- 所有需认证的 API 使用 `DependPermission`
- 密码使用 bcrypt 哈希存储
- JWT Token 设置合理过期时间
- RateLimiter 基于 Redis 滑动窗口
- 验证码使用服务端生成（非前端 Canvas）
- 敏感操作需二次确认 + 操作日志

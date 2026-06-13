# 安全注意事项

- 生产环境必须修改 `SECRET_KEY`；管理员密码首次启动自动生成并打印到控制台
- CORS 配置仅允许可信域名
- 所有需认证的 API 使用 `DependPermission`（认证+权限检查）、`DependAuth`（仅认证）、`DependUser`（类型安全用户注入）或 `DependRateLimit`（IP 限流），按场景选择
- 密码使用 bcrypt 哈希存储
- JWT Token 设置合理过期时间
- RateLimiter 基于 Redis 滑动窗口
- 验证码使用服务端生成（非前端 Canvas）
- 敏感操作需二次确认 + 操作日志

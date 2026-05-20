---
layout: home

hero:
  name: "ZgAdmin"
  text: "全栈管理平台模板"
  tagline: Python/FastAPI + Vue 3/TypeScript，克隆即用，改配置就上线
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/quick-start
    - theme: alt
      text: GitHub
      link: https://github.com/pylover7/ZgAdmin

features:
  - title: 一键启动
    details: ./scripts/start.sh 自动检测环境、安装依赖、创建配置、启动服务。从 git clone 到浏览器打开不超过 3 分钟。
  - title: 代码生成器
    details: uv run python -m app.cli generate-module 一行命令生成完整 CRUD 模块（模型+控制器+API 路由），改字段重新跑即可。
  - title: 功能开关
    details: .env 里 FEATURE_QQ_LOGIN=False 关闭第三方登录。FEATURE_EMAIL=False 跳过邮件。不改代码，只改配置。
  - title: 声明式菜单
    details: seed/data/menus.py 里定义菜单树，重启自动导入。加页面不需要碰路由代码。
  - title: 纯 bcrypt 密码
    details: bcrypt 120 轮 Blowfish，无 MD5 预处理的现代密码哈希方案。
  - title: 安全基线
    details: 登录限流、OAuth CSRF 防护、安全响应头、用户名枚举防护、事务异常回滚。
---

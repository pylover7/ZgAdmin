---
layout: home

hero:
  name: "ZgAdmin"
  text: "全栈管理平台模板"
  tagline: Python/FastAPI + Vue 3/TypeScript，克隆即用，改配置就上线
  image:
    src: /logo.svg
    alt: ZgAdmin
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/quick-start
    - theme: alt
      text: CNB
      link: https://cnb.cool/pylover/Tools/ZgAdmin

features:
  - icon: 🚀
    title: 一键启动
    details: ./scripts/start.sh 自动检测环境、安装依赖、创建配置、启动服务。从 git clone 到浏览器打开不超过 3 分钟。
  - icon: 🔔
    title: 通知系统
    details: 内置通知管理模块，支持系统/业务/公告三种类型、三级优先级、未读提醒，铃铛组件 30 秒轮询实时展示。
  - icon: ⚙️
    title: 功能开关
    details: .env 里 FEATURE_QQ_LOGIN=False 关闭第三方登录。FEATURE_EMAIL=False 跳过邮件。不改代码，只改配置。
  - icon: 📋
    title: 声明式菜单
    details: seed/data/menus.py 里定义菜单树，重启自动导入。加页面不需要碰路由代码。
  - icon: 📁
    title: 文件管理
    details: 上传/预览/签名下载/批量操作，扩展名白名单 + MIME 检测，按日期自动归档，存储统计一目了然。
  - icon: 🛡️
    title: 安全基线
    details: bcrypt 120 轮密码哈希、密码复杂度策略、账户锁定、IP 黑白名单、登录验证码、操作审计日志。
---

import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "ZgAdmin",
  description: "全栈管理平台模板 — FastAPI + Vue 3",
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/quick-start' }
    ],

    sidebar: [
      {
        text: '指南',
        items: [
          { text: '快速开始', link: '/guide/quick-start' },
          { text: '添加新模块', link: '/guide/add-module' },
          { text: '自定义配置', link: '/guide/customization' },
        ]
      },
      {
        text: '模块文档',
        items: [
          { text: '通知系统', link: '/guide/notice' },
          { text: '文件管理', link: '/guide/file-manager' },
          { text: '安全设置', link: '/guide/security' },
          { text: '系统设置', link: '/guide/settings' },
          { text: '系统监控与日志', link: '/guide/monitor' },
          { text: 'API 权限管理', link: '/guide/api-permission' },
          { text: '账户设置', link: '/guide/account-settings' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/pylover7/ZgAdmin' }
    ]
  }
})

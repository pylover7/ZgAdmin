import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "PyTool",
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
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/pylover7/PyTool' }
    ]
  }
})

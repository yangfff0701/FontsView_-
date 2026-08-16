# 本机字体 · Font Gallery

> ⚠️ 个人自用项目，用途为个人代码学习使用，不对外发布，不提供任何使用或维护承诺。

本机 Windows 字体展示页：将系统已安装的字体以卡片网格形式展示，支持搜索、分类筛选、中文字体过滤，以及自定义示例文字、字号、字重和斜体预览。纯本地页面，无需联网。

## 项目结构

```text
test_web/
├── index.html              # 生成的单页字体展示页
├── preview.png             # 页面预览截图
├── tools/
│   ├── collect_fonts.ps1   # 扫描本机字体并导出 JSON 数据
│   └── build_page.py       # 根据 JSON 数据生成 index.html
└── README.md
```

## 使用方法

直接用浏览器打开 `index.html` 即可查看。

字体列表更新后，需要重新生成页面：

1. 运行 `tools/collect_fonts.ps1` 导出字体数据（JSON）。
2. 运行 `python tools/build_page.py <数据文件> index.html` 重新生成页面。

## 说明

- 页面使用本机已安装的字体渲染，不包含任何字体文件。
- 字体分类（无衬线 / 衬线 / 等宽 / 手写 / 展示 / 其他）由 `build_page.py` 中的规则自动判断，可能有误差。
- 项目仅供个人代码学习使用，请勿用于商业用途或对外分发。

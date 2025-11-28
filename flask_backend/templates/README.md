# 模板资源目录

此目录用于存放模板文件，包括 PPT 模板和系统配置模板。

## 目录结构

```
templates/
├── README.md                      # 本说明文件
├── default_ppt_data.json          # 默认PPT模板（新用户初始化时使用）
├── default_system_config.json     # 系统配置模板（数据库初始化时使用）
├── template_01/                   # 模板1（未来扩展）
│   ├── ppt_data.json
│   ├── thumbnail.jpg
│   └── meta.json
└── template_02/                   # 模板2（未来扩展）
    ├── ppt_data.json
    ├── thumbnail.jpg
    └── meta.json
```

## 模板说明

### 1. default_ppt_data.json - PPT模板

新用户首次登录时自动复制到其工作目录的默认演示文稿。

### 2. default_system_config.json - 系统配置模板

数据库初始化时加载到 `system_config` 表的默认配置，包括：

| 配置键 | 用途 |
|--------|------|
| `system_settings` | 系统全局设置（注册开关、最大时长等） |
| `default_user_config` | 新用户的默认配置模板 |
| `render_config` | 渲染引擎配置 |
| `tts_services` | TTS 服务配置 |
| `ai_services` | AI 服务配置 |
| `manual_split_config` | 手动分割配置 |
| `phase3_intelligent_alignment` | Phase3智能对齐配置 |

**注意：** 系统配置使用 `$setOnInsert` 写入，只在配置不存在时才创建，管理员通过数据库修改后的配置不会被覆盖。

## PPT模板格式

```json
{
  "project_name": "模板名称",
  "slides": [
    {
      "id": "slide_1",
      "elements": [...],
      "background": {...},
      "script": "该页的解说词脚本",
      "notes": "备注信息"
    }
  ],
  "theme": {
    "themeColor": "#4A90D9",
    "fontColor": "#333333",
    "fontName": "Microsoft YaHei",
    "backgroundColor": "#ffffff"
  },
  "viewportSize": {
    "width": 1000,
    "height": 562.5
  },
  "viewportRatio": 0.5625,
  "_template_info": {
    "name": "模板名称",
    "description": "模板描述",
    "version": "1.0.0"
  }
}
```

## 管理员指南

### 1. 更新默认模板

直接编辑 `default_ppt_data.json` 文件，或使用 PPTist 编辑器创建后导出替换。

### 2. 添加新模板（未来功能）

1. 创建模板文件夹：`template_xx/`
2. 添加以下文件：
   - `ppt_data.json` - PPT 数据
   - `thumbnail.jpg` - 缩略图预览（推荐 400x225 像素）
   - `meta.json` - 模板元信息

### 3. 模板元信息格式 (meta.json)

```json
{
  "id": "template_01",
  "name": "商务简约",
  "description": "适合商务演示的简约风格模板",
  "category": "business",
  "tags": ["简约", "商务", "专业"],
  "author": "admin",
  "version": "1.0.0",
  "created_at": "2025-01-01T00:00:00.000Z",
  "slides_count": 5
}
```

## 注意事项

1. 模板文件使用 UTF-8 编码
2. JSON 文件需要符合 PPTist 的数据格式
3. 每页幻灯片建议包含 `script` 字段（解说词）
4. 图片资源应使用相对路径或 base64 编码

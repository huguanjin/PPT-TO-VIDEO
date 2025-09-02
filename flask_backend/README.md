# PPT转视频工具 Flask后端

这是PPT转视频工具的Flask后端重构版本，提供统一的API接口服务。

## 项目结构

```
flask_backend/
├── app/                    # Flask应用目录
│   ├── __init__.py        # 应用工厂
│   ├── api/               # API蓝图
│   │   ├── common.py      # 通用接口
│   │   ├── pptist.py      # PPTist导入接口
│   │   ├── workflow.py    # 工作流接口
│   │   └── project.py     # 项目管理接口
│   ├── models/            # 数据模型
│   └── services/          # 业务逻辑服务
├── config/                # 配置文件
│   └── settings.py       # 应用配置
├── app.py                # 应用入口
├── requirements.txt      # 依赖包
├── start_flask.bat      # Windows启动脚本
└── start_flask.sh       # Linux启动脚本
```

## 主要功能

### 1. PPTist导入 (`/api/pptist/`)
- `POST /api/pptist/import` - 导入PPTist导出数据
- `GET /api/pptist/status/<task_id>` - 获取导入状态
- `GET /api/pptist/projects` - 获取项目列表
- `GET /api/pptist/project/<project_name>` - 获取项目详情
- `DELETE /api/pptist/project/<project_name>` - 删除项目

### 2. 工作流处理 (`/api/workflow/`)
- `POST /api/workflow/start` - 启动视频生成工作流
- `GET /api/workflow/status/<task_id>` - 获取处理状态
- `GET /api/workflow/result/<task_id>` - 获取处理结果
- `GET /api/workflow/download/<task_id>` - 下载生成文件
- `GET /api/workflow/config` - 获取工作流配置
- `POST /api/workflow/cancel/<task_id>` - 取消任务

### 3. 项目管理 (`/api/project/`)
- `GET /api/project/list` - 获取所有项目列表
- `GET /api/project/<project_name>` - 获取项目详情
- `DELETE /api/project/<project_name>` - 删除项目
- `GET /api/project/<project_name>/download` - 下载项目视频
- `POST /api/project/create` - 创建新项目

### 4. 通用接口
- `GET /health` - 健康检查
- `GET /info` - 系统信息
- `GET /docs` - API文档

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务

#### Windows
```bash
start_flask.bat
```

#### Linux/Mac
```bash
chmod +x start_flask.sh
./start_flask.sh
```

#### 直接运行
```bash
python app.py
```

### 3. 访问服务
- API服务: http://localhost:5000
- 健康检查: http://localhost:5000/health
- API文档: http://localhost:5000/docs

## 配置说明

### 环境变量
- `FLASK_ENV` - Flask环境 (development/production)
- `FLASK_DEBUG` - 调试模式 (1/0)
- `SECRET_KEY` - 应用密钥

### 配置文件
配置文件位于 `config/settings.py`，包含：
- 文件上传限制
- 目录路径配置
- 任务超时设置
- 日志配置

## API使用示例

### 导入PPTist数据
```bash
curl -X POST http://localhost:5000/api/pptist/import \
  -F "project_name=test_project" \
  -F "json_data={\"slides\":[...]}" \
  -F "images=@slide1.jpg" \
  -F "images=@slide2.jpg"
```

### 启动工作流
```bash
curl -X POST http://localhost:5000/api/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"project_name": "test_project", "config": {...}}'
```

### 获取项目列表
```bash
curl http://localhost:5000/api/project/list
```

## 与原有FastAPI的区别

1. **统一入口**: 所有API都通过一个Flask应用提供服务
2. **蓝图架构**: 使用Flask蓝图组织不同模块的API
3. **简化配置**: 统一的配置管理
4. **更好的错误处理**: 统一的错误处理机制
5. **易于扩展**: 清晰的项目结构便于添加新功能

## 开发指南

### 添加新API
1. 在对应的蓝图文件中添加新路由
2. 或创建新的蓝图文件
3. 在`app/__init__.py`中注册新蓝图

### 添加新配置
在`config/settings.py`中添加配置项

### 错误处理
所有API都返回统一格式的JSON响应：
```json
{
  "success": true/false,
  "message": "消息内容",
  "data": {...}  // 成功时的数据
}
```

## 注意事项

1. 当前版本为初始重构版本，部分功能可能需要进一步完善
2. 后台任务处理建议使用Celery等专业任务队列
3. 生产环境建议使用Gunicorn等WSGI服务器
4. 需要确保原有的核心模块（core/、utils/）可以正常导入

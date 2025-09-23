# 手动分割数据存储方案

## 1. 数据结构设计

### 主要文件
- `output/manual_splits/slide_splits.json` - 分割数据
- `output/manual_splits/metadata.json` - 元数据和配置

### slide_splits.json 结构
```json
{
  "project_name": "项目名称",
  "version": "1.0",
  "created_at": "2025-09-23T01:30:00Z",
  "splits": {
    "slide_id": {
      "original_remark": "原始HTML内容",
      "manual_splits": [
        {
          "index": 1,
          "content": "分割后的文本段落",
          "char_count": 15,
          "estimated_duration": 3.5,
          "warnings": ["超出长度限制"]
        }
      ],
      "split_mode": "manual|auto",
      "char_limit": 20,
      "last_modified": "2025-09-23T01:30:00Z"
    }
  }
}
```

## 2. API接口设计

### 前端API
- `GET /api/manual-splits/{project_name}` - 获取分割数据
- `POST /api/manual-splits/{project_name}` - 保存分割数据
- `DELETE /api/manual-splits/{project_name}/{slide_id}` - 删除特定分割

### 数据同步
- 前端编辑时实时同步到分割文件
- 工作流执行时优先使用分割数据，回退到原始数据

## 3. 向后兼容策略

### 音频生成工作流
```python
def get_slide_content(slide_id, project_name):
    # 1. 优先尝试获取手动分割数据
    split_data = load_manual_splits(project_name)
    if split_data and slide_id in split_data['splits']:
        return split_data['splits'][slide_id]['manual_splits']
    
    # 2. 回退到原始PPT数据
    return load_original_slide_content(slide_id, project_name)
```

## 4. 迁移计划

### 阶段1：基础设施（当前）
- [ ] 创建分割数据文件结构
- [ ] 实现前端API接口
- [ ] 更新Vue组件以支持持久化

### 阶段2：工作流集成
- [ ] 更新音频生成工作流
- [ ] 添加数据同步机制
- [ ] 实现数据一致性检查

### 阶段3：优化和测试
- [ ] 性能优化
- [ ] 完整测试覆盖
- [ ] 用户文档更新
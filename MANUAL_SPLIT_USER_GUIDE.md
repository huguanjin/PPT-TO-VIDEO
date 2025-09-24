# PPTist手动分行功能使用指南

## 功能说明
PPTist转视频工具支持在备注中进行手动分行，每一行会生成独立的字幕条目，每个条目都有独立的时间戳，实现"两个独立的字幕行，而不是重叠显示"。

## 使用方法

### 1. 在PPTist编辑器中添加手动分行
- 在PPTist编辑器的幻灯片备注区域输入文本
- 在需要分行的位置按 `Shift+Enter` 或插入换行符
- 确保生成的HTML包含 `<br>` 标签

### 2. 期望的HTML格式
```html
<p style="">第一行内容<br>第二行内容<br>第三行内容</p>
```

### 3. 系统处理流程
1. **HTML解析**：系统提取备注中的HTML内容
2. **换行转换**：将 `<br>` 和 `<br/>` 标签转换为换行符 `\n`
3. **字幕分割**：按换行符分割为独立段落
4. **时间分配**：每个段落分配独立的时间戳

### 4. 生成结果示例

#### 输入（PPTist备注）：
```
第一行内容
第二行内容  
第三行内容
```

#### 输出（字幕文件）：
```
1
00:00:00,000 --> 00:00:02,000
第一行内容

2
00:00:02,000 --> 00:00:04,000
第二行内容

3
00:00:04,000 --> 00:00:06,000
第三行内容
```

## 技术实现

### HTML处理逻辑（已实现）
```python
# 位置：flask_backend/core/enhanced_workflow_executor.py 第218-234行
# 1. 将<br>标签转换为换行符
clean_remark = re.sub(r'<br\s*/?>', '\n', raw_remark, flags=re.IGNORECASE)
# 2. 去除其他HTML标签
clean_remark = re.sub(r'<[^>]+>', '', clean_remark)
# 3. 保留换行符，清理多余空白
```

### 字幕分割逻辑（已实现）
```python
# 位置：flask_backend/core/step04_subtitle_generator.py 第718-780行
def _split_text_to_segments(self, text, max_chars_per_line=36):
    # 首先按手动换行符分割
    manual_lines = text.split('\n')
    segments = []
    for line in manual_lines:
        # 每行生成独立字幕段落
        segments.append(line.strip())
    return segments
```

## 验证方法

### 1. 检查数据流
1. 确认 `ppt_data.json` 中包含 `<br>` 标签
2. 检查 `slides_metadata.json` 中是否有换行符
3. 验证 `scripts_metadata.json` 中的分段
4. 查看最终字幕文件的时间戳

### 2. 测试用例
创建包含以下内容的PPT备注：
```
are you ok，我的朋友们
今天来教大家安装cherry studio
```

期望生成2个独立的字幕条目。

## 当前状态
✅ HTML处理逻辑已正确实现  
✅ 字幕分割逻辑已正确实现  
✅ 数据流管道已建立  
⚠️ 需要用户在PPTist中进行手动分行操作

## 注意事项
1. 确保在PPTist编辑器中正确插入换行符
2. 导出时保持HTML格式完整
3. 每行内容不超过36个字符以获得最佳显示效果
4. 系统会自动为每个分段分配均匀的时间

## 问题排查
如果手动分行不生效：
1. 检查 `ppt_data.json` 中是否包含 `<br>` 标签
2. 确认PPTist导出时保留了HTML格式
3. 验证系统是否使用了最新的工作流处理逻辑
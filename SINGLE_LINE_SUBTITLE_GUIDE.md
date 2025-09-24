# 单行字幕模式使用说明

## 功能概述

PPTist工作流现在支持单行字幕模式，可以将多行字幕（由PPTist前端的手动换行生成）转换为连续的单行字幕，每行有独立的时间分配。

## 主要特性

### 1. 智能多行转单行
- 原始PPTist格式：`"are you ok，我的朋友们\n今天来教大家安装cherry studio"`
- 单行模式输出：两个独立的字幕条目
  ```
  1. 00:00:00,500 → 00:00:02,608: are you ok，我的朋友们
  2. 00:00:02,608 → 00:00:05,375: 今天来教大家安装cherry studio
  ```

### 2. 智能时间分配
- 基于字符数比例分配时间
- 支持最小/最大时间限制
- 确保时间连续性，避免重叠或间隙

### 3. 配置化控制
- 通过配置文件轻松开启/关闭
- 支持时间分配算法自定义
- 兼容现有多行字幕模式

## 使用方法

### 启用单行模式

编辑 `config/manual_split_config.json` 文件：

```json
{
  "manual_split_config": {
    "subtitle_display_mode": {
      "single_line_mode": true,
      "description": "启用后将多行字幕转换为连续的单行字幕，每行独立时间分配",
      "time_allocation": {
        "method": "proportional",
        "based_on": "character_count", 
        "min_line_duration": 1.0,
        "max_line_duration": 8.0
      }
    }
  }
}
```

### 关闭单行模式

将 `single_line_mode` 设置为 `false`：

```json
{
  "manual_split_config": {
    "subtitle_display_mode": {
      "single_line_mode": false
    }
  }
}
```

## 技术细节

### 实现原理

1. **换行符保护**：在HTML清理过程中保留 `\n` 换行符
2. **优先级处理**：单行模式在文本分割流程中具有最高优先级
3. **比例时间分配**：根据每行字符数占比分配时间段
4. **无缝集成**：与现有字幕生成流程完全兼容

### 核心修改

1. **配置系统**
   - 在 `manual_split_config.json` 中添加单行模式配置
   - 字幕生成器启动时自动读取配置

2. **HTML清理增强**
   - `_clean_html_tags()` 方法在单行模式下保留换行符
   - 智能空白字符处理，避免格式破坏

3. **文本分割优化**
   - `_split_text_to_segments()` 优先处理单行模式
   - 避免增强分割器干扰单行分割逻辑

4. **时间分配算法**
   - `_calculate_single_line_duration()` 专用时间计算
   - 基于字符数比例的精确时间分配

### 处理流程

```
PPTist输入 -> HTML清理(保留\\n) -> 单行模式检测 -> 按\\n分割 -> 比例时间分配 -> SRT生成
```

## 应用场景

### 适用情况
- PPTist用户手动添加换行符创建多行显示
- 需要每行独立控制显示时间
- 提高字幕可读性和观看体验

### 不适用情况  
- 单行文本（无换行符）
- 已经是理想字幕格式的内容
- 不需要时间分段的长文本

## 配置选项详解

### time_allocation 配置

```json
{
  "time_allocation": {
    "method": "proportional",           // 分配方法：比例分配
    "based_on": "character_count",      // 基于字符数计算
    "min_line_duration": 1.0,          // 最小单行时长（秒）
    "max_line_duration": 8.0           // 最大单行时长（秒）
  }
}
```

### 参数说明

- `method`: 时间分配算法
  - `proportional`: 基于内容比例分配（推荐）
  
- `based_on`: 比例计算依据
  - `character_count`: 按字符数比例（推荐）
  
- `min_line_duration`: 单行最小显示时间
  - 确保每行字幕有足够的阅读时间
  
- `max_line_duration`: 单行最大显示时间
  - 避免单行字幕显示过长

## 示例效果

### 输入文本
```
"are you ok，我的朋友们\n今天来教大家安装cherry studio"
```

### 多行模式输出（single_line_mode: false）
```
1
00:00:00,500 --> 00:00:05,375
are you ok，我的朋友们
今天来教大家安装cherry studio
```

### 单行模式输出（single_line_mode: true）
```
1
00:00:00,500 --> 00:00:02,608
are you ok，我的朋友们

2
00:00:02,608 --> 00:00:05,375
今天来教大家安装cherry studio
```

## 注意事项

1. **兼容性**：单行模式不影响不包含换行符的文本
2. **性能**：单行模式下文本处理效率更高，绕过复杂的AI分割
3. **精确性**：时间分配基于字符数比例，确保合理的阅读节奏
4. **可逆性**：可以随时在多行模式和单行模式之间切换

## 故障排除

### 常见问题

1. **配置不生效**
   - 检查 JSON 语法是否正确
   - 确认配置文件路径正确
   - 重启字幕生成器服务

2. **时间分配异常**
   - 检查 `min_line_duration` 和 `max_line_duration` 设置
   - 确认音频总时长足够分配给所有行

3. **换行符丢失**
   - 确认输入文本确实包含 `\n` 换行符
   - 检查 PPTist 前端是否正确生成换行符

### 调试日志

启用后查看日志中的关键信息：
```
✅ 单行字幕模式已启用 - 多行字幕将被拆分为连续单行
📋 检测到 2 行文本，将创建连续的单行字幕
🎯 单行模式最终结果: 2 个独立字幕片段
```

---

通过以上配置和说明，你可以轻松在PPTist工作流中启用单行字幕模式，获得更好的字幕显示效果和用户体验。
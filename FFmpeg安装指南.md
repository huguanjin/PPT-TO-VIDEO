# FFmpeg安装与配置指南

## 为什么需要FFmpeg？

FFmpeg是一个强大的多媒体处理框架，本项目使用它来实现高性能的视频合并功能。相比MoviePy，FFmpeg具有以下优势：

- ⚡ **性能更佳**: 原生C++实现，处理速度更快
- 🎯 **专业级**: 业界标准的视频处理工具
- 🔧 **可控性强**: 更多编码参数和质量控制选项
- 💾 **内存友好**: 流式处理，减少内存占用

## Windows安装FFmpeg

### 方法一：使用官方下载（推荐）

1. **下载FFmpeg**
   - 访问官方网站: https://ffmpeg.org/download.html
   - 选择Windows构建版本
   - 推荐下载: https://www.gyan.dev/ffmpeg/builds/

2. **解压文件**
   ```
   下载: ffmpeg-release-essentials.zip
   解压到: C:\\ffmpeg
   ```

3. **设置环境变量**
   - 打开"系统属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到"Path"，点击"编辑"
   - 添加新路径: `C:\\ffmpeg\\bin`
   - 点击"确定"保存

4. **验证安装**
   ```powershell
   # 重新打开PowerShell/命令提示符
   ffmpeg -version
   ```

### 方法二：使用Chocolatey

如果已安装Chocolatey包管理器：

```powershell
# 以管理员身份运行PowerShell
choco install ffmpeg
```

### 方法三：使用Winget

Windows 10/11内置包管理器：

```powershell
winget install ffmpeg
```

## 验证FFmpeg安装

运行以下命令验证FFmpeg是否正确安装：

```powershell
# 检查版本信息
ffmpeg -version

# 查看编码器列表
ffmpeg -codecs

# 测试简单转换
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 test.mp4
```

## 项目中的FFmpeg使用

### 自动回退机制

本项目实现了智能回退机制：

1. **优先使用FFmpeg**: 如果FFmpeg可用，使用高性能FFmpeg合并
2. **自动回退MoviePy**: 如果FFmpeg不可用，自动使用MoviePy作为备选

### 配置选项

在项目配置中可以设置FFmpeg参数：

```json
{
  "video_codec": "libx264",
  "audio_codec": "aac", 
  "video_bitrate": "2000k",
  "audio_bitrate": "128k",
  "fps": 30
}
```

## 故障排除

### 常见问题

1. **"ffmpeg不是内部或外部命令"**
   - 确认FFmpeg已下载并解压
   - 检查环境变量PATH设置
   - 重启终端/IDE

2. **权限错误**
   - 确保以管理员身份安装
   - 检查FFmpeg文件夹权限

3. **编码错误**
   - 更新到最新FFmpeg版本
   - 检查输入文件格式

### 测试FFmpeg功能

运行项目测试脚本：

```bash
python test_ffmpeg_merger.py
```

预期输出：
```
🧪 FFmpeg最终合并器功能测试
==================================================
🔍 测试FFmpeg可用性...
✅ FFmpeg可用: ffmpeg version 4.4.0
...
总计: 4/4 项测试通过
🎉 所有测试通过! FFmpeg合并器准备就绪
```

## 性能对比

| 功能 | FFmpeg | MoviePy |
|------|--------|---------|
| 处理速度 | ⚡ 极快 | 🐌 较慢 |
| 内存使用 | 💾 低 | 📈 高 |
| 文件质量 | 🎯 专业级 | ✅ 良好 |
| 安装复杂度 | 🔧 中等 | ✅ 简单 |

## 下一步

1. 安装FFmpeg并配置环境变量
2. 运行测试脚本验证安装
3. 在项目中享受高性能视频处理！

如果遇到问题，项目会自动使用MoviePy作为备选方案，确保功能正常运行。

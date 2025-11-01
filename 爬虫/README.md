# YouTube 转 MP3 工具

一个使用 JavaFX 创建的 YouTube 视频下载和 MP3 转换工具。

## 依赖项

### 必需的依赖项：
1. **Java JDK** (推荐版本 21 或更高)
2. **JavaFX SDK** (推荐版本 21.0.7)
3. **yt-dlp** - YouTube 下载工具

> **注意**: 此应用使用 yt-dlp 的内置音频处理功能，无需安装 FFmpeg。

## 安装指南

### 1. 安装 Java JDK
```powershell
winget install Oracle.JDK.21
```

### 2. 下载 JavaFX SDK
1. 访问 [OpenJFX 官网](https://openjfx.io/)
2. 下载 JavaFX SDK 21.0.7
3. 解压到 `C:\` 目录

### 3. 安装 yt-dlp
```powershell
pip install yt-dlp
```

## 使用方法

### 在 VS Code 中运行
1. 打开项目文件夹
2. 确保 `launch.json` 配置正确
3. 按 F5 运行程序

### 通过批处理文件运行
```powershell
.\run-auto.bat
```

## 功能特性

- **双下载模式**：
  - MP3 转换模式：下载视频并转换为 MP3
  - 纯音频模式：直接下载音频文件
- **中文界面**：完全中文化的用户界面
- **进度显示**：实时显示下载和转换进度
- **简单易用**：只需粘贴 YouTube 链接即可开始

## 故障排除

### 常见问题

1. **yt-dlp 未找到**
   - 确保 Python 已安装
   - 运行：`pip install yt-dlp`
   - 重启命令提示符

2. **程序无法启动**
   - 检查 Java 版本：`java --version`
   - 确保 JavaFX SDK 路径正确

3. **下载失败**
   - 检查网络连接
   - 确认 YouTube 链接有效
   - 尝试使用不同的视频链接

## 项目结构

```
youtubeDownloader/
├── youtubeConvertMP3.java    # 主程序文件
├── run-auto.bat             # 自动运行脚本
├── run.bat                  # 运行脚本
└── test-deps.bat           # 依赖检测脚本
```
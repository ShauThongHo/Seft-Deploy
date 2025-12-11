# YouTube批量下载器

一个简单易用的YouTube视频/音频批量下载工具，支持下载MP3音频和MP4视频格式。

## 功能特点

- ✅ 支持批量下载多个YouTube视频
- 🎵 支持下载为MP3音频格式（192kbps）
- 🎬 支持下载为MP4视频格式
- 📁 自定义下载保存路径
- 📊 实时显示下载进度和日志
- 🖥️ 简洁的图形化界面

## 系统要求

- Windows 操作系统
- 需要安装 FFmpeg（用于音视频格式转换）

## FFmpeg 安装

视频下载和音频转换需要FFmpeg支持。

### 方法一：使用 Chocolatey（推荐）
```powershell
choco install ffmpeg
```

### 方法二：手动安装
1. 访问 https://www.gyan.dev/ffmpeg/builds/
2. 下载最新版本的 FFmpeg
3. 解压到 `C:\ffmpeg`
4. 将 `C:\ffmpeg\bin` 添加到系统环境变量 PATH

### 验证安装
```powershell
ffmpeg -version
```

## 使用方法

### 使用可执行文件（推荐）
1. 下载 `youtube_downloader.exe`
2. 双击运行程序
3. 在文本框中输入YouTube URL（每行一个）
4. 选择下载格式（MP3或MP4）
5. 选择保存路径
6. 点击"开始批量下载"

### 从源码运行

#### 1. 安装依赖
```powershell
pip install yt-dlp
```

#### 2. 运行程序
```powershell
python youtube_downloader.py
```

## 打包说明

如果需要重新打包为可执行文件：

```powershell
# 安装 PyInstaller
pip install pyinstaller

# 打包程序
pyinstaller --onefile --windowed --name="YouTube下载器" youtube_downloader.py
```

打包后的exe文件位于 `dist` 目录下。

## 注意事项

⚠️ **重要提醒**：
- 请确保已安装FFmpeg，否则无法下载视频或转换音频
- 下载大量视频时请注意磁盘空间
- 请遵守YouTube服务条款和版权法规
- 仅用于个人学习和研究用途

## 常见问题

### Q: 无法下载视频？
A: 请确保：
1. 已正确安装FFmpeg
2. URL格式正确
3. 网络连接正常
4. 视频没有地区限制

### Q: 下载速度很慢？
A: 下载速度取决于：
- 您的网络速度
- YouTube服务器响应速度
- 视频文件大小

### Q: 出现错误提示？
A: 常见错误解决方法：
- 检查FFmpeg是否安装
- 确认URL有效
- 尝试使用管理员权限运行
- 查看日志输出获取详细错误信息

## 技术栈

- **Python 3.11+**
- **tkinter** - 图形界面
- **yt-dlp** - YouTube下载核心
- **FFmpeg** - 音视频处理

## 更新日志

### v1.1
- ✨ 新增MP4视频下载功能
- ✨ 添加格式选择界面
- 🐛 修复视频下载问题
- 💄 优化界面布局

### v1.0
- 🎉 初始版本
- 支持MP3音频批量下载
- 基础图形界面

## 许可证

本项目仅供学习交流使用，请勿用于商业用途。

## 作者

ShauThongHo

## 贡献

欢迎提交Issue和Pull Request！

---

⭐ 如果这个项目对您有帮助，请给个Star！

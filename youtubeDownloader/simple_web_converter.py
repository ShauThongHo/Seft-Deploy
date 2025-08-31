#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 YouTube 转换网站后端
使用 Flask + yt-dlp 实现
"""

from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import uuid
import threading
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = '/tmp/youtube_conversions'
ALLOWED_FORMATS = ['mp3', 'm4a', 'wav', 'ogg']
MAX_FILE_AGE = 3600  # 1小时后删除文件

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 存储转换任务状态
conversion_tasks = {}

class YouTubeConverter:
    def __init__(self):
        pass
    
    def get_video_info(self, url):
        """获取视频信息"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                }
        except Exception as e:
            raise Exception(f"无法获取视频信息: {str(e)}")
    
    def convert_to_audio(self, url, format='mp3', task_id=None):
        """转换视频为音频"""
        if format not in ALLOWED_FORMATS:
            raise ValueError(f"不支持的格式: {format}")
        
        output_filename = f"{task_id}.{format}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # 配置 yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path.replace(f'.{format}', '.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': '192',
            }] if format == 'mp3' else [],
        }
        
        # 如果不是mp3，直接下载最佳音频
        if format != 'mp3':
            ydl_opts = {
                'format': f'bestaudio[ext={format}]/bestaudio',
                'outtmpl': output_path,
            }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找实际生成的文件
            for file in os.listdir(UPLOAD_FOLDER):
                if file.startswith(task_id):
                    return os.path.join(UPLOAD_FOLDER, file)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"转换失败: {str(e)}")

converter = YouTubeConverter()

@app.route('/')
def index():
    """主页"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>YouTube 转 MP3</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { 
                color: #333; 
                text-align: center;
            }
            .form-group {
                margin: 20px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"], select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                width: 100%;
            }
            button:hover {
                background: #45a049;
            }
            button:disabled {
                background: #cccccc;
                cursor: not-allowed;
            }
            .status {
                margin: 20px 0;
                padding: 10px;
                border-radius: 5px;
            }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
            .info { background: #d1ecf1; color: #0c5460; }
            .download-link {
                display: inline-block;
                background: #007bff;
                color: white;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 YouTube 转 MP3 转换器</h1>
            <form id="convertForm">
                <div class="form-group">
                    <label for="url">YouTube URL:</label>
                    <input type="text" id="url" placeholder="https://www.youtube.com/watch?v=..." required>
                </div>
                
                <div class="form-group">
                    <label for="format">音频格式:</label>
                    <select id="format">
                        <option value="mp3">MP3 (推荐)</option>
                        <option value="m4a">M4A (高质量)</option>
                        <option value="wav">WAV (无损)</option>
                        <option value="ogg">OGG (开源)</option>
                    </select>
                </div>
                
                <button type="submit">🚀 开始转换</button>
            </form>
            
            <div id="status"></div>
        </div>

        <script>
            const form = document.getElementById('convertForm');
            const statusDiv = document.getElementById('status');
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const url = document.getElementById('url').value;
                const format = document.getElementById('format').value;
                const submitBtn = form.querySelector('button');
                
                // 禁用按钮
                submitBtn.disabled = true;
                submitBtn.textContent = '⏳ 转换中...';
                
                statusDiv.innerHTML = '<div class="status info">正在处理您的请求...</div>';
                
                try {
                    // 启动转换
                    const response = await fetch('/api/convert', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, format })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        statusDiv.innerHTML = '<div class="status info">转换中，请稍候...</div>';
                        
                        // 轮询检查状态
                        checkStatus(data.task_id);
                    } else {
                        statusDiv.innerHTML = `<div class="status error">错误: ${data.error}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="status error">网络错误: ${error.message}</div>`;
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '🚀 开始转换';
                }
            });
            
            async function checkStatus(taskId) {
                try {
                    const response = await fetch(`/api/status/${taskId}`);
                    const data = await response.json();
                    
                    if (data.status === 'completed') {
                        statusDiv.innerHTML = `
                            <div class="status success">
                                ✅ 转换完成！
                                <br>
                                <a href="/api/download/${taskId}" class="download-link" download>📥 下载文件</a>
                            </div>
                        `;
                    } else if (data.status === 'failed') {
                        statusDiv.innerHTML = `<div class="status error">❌ 转换失败: ${data.error}</div>`;
                    } else {
                        // 继续轮询
                        setTimeout(() => checkStatus(taskId), 2000);
                    }
                } catch (error) {
                    statusDiv.innerHTML = `<div class="status error">检查状态时出错: ${error.message}</div>`;
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/info', methods=['POST'])
def get_video_info():
    """获取视频信息"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': '缺少URL参数'})
        
        info = converter.get_video_info(url)
        return jsonify({'success': True, 'info': info})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/convert', methods=['POST'])
def convert_video():
    """开始转换任务"""
    try:
        data = request.get_json()
        url = data.get('url')
        format = data.get('format', 'mp3')
        
        if not url:
            return jsonify({'success': False, 'error': '缺少URL参数'})
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        conversion_tasks[task_id] = {
            'status': 'pending',
            'url': url,
            'format': format,
            'created_at': time.time(),
            'file_path': None,
            'error': None
        }
        
        # 在后台线程中执行转换
        thread = threading.Thread(target=background_convert, args=(task_id, url, format))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    task = conversion_tasks.get(task_id)
    
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'})
    
    return jsonify({
        'success': True,
        'status': task['status'],
        'error': task.get('error')
    })

@app.route('/api/download/<task_id>')
def download_file(task_id):
    """下载转换后的文件"""
    task = conversion_tasks.get(task_id)
    
    if not task:
        return jsonify({'success': False, 'error': '任务不存在'})
    
    if task['status'] != 'completed':
        return jsonify({'success': False, 'error': '文件尚未准备好'})
    
    file_path = task['file_path']
    if not file_path or not os.path.exists(file_path):
        return jsonify({'success': False, 'error': '文件不存在'})
    
    return send_file(file_path, as_attachment=True)

def background_convert(task_id, url, format):
    """后台转换任务"""
    try:
        conversion_tasks[task_id]['status'] = 'processing'
        
        # 执行转换
        file_path = converter.convert_to_audio(url, format, task_id)
        
        # 更新任务状态
        conversion_tasks[task_id]['status'] = 'completed'
        conversion_tasks[task_id]['file_path'] = file_path
        
    except Exception as e:
        conversion_tasks[task_id]['status'] = 'failed'
        conversion_tasks[task_id]['error'] = str(e)

def cleanup_old_files():
    """清理旧文件"""
    while True:
        try:
            current_time = time.time()
            
            # 清理任务记录
            expired_tasks = []
            for task_id, task in conversion_tasks.items():
                if current_time - task['created_at'] > MAX_FILE_AGE:
                    expired_tasks.append(task_id)
            
            for task_id in expired_tasks:
                task = conversion_tasks.pop(task_id, None)
                if task and task.get('file_path') and os.path.exists(task['file_path']):
                    os.remove(task['file_path'])
            
            # 清理孤立文件
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.getctime(file_path) < current_time - MAX_FILE_AGE:
                    os.remove(file_path)
                    
        except Exception as e:
            print(f"清理文件时出错: {e}")
        
        time.sleep(300)  # 每5分钟检查一次

if __name__ == '__main__':
    # 启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_old_files)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    
    # 启动Flask应用
    print("🚀 YouTube转换器已启动")
    print("📱 访问 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

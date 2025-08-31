#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换服务 - 专门负责音频转换
微服务架构中的一个独立服务
"""

from flask import Flask, request, jsonify
import yt_dlp
import os
import uuid
import threading
import time
import json
import redis
from celery import Celery

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = '/tmp/conversions'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Redis连接
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Celery配置（用于异步任务队列）
celery_app = Celery('converter',
                   broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
                   backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/0')

class ConversionService:
    """转换服务核心类"""
    
    def __init__(self):
        self.supported_formats = ['mp3', 'm4a', 'wav', 'ogg', 'aac', 'flac']
        self.quality_options = {
            'low': '128',
            'medium': '192', 
            'high': '320',
            'lossless': '0'  # 无损
        }
    
    def validate_url(self, url):
        """验证YouTube URL"""
        youtube_domains = [
            'youtube.com', 'youtu.be', 'm.youtube.com',
            'www.youtube.com', 'music.youtube.com'
        ]
        
        return any(domain in url for domain in youtube_domains)
    
    def get_video_info(self, url):
        """获取视频信息"""
        if not self.validate_url(url):
            raise ValueError("无效的YouTube链接")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', '')[:500],  # 限制描述长度
                    'upload_date': info.get('upload_date', ''),
                    'formats': self._extract_available_formats(info)
                }
        except Exception as e:
            raise Exception(f"获取视频信息失败: {str(e)}")
    
    def _extract_available_formats(self, info):
        """提取可用的音频格式"""
        available_formats = []
        
        for fmt in info.get('formats', []):
            if fmt.get('vcodec') == 'none':  # 仅音频
                available_formats.append({
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'acodec': fmt.get('acodec'),
                    'abr': fmt.get('abr'),  # 音频比特率
                    'filesize': fmt.get('filesize')
                })
        
        return available_formats
    
    def convert_audio(self, url, format='mp3', quality='medium', task_id=None):
        """转换音频"""
        if format not in self.supported_formats:
            raise ValueError(f"不支持的格式: {format}")
        
        if quality not in self.quality_options:
            raise ValueError(f"不支持的质量: {quality}")
        
        output_filename = f"{task_id}.{format}"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        # 构建yt-dlp选项
        ydl_opts = self._build_ydl_options(format, quality, output_path)
        
        try:
            # 更新任务状态
            self._update_task_status(task_id, 'downloading', 0)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 查找实际生成的文件
            actual_file = self._find_converted_file(task_id)
            
            # 更新任务状态
            file_size = os.path.getsize(actual_file) if actual_file else 0
            self._update_task_status(task_id, 'completed', 100, {
                'file_path': actual_file,
                'file_size': file_size,
                'format': format,
                'quality': quality
            })
            
            return actual_file
            
        except Exception as e:
            self._update_task_status(task_id, 'failed', 0, {'error': str(e)})
            raise Exception(f"转换失败: {str(e)}")
    
    def _build_ydl_options(self, format, quality, output_path):
        """构建yt-dlp选项"""
        quality_value = self.quality_options[quality]
        
        base_opts = {
            'outtmpl': output_path.replace(f'.{format}', '.%(ext)s'),
            'format': 'bestaudio/best',
        }
        
        # 根据格式添加后处理器
        if format == 'mp3':
            base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality_value,
            }]
        elif format in ['m4a', 'aac']:
            base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
                'preferredquality': quality_value,
            }]
        elif format == 'wav':
            base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }]
        elif format == 'flac':
            base_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'flac',
            }]
        else:
            # 对于其他格式，尝试直接下载
            base_opts['format'] = f'bestaudio[ext={format}]/bestaudio'
        
        return base_opts
    
    def _find_converted_file(self, task_id):
        """查找转换后的文件"""
        for file in os.listdir(UPLOAD_FOLDER):
            if file.startswith(task_id):
                return os.path.join(UPLOAD_FOLDER, file)
        return None
    
    def _update_task_status(self, task_id, status, progress, metadata=None):
        """更新任务状态到Redis"""
        task_data = {
            'status': status,
            'progress': progress,
            'timestamp': int(time.time()),
            'metadata': metadata or {}
        }
        
        redis_client.hset(f"task:{task_id}", mapping=task_data)
        redis_client.expire(f"task:{task_id}", 3600)  # 1小时过期

# 创建服务实例
converter_service = ConversionService()

# Celery任务
@celery_app.task(bind=True)
def convert_video_async(self, url, format='mp3', quality='medium', task_id=None):
    """异步转换任务"""
    try:
        result_file = converter_service.convert_audio(url, format, quality, task_id)
        return {'success': True, 'file_path': result_file}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# API端点
@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'converter',
        'status': 'healthy',
        'timestamp': int(time.time()),
        'supported_formats': converter_service.supported_formats
    })

@app.route('/info', methods=['POST'])
def get_video_info():
    """获取视频信息"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': '缺少URL参数'}), 400
        
        info = converter_service.get_video_info(url)
        return jsonify({'success': True, 'info': info})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/convert', methods=['POST'])
def start_conversion():
    """开始转换任务"""
    try:
        data = request.get_json()
        url = data.get('url')
        format = data.get('format', 'mp3')
        quality = data.get('quality', 'medium')
        
        if not url:
            return jsonify({'success': False, 'error': '缺少URL参数'}), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 启动异步任务
        convert_video_async.delay(url, format, quality, task_id)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'estimated_time': '2-5分钟'  # 估算时间
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        
        if not task_data:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'status': task_data.get('status'),
            'progress': int(task_data.get('progress', 0)),
            'metadata': json.loads(task_data.get('metadata', '{}'))
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<task_id>')
def download_file(task_id):
    """下载转换后的文件"""
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        
        if not task_data:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        if task_data.get('status') != 'completed':
            return jsonify({'success': False, 'error': '文件尚未准备好'}), 400
        
        metadata = json.loads(task_data.get('metadata', '{}'))
        file_path = metadata.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        from flask import send_file
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/formats')
def get_supported_formats():
    """获取支持的格式"""
    return jsonify({
        'success': True,
        'formats': converter_service.supported_formats,
        'quality_options': list(converter_service.quality_options.keys())
    })

if __name__ == '__main__':
    print("🎵 转换服务已启动")
    print("📍 端口: 5001")
    app.run(debug=True, host='0.0.0.0', port=5001)

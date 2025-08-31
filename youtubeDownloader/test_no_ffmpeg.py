#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无需 FFmpeg 的 YouTube 音频下载测试脚本
使用 yt-dlp 的内置音频处理功能
"""

import subprocess
import sys
import os

def test_no_ffmpeg_download():
    """测试无需 FFmpeg 的音频下载方法"""
    
    print("=" * 60)
    print("测试无需 FFmpeg 的 YouTube 音频下载方法")
    print("=" * 60)
    
    # 测试 URL (一个短的测试视频)
    test_url = input("请输入 YouTube URL (或按回车使用默认测试): ").strip()
    if not test_url:
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - 短视频
    
    output_dir = input("输出目录 (或按回车使用当前目录): ").strip()
    if not output_dir:
        output_dir = "."
    
    print(f"\n测试URL: {test_url}")
    print(f"输出目录: {output_dir}")
    
    # 方法A的不同格式选项
    methods = [
        {
            "name": "方法A1: 下载最佳 M4A 音频",
            "args": ["-f", "bestaudio[ext=m4a]/bestaudio", "--output", f"{output_dir}/%(title)s_m4a.%(ext)s"]
        },
        {
            "name": "方法A2: 下载最佳 WEBM 音频", 
            "args": ["-f", "bestaudio[ext=webm]/bestaudio", "--output", f"{output_dir}/%(title)s_webm.%(ext)s"]
        },
        {
            "name": "方法A3: 下载最佳音频 (自动格式)",
            "args": ["-f", "bestaudio", "--output", f"{output_dir}/%(title)s_best.%(ext)s"]
        },
        {
            "name": "方法A4: 下载音频并保留原始格式",
            "args": ["--format", "bestaudio", "--output", f"{output_dir}/%(title)s_original.%(ext)s"]
        }
    ]
    
    print("\n" + "=" * 60)
    print("开始测试各种无需 FFmpeg 的下载方法...")
    print("=" * 60)
    
    for i, method in enumerate(methods, 1):
        print(f"\n[{i}/4] {method['name']}")
        print("-" * 40)
        
        try:
            # 构建 yt-dlp 命令
            cmd = ["yt-dlp"] + method["args"] + [test_url]
            print(f"执行命令: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ 成功!")
                print("输出:", result.stdout.strip()[:200] + "..." if len(result.stdout) > 200 else result.stdout.strip())
            else:
                print("❌ 失败!")
                print("错误:", result.stderr.strip()[:200] + "..." if len(result.stderr) > 200 else result.stderr.strip())
                
        except subprocess.TimeoutExpired:
            print("⏰ 超时 (5分钟)")
        except FileNotFoundError:
            print("❌ 找不到 yt-dlp 命令")
            print("请确保 yt-dlp 已安装: pip install yt-dlp")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    # 显示下载的文件
    print("\n下载的文件:")
    for file in os.listdir(output_dir):
        if any(keyword in file.lower() for keyword in ['m4a', 'webm', 'ogg', 'mp3', 'wav']):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            print(f"  📁 {file} ({size:,} bytes)")

def show_format_info():
    """显示各种音频格式的信息"""
    print("\n" + "=" * 60)
    print("音频格式说明 (无需 FFmpeg)")
    print("=" * 60)
    
    formats = [
        {
            "format": "M4A",
            "description": "高质量音频，广泛支持",
            "pros": "质量好，文件小，兼容性强",
            "cons": "专利格式"
        },
        {
            "format": "WEBM", 
            "description": "Google 开发的开源格式",
            "pros": "开源，压缩率高，现代浏览器支持",
            "cons": "某些设备可能不支持"
        },
        {
            "format": "OGG",
            "description": "开源音频格式",
            "pros": "完全开源，质量好",
            "cons": "支持设备较少"
        }
    ]
    
    for fmt in formats:
        print(f"\n🎵 {fmt['format']}:")
        print(f"   描述: {fmt['description']}")
        print(f"   优点: {fmt['pros']}")
        print(f"   缺点: {fmt['cons']}")

def main():
    print("YouTube 音频下载器 (无需 FFmpeg)")
    print("使用 yt-dlp 内置音频处理功能")
    
    while True:
        print("\n" + "=" * 40)
        print("请选择:")
        print("1. 运行下载测试")
        print("2. 查看格式说明")
        print("3. 退出")
        print("=" * 40)
        
        choice = input("输入选择 (1-3): ").strip()
        
        if choice == "1":
            test_no_ffmpeg_download()
        elif choice == "2":
            show_format_info()
        elif choice == "3":
            print("再见!")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import yt_dlp
import os
import threading

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube批量音乐下载器")
        self.root.geometry("500x400")
        
        # URL输入框
        tk.Label(root, text="输入YouTube URL（每行一个）:").pack(pady=5)
        self.url_text = scrolledtext.ScrolledText(root, height=8, width=60)
        self.url_text.pack(pady=5)
        
        # 下载路径
        tk.Label(root, text="下载路径:").pack(pady=5)
        self.path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))  # 默认下载文件夹
        path_frame = tk.Frame(root)
        path_frame.pack(pady=5)
        tk.Entry(path_frame, textvariable=self.path_var, width=40).pack(side=tk.LEFT)
        tk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.LEFT, padx=5)
        
        # 下载按钮
        tk.Button(root, text="开始批量下载", command=self.start_download, bg="green", fg="white").pack(pady=10)
        
        # 日志输出
        tk.Label(root, text="下载日志:").pack(pady=5)
        self.log_text = scrolledtext.ScrolledText(root, height=6, width=60, state=tk.DISABLED)
        self.log_text.pack(pady=5)
    
    def browse_path(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def download_single(self, url, path):
        ydl_opts = {
            'format': 'bestaudio/best',  # 只下载最佳音频
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),  # 文件名格式
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return f"成功: {url}"
        except Exception as e:
            return f"失败: {url} - {str(e)}"
    
    def start_download(self):
        urls = [line.strip() for line in self.url_text.get(1.0, tk.END).strip().split('\n') if line.strip()]
        if not urls:
            messagebox.showwarning("警告", "请输入至少一个URL！")
            return
        
        path = self.path_var.get()
        if not os.path.exists(path):
            os.makedirs(path)
        
        self.log("开始下载...")
        threading.Thread(target=self._download_thread, args=(urls, path), daemon=True).start()
    
    def _download_thread(self, urls, path):
        for i, url in enumerate(urls, 1):
            self.log(f"[{i}/{len(urls)}] 下载中: {url}")
            result = self.download_single(url, path)
            self.log(result)
        self.log("所有下载完成！")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
import streamlit as st
import yt_dlp
import os

def download_youtube_video_or_audio(url, choice):
    # 根据用户选择设置下载选项
    if choice == 'Video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',  # 确保输出格式为 mp4
            'playlistend': 10,  # 只下载前10个视频
            'progress_hooks': [my_hook],
        }
    elif choice == 'Audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # 将编解码器更改为 mp3
                'preferredquality': '192',
            }],
            'playlistend': 10,  # 只下载前10个音频
            'progress_hooks': [my_hook],
            'keepvideo': True,  # 提取后保留视频文件
        }
    else:
        st.error("无效选择。请选择 'Video' 或 'Audio'。")
        return None
    
    # 使用 yt-dlp 下载视频或音频
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            
            # 检查文件是否为 webm 格式，如果是则转换为 mp3
            if choice == 'Audio' and file_name.endswith('.webm'):
                mp3_file_name = file_name.replace('.webm', '.mp3') 
                if os.path.exists(file_name):
                    os.rename(file_name, mp3_file_name)
                    file_name = mp3_file_name
            return file_name
    except yt_dlp.utils.DownloadError as e:
        st.error(f"下载错误：{str(e)}")
        return None
    
def my_hook(d):
    if d['status'] == 'downloading':
        percent_str = d['_percent_str'].strip().replace('%', '')
        try:
            percent = float(percent_str)
            st.session_state.progress_bar.progress(int(percent))
        except ValueError:
            st.error(f"Invalid progress value: {percent_str}")
    elif d['status'] == 'finished':
        st.session_state.progress_bar.empty()
        st.success('Download complete, now converting ...')
    elif d['status'] == 'postprocessing':
        percent_str = d.get('_percent_str', '0.0').strip().replace('%', '')
        try:
            percent = float(percent_str)
            st.session_state.conversion_progress_bar.progress(int(percent))
        except ValueError:
            st.error(f"Invalid conversion progress value: {percent_str}")

# Function to clear the input field
def clear_input():
    st.session_state['url'] = ""

# Streamlit app
st.title("YouTube Video/Audio Downloader")

# Initialize the URL in session state if not already done
if 'url' not in st.session_state:
    st.session_state['url'] = ""

# Input URL
url = st.text_input("Enter the YouTube URL:", key="url")

# Select download type
choice = st.selectbox("Do you want to download video or audio?", ('Video', 'Audio'))

# Initialize the progress bars in session state
if 'progress_bar' not in st.session_state:
    st.session_state.progress_bar = st.empty()
if 'conversion_progress_bar' not in st.session_state:
    st.session_state.conversion_progress_bar = st.empty()

# Download button
if st.button("Download"):
    if url:
        file_path = download_youtube_video_or_audio(url, choice)
        if file_path and os.path.exists(file_path):
            st.success(f"Download available: {file_path}")
            with open(file_path, "rb") as file:
                btn = st.download_button(
                    label="Download File",
                    data=file,
                    file_name=os.path.basename(file_path),
                    mime="audio/mpeg" if choice == "Audio" else "video/mp4"
                )
            clear_input()  # Clear the input field after download
        else:
            st.error("File not found. Please try again.")
    else:
        st.error("Please enter a valid YouTube URL.")

# Quit button
if st.button("Clear"):
    clear_input()  # Clear the input field when quitting
    st.stop()

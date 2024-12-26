import streamlit as st
import yt_dlp
import pytube
import youtube_dl
import os
import threading

# Function to download YouTube video or audio using yt-dlp
def download_with_ytdlp(url, choice):
    if choice == 'Video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'playlistend': 1,
            'progress_hooks': [my_hook],
        }
    elif choice == 'Audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'playlistend': 1,
            'progress_hooks': [my_hook],
            'keepvideo': True,
        }
    else:
        st.error("Invalid choice. Please select 'Video' or 'Audio'.")
        return None
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            st.write(f"Downloaded file: {file_name}")
            if choice == 'Audio' and file_name.endswith('.webm'):
                mp3_file_name = file_name.replace('.webm', '.mp3')
                if os.path.exists(file_name):
                    os.rename(file_name, mp3_file_name)
                    file_name = mp3_file_name
                    st.write(f"Renamed file: {file_name}")
            if os.path.exists(file_name):
                return file_name
            else:
                st.error("File not found after download.")
                return None
    except yt_dlp.utils.DownloadError as e:
        st.error(f"yt-dlp error: {str(e)}")
        return None

# Function to download YouTube video or audio using pytube
def download_with_pytube(url, choice):
    try:
        yt = pytube.YouTube(url)
        if choice == 'Video':
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        elif choice == 'Audio':
            stream = yt.streams.filter(only_audio=True).first()
        else:
            st.error("Invalid choice. Please select 'Video' or 'Audio'.")
            return None
        
        file_name = stream.download()
        if choice == 'Audio':
            base, ext = os.path.splitext(file_name)
            new_file = base + '.mp3'
            os.rename(file_name, new_file)
            file_name = new_file
        return file_name
    except Exception as e:
        st.error(f"pytube error: {str(e)}")
        return None

# Function to download YouTube video or audio using youtube-dl
def download_with_youtubedl(url, choice):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if choice == 'Video' else 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if choice == 'Audio' else [],
    }
    
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            if choice == 'Audio' and file_name.endswith('.webm'):
                mp3_file_name = file_name.replace('.webm', '.mp3')
                if os.path.exists(file_name):
                    os.rename(file_name, mp3_file_name)
                    file_name = mp3_file_name
            return file_name
    except youtube_dl.utils.DownloadError as e:
        st.error(f"youtube-dl error: {str(e)}")
        return None

# Function to download YouTube video or audio
def download_youtube_video_or_audio(url, choice):
    file_name = download_with_ytdlp(url, choice)
    if not file_name:
        file_name = download_with_pytube(url, choice)
    if not file_name:
        file_name = download_with_youtubedl(url, choice)
    return file_name

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

# Callback function to clear the input field
def clear_input():
    st.session_state.url = ""

# Function to keep the app active
def keep_active():
    threading.Timer(345600, keep_active).start()

# Streamlit app
st.title("YouTube Video/Audio Downloader")

if 'url' not in st.session_state:
    st.session_state.url = ""

url = st.text_input("Enter the YouTube URL:", key="url")
choice = st.selectbox("Do you want to download video or audio?", ('Video', 'Audio'))

if 'progress_bar' not in st.session_state:
    st.session_state.progress_bar = st.empty()
if 'conversion_progress_bar' not in st.session_state:
    st.session_state.conversion_progress_bar = st.empty()

keep_active()

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
                    mime="audio/mpeg" if choice == "Audio" else "video/mp4",
                    on_click=clear_input
                )
        else:
            st.error("File not found. Please try again.")
    else:
        st.error("Please enter a valid YouTube URL.")
        
if st.button("Clear", on_click=clear_input):
    st.stop()
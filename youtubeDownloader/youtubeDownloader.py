import streamlit as st
import yt_dlp
import os
import threading
import zipfile

# Function to download individual video or audio using yt-dlp
def download_individual_with_ytdlp(url, choice):
    if choice == 'Video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
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
            if choice == 'Audio' and not file_name.endswith('.mp3'):
                mp3_file_name = file_name.rsplit('.', 1)[0] + '.mp3'
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

# Function to download YouTube playlist using yt-dlp
# Function to download YouTube playlist using yt-dlp
def download_playlist_with_ytdlp(url, choice):
    ydl_opts = {
        'format': 'bestaudio/best' if choice == 'Audio' else 'bestvideo+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if choice == 'Audio' else [],
        'progress_hooks': [my_hook],
        'keepvideo': True,
        'noplaylist': False,  # Ensure playlists are not ignored
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_dict = ydl.extract_info(url, download=True)
            downloaded_files = []
            if 'entries' in playlist_dict:
                for entry in playlist_dict['entries']:
                    file_name = ydl.prepare_filename(entry)
                    if choice == 'Audio' and not file_name.endswith('.mp3'):
                        mp3_file_name = file_name.rsplit('.', 1)[0] + '.mp3'
                        if os.path.exists(file_name):
                            os.rename(file_name, mp3_file_name)
                            file_name = mp3_file_name
                    if os.path.exists(file_name):
                        downloaded_files.append(file_name)
                        st.success(f"Downloaded: {file_name}")
                    else:
                        st.error(f"Failed to download: {entry['title']}")
            else:
                st.error("No entries found in the playlist.")
    except yt_dlp.utils.DownloadError as e:
        st.error(f"yt-dlp error: {str(e)}")

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
        st.success('Download complete, now converting...')
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
st.set_page_config(page_title="YouTube Downloader", layout="centered")

st.title("YouTube Video/Audio Downloader")
st.write("**Haven't supported playlist download,please input the video url directly.")

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
        if 'watch' in url:
            download_playlist_with_ytdlp(url, choice)
        else:
            file_path = download_individual_with_ytdlp(url, choice)
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

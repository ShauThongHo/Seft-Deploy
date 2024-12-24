import streamlit as st
import yt_dlp
from tqdm import tqdm

# Function to download YouTube video or audio
def download_youtube_video_or_audio(url, choice):
    # Set the download options based on user choice
    if choice == 'Video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
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
        }
    else:
        st.error("Invalid choice. Please select 'Video' or 'Audio'.")
        return
    
    # Initialize the progress bar
    global pbar
    pbar = tqdm(total=100, unit='B', unit_scale=True, desc='Downloading')
    
    # Download the video or audio using yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def my_hook(d):
    if d['status'] == 'downloading':
        pbar.update(d['downloaded_bytes'] - pbar.n)
        st.progress(int(d['_percent_str'].strip('%')))
    elif d['status'] == 'finished':
        pbar.close()
        st.success('Download complete, now converting ...')

# Streamlit app
st.title("YouTube Video/Audio Downloader")

# Input URL
url = st.text_input("Enter the YouTube URL:")

# Select download type
choice = st.selectbox("Do you want to download video or audio?", ('Video', 'Audio'))

# Download button
if st.button("Download"):
    if url:
        download_youtube_video_or_audio(url, choice)
    else:
        st.error("Please enter a valid YouTube URL.")

# Quit button
if st.button("Quit"):
    st.stop()

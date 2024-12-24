import streamlit as st
import yt_dlp
import os

# Function to download YouTube audio as mp3
def download_youtube_audio(url):
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
    
    # Download the audio using yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        file_name = ydl.prepare_filename(info_dict)
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
        percent_str = d['_percent_str'].strip().replace('%', '')
        try:
            percent = float(percent_str)
            st.session_state.conversion_progress_bar.progress(int(percent))
        except ValueError:
            st.error(f"Invalid conversion progress value: {percent_str}")

# Streamlit app
st.title("YouTube Audio Downloader")

# Input URL
url = st.text_input("Enter the YouTube URL:")

# Initialize the progress bars in session state
if 'progress_bar' not in st.session_state:
    st.session_state.progress_bar = st.empty()
if 'conversion_progress_bar' not in st.session_state:
    st.session_state.conversion_progress_bar = st.empty()

# Download button
if st.button("Download"):
    if url:
        file_path = download_youtube_audio(url)
        if file_path and os.path.exists(file_path):
            st.success(f"Download complete: {file_path}")
            with open(file_path, "rb") as file:
                btn = st.download_button(
                    label="Download File",
                    data=file,
                    file_name=os.path.basename(file_path),
                    mime="audio/mpeg"
                )
        else:
            st.error("File not found. Please try again.")
    else:
        st.error("Please enter a valid YouTube URL.")

# Quit button
if st.button("Quit"):
    st.stop()

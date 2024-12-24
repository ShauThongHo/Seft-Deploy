import streamlit as st
import yt_dlp
import os
import subprocess

# Check if ffmpeg is installed
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        st.write("FFmpeg is installed.")
    except subprocess.CalledProcessError:
        st.error("FFmpeg is not installed. Please install FFmpeg to proceed.")

# Function to download YouTube video or audio
def download_youtube_video_or_audio(url, choice):
    # Extract information to determine if it's a playlist or a single video
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        is_playlist = 'entries' in info_dict
        st.write(f"Is playlist: {is_playlist}")

    # Set the download options based on user choice and type (video or playlist)
    if choice == 'Video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(playlist)s/%(title)s.%(ext)s' if is_playlist else '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',  # Ensure the output format is mp4
            'progress_hooks': [my_hook],
            'noplaylist': False  # Ensure playlists are downloaded
        }
    elif choice == 'Audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(playlist)s/%(title)s.%(ext)s' if is_playlist else '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # Change the codec to mp3
                'preferredquality': '192',
            }],
            'progress_hooks': [my_hook],
            'keepvideo': True,  # Keep the video file after extraction
            'noplaylist': False  # Ensure playlists are downloaded
        }
    else:
        st.error("Invalid choice. Please select 'Video' or 'Audio'.")
        return None
    
    # Download the video or audio using yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        if is_playlist:
            for entry in info_dict['entries']:
                file_name = ydl.prepare_filename(entry)
                st.write(f"Downloaded file: {file_name}")
        else:
            file_name = ydl.prepare_filename(info_dict)
            st.write(f"Downloaded file: {file_name}")
        
        # Check if the file is in webm format and convert it to mp3 if necessary
        if choice == 'Audio' and file_name.endswith('.webm'):
            mp3_file_name = file_name.replace('.webm', '.mp3') 
            if os.path.exists(file_name):
                os.rename(file_name, mp3_file_name)
                file_name = mp3_file_name
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

# Streamlit app
st.title("YouTube Video/Audio Downloader")

# Check if ffmpeg is installed
check_ffmpeg()

# Initialize the URL in session state if not already done
if 'url' not in st.session_state:
    st.session_state.url = ""

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
                    mime="audio/mpeg" if choice == "Audio" else "video/mp4",
                    on_click=clear_input  # Clear the input field after download
                )
        else:
            st.error("File not found. Please try again.")
    else:
        st.error("Please enter a valid YouTube URL.")

# Quit button
if st.button("Quit", on_click=clear_input):
    st.stop()

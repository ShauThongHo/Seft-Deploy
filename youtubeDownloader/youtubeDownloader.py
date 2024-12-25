import streamlit as st
import yt_dlp
import os
import threading

# Function to download YouTube video or audio
def download_youtube_video_or_audio(url, choice):
    # Set the download options based on user choice
    if choice == 'Video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',  # Ensure the output format is mp4
            'playlistend': 1,  # Download only the first video in the playlist
            'progress_hooks': [my_hook],
        }
    elif choice == 'Audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',  # Change the codec to mp3
                'preferredquality': '192',
            }],
            'playlistend': 1,  # Download only the first audio in the playlist
            'progress_hooks': [my_hook],
            'keepvideo': True,  # Keep the video file after extraction
        }
    else:
        st.error("Invalid choice. Please select 'Video' or 'Audio'.")
        return None
    
    # Download the video or audio using yt-dlp
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)
            
            # Check if the file is in webm format and convert it to mp3 if necessary
            if choice == 'Audio' and file_name.endswith('.webm'):
                mp3_file_name = file_name.replace('.webm', '.mp3') 
                if os.path.exists(file_name):
                    os.rename(file_name, mp3_file_name)
                    file_name = mp3_file_name
            return file_name
    except yt_dlp.utils.DownloadError as e:
        st.error(f"Download error: {str(e)}")
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

# Callback function to clear the input field
def clear_input():
    st.session_state.url = ""

# Function to keep the app active
def keep_active():
    threading.Timer(345600, keep_active).start()  # Set the timer to 4 days (345600 seconds)

# Streamlit app
st.title("YouTube Video/Audio Downloader")

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

# Start the timer to keep the app active
keep_active()

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
if st.button("Clear", on_click=clear_input):
    st.stop()

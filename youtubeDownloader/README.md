# YouTube to MP3 Converter (JavaFX)

A JavaFX application that downloads YouTube videos and converts them to MP3 format.

## Features

- Clean and intuitive JavaFX user interface
- Download YouTube videos and convert to MP3
- Choose output directory
- Real-time download progress
- Detailed logging
- Support for various YouTube URL formats

## Prerequisites

Before running this application, you need to install:

### 1. Java Development Kit (JDK) 11 or higher
Download from [Oracle](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://openjdk.org/)

### 2. JavaFX SDK
Download JavaFX SDK from [Gluon](https://gluonhq.com/products/javafx/)
- Extract to a directory (e.g., `C:\Program Files\JavaFX\javafx-sdk-17.0.2`)
- Update the paths in `run.bat` to match your JavaFX installation

### 3. yt-dlp
Install yt-dlp (YouTube downloader):
```bash
# Using pip
pip install yt-dlp

# Or download executable from GitHub
# https://github.com/yt-dlp/yt-dlp/releases
```

### 4. FFmpeg
Install FFmpeg for audio conversion:
- Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- Add FFmpeg to your system PATH

## Installation

1. Clone or download this repository
2. Navigate to the `youtubeDownloader` directory
3. Update the JavaFX path in `run.bat` to match your installation
4. Make sure `yt-dlp` and `ffmpeg` are in your system PATH

## Usage

### Option 1: Using the batch file (Windows)
```bash
cd youtubeDownloader
run.bat
```

### Option 2: Manual compilation and execution
```bash
# Compile
javac --module-path "path/to/javafx/lib" --add-modules javafx.controls,javafx.fxml youtubeConvertMP3.java

# Run
java --module-path "path/to/javafx/lib" --add-modules javafx.controls,javafx.fxml youtubeDownloader.youtubeConvertMP3
```

### Using the Application

1. **Enter YouTube URL**: Paste the YouTube video URL in the text field
2. **Select Output Folder**: Choose where to save the MP3 file (defaults to Downloads folder)
3. **Click Download**: The application will download the video and convert it to MP3
4. **Monitor Progress**: Watch the progress bar and log for real-time updates

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`
- YouTube playlist URLs

## Troubleshooting

### "yt-dlp is not installed"
- Install yt-dlp using pip: `pip install yt-dlp`
- Or download the executable and add it to your PATH

### "ffmpeg is not installed"
- Download FFmpeg and add it to your system PATH
- Verify installation: `ffmpeg -version`

### JavaFX Module Issues
- Ensure JavaFX SDK is properly installed
- Update the module path in your run command
- For Java 11+, JavaFX is not included and must be added separately

### Download Fails
- Check your internet connection
- Verify the YouTube URL is valid and accessible
- Some videos may be geo-restricted or have download limitations

## File Structure

```
youtubeDownloader/
├── youtubeConvertMP3.java  # Main JavaFX application
├── run.bat                 # Windows batch file to compile and run
└── README.md              # This file
```

## Dependencies

- **JavaFX**: For the graphical user interface
- **yt-dlp**: For downloading YouTube videos
- **FFmpeg**: For audio conversion and processing

## License

This project is for educational purposes. Please respect YouTube's Terms of Service and copyright laws when downloading content.

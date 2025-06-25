import yt_dlp
import os
from pathlib import Path
import click

def download_audio(url, output_dir):
    """Download audio from YouTube URL using yt-dlp."""
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'extractaudio': True,
        'audioformat': 'mp3',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Get video info to determine output filename
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'audio')
        
        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        audio_filename = f"{safe_title}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        # Download the audio
        ydl.download([url])
        
        # Find the actual downloaded file (yt-dlp might modify the filename)
        for file in os.listdir(output_dir):
            if file.endswith('.mp3'):
                actual_path = os.path.join(output_dir, file)
                if actual_path != audio_path:
                    os.rename(actual_path, audio_path)
                return audio_path, safe_title
        
        raise FileNotFoundError("Downloaded audio file not found")
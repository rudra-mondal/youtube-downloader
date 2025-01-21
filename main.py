"""
YouTube Downloader
Author: Rudra Mondal

This script allows users to download videos from YouTube and Facebook. 
It provides a graphical user interface built with CustomTkinter for ease of use.

Features:

- Supports downloading from both YouTube and Facebook.
- Detects video platform automatically from the provided URL.
- Displays video thumbnail, title, uploader, and duration.
- Offers quality selection (e.g., 720p, 1080p) based on available formats.
- Allows choosing between video (MP4) and audio (MP3) downloads.
- Customizable download path.
- Real-time download progress with speed and ETA estimations.
- Automatic conversion to MP3 or MP4 (H.264) format using FFmpeg.
- Error handling for invalid URLs and download issues.

Dependencies:

- yt-dlp: For downloading video and audio streams.
- CustomTkinter: For the GUI.
- Pillow (PIL): For image processing (thumbnail display).
- requests: For fetching data from URLs.
- ffmpeg: For video and audio conversion.
- ffprobe: For retrieving media information (used to calculate video duration for progress display during conversion).
- threading: To improve download speed and prevent UI freezes

**NOTE**:

- The bundled FFmpeg and FFprobe executables are located in the "bin" folder. Ensure this folder is present in the same directory as the 'main.py'. Make sure both executables have execute permissions.
- When using PyInstaller, the `resource_path` function might need adjustments depending on your system.  If `sys._MEIPASS2` doesn't work, try using `sys._MEIPASS` instead in the `resource_path` function (In the line: 67).
- Downloading copyrighted content without permission is illegal. This script is provided for educational and personal use only.

"""


import os
import re
import sys
import yt_dlp
import threading
import webbrowser
import subprocess
from customtkinter import CTkLabel
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import requests
from io import BytesIO
import time

# Set the appearance mode and blue color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Constants for colors
RED = "#FF0000"
GREEN = "#00FF00"
BLUE = "#0000FF"

# Asset Loading
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS2       # If this not work, try "base_path = sys._MEIPASS"
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Animated label for the footer
class AniLabel(CTkLabel):
    def __init__(self, master, text, font, text_color, cursor="hand2"):
        super().__init__(master, text=text, font=font, text_color=text_color, cursor=cursor)
        self.colors = ["#373737", "#393939", "#3a3a3a", "#3c3c3c", "#3d3d3d", "#3f3f3f", "#404040", "#424242", "#434343", "#454545", "#464646", "#484848", "#494949", "#4b4b4b", "#4c4c4c", "#4e4e4e", "#4f4f4f", "#515151", "#525252", "#545454", "#555555", "#575757", "#585858", "#5a5a5a", "#5b5b5b", "#5d5d5d", "#5e5e5e", "#606060", "#616161", "#636363", "#646464", "#666666", "#676767", "#696969", "#6a6a6a", "#6c6c6c", "#6d6d6d", "#6f6f6f", "#707070", "#727272", "#737373", "#757575", "#767676", "#787878", "#797979", "#7b7b7b", "#7c7c7c", "#7b7b7b", "#797979", "#787878", "#767676", "#757575", "#737373", "#727272", "#707070", "#6f6f6f", "#6d6d6d", "#6c6c6c", "#6a6a6a", "#696969", "#676767", "#666666", "#646464", "#636363", "#616161", "#606060", "#5e5e5e", "#5d5d5d", "#5b5b5b", "#5a5a5a", "#585858", "#575757", "#555555", "#545454", "#525252", "#515151", "#4f4f4f", "#4e4e4e", "#4c4c4c", "#4b4b4b", "#494949", "#484848", "#464646", "#454545", "#434343", "#424242", "#404040", "#3f3f3f", "#3d3d3d", "#3c3c3c", "#3a3a3a", "#393939", "#373737"]
        self.color_index = 0
        self.animate()

    def animate(self):
        self.configure(text_color=self.colors[self.color_index])
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.after(100, self.animate)  # Adjust animation speed here (milliseconds)

# Main app class
class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        # App settings
        self.title("YouTube & Facebook Downloader")
        self.geometry("900x800")
        self.resizable(False, False)
        self.iconbitmap(resource_path("images\\icon.ico"))

        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Title
        self.title_label = ctk.CTkLabel(self.main_frame, text="YouTube & Facebook Downloader", font=("Helvetica", 24, "bold"))
        self.title_label.pack(pady=10)

        # URL Input - Integrated with fetch button, Rounded search bar
        self.input_frame = ctk.CTkFrame(self.main_frame, corner_radius=50)
        self.input_frame.pack(pady=10, padx=100, fill="x")
        self.url_entry = ctk.CTkEntry(self.input_frame, width=450, height=45, border_width=0, fg_color="transparent", placeholder_text="Paste YouTube or Facebook Video URL Here", font=("SF Pro Text", 14))
        self.url_entry.pack(side="left", padx=20)  # Add padding to the right of the entry
        # Fetch Button
        search_image = ctk.CTkImage(Image.open(resource_path(r"images\\search.png")), size=(22, 22))
        self.fetch_button = ctk.CTkButton(self.input_frame, image=search_image, text="Fetch", height=45, corner_radius=20, font=("SF Pro Text", 14), command=self.fetch_video_info) # image=search_image
        self.fetch_button.pack(side="right", padx=(0, 15))

        # Video Thumbnail
        self.thumbnail_label = ctk.CTkLabel(self.main_frame, text="")
        self.thumbnail_label.pack(pady=10)

        # Video Metadata
        self.metadata_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.metadata_frame.pack(pady=10, fill="x", padx=20)
        self.metadata_label = ctk.CTkLabel(self.metadata_frame, text="", justify="left", text_color="#FFFFFF")
        self.metadata_label.pack(pady=10, padx=10)

        # Status Label (initially hidden)
        self.status_label = ctk.CTkLabel(self.main_frame, text="", font=("Helvetica", 14))
        self.status_label.pack(pady=1)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=600, fg_color="#333333")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)  # Initialize progress to 0%

        # Time Estimate Label
        self.time_label = ctk.CTkLabel(self.main_frame, text="", font=("Helvetica", 12))
        self.time_label.pack(pady=1)

        # Video Quality and Format Options
        self.options_frame = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.options_frame.pack(pady=10, fill="x", padx=20)
        self.quality_label = ctk.CTkLabel(self.options_frame, text="Choose Quality:")
        self.quality_label.grid(row=0, column=0, padx=10, pady=10)
        self.quality_options = ctk.CTkOptionMenu(self.options_frame, values=[], command=self.set_quality)
        self.quality_options.grid(row=0, column=1, padx=10, pady=10)
        self.format_label = ctk.CTkLabel(self.options_frame, text="Choose Format:")
        self.format_label.grid(row=1, column=0, padx=10, pady=10)
        self.format_options = ctk.CTkOptionMenu(self.options_frame, values=["Video", "Audio (MP3)"], command=self.set_format)
        self.format_options.grid(row=1, column=1, padx=10, pady=10)

        # Download Path
        self.path_label = ctk.CTkLabel(self.options_frame, text="Choose Folder:")
        self.path_label.grid(row=2, column=0, padx=10, pady=10)
        self.path_button = ctk.CTkButton(self.options_frame, text="Choose Download Folder", command=self.choose_path)
        self.path_button.grid(row=2, column=1, padx=10, pady=10)
       
        # Path Display
        self.path_display = ctk.CTkLabel(self.options_frame, text=os.path.join(os.environ['USERPROFILE'], 'Downloads'), text_color="#ffff00", font=("Arial", 12))
        self.path_display.grid(row=2, column=2, padx=10, pady=10)

        # Download Button
        self.download_button = ctk.CTkButton(self.main_frame, text="Download", command=self.start_download, fg_color="green", hover_color="#005100")
        self.download_button.pack(pady=10)

        # Footer
        self.footer_label = AniLabel(self.main_frame, text="𓆩ʚ Crafted by Rudra ɞ𓆪", font=("Helvetica", 12, "bold"), text_color="#777777", cursor="hand2")
        self.footer_label.place(relx=0.5, rely=0.98, anchor="s")
        self.footer_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/rudra-mondal"))

        # Initialize variables
        self.video_data = None
        self.download_quality = None
        self.download_format = "mp4"
        self.download_path = os.path.join(os.environ['USERPROFILE'], 'Downloads')
        self.start_time = None
        self.last_downloaded_bytes = 0
        self.last_time = None
        os.makedirs(self.download_path, exist_ok=True)
    
    # Fetches video information based on the provided URL.
    def fetch_video_info(self):
        url = self.url_entry.get()
        if not url:
            self.metadata_label.configure(text="Please enter a valid URL first!", text_color=RED)
            return
        
        self.status_label.configure(text="Detecting Platform...", text_color="yellow")
        self.fetch_button.configure(state="disabled")
        threading.Thread(target=self.fetch_video_info_thread, args=(url,), daemon=True).start()
    
    # Detects if the provided link is from YouTube or Facebook.
    def detect_video_platform(self, link):
        # Patterns to detect Facebook video links
        facebook_patterns = [
            r"^(https?://)?(www\.)?facebook\.com/.*/videos/.*",     # Standard Facebook video link
            r"^(https?://)?(www\.)?fb\.watch/.*",                   # fb.watch short links
            r"^(https?://)?(www\.)?facebook\.com/reel/.*",          # Facebook Reels
            r"^(https?://)?(www\.)?facebook\.com/.*/posts/.*",      # Facebook posts with videos
        ]
        
        # Patterns to detect YouTube video links
        youtube_patterns = [
            r"^(https?://)?(www\.)?youtube\.com/watch\?v=.*",       # Standard YouTube video link
            r"^(https?://)?youtu\.be/.*",                           # Shortened YouTube links
            r"^(https?://)?(www\.)?youtube\.com/shorts/.*",         # YouTube Shorts
        ]

        for pattern in facebook_patterns:
            if re.match(pattern, link, re.IGNORECASE):
                return "facebook"

        for pattern in youtube_patterns:
            if re.match(pattern, link, re.IGNORECASE):
                return "youtube"
        
        return None
    
    # Fetches video information in a separate thread to prevent UI blocking.
    def fetch_video_info_thread(self, url):
        platform = self.detect_video_platform(url)

        if platform == "youtube":
            self.status_label.configure(text="Getting YouTube video information...", text_color="yellow")
            self._fetch_youtube_info(url)
        elif platform == "facebook":
            self.status_label.configure(text="Getting Facebook video information...", text_color="yellow")
            self._fetch_facebook_info(url)
        else:
            self.metadata_label.configure(text="Unsupported video platform or invalid URL.", text_color=RED)
            self.status_label.configure(text="")
            self.fetch_button.configure(state="normal")
            self.download_button.configure(state="normal")
    
    # Fetches video information for YouTube videos.
    def _fetch_youtube_info(self, url):
         try:
             with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                 self.video_data = ydl.extract_info(url, download=False)

                 thumbnail_url = self.video_data['thumbnail']
                 response = requests.get(thumbnail_url)
                 img_data = BytesIO(response.content)
                 thumbnail = Image.open(img_data).resize((320, 180))
                 thumbnail_image = ctk.CTkImage(thumbnail, size=(320, 180))
                 self.thumbnail_label.configure(image=thumbnail_image)
                 self.thumbnail_label.image = thumbnail_image

                 title = self.video_data['title']
                 uploader = self.video_data['uploader']
                 duration = self.video_data.get('duration_string', 'Unknown duration')
                 self.metadata_label.configure(
                     text=f"Title: {title}\nUploader: {uploader}\nDuration: {duration}", text_color="white"
                 )

                 formats = self.video_data['formats']
                 quality_choices = [
                     f"{fmt.get('height')}p"
                     for fmt in formats if fmt.get("vcodec") != "none" and fmt.get("height")
                 ]
                 quality_choices = sorted(set(quality_choices), key=lambda x: int(x[:-1]))
                 self.quality_options.configure(values=quality_choices)
                 self.quality_options.set(quality_choices[0])
                 self.status_label.configure(text="")
                 self.fetch_button.configure(state="normal")
                 self.download_button.configure(state="normal")
         except Exception as e:
             self.metadata_label.configure(text=f"Error fetching YouTube video info: {e}", text_color=RED)
             self.status_label.configure(text="")
             self.fetch_button.configure(state="normal")
             self.download_button.configure(state="normal")
    
    # Fetches video information for Facebook videos.
    def _fetch_facebook_info(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                self.video_data = ydl.extract_info(url, download=False)

                thumbnail_url = self.video_data['thumbnail']
                response = requests.get(thumbnail_url)
                img_data = BytesIO(response.content)
                thumbnail = Image.open(img_data).resize((320, 180))
                thumbnail_image = ctk.CTkImage(thumbnail, size=(320, 180))
                self.thumbnail_label.configure(image=thumbnail_image)
                self.thumbnail_label.image = thumbnail_image

                title = self.video_data['title']
                title = re.sub(r"^[^|]*\| ", "", title)
                title = re.sub(r'\s+', ' ', title).strip()
                title = title[:100]
                uploader = self.video_data['uploader']
                duration = self.video_data.get('duration_string', 'Unknown duration')
                self.metadata_label.configure(
                    text=f"Title: {title}\nUploader: {uploader}\nDuration: {duration}", text_color="white"
                )

                formats = self.video_data['formats']
                quality_choices = [
                    f"{fmt.get('height')}p"
                    for fmt in formats if fmt.get("vcodec") != "none" and fmt.get("height")
                ]
                quality_choices = sorted(set(quality_choices), key=lambda x: int(x[:-1]))
                self.quality_options.configure(values=quality_choices)
                self.quality_options.set(quality_choices[0])
                self.status_label.configure(text="")
                self.fetch_button.configure(state="normal")
                self.download_button.configure(state="normal")
        except Exception as e:
            self.metadata_label.configure(text=f"Error fetching Facebook video info: {e}", text_color=RED)
            self.status_label.configure(text="")
            self.fetch_button.configure(state="normal")
            self.download_button.configure(state="normal")

    # Sets the download quality.
    def set_quality(self, choice):
        self.download_quality = choice

    # Sets the download format.
    def set_format(self, choice):
        self.download_format = "mp4" if choice == "Video" else "mp3"
    
    # Opens a dialog to choose the download path.
    def choose_path(self):
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.download_path = selected_path
            self.path_display.configure(text=self.download_path)
    
    # Starts the download process based on the video platform.
    def start_download(self):
        if not self.video_data:
            self.metadata_label.configure(text="Please fetch a video first!", text_color=RED)
            self.download_button.configure(state="normal")
            return

        url = self.url_entry.get()
        if not url:
            self.metadata_label.configure(text="Please enter a valid URL first!", text_color=RED)
            self.download_button.configure(state="normal")
            return

        platform = self.detect_video_platform(url)
        self.start_time = time.time()
        self.last_downloaded_bytes = 0
        self.last_time = self.start_time
        self.download_button.configure(state="disabled")

        if platform == "youtube":
            threading.Thread(target=self.download_youtube_video, args=(url,), daemon=True).start()
        elif platform == "facebook":
            threading.Thread(target=self.download_facebook_video, args=(url,), daemon=True).start()
        else:
            self.status_label.configure(text="Unsupported video platform or invalid URL.", text_color=RED)
            self.download_button.configure(state="normal")
        
    def progress_callback(self, d):
        """
        Callback function for yt-dlp to update download progress.
        Calculates speed, eta and updates the progress bar
        """
        if d['status'] == 'downloading':
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = d.get('total_bytes', 1)
            progress = downloaded_bytes / total_bytes
            self.progress_bar.set(progress)

            # Calculate download speed and ETA
            current_time = time.time()
            if current_time - self.last_time >= 1:  # Update every second
                speed = (downloaded_bytes - self.last_downloaded_bytes) / (current_time - self.last_time)
                remaining_bytes = total_bytes - downloaded_bytes
                eta = remaining_bytes / speed if speed > 0 else 0

                # Format total
                if total_bytes < 1024:
                    total_str = f"{total_bytes:.1f} B"
                elif total_bytes < 1024*1024:
                    total_str = f"{total_bytes/1024:.1f} KB"
                else:
                    total_str = f"{total_bytes/(1024*1024):.1f} MB"
                
                # Format downloaded
                if downloaded_bytes < 1024:
                    downloaded_str = f"{downloaded_bytes:.1f} B"
                elif total_bytes < 1024*1024:
                    downloaded_str = f"{downloaded_bytes/1024:.1f} KB"
                else:
                    downloaded_str = f"{downloaded_bytes/(1024*1024):.1f} MB"
                
                # Format speed and ETA
                if speed < 1024:
                    speed_str = f"{speed:.1f} B/s"
                elif speed < 1024*1024:
                    speed_str = f"{speed/1024:.1f} KB/s"
                else:
                    speed_str = f"{speed/(1024*1024):.1f} MB/s"

                eta_min = int(eta // 60)
                eta_sec = int(eta % 60)
                
                self.time_label.configure(text=f"Speed: {speed_str}  |  Downloaded: {downloaded_str} / {total_str}  |  ETA: {eta_min}m {eta_sec}s")
                
                self.last_downloaded_bytes = downloaded_bytes
                self.last_time = current_time
    
    def download_youtube_video(self, url):
        """Downloads a video from YouTube."""
        if not self.video_data:
            self.metadata_label.configure(text="Please fetch a video first!", text_color=RED)
            self.download_button.configure(state="normal")
            return

        if not url:
            self.metadata_label.configure(text="Please enter a valid URL!", text_color=RED)
            self.download_button.configure(state="normal")
            return
        
        title = self.video_data['title']
        title = re.sub(r'[\\/*?:"<>|]', "", title)      # Remove invalid characters
        title = re.sub(r'\s+', ' ', title).strip()      # Remove extra spaces and line breaks
        title = title[:100]                             # Limit title to 100 characters

        output_file = os.path.join(self.download_path, f'{title}.%(ext)s')
      
        ydl_opts = {
            'format': 'bestaudio' if self.download_format == "mp3" else f"bestvideo[height={self.download_quality[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            'outtmpl': output_file,
            'progress_hooks': [self.progress_callback],
            'ffmpeg_location': resource_path('bin')
        }

        try:
            self.status_label.configure(text="Downloading...", text_color="yellow")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info_dict)

                if self.download_format == "mp3":
                    self._convert_to_mp3(downloaded_file)

                elif self.download_format == "mp4":
                    self._convert_to_mp4(downloaded_file)

                self.status_label.configure(text="")
                self.time_label.configure(text="")

                total_time = time.time() - self.start_time
                minutes = int(total_time // 60)
                seconds = int(total_time % 60)
                self.metadata_label.configure(text=f"Download and conversion completed in {minutes}m {seconds}s!", text_color=GREEN)
                self.download_button.configure(state="normal")
        except Exception as e:
            self.metadata_label.configure(text=f"Error during download or conversion: {e}", text_color=RED)
            self.download_button.configure(state="normal")

    def download_facebook_video(self, url):
         """Downloads a video from Facebook."""
         if not self.video_data:
             self.metadata_label.configure(text="Please fetch a video first!", text_color=RED)
             self.download_button.configure(state="normal")
             return

         if not url:
             self.metadata_label.configure(text="Please enter a valid URL!", text_color=RED)
             self.download_button.configure(state="normal")
             return
         
         title = self.video_data['title']
         title = re.sub(r"^[^|]*\| ", "", title)          # Remove the part before the first '|' (This is only needed for Facebook for filtering out the reaction and share count)
         title = re.sub(r'[\\/:*?\"<>|]', '', title)      # Remove invalid characters
         title = re.sub(r'\s+', ' ', title).strip()       # Remove extra spaces and line breaks
         title = title[:100]                              # Limit title to 100 characters
         
         output_file = os.path.join(self.download_path, f'{title}.%(ext)s')
        
         ydl_opts = {
             'format': 'bestaudio' if self.download_format == "mp3" else f"bestvideo[height={self.download_quality[:-1]}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
             'outtmpl': output_file,
             'progress_hooks': [self.progress_callback],
             'ffmpeg_location': resource_path('bin')
         }

         try:
             self.status_label.configure(text="Downloading...", text_color="yellow")

             with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                 ydl.params['encoding'] = 'utf-8'
                 info_dict = ydl.extract_info(url, download=True)
                 downloaded_file = ydl.prepare_filename(info_dict)

                 if self.download_format == "mp3":
                    self._convert_to_mp3(downloaded_file)

                 elif self.download_format == "mp4":
                    self._convert_to_mp4(downloaded_file)

                 self.status_label.configure(text="")
                 self.time_label.configure(text="")

                 total_time = time.time() - self.start_time
                 minutes = int(total_time // 60)
                 seconds = int(total_time % 60)
                 self.metadata_label.configure(text=f"Download and conversion completed in {minutes}m {seconds}s!", text_color=GREEN)
                 self.download_button.configure(state="normal")
         except Exception as e:
             self.metadata_label.configure(text=f"Error during download or conversion: {e}", text_color=RED)
             self.download_button.configure(state="normal")

    def _convert_to_mp3(self, downloaded_file):
        """Converts a downloaded file to MP3 format."""
        self.status_label.configure(text="Converting to MP3...", text_color="yellow")
        self.time_label.configure(text="")

        converted_file = os.path.splitext(downloaded_file)[0] + ".mp3"

        conversion_command = [
            resource_path("bin\\ffmpeg"),
            "-y",
            "-i", downloaded_file,
            "-vn",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "192k",
            "-progress", "pipe:1",
            converted_file
        ]

        process = subprocess.Popen(
            conversion_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        duration = float(subprocess.check_output([
            resource_path("bin\\ffprobe"),
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            downloaded_file
        ]).decode().strip())


        while True:
            try:
                line = process.stdout.readline().decode('utf-8', 'ignore')
            except UnicodeDecodeError:  # improved error handling
                continue
            if not line:
                break
            if "out_time=" in line:
                time_str = line.split("out_time=")[1].split(".")[0]
                try:
                    current_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(time_str.split(":"))))
                    progress = (current_time / duration) * 100
                    self.progress_bar.set(progress / 100)
                    self.status_label.configure(text=f"Converting to MP3: {progress:.1f}%")
                except (ValueError, IndexError):  # More specific error catching
                    continue

        process.wait()
        os.remove(downloaded_file)


    def _convert_to_mp4(self, downloaded_file):
        """Converts a downloaded file to MP4 format."""
        self.status_label.configure(text="Converting to MP4...", text_color="yellow")
        self.time_label.configure(text="")
        converted_file = os.path.splitext(downloaded_file)[0] + f"_{self.download_quality}.mp4"

        conversion_command = [
            resource_path("bin\\ffmpeg"),
            "-y",
            "-i", downloaded_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-progress", "pipe:1",
            converted_file
        ]

        process = subprocess.Popen(
            conversion_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        duration = float(subprocess.check_output([
            resource_path("bin\\ffprobe"), 
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            downloaded_file
        ]).decode().strip())


        while True:
            try:
                line = process.stdout.readline().decode('utf-8', 'ignore')
            except UnicodeDecodeError:
                continue  # Or errors='replace'
            if not line:
                break
            if "out_time=" in line:
                time_str = line.split("out_time=")[1].split(".")[0]
                try:
                    current_time = sum(float(x) * 60 ** i for i, x in enumerate(reversed(time_str.split(":"))))
                    progress = (current_time / duration) * 100
                    self.progress_bar.set(progress / 100)
                    self.status_label.configure(text=f"Converting to MP4: {progress:.1f}%")
                except (ValueError, IndexError):
                    continue

        process.wait()
        os.remove(downloaded_file)
              
# Run the app
if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()

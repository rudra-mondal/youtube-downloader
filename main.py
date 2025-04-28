# -*- coding: utf-8 -*-
"""
YouTube, Facebook & Pinterest Downloader (Flet UI)
Author: Rudra Mondal

This script allows users to download videos, images, and GIFs from YouTube, Facebook, and Pinterest.
It provides a modern, responsive graphical user interface built with Flet,
using explicit FFmpeg conversion after initial download for reliability and accurate progress.

Dependencies: yt-dlp, flet==0.23.0, Pillow, requests, ffmpeg, ffprobe, pygame, threading
"""

import os
import re
import sys
import yt_dlp
import pygame
import threading
import webbrowser
import subprocess
import math
import flet as ft
from flet import (
    Page, Column, Row, Container, Text, TextField, ElevatedButton, IconButton, FilledButton, OutlinedButton,
    Image, ProgressBar, Dropdown, FilePicker, FilePickerResultEvent, TextButton, Divider, ResponsiveRow,
    alignment, padding, border_radius, border, margin, animation, transform, Theme, TextSpan, TextStyle,
    ScrollMode, CrossAxisAlignment, MainAxisAlignment
)
from flet import colors as ft_colors # Use alias for clarity
from PIL import Image as PILImage
import requests
from io import BytesIO
import time
import base64

# --- Enhanced Theme & Color Palette ---
PRIMARY_COLOR = ft_colors.BLUE_GREY_700
ACCENT_COLOR = ft_colors.CYAN_ACCENT_700
BG_COLOR = "#1A1C26"
CARD_BG_COLOR = "#232635"
INPUT_BG_COLOR = ft_colors.with_opacity(0.05, ft_colors.WHITE)
TEXT_COLOR_PRIMARY = ft_colors.WHITE
TEXT_COLOR_SECONDARY = ft_colors.with_opacity(0.7, ft_colors.WHITE)
TEXT_COLOR_MUTED = ft_colors.with_opacity(0.5, ft_colors.WHITE)
SUCCESS_COLOR = ft_colors.GREEN_ACCENT_400
ERROR_COLOR = ft_colors.RED_ACCENT_400
WARNING_COLOR = ft_colors.AMBER_ACCENT_400
INFO_COLOR = ft_colors.BLUE_ACCENT_100

# --- UI Dimensions ---
THUMBNAIL_WIDTH = 280
THUMBNAIL_HEIGHT = 158
CONTROL_HEIGHT = 48
BORDER_RAD = 10

# --- Resource Path Function (Updated for PyInstaller --onedir mode) ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller --onedir """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Sound Handling (Unchanged) ---
try:
    pygame.mixer.init()
    fetch_start_sound = pygame.mixer.Sound(resource_path("audio/click.mp3"))
    download_start_sound = pygame.mixer.Sound(resource_path("audio/click.mp3"))
    fetch_complete_sound = pygame.mixer.Sound(resource_path("audio/fetch_complete.mp3"))
    download_complete_sound = pygame.mixer.Sound(resource_path("audio/download_complete.mp3"))
    error_sound = pygame.mixer.Sound(resource_path("audio/error.mp3"))
    no_url_sound = pygame.mixer.Sound(resource_path("audio/no_url.mp3"))
    def play_sound(sound_object):
        try: sound_object.play()
        except Exception as e: print(f"Warning: Could not play sound - {e}")
except Exception as e:
    print(f"Warning: Pygame mixer initialization failed. Sounds will be disabled. Error: {e}")
    class DummySound:
        def play(self): pass
    fetch_start_sound, download_start_sound, fetch_complete_sound, download_complete_sound, error_sound, no_url_sound = (DummySound(),)*6
    def play_sound(sound_object): pass


# --- Custom Logger for yt-dlp (Unchanged) ---
class YtDlpLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"YT-DLP ERROR: {msg}")

# --- Core Downloader Logic Class (FFmpeg/probe path fixed) ---
class DownloaderAppLogic:
    def __init__(self, page: Page):
        self.page = page
        self.content_data = None
        self.download_quality = None
        self.download_format = "mp4"
        self.initial_download_path = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser("~")), 'Downloads')
        self.download_path = self.initial_download_path
        self.current_platform = None
        self.is_pinterest_video = False
        self.start_time = None
        self.last_downloaded_bytes = 0
        self.last_time = None
        self.last_speed = None
        # UI Control References
        self.url_entry: TextField = None
        self.fetch_button: FilledButton = None
        self.thumbnail_image: Image = None
        self.metadata_container: Container = None
        self.metadata_text: Text = None
        self.status_text: Text = None
        self.progress_bar: ProgressBar = None
        self.time_label: Text = None
        self.quality_dropdown: Dropdown = None
        self.format_dropdown: Dropdown = None
        self.path_display_text: Text = None
        self.download_button: FilledButton = None
        self.file_picker: FilePicker = None
        self.placeholder_base64 = self._create_placeholder_base64(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, (35, 38, 53))

        # Determine correct FFmpeg/FFprobe paths once
        self.ffmpeg_exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
        self.ffprobe_exe = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'
        self.ffmpeg_path = resource_path(os.path.join("bin", self.ffmpeg_exe))
        self.ffprobe_path = resource_path(os.path.join("bin", self.ffprobe_exe))

        os.makedirs(self.download_path, exist_ok=True)

    def _create_placeholder_base64(self, width, height, color):
        try:
            img = PILImage.new('RGB', (width, height), color=color)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        except Exception as e: print(f"Error creating placeholder: {e}"); return None

    def _update_ui(self, control, **kwargs):
        if not control or not control.uid or not self.page or not control.page:
            for key, value in kwargs.items(): setattr(control, key, value)
            return
        try:
            for key, value in kwargs.items(): setattr(control, key, value)
            control.update()
        except Exception as e: print(f"Error updating control {type(control)} ({control.uid}): {e}")

    def _update_page(self):
        if self.page:
            try: self.page.update()
            except Exception as e: print(f"Error updating page: {e}")

    def set_ui_controls(self, controls: dict):
        for key, control in controls.items(): setattr(self, key, control)
        if "metadata_container" in controls: self.metadata_container = controls["metadata_container"]
        if "metadata_text" in controls: self.metadata_text = controls["metadata_text"]
        self.update_path_display()

    def _update_metadata_content(self, widget):
        if self.metadata_container:
            self.metadata_container.content = widget
            self._update_ui(self.metadata_container)
            self.metadata_text = widget
        else: print("Error: metadata_container reference not set.")

    # --- Fetching Logic (Unchanged) ---
    def fetch_content_info(self, e=None):
        url = self.url_entry.value.strip() if self.url_entry else ""
        if not url:
            error_text = Text("Please enter a valid URL first!", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
            self._update_metadata_content(error_text); play_sound(no_url_sound); return

        placeholder_text = Text("Fetching details...", color=TEXT_COLOR_MUTED, size=13, text_align=ft.TextAlign.CENTER)
        self._update_metadata_content(placeholder_text)
        self._update_ui(self.status_text, value="Detecting Platform...", color=WARNING_COLOR)
        self._update_ui(self.thumbnail_image, src_base64=self.placeholder_base64, tooltip="Preview will appear here")
        self._update_ui(self.progress_bar, value=0, color=PRIMARY_COLOR)
        self._update_ui(self.time_label, value="")
        self._update_ui(self.quality_dropdown, options=[ft.dropdown.Option("N/A")], value="N/A", disabled=True)
        self._update_ui(self.format_dropdown, options=[ft.dropdown.Option("N/A")], value="N/A", disabled=True)
        self._update_ui(self.download_button, disabled=True)
        self._update_ui(self.fetch_button, disabled=True)
        self.content_data = None; self.is_pinterest_video = False
        threading.Thread(target=self.fetch_content_info_thread, args=(url,), daemon=True).start()

    def detect_video_platform(self, link): # Unchanged
        fb_watch_pattern = r"^(https?://)?fb\.watch/.*"; pin_it_pattern = r"^(https?://)?pin\.it/.*"
        if re.match(pin_it_pattern, link, re.IGNORECASE): return "pinterest"
        if re.match(fb_watch_pattern, link, re.IGNORECASE): return "facebook"
        facebook_patterns=[r"^(https?://)?(www\.|m\.)?facebook\.com/(.*)?(videos|reel|watch|live|posts|story\.php|video/embed|v|photos|groups/.*/(permalink/\d+|.*)|events/.*/(permalink/\d+|.*)|share/(v|r)/.*|share/.*)/.*"]
        youtube_patterns=[r"^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|embed/|v/|shorts/|c/|user/|channel/|live/|playlist\?list=|attribution_link\?)|youtu\.be/).*",r"^(https?://)?(www\.)?youtube-nocookie\.com/embed/.*"]
        pinterest_patterns=[r"^(https?://)?(www\.)?pinterest\.(com|ca|co\.uk|de|fr|es|it|jp|com\.au|com\.br|ch|at|be|dk|fi|ie|kr|mx|nl|no|nz|ph|pt|ru|se|sg)\/pin\/(\d+)\/?.*"]
        for p in pinterest_patterns:
            if re.match(p,link,re.IGNORECASE): return "pinterest"
        for p in facebook_patterns:
            if re.match(p,link,re.IGNORECASE): return "facebook"
        for p in youtube_patterns:
            if re.match(p,link,re.IGNORECASE): return "youtube"
        return None

    def fetch_content_info_thread(self, url): # Unchanged
        self.current_platform = self.detect_video_platform(url)
        if not self.current_platform:
            error_text = Text("Unsupported platform or invalid URL.", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
            self._update_metadata_content(error_text); self._update_ui(self.status_text, value=""); self._update_ui(self.fetch_button, disabled=False); play_sound(no_url_sound); return
        platform_name = self.current_platform.capitalize()
        self._update_ui(self.status_text, value=f"Getting {platform_name} info...", color=WARNING_COLOR); play_sound(fetch_start_sound)
        try:
            ydl_opts_fetch = {'quiet': True, 'skip_download': True, 'forcejson': False, 'noplaylist': True, 'logger': YtDlpLogger()}
            if self.current_platform == "facebook": cookie_path = resource_path("cookies/facebook_cookies.txt"); ydl_opts_fetch['cookiefile'] = cookie_path if os.path.exists(cookie_path) else None
            with yt_dlp.YoutubeDL(ydl_opts_fetch) as ydl:
                try: self.content_data = ydl.extract_info(url, download=False)
                except yt_dlp.utils.DownloadError as e:
                    error_msg = f"{e}"; error_msg += "\nTry adding cookies." if "login required" in error_msg.lower() else ""; error_msg = "Content unavailable or private." if "unavailable" in error_msg.lower() else error_msg
                    error_widget = Text(f"Error fetching info: {error_msg}", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER); self._update_metadata_content(error_widget)
                    self._update_ui(self.status_text, value=""); self._update_ui(self.fetch_button, disabled=False); play_sound(error_sound); return
            if not self.content_data: raise ValueError("Failed to extract content data.")
            if self.current_platform == "pinterest": formats = self.content_data.get('formats', []); self.is_pinterest_video = any(fmt.get('vcodec') not in (None, 'none') for fmt in formats)
            thumbnail_url = self.content_data.get('thumbnail')
            if self.current_platform == "pinterest" and not self.is_pinterest_video: image_url = self.content_data.get('url'); thumbnail_url = image_url if image_url and ('/170x/' not in (thumbnail_url or '') and '170x.' not in (thumbnail_url or '')) else thumbnail_url
            self._display_thumbnail(thumbnail_url or self.content_data.get('url'))
            title = self.content_data.get('title', 'No Title Found'); uploader = self.content_data.get('uploader', 'Unknown Uploader'); duration_raw = self.content_data.get('duration'); duration = self.content_data.get('duration_string', None)
            if not duration and isinstance(duration_raw, (int, float)): td = time.gmtime(duration_raw); duration = time.strftime('%H:%M:%S' if duration_raw >= 3600 else '%M:%S', td)
            duration = duration or "N/A"; content_type = None
            if self.current_platform == "pinterest": content_type = "Video" if self.is_pinterest_video else self.content_data.get('ext', 'Image/GIF').upper()
            metadata_widget = self._create_metadata_display(platform_name, title, uploader, duration if (self.current_platform != "pinterest" or self.is_pinterest_video) else None, content_type)
            self._update_metadata_content(metadata_widget)
            available_formats = []; quality_choices = []
            if self.current_platform == "pinterest" and not self.is_pinterest_video:
                original_ext = self.content_data.get('ext', 'file').upper(); format_name = f"{original_ext}" if original_ext != 'FILE' else "Image/GIF"; available_formats = [ft.dropdown.Option(format_name)]
                self._update_ui(self.quality_dropdown, options=[ft.dropdown.Option("Original")], value="Original", disabled=True); self.download_quality = "Original"
            else:
                formats = self.content_data.get('formats', []); quality_choices_mp4 = sorted(list(set(f"{int(fmt.get('height'))}p" for fmt in formats if fmt.get("vcodec") not in [None, 'none'] and fmt.get("height") and fmt.get('ext') == 'mp4')), key=lambda x: int(x[:-1]), reverse=True)
                if not quality_choices_mp4: quality_choices_mp4 = sorted(list(set(f"{int(fmt.get('height'))}p" for fmt in formats if fmt.get("vcodec") not in [None, 'none'] and fmt.get("height"))), key=lambda x: int(x[:-1]), reverse=True)
                quality_choices = [ft.dropdown.Option(q) for q in quality_choices_mp4] if quality_choices_mp4 else []
                available_formats = [ft.dropdown.Option("Video (MP4)"), ft.dropdown.Option("Audio (MP3)")]
                if quality_choices:
                     self._update_ui(self.quality_dropdown, options=quality_choices, disabled=False); default_quality = next((q.key for q in quality_choices if "1080" in q.key), quality_choices[0].key if quality_choices else "N/A")
                     self._update_ui(self.quality_dropdown, value=default_quality); self.download_quality = default_quality
                else: self._update_ui(self.quality_dropdown, options=[ft.dropdown.Option("N/A")], value="N/A", disabled=True); self.download_quality = None
            self._update_ui(self.format_dropdown, options=available_formats, disabled=False); default_format = available_formats[0].key; self._update_ui(self.format_dropdown, value=default_format); self.set_format(None)
            self._finalize_fetch(success=True)
        except Exception as e:
             error_widget = Text(f"Error processing info: {e}", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER); self._update_metadata_content(error_widget)
             self._update_ui(self.status_text, value=""); self._update_ui(self.fetch_button, disabled=False); play_sound(error_sound); print(f"Detailed fetch processing error: {type(e).__name__}: {e}")

    def _display_thumbnail(self, thumbnail_url): # Unchanged
        if not thumbnail_url: self._update_ui(self.thumbnail_image, src_base64=self.placeholder_base64, tooltip="No thumbnail URL"); return
        try:
            response = requests.get(thumbnail_url, timeout=10); response.raise_for_status()
            img_data = BytesIO(response.content); thumbnail = PILImage.open(img_data)
            thumbnail.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)); buffered = BytesIO()
            thumbnail.save(buffered, format="PNG"); img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            self._update_ui(self.thumbnail_image, src_base64=img_base64, tooltip="Content Thumbnail")
        except Exception as e: print(f"Error processing thumbnail: {e}"); self._update_ui(self.thumbnail_image, src_base64=self.placeholder_base64, tooltip=f"Thumbnail Error: {e}")

    def _finalize_fetch(self, success=True, error_message=None): # Unchanged
        if success:
            self._update_ui(self.status_text, value="Ready to Download!", color=SUCCESS_COLOR); self._update_ui(self.download_button, disabled=False); play_sound(fetch_complete_sound)
        else:
            self._update_ui(self.status_text, value="Fetch Failed!", color=ERROR_COLOR)
            display_error = "An error occurred during fetching."
            if error_message:
                 if isinstance(error_message, str):
                    if "HTTP Error 404" in error_message: display_error = "Content not found (404 Error)."
                    elif "private video" in error_message.lower(): display_error = "Cannot access private content."
                    elif "login required" in error_message.lower(): display_error = "Login required. Check cookies if needed."
                    elif "urlopen error" in error_message.lower(): display_error = "Network error. Please check connection."
                    elif "Unsupported URL" in error_message: display_error = "This specific URL format might not be supported."
                    else: display_error = f"Fetch Error: {error_message[:120]}"
                 else: display_error = f"Fetch Error: {str(error_message)[:120]}"
            error_text_widget = Text(display_error, color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
            self._update_metadata_content(error_text_widget); play_sound(error_sound)
        self._update_ui(self.fetch_button, disabled=False)

    def _create_metadata_display(self, platform, title, uploader, duration, content_type=None): # Unchanged
        controls = [
            TextSpan(f"{platform.capitalize()}", TextStyle(weight=ft.FontWeight.BOLD, color=ACCENT_COLOR, size=14)),
            TextSpan(f" • {content_type}" if content_type else "", TextStyle(color=TEXT_COLOR_SECONDARY)),
            TextSpan("\n"), TextSpan(f"{title}\n", TextStyle(size=15, weight=ft.FontWeight.W_500, color=TEXT_COLOR_PRIMARY)),
            TextSpan(f"By: {uploader}", TextStyle(size=13, color=TEXT_COLOR_SECONDARY)),
        ]
        if duration and duration != 'N/A': controls.append(TextSpan(f"  •  Duration: {duration}", TextStyle(size=13, color=TEXT_COLOR_SECONDARY)))
        return Text(spans=controls, selectable=True)

    def set_quality(self, e): self.download_quality = self.quality_dropdown.value if self.quality_dropdown else None # Unchanged
    def set_format(self, e): # Unchanged
        choice = self.format_dropdown.value if self.format_dropdown else None;
        if not choice: return
        is_video = "Video (MP4)" in choice; is_audio = "Audio (MP3)" in choice; is_pinterest_image = self.current_platform == "pinterest" and not self.is_pinterest_video
        if is_audio:
            self.download_format = "mp3"; self._update_ui(self.quality_dropdown, disabled=True, value="N/A"); self.download_quality = None
        elif is_video:
            self.download_format = "mp4"; quality_options = self.quality_dropdown.options if self.quality_dropdown else []; quality_available = quality_options and quality_options[0].key != "N/A"
            self._update_ui(self.quality_dropdown, disabled=not quality_available)
            if quality_available and (not self.download_quality or self.download_quality == "N/A"): self.download_quality = quality_options[0].key
            if not quality_available: self.download_quality = None; self._update_ui(self.quality_dropdown, value="N/A")
            else: self._update_ui(self.quality_dropdown, value=self.download_quality)
        elif is_pinterest_image:
             self.download_format = self.content_data.get('ext', 'file'); self._update_ui(self.quality_dropdown, disabled=True, value="Original"); self.download_quality = "Original"
        else: self.download_format = "mp4"; self._update_ui(self.quality_dropdown, disabled=False if self.quality_dropdown.options and self.quality_dropdown.options[0].key != "N/A" else True)

    def choose_path(self, e): # Unchanged
        if self.file_picker: self.file_picker.get_directory_path(initial_directory=self.download_path, dialog_title="Select Download Folder")
    def on_path_selected(self, e: FilePickerResultEvent): # Unchanged
        if e.path: self.download_path = e.path; self.update_path_display()
    def update_path_display(self): # Unchanged
        if self.path_display_text:
            max_display_len=40; display_text=self.download_path
            if len(display_text) > max_display_len: display_text="..."+display_text[-(max_display_len-3):]
            self._update_ui(self.path_display_text, value=display_text, tooltip=self.download_path)

    def start_download(self, e=None): # Unchanged
        if not self.content_data: error_text = Text("Please fetch content details first!", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER); self._update_metadata_content(error_text); play_sound(no_url_sound); return
        url = self.url_entry.value.strip() if self.url_entry else ""
        if not url: error_text = Text("URL seems to be missing!", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER); self._update_metadata_content(error_text); play_sound(no_url_sound); return
        is_video_download = (self.current_platform != "pinterest" or self.is_pinterest_video)
        if is_video_download and self.download_format == "mp4" and (not self.download_quality or self.download_quality == "N/A"): error_text = Text("Please select a valid video quality for MP4 download!", color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER); self._update_metadata_content(error_text); play_sound(no_url_sound); return
        self._update_ui(self.progress_bar, value=None, color=ACCENT_COLOR); self._update_ui(self.time_label, value=""); self._update_ui(self.status_text, value="Preparing download...", color=INFO_COLOR)
        self._update_ui(self.download_button, disabled=True); self._update_ui(self.fetch_button, disabled=True)
        self.start_time = time.time(); self.last_downloaded_bytes, self.last_time, self.last_speed = 0, self.start_time, None; play_sound(download_start_sound)
        threading.Thread(target=self._execute_download_and_convert, args=(url,), daemon=True).start()

    def _execute_download_and_convert(self, url): # Unchanged
        if not self.content_data: self._finalize_download(success=False, message="Error: Content data missing."); return
        if not self.current_platform: self._finalize_download(success=False, message="Error: Platform not identified."); return
        is_pinterest_image_gif = self.current_platform == "pinterest" and not self.is_pinterest_video
        needs_conversion = not is_pinterest_image_gif
        try:
            title = self.content_data.get('title', 'downloaded_media'); title = self.sanitize_filename(title)
            output_template = os.path.join(self.download_path, f'{title}.%(ext)s')
            if is_pinterest_image_gif: format_selection = 'best'; merge_format = None
            elif self.download_format == 'mp3': format_selection = 'bestaudio/best'; merge_format = None
            else: quality_spec = f"[height<={self.download_quality[:-1]}]" if self.download_quality and 'p' in self.download_quality else ""; format_selection = f'bestvideo{quality_spec}+bestaudio/bestvideo{quality_spec}/best{quality_spec}/best'; merge_format = 'mkv'
            ydl_opts = {'format': format_selection, 'outtmpl': output_template, 'progress_hooks': [self.progress_callback], 'ffmpeg_location': self.ffmpeg_path, 'noplaylist': True, 'merge_output_format': merge_format, 'encoding': 'utf-8', 'logger': YtDlpLogger(), 'quiet': True, 'noprogress': True} # Use self.ffmpeg_path
            if self.current_platform == "facebook": cookie_path = resource_path("cookies/facebook_cookies.txt"); ydl_opts['cookiefile'] = cookie_path if os.path.exists(cookie_path) else None
            self._update_ui(self.status_text, value="Downloading...", color=INFO_COLOR); downloaded_file_path = None; info_dict = None
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info_dict = ydl.extract_info(url, download=True); downloaded_file_path = ydl.prepare_filename(info_dict)
                    if not downloaded_file_path or not os.path.exists(downloaded_file_path):
                         expected_ext = info_dict.get('ext', 'tmp'); expected_ext = merge_format if merge_format and expected_ext != merge_format else expected_ext
                         guessed_path = os.path.splitext(output_template % {'ext': 'dummy'})[0] + '.' + expected_ext
                         if os.path.exists(guessed_path): downloaded_file_path = guessed_path; print(f"Warning: prepare_filename unreliable, using guessed path: {downloaded_file_path}")
                         else: raise yt_dlp.utils.DownloadError(f"Download finished, but cannot locate output file. Info: {info_dict.get('filepath', 'N/A')}")
                except yt_dlp.utils.DownloadError as e: self._finalize_download(success=False, message=f"Download Error: {e}"); return
                except Exception as e: self._finalize_download(success=False, message=f"Error during download: {e}"); print(f"Detailed ydl error: {e}"); return
            if not downloaded_file_path or not os.path.exists(downloaded_file_path): self._finalize_download(success=False, message="Error: Output file not found after download."); return
            final_filepath = downloaded_file_path
            if needs_conversion:
                try:
                    if self.download_format == "mp3": final_filepath = self._convert_to_mp3(downloaded_file_path)
                    elif self.download_format == "mp4": final_filepath = self._convert_to_mp4(downloaded_file_path)
                except Exception as e: self._finalize_download(success=False, message=f"Conversion Error: {e}"); return
            if final_filepath and os.path.exists(final_filepath):
                total_time = time.time() - self.start_time; minutes, seconds = divmod(int(total_time), 60); final_filename = os.path.basename(final_filepath)
                msg = f"{'Download' if not needs_conversion else 'Download & Conversion'} complete!\nTime: {minutes}m {seconds}s"
                self._finalize_download(success=True, message=msg)
            else: self._finalize_download(success=False, message="Error: Final file not found after processing.")
        except Exception as e: self._finalize_download(success=False, message=f"An unexpected error occurred: {e}"); print(f"Detailed download/convert thread error: {type(e).__name__}: {e}")

    def _finalize_download(self, success=True, message=None): # Unchanged
        final_progress = 1.0 if success else (self.progress_bar.value if self.progress_bar.value is not None else 0); bar_color = SUCCESS_COLOR if success else ERROR_COLOR
        self._update_ui(self.progress_bar, value=final_progress, color=bar_color); self._update_ui(self.status_text, value=""); self._update_ui(self.time_label, value="")
        if success:
             final_message = message or "Operation successful!"; success_text_widget = Text(final_message, color=SUCCESS_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
             self._update_metadata_content(success_text_widget); play_sound(download_complete_sound); self.page.run_thread(self._reset_progress_after_delay, 2.5, PRIMARY_COLOR)
        else:
             error_message = message or "Operation failed!"; error_text_widget = Text(error_message, color=ERROR_COLOR, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)
             self._update_metadata_content(error_text_widget); play_sound(error_sound); self.page.run_thread(self._reset_progress_after_delay, 4.0, PRIMARY_COLOR)
        self._update_ui(self.download_button, disabled=False); self._update_ui(self.fetch_button, disabled=False)

    def _reset_progress_after_delay(self, delay_seconds, default_color): # Unchanged
        time.sleep(delay_seconds); self._update_ui(self.progress_bar, value=0, color=default_color)

    def progress_callback(self, d): # Unchanged
        if d['status'] == 'downloading':
            total_bytes, downloaded_bytes = d.get('total_bytes') or d.get('total_bytes_estimate'), d.get('downloaded_bytes', 0)
            if total_bytes and total_bytes > 0:
                progress = max(0.0, min(1.0, downloaded_bytes / total_bytes)); self._update_ui(self.progress_bar, value=progress, color=ACCENT_COLOR)
                current_time = time.time(); time_diff = current_time - (self.last_time or self.start_time)
                if time_diff >= 0.5:
                    bytes_diff = downloaded_bytes - self.last_downloaded_bytes; speed = max(0, bytes_diff / time_diff if time_diff > 0 else 0)
                    alpha = 0.3; speed = alpha * speed + (1 - alpha) * self.last_speed if self.last_speed is not None else speed
                    self.last_speed = speed; remaining_bytes = total_bytes - downloaded_bytes; eta = remaining_bytes / speed if speed > 1 else float('inf')
                    def format_size(b):
                        if b is None or b < 0: return "N/A";
                        if b == 0: return "0 B";
                        try: s=" BKBMBGBTB";i=min(len(s)//2-1,int(math.floor(math.log(max(1,b),1024))));p=math.pow(1024,i);r=round(b/p,1);return f"{r} {s[i*2:i*2+2]}"
                        except: return f"{b} B"
                    t, dn, sp = format_size(total_bytes), format_size(downloaded_bytes), f"{format_size(speed)}/s" if speed > 0 else "---/s"
                    et = "--:--" if eta==float('inf') or eta<0 or eta>86400 else f"{int(eta//60):02d}m{int(eta%60):02d}s"
                    self._update_ui(self.status_text, value=f"Downloading... {progress*100:.1f}%", color=INFO_COLOR); self._update_ui(self.time_label, value=f"{sp} • {dn} / {t} • ETA: {et}")
                    self.last_downloaded_bytes, self.last_time = downloaded_bytes, current_time
            else: downloaded_str = format_size(downloaded_bytes) if downloaded_bytes else "0 B"; self._update_ui(self.status_text, value=f"Downloading... ({downloaded_str})", color=INFO_COLOR); self._update_ui(self.progress_bar, value=None, color=ACCENT_COLOR); self._update_ui(self.time_label, value="Calculating size...")
        elif d['status'] == 'finished': self._update_ui(self.progress_bar, value=1.0, color=ACCENT_COLOR); self._update_ui(self.time_label, value="")
        elif d['status'] == 'error': self._update_ui(self.status_text, value="Download Error", color=ERROR_COLOR)

    # *** Conversion methods using robust regex parsing ***
    def _update_conversion_progress(self, progress, task_name="Converting"):
        progress = min(1.0, max(0.0, progress))
        self._update_ui(self.progress_bar, value=progress, color=WARNING_COLOR) # Use warning color
        self._update_ui(self.status_text, value=f"{task_name}: {progress*100:.1f}%", color=WARNING_COLOR)

    def _convert_to_mp3(self, downloaded_file):
        self._update_ui(self.status_text, value="Converting to MP3...", color=WARNING_COLOR); self._update_ui(self.time_label, value=""); self._update_ui(self.progress_bar, value=0)
        # Use the pre-determined correct path from __init__
        ffmpeg_cmd_path = self.ffmpeg_path
        ffprobe_cmd_path = self.ffprobe_path
        if not os.path.exists(ffmpeg_cmd_path): raise FileNotFoundError(f"ffmpeg not found at {ffmpeg_cmd_path}")
        if not os.path.exists(ffprobe_cmd_path): raise FileNotFoundError(f"ffprobe not found at {ffprobe_cmd_path}")

        base_name = os.path.splitext(downloaded_file)[0]; converted_file = os.path.abspath(base_name + ".mp3").replace('\\', '/')
        downloaded_file_abs = os.path.abspath(downloaded_file).replace('\\', '/')
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        duration = self._get_media_duration(downloaded_file_abs) or 1

        command = [ ffmpeg_cmd_path, "-y", "-i", downloaded_file_abs, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", "-progress", "pipe:1", converted_file ]
        process = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=creation_flags, encoding='utf-8', errors='replace' )
        last_update_time = time.time()
        while True:
            line = process.stdout.readline();
            if not line: break
            # print(f"FFMPEG_MP3_RAW: {line.strip()}") # Debugging
            time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line) or re.search(r"out_time_ms=(\d+)", line)
            current_seconds = None
            if time_match:
                try:
                     if "out_time_ms" in time_match.group(0): current_seconds = int(time_match.group(1)) / 1_000_000
                     else: h, m, s = map(float, time_match.group(1).split(':')); current_seconds = h * 3600 + m * 60 + s
                except Exception as e: print(f"Error parsing time format: {e}")
            if current_seconds is not None and duration > 0:
                now = time.time()
                if now - last_update_time > 0.2:
                    progress = current_seconds / duration
                    self._update_conversion_progress(progress, "Converting to MP3")
                    last_update_time = now
        process.wait()
        if process.returncode == 0 and os.path.exists(converted_file):
            print(f"MP3 Conversion successful: {converted_file}");
            try: os.remove(downloaded_file_abs); print(f"Removed original: {downloaded_file_abs}")
            except OSError as e: print(f"Warning: Could not remove original file {downloaded_file_abs}: {e}")
            return converted_file
        else:
            error_output = process.stdout.read(); print(f"FFmpeg MP3 conversion failed! Code: {process.returncode}\nOutput:\n{error_output}")
            raise RuntimeError(f"FFmpeg MP3 conversion failed (Code: {process.returncode}).")

    def _convert_to_mp4(self, downloaded_file):
        if not self.download_quality or self.download_quality == "N/A": raise ValueError("MP4 conversion requires a valid quality selection.")
        self._update_ui(self.status_text, value="Converting to MP4...", color=WARNING_COLOR); self._update_ui(self.time_label, value=""); self._update_ui(self.progress_bar, value=0)
        # Use the pre-determined correct path from __init__
        ffmpeg_cmd_path = self.ffmpeg_path
        ffprobe_cmd_path = self.ffprobe_path
        if not os.path.exists(ffmpeg_cmd_path): raise FileNotFoundError(f"ffmpeg not found at {ffmpeg_cmd_path}")
        if not os.path.exists(ffprobe_cmd_path): raise FileNotFoundError(f"ffprobe not found at {ffprobe_cmd_path}")

        base_name = os.path.splitext(downloaded_file)[0]; converted_file = os.path.abspath(base_name + f"_{self.download_quality}.mp4").replace('\\', '/')
        downloaded_file_abs = os.path.abspath(downloaded_file).replace('\\', '/')
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        duration = self._get_media_duration(downloaded_file_abs) or 1

        command = [ ffmpeg_cmd_path, "-y", "-i", downloaded_file_abs, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "192k", "-progress", "pipe:1", converted_file ]
        process = subprocess.Popen( command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=creation_flags, encoding='utf-8', errors='replace' )
        last_update_time = time.time()
        while True:
            line = process.stdout.readline();
            if not line: break
            # print(f"FFMPEG_MP4_RAW: {line.strip()}") # Debugging
            time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line) or re.search(r"out_time_ms=(\d+)", line)
            current_seconds = None
            if time_match:
                try:
                     if "out_time_ms" in time_match.group(0): current_seconds = int(time_match.group(1)) / 1_000_000
                     else: h, m, s = map(float, time_match.group(1).split(':')); current_seconds = h * 3600 + m * 60 + s
                except Exception as e: print(f"Error parsing time format: {e}")
            if current_seconds is not None and duration > 0:
                 now = time.time()
                 if now - last_update_time > 0.2:
                    progress = current_seconds / duration
                    self._update_conversion_progress(progress, "Converting to MP4")
                    last_update_time = now
        process.wait()
        if process.returncode == 0 and os.path.exists(converted_file):
            print(f"MP4 Conversion successful: {converted_file}")
            try: os.remove(downloaded_file_abs); print(f"Removed original: {downloaded_file_abs}")
            except OSError as e: print(f"Warning: Could not remove original file {downloaded_file_abs}: {e}")
            return converted_file
        else:
            error_output = process.stdout.read(); print(f"FFmpeg MP4 conversion failed! Code: {process.returncode}\nOutput:\n{error_output}")
            raise RuntimeError(f"FFmpeg MP4 conversion failed (Code: {process.returncode}).")

    def _get_media_duration(self, filepath): # Now uses self.ffprobe_path
        ffprobe_cmd_path = self.ffprobe_path # Use path determined at init
        try:
             if not os.path.exists(ffprobe_cmd_path): print(f"ffprobe not found at: {ffprobe_cmd_path}"); return None
             cmd = [ffprobe_cmd_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
             startupinfo, creationflags = None, 0
             if os.name == 'nt': startupinfo=subprocess.STARTUPINFO(); startupinfo.dwFlags|=subprocess.STARTF_USESHOWWINDOW; startupinfo.wShowWindow=subprocess.SW_HIDE; creationflags=subprocess.CREATE_NO_WINDOW
             res = subprocess.run(cmd, capture_output=True, text=True, check=True, startupinfo=startupinfo, creationflags=creationflags)
             duration = float(res.stdout.strip())
             # print(f"Duration for {filepath}: {duration}") # Debug duration
             return duration if duration > 0 else None # Return None if duration is zero or negative
        except Exception as e: print(f"Error getting duration: {e}"); return None

    def sanitize_filename(self, filename): # Unchanged
        sanitized = re.sub(r'[\\/*?:"<>|\x00-\x1f\x7f]', '', filename); sanitized = re.sub(r'\s+', '_', sanitized).strip('_'); sanitized = re.sub(r'__+', '_', sanitized)
        sanitized = re.sub(r'\.+', '.', sanitized); return sanitized[:100] if sanitized and sanitized.strip('.') != '' else "downloaded_file"

# --- Flet UI Main Function (Unchanged from V6) ---
def main(page: Page):
    page.title = "YouTube Downloader"
    page.window.width = 800
    page.window.height = 840
    page.window.min_width = 700
    page.window.min_height = 750
    page.window.resizable = True
    page.window.maximizable = True
    page.window.icon = resource_path("images/icon.ico")
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = MainAxisAlignment.START
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = BG_COLOR
    page.padding = padding.symmetric(horizontal=25, vertical=25)
    page.fonts = { "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" }
    page.theme = Theme(font_family="Roboto")

    app_logic = DownloaderAppLogic(page)

    file_picker = FilePicker(on_result=app_logic.on_path_selected)
    page.overlay.append(file_picker)

    url_entry = TextField(
        hint_text="Paste URL (YouTube, Facebook, Pinterest)...", expand=True, height=CONTROL_HEIGHT,
        bgcolor=INPUT_BG_COLOR, border_radius=BORDER_RAD, border_color=ft_colors.TRANSPARENT,
        focused_border_color=ACCENT_COLOR, focused_border_width=2, prefix_icon=ft.icons.LINK_ROUNDED,
        content_padding=padding.symmetric(horizontal=18), text_size=14, tooltip="Enter the media link here"
    )
    fetch_button = FilledButton(
        text="Fetch", icon=ft.icons.MANAGE_SEARCH_ROUNDED,
        height=CONTROL_HEIGHT, width=120, on_click=app_logic.fetch_content_info,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BORDER_RAD), bgcolor=PRIMARY_COLOR, color=ft_colors.WHITE),
        tooltip="Fetch media information"
    )
    input_row = Row([url_entry, fetch_button], alignment=MainAxisAlignment.SPACE_BETWEEN, spacing=15, vertical_alignment=CrossAxisAlignment.CENTER)

    thumbnail_image = Image(
        src_base64=app_logic.placeholder_base64, width=THUMBNAIL_WIDTH, height=THUMBNAIL_HEIGHT,
        fit=ft.ImageFit.CONTAIN, border_radius=border_radius.all(BORDER_RAD - 2), tooltip="Preview"
    )
    thumbnail_container = Container(
        content=thumbnail_image, alignment=alignment.center, padding=padding.all(5),
        border_radius=border_radius.all(BORDER_RAD), bgcolor=CARD_BG_COLOR,
        border=border.all(1, ft_colors.with_opacity(0.1, ft_colors.WHITE)),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft_colors.with_opacity(0.15, ft_colors.BLACK), offset=ft.Offset(2, 2)),
        width=THUMBNAIL_WIDTH + 10, height=THUMBNAIL_HEIGHT + 10
    )

    metadata_placeholder = Text("Enter a URL and click 'Fetch' to see details.", color=TEXT_COLOR_MUTED, size=13, text_align=ft.TextAlign.CENTER)
    metadata_card = Container(
        content=metadata_placeholder, padding=padding.all(18), border_radius=border_radius.all(BORDER_RAD),
        bgcolor=CARD_BG_COLOR, border=border.all(1, ft_colors.with_opacity(0.1, ft_colors.WHITE)),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft_colors.with_opacity(0.15, ft_colors.BLACK), offset=ft.Offset(2, 2)),
        animate=animation.Animation(300, "easeOut"), clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        expand=True, alignment=alignment.top_left, height=THUMBNAIL_HEIGHT + 10
    )

    preview_info_row = Row(
        [
            thumbnail_container,
            Container(metadata_card, padding=padding.only(left=20), expand=True),
        ],
        vertical_alignment=CrossAxisAlignment.START, spacing=0,
    )

    status_text = Text("", size=14, weight=ft.FontWeight.W_500, animate_opacity=300, color=INFO_COLOR)
    progress_bar = ProgressBar(
        expand=True, value=0, bar_height=10, color=PRIMARY_COLOR,
        bgcolor=ft_colors.with_opacity(0.1, ft_colors.WHITE), border_radius=5, animate_size=300
    )
    time_label = Text("", size=12, color=TEXT_COLOR_MUTED, animate_opacity=300, no_wrap=True)
    progress_row = Row(
        [status_text, Container(progress_bar, expand=True, padding=padding.symmetric(horizontal=15)), time_label],
        spacing=10, vertical_alignment=CrossAxisAlignment.CENTER, alignment=MainAxisAlignment.SPACE_BETWEEN, height=40,
    )
    progress_container = Container(content=progress_row, margin=margin.only(top=20))

    quality_dropdown = Dropdown(
        hint_text="Quality", options=[ft.dropdown.Option("N/A")], value="N/A", disabled=True, expand=True, height=CONTROL_HEIGHT,
        border_radius=BORDER_RAD, bgcolor=INPUT_BG_COLOR, border_color=ft_colors.TRANSPARENT,
        focused_border_color=ACCENT_COLOR, focused_border_width=2, content_padding=padding.only(left=15, right=5),
        on_change=app_logic.set_quality, tooltip="Video resolution", prefix_icon=ft.icons.HIGH_QUALITY_OUTLINED
    )
    format_dropdown = Dropdown(
        hint_text="Format", options=[ft.dropdown.Option("N/A")], value="N/A", disabled=True, expand=True, height=CONTROL_HEIGHT,
        border_radius=BORDER_RAD, bgcolor=INPUT_BG_COLOR, border_color=ft_colors.TRANSPARENT,
        focused_border_color=ACCENT_COLOR, focused_border_width=2, content_padding=padding.only(left=15, right=5),
        on_change=app_logic.set_format, tooltip="Download format", prefix_icon=ft.icons.TRANSFORM_ROUNDED
    )
    options_row1 = ResponsiveRow(
        [
            Container(quality_dropdown, col={"sm": 12, "md": 6}, padding=padding.only(right=10, bottom=10)),
            Container(format_dropdown, col={"sm": 12, "md": 6}, padding=padding.only(left=10, bottom=10)),
        ],
        spacing=0,
    )

    path_button = OutlinedButton(
        "Choose Folder", icon=ft.icons.FOLDER_OPEN_ROUNDED, on_click=app_logic.choose_path, height=CONTROL_HEIGHT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=BORDER_RAD), side=ft.BorderSide(1, ft_colors.with_opacity(0.3, ft_colors.WHITE)), color=TEXT_COLOR_SECONDARY),
        tooltip="Select save location"
    )
    path_display_text = Text("...", color=TEXT_COLOR_MUTED, size=12, no_wrap=True, expand=True, tooltip="Current download folder", text_align=ft.TextAlign.LEFT)
    options_row2 = Row(
        [
            Row([ft.Icon(ft.icons.FOLDER_SHARED_OUTLINED, size=22, opacity=0.8, color=TEXT_COLOR_SECONDARY), path_button], spacing=10),
            Container(path_display_text, padding=padding.only(left=15), alignment=alignment.center_left, expand=True),
        ],
        spacing=15, vertical_alignment=CrossAxisAlignment.CENTER, alignment=MainAxisAlignment.START,
    )

    options_card = Container(
         Column([options_row1, Divider(height=1, color=ft_colors.with_opacity(0.1, ft_colors.WHITE)), options_row2], spacing=18),
         padding=padding.symmetric(horizontal=25, vertical=20), border_radius=border_radius.all(BORDER_RAD), bgcolor=CARD_BG_COLOR,
         margin=margin.only(top=20), border=border.all(1, ft_colors.with_opacity(0.1, ft_colors.WHITE)),
         shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft_colors.with_opacity(0.15, ft_colors.BLACK), offset=ft.Offset(2, 2)),
    )

    download_button = FilledButton(
        "Download", icon=ft.icons.FILE_DOWNLOAD_OUTLINED,
        height=CONTROL_HEIGHT + 4, width=220, disabled=True, on_click=app_logic.start_download,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BORDER_RAD),
            bgcolor={ft.MaterialState.DEFAULT: ACCENT_COLOR, ft.MaterialState.DISABLED: ft_colors.with_opacity(0.5, CARD_BG_COLOR)},
            color=ft_colors.BLACK if ACCENT_COLOR in [ft_colors.CYAN_ACCENT_700, ft_colors.GREEN_ACCENT_400, ft_colors.AMBER_ACCENT_400, ft_colors.LIME_ACCENT_700, ft_colors.YELLOW_ACCENT_700] else ft_colors.WHITE,
            padding=padding.symmetric(vertical=10)
        ),
        tooltip="Start download"
    )
    download_button_container = Container(download_button, margin=margin.only(top=25), alignment=alignment.center)

    footer_label = TextButton(
        content=Row([Text("𓆩",size=12,color=TEXT_COLOR_MUTED,weight=ft.FontWeight.BOLD), ft.Icon(ft.icons.CODE_ROUNDED, color=ft_colors.PINK_ACCENT_100, size=14), Text(" Crafted by Rudra ", size=12, color=TEXT_COLOR_MUTED, weight=ft.FontWeight.W_500, font_family="Roboto"), ft.Icon(ft.icons.FAVORITE_ROUNDED, color=ft_colors.PINK_ACCENT_100, size=14), Text("𓆪", size=12, color=TEXT_COLOR_MUTED, weight=ft.FontWeight.BOLD)], alignment=MainAxisAlignment.CENTER, spacing=3),
        url="https://github.com/rudra-mondal", tooltip="Visit Rudra's GitHub", style=ft.ButtonStyle(overlay_color=ft_colors.with_opacity(0.05, ft_colors.WHITE)),
    )
    footer_container = Container(footer_label, margin=margin.only(top=25, bottom=5), alignment=alignment.center)

    # --- Build Main Layout ---
    main_column = Column(
        [
            Row([ft.Icon(ft.icons.ONDEMAND_VIDEO, size=32, color=ACCENT_COLOR),
                 Text("YouTube Downloader", size=28, weight=ft.FontWeight.BOLD, color=TEXT_COLOR_PRIMARY)],
                alignment=MainAxisAlignment.CENTER, spacing=10),
            Container(content=Text("Download from YouTube, Facebook & Pinterest", size=14, color=TEXT_COLOR_SECONDARY, text_align=ft.TextAlign.CENTER), margin=margin.only(bottom=25)),
            input_row,
            Container(preview_info_row, margin=margin.only(top=25)),
            progress_container,
            options_card,
            download_button_container,
            footer_container,
        ],
        spacing=0, scroll=ScrollMode.ADAPTIVE, horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    page_layout = Container(
        content=main_column, alignment=alignment.top_center, padding=padding.only(bottom=10),
        expand=True
    )

    page.add(page_layout)

    # --- Pass Controls ---
    app_logic.set_ui_controls({
        "url_entry": url_entry, "fetch_button": fetch_button, "thumbnail_image": thumbnail_image,
        "metadata_container": metadata_card, "metadata_text": metadata_placeholder, "status_text": status_text,
        "progress_bar": progress_bar, "time_label": time_label, "quality_dropdown": quality_dropdown,
        "format_dropdown": format_dropdown, "path_display_text": path_display_text,
        "download_button": download_button, "file_picker": file_picker
    })

# --- Run ---
if __name__ == "__main__":
    # Ensure required directories exist
    for folder in ["bin", "audio", "images", "cookies"]:
        os.makedirs(resource_path(folder), exist_ok=True)

    # Check for FFmpeg/FFprobe using the correct logic from the AppLogic class
    ffmpeg_exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
    ffprobe_exe = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'
    ffmpeg_path_check = resource_path(os.path.join("bin", ffmpeg_exe))
    ffprobe_path_check = resource_path(os.path.join("bin", ffprobe_exe))

    if not os.path.exists(ffmpeg_path_check): print(f"WARNING: {ffmpeg_exe} not found in bin directory ({ffmpeg_path_check}). Conversions may fail.")
    if not os.path.exists(ffprobe_path_check): print(f"WARNING: {ffprobe_exe} not found in bin directory ({ffprobe_path_check}).")

    # Run the Flet app
    ft.app(target=main)
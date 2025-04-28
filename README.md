<p align="center">
  <img src="https://github.com/user-attachments/assets/9fe6761a-63d3-4517-9572-9aa284f67a0a" alt="Logo" width="500"> 
</p>

# 🚀 YouTube Downloader 🚀

This Python application allows you to easily download videos from YouTube and Facebook. It provides a user-friendly graphical interface built with Flet and uses `yt-dlp` for downloading and `ffmpeg` for format conversion.

<h3 align="center"><i>👇 Here is a quick look 👇</i></h3>

<p align="center">
  <img src="https://github.com/user-attachments/assets/c97b09bc-2f20-4001-b640-76eb73a596b0" alt="App Interface" width="550"> 
</p>

## ✨ Features

- **Support for YouTube and Facebook:** Download videos from both platforms.
- **GUI Interface:** Easy-to-use graphical interface for a seamless experience.
- **Quality Selection:** Choose the desired video quality (e.g., 720p, 1080p etc).
- **Format Options:** Download as video (MP4) or audio (MP3).
- **Custom Download Path:** Select your preferred download location.
- **Progress Tracking:** Monitor download and conversion progress with a progress bar, speed indicator, and estimated time remaining.
- **Automatic Conversion:** Downloaded videos are automatically converted to MP4 (H.264) or MP3 format.
- **Error Handling:** Robust error handling to manage issues during download or conversion.
## 💖 Supporting the Project ❤️

This project has been a *labor of love*, poured over countless hours to bring it to life and share it freely with the world. I'm giving this creation to you, like a tree offering its shade and fruit to all who seek shelter or sustenance. 🌳

However, like a tree needing sun and water to thrive, I too rely on a bit of support to continue nurturing this project (and myself!).  If you find this application valuable and wish to contribute to its ongoing growth and maintenance—or simply buy a grateful developer a cup of coffee—any donation, big or small, would be deeply appreciated. Your generosity helps keep the leaves green and the code compiling! ⚙️


Even if you can't contribute financially, spreading the word about this project is a wonderful way to help it flourish.  Share it with friends, colleagues, or anyone who might find it useful!  Thank you for your kindness and support. It means the world to me! 😌

## 💾 Installation

This application offers two installation methods: a simple installer for end-users and a manual installation for developers or users who prefer that approach.

**Method 1: Installer (Recommended) ✨**
- Download the latest installer for your operating system from the [Releases](https://github.com/rudra-mondal/youtube-downloader/releases) page.
- Run the downloaded installer file and follow the on-screen instructions.  This will install the application and all required dependencies, including FFmpeg.
- After installation, you can find the application in your start menu.


**Method 2: Manual Installation (for Developers/Advanced Users) 🛠️**

This project requires Python 3.7 or higher.  We strongly recommend using a virtual environment to manage dependencies.

**1. Clone the Repository:**

```bash
git clone https://github.com/rudra-mondal/youtube-downloader.git
```

**2. Navigate to the Project Directory:**

```bash
cd youtube-downloader
```

**3. Create and Activate a Virtual Environment (Optional-Recommended):**

- Create the virtual environment:

```bash
python3 -m venv .venv
```
- Activate the virtual environment:

  - For Linux/macOS:

    ```bash
    source .venv/bin/activate
    ```
  - For Windows:
    ```bash
    .venv\Scripts\activate
    ```

**4. Install Dependencies:**

A `requirements.txt` file is provided for easy installation of the necessary Python packages.

```bash
pip install -r requirements.txt
```

**5. FFmpeg Installation:**

FFmpeg is **already included** in the `bin` folder of this repository, so you don't need to download or install it separately. The application is configured to use the FFmpeg executables from this folder.
## ⌨️ Usage/Examples


1. **Run the Application:** Doubble-Click on the installed file *or:*
   ```bash
   python main.py 
   ```

2. **Paste Video URL:** Enter the YouTube or Facebook video URL in the input field.

![Image](https://github.com/user-attachments/assets/03b0679c-f591-4bc7-b65a-cb590fe7ccb5)

3. **Fetch Video Info:** Click the "Fetch" button to retrieve video details.

![Image](https://github.com/user-attachments/assets/5dc447bb-e01a-4114-b02a-b2c11cfc4692)

The thumbnail, title, uploader, and duration will appear:

![Image](https://github.com/user-attachments/assets/d543e380-e01c-40d0-b426-ab39ac26e9cf)

4. **Choose Quality and Format:** Select your desired video quality and format (video or audio).

![Image](https://github.com/user-attachments/assets/a4545dcb-cea2-447d-ba87-4726f5307153)

5. **Choose Download Path (Optional):** Click "Choose Download Folder" to change the download location. The default is your Downloads folder.

![Image](https://github.com/user-attachments/assets/3212f71b-bda0-44dd-a231-044a7dc12613)

6. **Download:** Click the "Download" button to start the download and conversion process.

![Image](https://github.com/user-attachments/assets/8eea58a6-c74f-44ec-94d2-a9a3825b71f2)
## ⚠️ Troubleshooting

This section provides solutions to common problems you might encounter.  If you're stuck, check here first!

**1. 📦 `ModuleNotFoundError`:**

* **Problem:** You see an error like `ModuleNotFoundError: No module named 'flet'` (or another module).
* **Solution:** This means some Python packages are missing. 
    1. Activate your virtual environment *(if you're using one)*.
    2. Run `pip install -r requirements.txt` in your project directory.


**2. ⚙️ FFmpeg Errors:**

* **Problem:** Errors related to FFmpeg, such as "ffmpeg not found" or conversion failures.
* **Solution:** FFmpeg is bundled with the app! If using the installer, it's already set up. For manual installs:
    1. **Check `bin` folder:** Make sure `ffmpeg.exe`, `ffplay.exe`, and `ffprobe.exe` (on Windows) are inside the `bin` folder.
    2. **PyInstaller:** If you made an executable, did you include the `bin` folder with `--add-data`?  See the Installation section.

**3. 💥 Application Crashes During Conversion:**

* **Problem:** The app crashes or freezes when converting.
* **Solution:** This could be due to low system resources or a huge video file. Try shorter/smaller videos. Still crashing? Report it on GitHub with details!

**4. ⬇️ Download Errors:**

* **Problem:** Problems downloading videos (network issues, bad URLs, etc.).
* **Solution:**
    1. **Check Internet:**  Is your internet working? 🤔
    2. **Double-Check URL:** Is the YouTube/Facebook link correct?
    3. **`yt-dlp` Gremlins:**  Updates to `yt-dlp` can sometimes cause trouble. Check for updates or try an older version.

**5. 🛠️ Installer Issues:**
* **Problem:** Problems creating the installer file with `pyinstaller`.
* **Solution:** Make sure you've included the `images`, `bin`, `audio` and `cookies` folders with your executable. Use this command:  `pyinstaller --name YouTubeDownloader --onedir --windowed --icon=images/icon.ico main.py`. After that you will find a `YouTubeDownloader` named folder into the `dist` folder where you have to manually copy all the assets folders to make the exe workable. 

**6.  📁 `sys._MEIPASS2` Issues (for Packaged Executables):**

* **Problem:** Errors about `sys._MEIPASS2` when running the packaged app.
* **Solution:** Change the `resource_path` function in your code.  If `base_path = sys._MEIPASS2` fails, use `base_path = sys._MEIPASS`:

   ```python
   def resource_path(relative_path):
       """Get absolute path to resource, works for dev and PyInstaller"""
       try:
           base_path = sys._MEIPASS  # Try this!
       except Exception:
           base_path = os.path.abspath(".")
       return os.path.join(base_path, relative_path)
   ```

**7. 🤔 Other Issues?**

* **GitHub is your friend:** Create a detailed issue on GitHub. Include the error, steps to reproduce, your OS, Python version, and anything else helpful!
## ⚠️ Limitations

While this application strives to provide a smooth and efficient download experience, there are a few limitations to be aware of:

* **Conversion Speed:** Video conversion, especially for lengthy videos or on less powerful computers, can take a significant amount of time. The conversion process relies on FFmpeg, and the speed depends on factors like CPU performance, video resolution, and file size. Please be patient during conversion.

* **Network Connectivity:** Download speeds are ultimately limited by your internet connection. Slow or unstable internet connections can result in longer download times or interruptions.

* **Platform-Specific Issues:** Although the application is designed to be cross-platform, unforeseen issues might arise due to differences in operating systems or dependencies. Please report any platform-specific problems you encounter on the GitHub repository.

* **No Support for All Websites:** The application currently supports YouTube and Facebook.  Downloading from other video-sharing platforms is not yet implemented.

* **Third-Party Library Dependence:** This application relies on `yt-dlp` and FFmpeg.  Changes or updates to these libraries could potentially affect functionality.

* **No Live Streaming Download:**  The application does not support downloading live streams.  


I am continuously working to improve the application and address these limitations.  Your feedback and contributions are welcome!
## ❓ FAQ

**Q: Why is FFmpeg conversion needed? Why can't the app download videos directly in the desired format?**

A:  Many online video downloaders perform the conversion process on their servers before sending the file to you.  Since this application runs locally on your computer, it downloads the video stream and audio stream separately and then uses FFmpeg to combine and convert them into the format you've chosen (MP4 or MP3). This gives you more control over the final output quality and allows the app to function independently without relying on external servers.

**Q: Why is the conversion process sometimes slow?**

A:  Video conversion, especially for high-resolution or long videos, can be computationally intensive. The speed depends on your computer's processing power (primarily CPU) and the complexity of the conversion.  Be patient during the conversion process, especially for larger files.

**Q: Where can I find the downloaded files?**

A:  Downloaded files are saved to the default Downloads folder on your computer by default. You can also change the download directory in the application's settings.

**Q: The application crashed/I encountered an error. What should I do?**

A: Please create an issue on the GitHub repository, providing as much detail as possible, including:
- The error message (if any).
- The video URL you were trying to download.
- Your operating system and Python version.
- The steps you took before encountering the error.
- Any relevant screenshots.

#### **Q: How can I contribute to the project?**

A: Contributions are welcome!  You can contribute by:
- Reporting bugs or suggesting new features.
- Improving the code or documentation.
- Translating the application into different languages.
- Spreading the word about the project.  See the Contributing section of the README for more details.


**Q: Can I use this application to download copyrighted videos?**

A:  Downloading copyrighted material without permission is illegal in most jurisdictions. This application is provided for educational and personal use only. Please respect copyright laws and the terms of service of video-sharing platforms.  The developer is not responsible for any misuse of this application.


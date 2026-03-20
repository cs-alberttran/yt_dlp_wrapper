# YT-DLP Wrapper

A desktop GUI for yt-dlp that lets you download videos and audio from YouTube
and other supported sites without touching the command line after setup.

---

## Author

**Albert "ssjalby / alby2k" Tran**

Contact: tranalbert50@gmail.com

---

## Features

- Download video (MP4, MKV, WebM, and more) or audio (MP3, FLAC, WAV, and more)
- Quality and format selection
- Automatic filename from video title 
- Thumbnail preview that updates per video during playlist downloads
- Subtitle download and embedding
- Metadata and thumbnail embedding
- Playlist range control
- light / dark theme toggle with persistent preference

---

## Requirements

- Windows 10 or 11 (64-bit)
- Internet connection

You do NOT need an IDE or any coding knowledge. Everything is installed through
the steps below.

---

## Setup and Run (first time)

Follow each step in order. Open Command Prompt (press Windows + R, type `cmd`,
press Enter) and paste the commands one at a time.

### Step 1 - Install Python

Download and install Python 3.11 or later from:

    https://www.python.org/downloads/

During installation, check the box that says "Add Python to PATH" before
clicking Install.

Verify the installation worked:

    python --version

You should see a version number printed. If you get an error, restart Command
Prompt and try again.

### Step 2 - Install FFmpeg

FFmpeg handles audio/video merging. Download a Windows build from:

    https://www.gyan.dev/ffmpeg/builds/

Add the bin folder to your PATH manually:
1. Open Start, search "Environment Variables"
2. Under System Variables, select Path and click Edit
3. Click New and paste the full path to the bin folder
4. Click OK on all dialogs, then restart Command Prompt

Verify:

    ffmpeg -version

### Step 3 - Download the app

Download or clone this repository so that all files sit in one folder, for
example C:\Users\\"yourname"\yt_dlp_wrapper

Then open Command Prompt and navigate to that folder:

    cd C:\yt_dlp_wrapper

### Step 4 - Install Python dependencies

    pip install -r requirements.txt

This installs yt-dlp, the GUI library, and image handling support.

### Step 5 - Run the app

    python main.py

The window will open. Paste a URL, choose your options, and click Download.

---

## Running the app after the first time

Open Command Prompt, navigate to the app folder, and run:

    python main.py

---

## Known Issues

- Thumbnail preview requires Pillow to be installed (included in
  requirements.txt). If Pillow is missing the thumbnail area will stay blank
  but downloads will still work normally.

- Some sites block thumbnail fetches, in which case the preview will show
  "No preview" even though the download completes successfully.

- The "Lossless" audio quality option depends on the source site offering a
  lossless stream. Most YouTube videos do not, so the result will still be a
  high-quality lossy track in that case.

- Playlist downloads show overall progress rather than a per-video progress
  bar. The thumbnail updates per video to indicate which item is currently
  downloading.

- If FFmpeg is not installed or not on PATH, video downloads that require
  merging audio and video tracks will fail. The error will appear in the
  Status section.

---

## Updating yt-dlp

Sites change frequently and yt-dlp releases updates to keep up. If downloads
start failing, update yt-dlp from Command Prompt inside the app folder:

    pip install --upgrade yt-dlp

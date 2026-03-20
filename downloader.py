import os
import re
import threading

import yt_dlp


def sanitize_custom_name(text):
    """Strip emojis, control chars and filesystem-unsafe chars from a plain filename."""
    # Control characters
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    # Windows / cross-platform forbidden chars
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # Emojis and symbols: supplementary planes + BMP symbol blocks
    text = re.sub(
        r'[\U0001F000-\U0010FFFF\u2600-\u27BF\uFE00-\uFE0F\u200D\u20E3]',
        '', text,
    )
    text = re.sub(r'\s+', ' ', text).strip()
    return text or 'download'


def is_valid_url(url):
    pattern = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(pattern, url) is not None


def _build_ydl_options(settings, status_callback, thumbnail_callback=None):
    output_dir = settings["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    template = settings.get("output_template", "").strip()
    if not template:
        effective_template = "%(title)s.%(ext)s"
    elif '%(' in template:
        effective_template = template
    else:
        effective_template = sanitize_custom_name(template) + ".%(ext)s"

    # Closure: tracks the current video ID so we fire thumbnail_callback
    # exactly once per new video (not on every progress tick).
    _current_id = [None]

    def _hook(d):
        if d['status'] == 'downloading':
            info = d.get('info_dict') or {}
            vid_id = info.get('id') or d.get('filename', '')
            if vid_id and vid_id != _current_id[0]:
                _current_id[0] = vid_id
                if thumbnail_callback:
                    thumb = info.get('thumbnail')
                    if thumb:
                        thumbnail_callback(thumb)

            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            speed = d.get('speed', 0)

            if total:
                percent = downloaded / total
                msg = f"Downloading: {percent:.1%} - {downloaded / (1024 * 1024):.1f}/{total / (1024 * 1024):.1f} MB"
            else:
                percent = 0
                msg = f"Downloading: {downloaded / (1024 * 1024):.1f} MB"

            if speed:
                msg += f" @ {speed / (1024 * 1024):.1f} MB/s"

            status_callback(msg, progress_val=percent)

        elif d['status'] == 'finished':
            status_callback("Processing...", progress_val=1.0)

    ydl_opts = {
        'progress_hooks': [_hook],
        'outtmpl': os.path.join(output_dir, effective_template),
        'quiet': True,
        'no_warnings': False,
        'restrictfilenames': True,
    }

    mode = settings["mode"]
    quality = settings["quality"]
    fmt = settings["format"]

    resolution = None
    if "p" in quality and quality != "Best":
        resolution = ''.join(filter(str.isdigit, quality))

    if mode == "audio":
        postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': fmt}]
        if quality != "Best":
            postprocessors[0]['preferredquality'] = quality.replace("kbps", "")
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': postprocessors,
        })
    else:
        if fmt == "mp4":
            if resolution:
                format_str = (
                    f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]"
                    f"/bestvideo[height<={resolution}]+bestaudio/best"
                )
            else:
                format_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        else:
            if resolution:
                format_str = f"bestvideo[height<={resolution}]+bestaudio/best"
            else:
                format_str = "bestvideo+bestaudio/best"
        ydl_opts.update({
            'format': format_str,
            'merge_output_format': fmt,
        })

    if settings.get("subtitles"):
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        ydl_opts['subtitleslangs'] = [settings.get("subtitle_lang", "en")]

    if settings.get("embed_thumbnail"):
        ydl_opts['embedthumbnail'] = True

    if settings.get("embed_metadata"):
        ydl_opts['addmetadata'] = True

    if settings.get("no_playlist"):
        ydl_opts['noplaylist'] = True

    if settings.get("playlist_start"):
        try:
            ydl_opts['playliststart'] = int(settings["playlist_start"])
        except ValueError:
            pass

    if settings.get("playlist_end"):
        try:
            ydl_opts['playlistend'] = int(settings["playlist_end"])
        except ValueError:
            pass

    return ydl_opts


def _download(url, settings, status_callback, done_callback, thumbnail_callback=None):
    try:
        ydl_opts = _build_ydl_options(settings, status_callback, thumbnail_callback)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info_dict)

            if settings["mode"] == "audio":
                final_filename = os.path.splitext(final_filename)[0] + '.' + settings["format"]

            entries = info_dict.get('entries') if info_dict else None
            if entries:
                first = next((e for e in entries if e), None)
                thumb_url = first.get('thumbnail') if first else None
            else:
                thumb_url = info_dict.get('thumbnail') if info_dict else None

        done_callback(True, "Download completed! Ready for next download.", final_filename, thumb_url)

    except yt_dlp.utils.DownloadError as e:
        done_callback(False, f"Error: {str(e)}", None, None)
    except Exception as e:
        done_callback(False, f"Unexpected error: {str(e)}", None, None)


def download_async(url, settings, status_callback, done_callback, thumbnail_callback=None):
    thread = threading.Thread(
        target=_download,
        args=(url, settings, status_callback, done_callback, thumbnail_callback),
        daemon=True,
    )
    thread.start()

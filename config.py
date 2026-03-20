import os

TITLE = "YT-DLP Wrapper"
WIDTH = 1024
HEIGHT = 768

VIDEO_QUALITIES = [
    "Best", "144p", "240p", "360p", "480p",
    "720p HD", "1080p FHD", "1440p QHD", "2160p 4K", "4320p 8K",
]
AUDIO_QUALITIES = [
    "Best", "64kbps", "96kbps", "128kbps",
    "192kbps", "256kbps", "320kbps", "Lossless",
]
VIDEO_FORMATS = ["mp4", "mkv", "webm", "flv", "avi", "mov"]
AUDIO_FORMATS = ["mp3", "wav", "flac", "m4a", "ogg", "opus", "aac"]
SUBTITLE_LANGUAGES = ["en", "es", "fr", "de", "pt", "it", "ru", "ja", "zh", "auto"]

DEFAULT_OUTPUT = os.path.expanduser("~/Downloads")
DEFAULT_TEMPLATE = "%(title)s.%(ext)s"

# -- 90s Windows color palette (light) --
LIGHT_COLORS = {
    "bg": "#c0c0c0",
    "frame": "#d4d0c8",
    "accent": "#008080",
    "accent_hover": "#006060",
    "navy": "#000080",
    "white": "#ffffff",
    "black": "#000000",
    "progress": "#008080",
    "button": "#d4d0c8",
    "button_hover": "#b0b0b0",
    "entry": "#ffffff",
    "border": "#808080",
}

# -- Dark variant --
DARK_COLORS = {
    "bg": "#1e1e1e",
    "frame": "#2b2b2b",
    "accent": "#00b4b4",
    "accent_hover": "#008888",
    "navy": "#3a7bd5",
    "white": "#e0e0e0",
    "black": "#e0e0e0",
    "progress": "#00b4b4",
    "button": "#3c3c3c",
    "button_hover": "#505050",
    "entry": "#1a1a1a",
    "border": "#555555",
}

# Mutable active theme — mutated in-place on toggle
COLORS = dict(DARK_COLORS)

FONT = "Tahoma"
FONT_MONO = "Courier New"

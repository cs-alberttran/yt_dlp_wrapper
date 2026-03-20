import io
import json
import os
import threading
import urllib.request

import customtkinter as ctk
from tkinter import filedialog

try:
    from PIL import Image as _PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

PREFS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prefs.json")

from config import (
    TITLE, WIDTH, HEIGHT, COLORS, LIGHT_COLORS, DARK_COLORS, FONT, FONT_MONO,
    VIDEO_QUALITIES, AUDIO_QUALITIES,
    VIDEO_FORMATS, AUDIO_FORMATS,
    SUBTITLE_LANGUAGES,
    DEFAULT_OUTPUT, DEFAULT_TEMPLATE,
)
from downloader import is_valid_url, download_async


class App:
    def __init__(self, root):
        self.root = root
        self._dark = self._load_prefs()
        _colors = DARK_COLORS if self._dark else LIGHT_COLORS
        COLORS.clear()
        COLORS.update(_colors)
        ctk.set_appearance_mode("dark" if self._dark else "light")
        self._setup_window()
        self._create_variables()
        self._build_ui()

    def _setup_window(self):
        self.root.title(TITLE)
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.minsize(WIDTH, HEIGHT)
        self.root.configure(fg_color=COLORS["bg"])
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

    def _create_variables(self):
        self._thumb_ctk_img = None
        self.url_var = ctk.StringVar()
        self.mode_var = ctk.StringVar(value="video")
        self.quality_var = ctk.StringVar(value="Best")
        self.format_var = ctk.StringVar(value="mp4")
        self.download_subs_var = ctk.BooleanVar(value=False)
        self.subtitle_lang_var = ctk.StringVar(value="en")
        self.embed_thumbnail_var = ctk.BooleanVar(value=False)
        self.embed_metadata_var = ctk.BooleanVar(value=False)
        self.no_playlist_var = ctk.BooleanVar(value=False)
        self.playlist_start_var = ctk.StringVar()
        self.playlist_end_var = ctk.StringVar()
        self.output_path_var = ctk.StringVar(value=DEFAULT_OUTPUT)
        self.output_template_var = ctk.StringVar(value=DEFAULT_TEMPLATE)

    # -- Layout helpers --

    def _section(self, parent, label, row):
        frame = ctk.CTkFrame(
            parent, corner_radius=0, fg_color=COLORS["frame"],
            border_width=1, border_color=COLORS["border"],
        )
        frame.grid(row=row, column=0, sticky="ew", padx=8, pady=(6, 2))
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text=f" {label} ", font=(FONT, 13, "bold"),
            text_color=COLORS["navy"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(4, 2))

        content = ctk.CTkFrame(frame, corner_radius=0, fg_color="transparent")
        content.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        content.grid_columnconfigure(0, weight=1)
        return content

    # -- Build sections --

    def _build_ui(self):
        main = ctk.CTkFrame(
            self.root, corner_radius=0, fg_color=COLORS["frame"],
            border_width=2, border_color=COLORS["border"],
        )
        main.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        self._main = main

        # Title banner
        banner = ctk.CTkFrame(main, corner_radius=0, fg_color=COLORS["navy"], height=38)
        banner.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))
        banner.grid_propagate(False)
        self._toggle_btn = ctk.CTkButton(
            banner, text="☀️" if self._dark else "🌙", width=34, height=30, corner_radius=0,
            font=("Segoe UI Emoji", 15), fg_color=COLORS["navy"],
            hover_color=COLORS["accent_hover"], text_color=COLORS["white"],
            border_width=0, command=self._toggle_theme,
        )
        self._toggle_btn.pack(side="right", padx=4, pady=4)
        ctk.CTkLabel(
            banner, text=f"  {TITLE}", font=(FONT, 15, "bold"),
            text_color=COLORS["white"], anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=4, pady=4)

        self._build_url(main, 1)
        self._build_options(main, 2)
        self._build_advanced(main, 3)
        self._build_output(main, 4)
        self._build_status(main, 5)
        self._build_download_btn(main, 6)

    def _build_url(self, parent, row):
        content = self._section(parent, "URL", row)
        self.url_entry = ctk.CTkEntry(
            content, textvariable=self.url_var,
            placeholder_text="Paste video, playlist, or channel URL here...",
            height=30, corner_radius=0, font=(FONT, 13),
            fg_color=COLORS["entry"], border_color=COLORS["border"], border_width=1,
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", pady=2)

    def _build_options(self, parent, row):
        content = self._section(parent, "Download Options", row)
        content.grid_columnconfigure((0, 1, 2), weight=1, uniform="opts")

        # Mode
        mode_f = ctk.CTkFrame(content, fg_color="transparent")
        mode_f.grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkLabel(mode_f, text="Mode:", font=(FONT, 12, "bold"),
                     text_color=COLORS["black"]).grid(row=0, column=0, sticky="w")
        ctk.CTkRadioButton(
            mode_f, text="Video", variable=self.mode_var, value="video",
            font=(FONT, 12), fg_color=COLORS["accent"],
            command=self._on_mode_change,
        ).grid(row=0, column=1, padx=(8, 4))
        ctk.CTkRadioButton(
            mode_f, text="Audio", variable=self.mode_var, value="audio",
            font=(FONT, 12), fg_color=COLORS["accent"],
            command=self._on_mode_change,
        ).grid(row=0, column=2, padx=4)

        # Quality
        quality_f = ctk.CTkFrame(content, fg_color="transparent")
        quality_f.grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(quality_f, text="Quality:", font=(FONT, 12, "bold"),
                     text_color=COLORS["black"]).grid(row=0, column=0, sticky="w")
        self.quality_menu = ctk.CTkOptionMenu(
            quality_f, variable=self.quality_var, values=VIDEO_QUALITIES,
            width=130, corner_radius=0, font=(FONT, 12),
            fg_color=COLORS["button"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], text_color=COLORS["black"],
        )
        self.quality_menu.grid(row=0, column=1, padx=(8, 0))

        # Format
        format_f = ctk.CTkFrame(content, fg_color="transparent")
        format_f.grid(row=0, column=2, sticky="w", padx=4)
        ctk.CTkLabel(format_f, text="Format:", font=(FONT, 12, "bold"),
                     text_color=COLORS["black"]).grid(row=0, column=0, sticky="w")
        self.format_menu = ctk.CTkOptionMenu(
            format_f, variable=self.format_var, values=VIDEO_FORMATS,
            width=90, corner_radius=0, font=(FONT, 12),
            fg_color=COLORS["button"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], text_color=COLORS["black"],
        )
        self.format_menu.grid(row=0, column=1, padx=(8, 0))

    def _build_advanced(self, parent, row):
        content = self._section(parent, "Advanced", row)
        content.grid_columnconfigure((0, 1, 2), weight=1, uniform="adv")

        # Subtitles
        subs_f = ctk.CTkFrame(content, fg_color="transparent")
        subs_f.grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkCheckBox(
            subs_f, text="Subtitles", variable=self.download_subs_var,
            font=(FONT, 12), fg_color=COLORS["accent"],
            command=self._on_subs_toggle,
        ).grid(row=0, column=0)
        self.subtitle_lang_menu = ctk.CTkOptionMenu(
            subs_f, variable=self.subtitle_lang_var, values=SUBTITLE_LANGUAGES,
            width=70, corner_radius=0, font=(FONT, 12),
            fg_color=COLORS["button"], button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"], text_color=COLORS["black"],
            state="disabled",
        )
        self.subtitle_lang_menu.grid(row=0, column=1, padx=(8, 0))

        # Embed
        embed_f = ctk.CTkFrame(content, fg_color="transparent")
        embed_f.grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkCheckBox(
            embed_f, text="Thumbnail", variable=self.embed_thumbnail_var,
            font=(FONT, 12), fg_color=COLORS["accent"],
        ).grid(row=0, column=0, padx=4)
        ctk.CTkCheckBox(
            embed_f, text="Metadata", variable=self.embed_metadata_var,
            font=(FONT, 12), fg_color=COLORS["accent"],
        ).grid(row=0, column=1, padx=4)

        # Playlist
        pl_f = ctk.CTkFrame(content, fg_color="transparent")
        pl_f.grid(row=0, column=2, sticky="w", padx=4)
        ctk.CTkCheckBox(
            pl_f, text="No Playlist", variable=self.no_playlist_var,
            font=(FONT, 12), fg_color=COLORS["accent"],
        ).grid(row=0, column=0)
        ctk.CTkLabel(pl_f, text="Range:", font=(FONT, 12)).grid(row=0, column=1, padx=(10, 4))
        ctk.CTkEntry(
            pl_f, textvariable=self.playlist_start_var, width=44, height=26,
            corner_radius=0, font=(FONT, 12), placeholder_text="#",
            fg_color=COLORS["entry"], border_color=COLORS["border"], border_width=1,
        ).grid(row=0, column=2)
        ctk.CTkLabel(pl_f, text="-", font=(FONT, 12)).grid(row=0, column=3, padx=2)
        ctk.CTkEntry(
            pl_f, textvariable=self.playlist_end_var, width=44, height=26,
            corner_radius=0, font=(FONT, 12), placeholder_text="#",
            fg_color=COLORS["entry"], border_color=COLORS["border"], border_width=1,
        ).grid(row=0, column=4)

    def _build_output(self, parent, row):
        content = self._section(parent, "Output", row)

        path_f = ctk.CTkFrame(content, fg_color="transparent")
        path_f.grid(row=0, column=0, sticky="ew", pady=2)
        path_f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(path_f, text="Save to:", font=(FONT, 12, "bold"),
                     text_color=COLORS["black"]).grid(row=0, column=0, sticky="w", padx=(0, 6))
        ctk.CTkEntry(
            path_f, textvariable=self.output_path_var, height=26, corner_radius=0,
            font=(FONT, 12), fg_color=COLORS["entry"],
            border_color=COLORS["border"], border_width=1,
        ).grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(
            path_f, text="Browse...", width=76, height=26, corner_radius=0,
            font=(FONT, 12), fg_color=COLORS["button"], text_color=COLORS["black"],
            hover_color=COLORS["button_hover"], border_width=1, border_color=COLORS["border"],
            command=self._browse_output,
        ).grid(row=0, column=2, padx=(4, 0))

        tmpl_f = ctk.CTkFrame(content, fg_color="transparent")
        tmpl_f.grid(row=1, column=0, sticky="ew", pady=2)
        tmpl_f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tmpl_f, text="Filename:", font=(FONT, 12, "bold"),
                     text_color=COLORS["black"]).grid(row=0, column=0, sticky="w", padx=(0, 6))
        ctk.CTkEntry(
            tmpl_f, textvariable=self.output_template_var, height=26, corner_radius=0,
            font=(FONT_MONO, 12), fg_color=COLORS["entry"],
            border_color=COLORS["border"], border_width=1,
            placeholder_text="Auto: uses video title  |  or type a name  |  or use %(title)s template",
        ).grid(row=0, column=1, sticky="ew")

    def _build_status(self, parent, row):
        content = self._section(parent, "Status", row)
        content.grid_columnconfigure(0, weight=0, minsize=130)
        content.grid_columnconfigure(1, weight=1)

        # Left: square thumbnail placeholder
        self.thumb_label = ctk.CTkLabel(
            content, text="No\npreview", width=120, height=120,
            font=(FONT, 10), text_color=COLORS["border"],
            fg_color=COLORS["entry"], corner_radius=0, anchor="center",
        )
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=(0, 10), pady=2, sticky="nw")

        # Right: progress + labels
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=4, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(
            right, mode="determinate", height=16, corner_radius=0,
            progress_color=COLORS["progress"], fg_color=COLORS["entry"],
            border_color=COLORS["border"], border_width=1,
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(2, 4))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(
            right, text="Ready.", anchor="w", height=20,
            font=(FONT, 12), text_color=COLORS["black"],
        )
        self.status_label.grid(row=1, column=0, sticky="ew")

        self.file_label = ctk.CTkLabel(
            right, text="", anchor="w", height=20,
            font=(FONT, 12), text_color=COLORS["navy"],
        )
        self.file_label.grid(row=2, column=0, sticky="ew")

        self.speed_label = ctk.CTkLabel(
            right, text="", anchor="w", height=20,
            font=(FONT_MONO, 12), text_color=COLORS["accent"],
        )
        self.speed_label.grid(row=3, column=0, sticky="ew", pady=(0, 2))

    def _build_download_btn(self, parent, row):
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=row, column=0, pady=(4, 8))
        self.download_btn = ctk.CTkButton(
            btn_frame, text="Download", width=220, height=40, corner_radius=0,
            font=(FONT, 14, "bold"), fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"], text_color=COLORS["white"],
            border_width=1, border_color=COLORS["border"],
            command=self._on_download,
        )
        self.download_btn.pack()

    # -- Callbacks --

    def _on_mode_change(self):
        if self.mode_var.get() == "video":
            self.quality_menu.configure(values=VIDEO_QUALITIES)
            self.format_menu.configure(values=VIDEO_FORMATS)
            self.format_var.set("mp4")
        else:
            self.quality_menu.configure(values=AUDIO_QUALITIES)
            self.format_menu.configure(values=AUDIO_FORMATS)
            self.format_var.set("mp3")
        self.quality_var.set("Best")

    def _on_subs_toggle(self):
        state = "normal" if self.download_subs_var.get() else "disabled"
        self.subtitle_lang_menu.configure(state=state)

    def _browse_output(self):
        path = filedialog.askdirectory(initialdir=self.output_path_var.get())
        if path:
            self.output_path_var.set(path)

    def _get_settings(self):
        return {
            "mode": self.mode_var.get(),
            "quality": self.quality_var.get(),
            "format": self.format_var.get(),
            "output_dir": self.output_path_var.get(),
            "output_template": self.output_template_var.get(),
            "subtitles": self.download_subs_var.get(),
            "subtitle_lang": self.subtitle_lang_var.get(),
            "embed_thumbnail": self.embed_thumbnail_var.get(),
            "embed_metadata": self.embed_metadata_var.get(),
            "no_playlist": self.no_playlist_var.get(),
            "playlist_start": self.playlist_start_var.get().strip(),
            "playlist_end": self.playlist_end_var.get().strip(),
        }

    def _update_status(self, msg, filename=None, progress_val=None):
        self.status_label.configure(text=msg)
        if filename:
            self.file_label.configure(text=f"File: {os.path.basename(filename)}")
        if progress_val is not None:
            self.progress_bar.set(progress_val)
        if "downloading" in msg.lower():
            speed_part = msg.split("@")[-1].strip() if "@" in msg else ""
            self.speed_label.configure(text=speed_part)
        else:
            self.speed_label.configure(text="")

    def _on_download_done(self, success, message, filename, thumbnail_url=None):
        self._update_status(message, filename=filename)
        if thumbnail_url:
            self._update_thumbnail(thumbnail_url)
        self.progress_bar.set(0)
        self.download_btn.configure(state="normal", text="Download")

    def _on_download(self):
        url = self.url_var.get().strip()
        if not url:
            self._update_status("Please enter a URL!")
            return
        if not is_valid_url(url):
            self._update_status("Invalid URL format!")
            return

        self.progress_bar.set(0)
        self.file_label.configure(text="")
        self.speed_label.configure(text="")
        self.thumb_label.configure(image=None, text="Loading...")
        self._thumb_ctk_img = None
        self.download_btn.configure(state="disabled", text="Downloading...")

        download_async(
            url, self._get_settings(),
            self._update_status, self._on_download_done,
            thumbnail_callback=self._update_thumbnail,
        )

    def _toggle_theme(self):
        self._dark = not self._dark
        self._save_prefs()
        new_colors = DARK_COLORS if self._dark else LIGHT_COLORS
        COLORS.clear()
        COLORS.update(new_colors)
        ctk.set_appearance_mode("dark" if self._dark else "light")
        self._main.destroy()
        self._build_ui()

    # -- Persistence --

    def _load_prefs(self):
        try:
            with open(PREFS_PATH, "r") as f:
                return bool(json.load(f).get("dark", True))
        except Exception:
            return True  # default dark

    def _save_prefs(self):
        try:
            with open(PREFS_PATH, "w") as f:
                json.dump({"dark": self._dark}, f)
        except Exception:
            pass

    # -- Thumbnail --

    def _update_thumbnail(self, url):
        if not url or not _PIL_AVAILABLE:
            return

        # Immediately show loading state on the UI thread
        self.root.after(0, lambda: self.thumb_label.configure(image=None, text="Loading..."))

        def _fetch():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                img = _PILImage.open(io.BytesIO(data)).convert("RGB")
                w, h = img.size
                side = min(w, h)
                img = img.crop(((w - side) // 2, (h - side) // 2,
                                (w + side) // 2, (h + side) // 2))
                img = img.resize((120, 120), _PILImage.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
                self._thumb_ctk_img = ctk_img  # keep reference
                self.root.after(0, lambda: self.thumb_label.configure(image=ctk_img, text=""))
            except Exception:
                self.root.after(0, lambda: self.thumb_label.configure(image=None, text="No\npreview"))

        threading.Thread(target=_fetch, daemon=True).start()

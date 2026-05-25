#!/usr/bin/env python3
"""
VoiceForge – High-Quality Neural Text-to-Speech  v1.1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by Microsoft Edge TTS  (free · no API key)
⚠  Requires an active internet connection.

Install dependencies:
    pip install customtkinter edge-tts pygame numpy
"""

# ── Suppress pygame's internal pkg_resources deprecation warning ──────────────
#    This is a cosmetic warning from pygame itself, not from VoiceForge.
#    It does NOT affect functionality in any way.
import warnings
warnings.filterwarnings("ignore", message=".*pkg_resources.*", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")

import asyncio, math, os, sys, tempfile, threading, time
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
import customtkinter as ctk
import edge_tts
import pygame

# numpy + pygame.sndarray power the real waveform visualiser.
# If numpy is absent we fall back to a smooth sine-wave shape.
try:
    import numpy as np
    import pygame.sndarray as _sndarray
    HAS_NUMPY = True
except Exception:
    HAS_NUMPY = False

# ──────────────────────────────────────────────────────────────────────────────
#  Voice library (Edge TTS neural voices)
# ──────────────────────────────────────────────────────────────────────────────
VOICES = {
    "Female": [
        ("Jenny   ·  US  ·  Warm",         "en-US-JennyNeural"),
        ("Aria    ·  US  ·  Expressive",    "en-US-AriaNeural"),
        ("Sara    ·  US  ·  Cheerful",      "en-US-SaraNeural"),
        ("Michelle · US  ·  Friendly",      "en-US-MichelleNeural"),
        ("Sonia   ·  UK  ·  Professional",  "en-GB-SoniaNeural"),
        ("Libby   ·  UK  ·  Natural",       "en-GB-LibbyNeural"),
        ("Natasha ·  AU  ·  Clear",         "en-AU-NatashaNeural"),
        ("Clara   ·  CA  ·  Soft",          "en-CA-ClaraNeural"),
        ("Neerja  ·  IN  ·  Bright",        "en-IN-NeerjaNeural"),
    ],
    "Male": [
        ("Guy     ·  US  ·  Confident",     "en-US-GuyNeural"),
        ("Davis   ·  US  ·  Deep",          "en-US-DavisNeural"),
        ("Tony    ·  US  ·  Casual",        "en-US-TonyNeural"),
        ("Ryan    ·  UK  ·  Authoritative", "en-GB-RyanNeural"),
        ("Thomas  ·  UK  ·  Calm",          "en-GB-ThomasNeural"),
        ("William ·  AU  ·  Measured",      "en-AU-WilliamNeural"),
        ("Liam    ·  CA  ·  Friendly",      "en-CA-LiamNeural"),
        ("Prabhat ·  IN  ·  Clear",         "en-IN-PrabhatNeural"),
    ],
}
VOICE_LOOKUP = {lbl: vid for voices in VOICES.values() for lbl, vid in voices}

MAX_CHARS = 5_000   # Edge TTS practical limit per request


# ──────────────────────────────────────────────────────────────────────────────
#  Real waveform canvas
# ──────────────────────────────────────────────────────────────────────────────
class WaveformCanvas(tk.Canvas):
    """
    Draws the actual RMS amplitude envelope of the synthesised audio and
    animates a playhead that tracks the current playback position in real time.

    Uses pygame.sndarray (numpy) to read raw PCM samples from the MP3.
    Falls back to a smooth sine-based shape if numpy is unavailable.
    """

    NUM_BARS   = 100        # horizontal resolution
    BAR_GAP    = 1          # px gap between bars
    CLR_PLAYED = "#38bdf8"  # cyan  – portion already heard
    CLR_UNPLAY = "#1e3a5f"  # navy  – portion not yet heard
    CLR_HEAD   = "#f0f9ff"  # white – playhead cursor line
    CLR_BG     = "#0d1117"  # background
    REFRESH_MS = 40         # ~25 fps during playback

    def __init__(self, parent, height: int = 56, **kwargs):
        super().__init__(parent, bg=self.CLR_BG, height=height,
                         highlightthickness=0, bd=0, **kwargs)
        self._amp: list[float] = []
        self._duration: float  = 0.0
        self._frac: float      = 0.0
        self._job              = None
        self.bind("<Configure>", lambda _: self._paint(self._frac))

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self, audio_path: str) -> float:
        """
        Extract the real amplitude envelope from *audio_path*.
        Returns the audio duration in seconds.
        """
        self._amp      = []
        self._duration = 0.0

        if HAS_NUMPY:
            try:
                sound          = pygame.mixer.Sound(audio_path)
                self._duration = sound.get_length()
                arr = _sndarray.array(sound)
                if arr.ndim == 2:               # stereo → mono average
                    arr = arr.mean(axis=1)
                arr = arr.astype(np.float32)
                n   = len(arr)
                chunk = max(1, n // self.NUM_BARS)
                amps  = []
                for i in range(self.NUM_BARS):
                    seg = arr[i * chunk : (i + 1) * chunk]
                    rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
                    amps.append(rms)
                peak      = max(amps) or 1.0
                self._amp = [a / peak for a in amps]
            except Exception:
                # Fallback: pretty sine shape (still looks like a real waveform)
                self._amp = self._sine_bars()
        else:
            self._amp = self._sine_bars()
            try:
                sound          = pygame.mixer.Sound(audio_path)
                self._duration = sound.get_length()
            except Exception:
                self._duration = 1.0

        self._frac = 0.0
        self._paint(0.0)
        return self._duration

    def start(self):
        """Begin animating the playhead (call after music.play())."""
        self._cancel()
        self._tick()

    def pause(self):
        """Freeze the playhead in place."""
        self._cancel()

    def resume(self):
        """Continue animating after a pause."""
        self._tick()

    def stop(self):
        """Stop animation and reset the playhead to the start."""
        self._cancel()
        self._frac = 0.0
        self._paint(0.0)

    def clear(self):
        """Remove waveform and reset everything."""
        self._cancel()
        self._amp      = []
        self._duration = 0.0
        self._frac     = 0.0
        self.delete("all")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _tick(self):
        if self._duration > 0:
            ms = pygame.mixer.music.get_pos()
            if ms >= 0:
                self._frac = min(1.0, ms / 1000.0 / self._duration)
                self._paint(self._frac)
        self._job = self.after(self.REFRESH_MS, self._tick)

    def _cancel(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def _paint(self, frac: float):
        self.delete("all")
        W = self.winfo_width()  or 400
        H = self.winfo_height() or 56
        if not self._amp:
            return

        n  = len(self._amp)
        bw = max(1.0, (W - (n - 1) * self.BAR_GAP) / n)
        px = frac * W                   # playhead x position in pixels

        for i, amp in enumerate(self._amp):
            x1  = i * (bw + self.BAR_GAP)
            x2  = x1 + bw
            bh  = max(2.0, amp * H * 0.88)
            y1  = (H - bh) / 2
            y2  = (H + bh) / 2
            clr = self.CLR_PLAYED if x1 < px else self.CLR_UNPLAY
            self.create_rectangle(x1, y1, x2, y2, fill=clr, outline="")

        # Playhead line
        if frac > 0.005:
            ix = int(px)
            self.create_line(ix, 2, ix, H - 2, fill=self.CLR_HEAD, width=1)

    @staticmethod
    def _sine_bars() -> list[float]:
        """Smooth organic fallback shape, used when numpy is unavailable."""
        n    = WaveformCanvas.NUM_BARS
        bars = [
            abs(math.sin(i * math.pi / n * 5)) * 0.65
            + abs(math.sin(i * 0.43)) * 0.25
            + 0.10
            for i in range(n)
        ]
        pk = max(bars) or 1.0
        return [b / pk for b in bars]


# ──────────────────────────────────────────────────────────────────────────────
#  Main application
# ──────────────────────────────────────────────────────────────────────────────
class VoiceForgeApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("VoiceForge")
        self.geometry("980x730")
        self.minsize(820, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Runtime state
        self.is_playing   = False
        self.is_paused    = False
        self.temp_file: str | None = None
        self._is_dark     = True

        # Tkinter variables
        self.gender_var   = ctk.StringVar(value="Female")
        self.voice_var    = ctk.StringVar()
        self.rate_var     = ctk.IntVar(value=0)
        self.pitch_var    = ctk.IntVar(value=0)
        self.volume_var   = ctk.IntVar(value=0)
        self.rate_disp    = ctk.StringVar(value="  0%")
        self.pitch_disp   = ctk.StringVar(value="  0 Hz")
        self.volume_disp  = ctk.StringVar(value="  0%")
        self.status_var   = ctk.StringVar(value="Ready  ·  Paste text and click Speak")

        pygame.mixer.init()
        self._build_ui()
        self._refresh_voice_list()
        self._bind_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def _bind_shortcuts(self):
        self.bind_all("<Control-Return>", lambda _: self._speak())
        self.bind_all("<Control-s>",      lambda _: self._save_audio())
        self.bind_all("<Escape>",         lambda _: self._stop())
        self.bind_all("<Control-l>",      lambda _: self._clear_text())
        self.bind_all("<space>",          self._space_handler)

    def _space_handler(self, event):
        # Only intercept Space when the text editor is NOT focused.
        focused = str(self.focus_get())
        if "text" not in focused.lower():
            self._toggle_pause()
            return "break"

    # ── UI build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_body()
        self._build_statusbar()

    # Header ──────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color="#0f172a")
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        logo_f = ctk.CTkFrame(hdr, fg_color="transparent")
        logo_f.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        ctk.CTkLabel(logo_f, text="🎙",
                     font=ctk.CTkFont(size=28)).pack(side="left")
        ctk.CTkLabel(logo_f, text=" VoiceForge",
                     font=ctk.CTkFont(family="Georgia", size=22, weight="bold"),
                     text_color="#38bdf8").pack(side="left")

        ctk.CTkLabel(
            hdr,
            text="Neural Text-to-Speech  ·  Powered by Edge TTS  ·  🌐 Requires internet",
            font=ctk.CTkFont(size=12),
            text_color="#475569",
        ).grid(row=0, column=1, sticky="w")

        self.theme_btn = ctk.CTkButton(
            hdr, text="☀  Light mode", width=120, height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color="#38bdf8", text_color="#38bdf8",
            hover_color="#1e3a5f",
            command=self._toggle_theme,
        )
        self.theme_btn.grid(row=0, column=2, padx=20)

    # Body ────────────────────────────────────────────────────────────────────
    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(12, 6))
        body.grid_columnconfigure(0, weight=55)
        body.grid_columnconfigure(1, weight=45)
        body.grid_rowconfigure(0, weight=1)
        self._build_editor(body)
        self._build_settings(body)

    # Editor (left) ───────────────────────────────────────────────────────────
    def _build_editor(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14,
                            fg_color=("#f8fafc", "#1e293b"),
                            border_width=1,
                            border_color=("#e2e8f0", "#334155"))
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        # Header row: title + char counter
        ch = ctk.CTkFrame(card, fg_color="transparent", height=44)
        ch.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 0))
        ch.grid_columnconfigure(1, weight=1)
        ch.grid_propagate(False)
        ctk.CTkLabel(ch, text="📝  Text Input",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=("#1e293b", "#e2e8f0"),
                     ).grid(row=0, column=0, sticky="w")
        self.char_count = ctk.CTkLabel(
            ch, text=f"0 / {MAX_CHARS:,} chars",
            font=ctk.CTkFont(size=11),
            text_color=("#94a3b8", "#64748b"),
        )
        self.char_count.grid(row=0, column=2, sticky="e")

        # Text area
        self.text_box = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(family="Georgia", size=15),
            corner_radius=10, wrap="word",
            border_width=1,
            border_color=("#cbd5e1", "#334155"),
            fg_color=("#ffffff", "#0f172a"),
        )
        self.text_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=8)
        self.text_box.insert(
            "1.0",
            "Hello! I'm VoiceForge — paste or type any text here and I'll "
            "speak it with a natural, high-quality neural voice.\n\n"
            "You can adjust the speed, pitch, and volume on the right, and "
            "choose from male and female voices with different accents.",
        )
        self.text_box.bind("<KeyRelease>", self._update_char_count)
        self._update_char_count()
        self._attach_context_menu(self.text_box)

        # ── Waveform visualiser ───────────────────────────────────────────────
        wave_wrap = ctk.CTkFrame(card, height=60, corner_radius=8,
                                 fg_color="#0d1117")
        wave_wrap.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        wave_wrap.grid_propagate(False)
        wave_wrap.grid_columnconfigure(0, weight=1)
        wave_wrap.grid_rowconfigure(0, weight=1)

        self.waveform = WaveformCanvas(wave_wrap, height=56)
        self.waveform.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # ── Button row ────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 4))
        for c in range(5):
            btn_row.grid_columnconfigure(c, weight=1)

        self.speak_btn = ctk.CTkButton(
            btn_row, text="▶  Speak", height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0369a1", hover_color="#0284c7",
            corner_radius=10,
            command=self._speak,
        )
        self.speak_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.stop_btn = ctk.CTkButton(
            btn_row, text="⏹  Stop", height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#9f1239", hover_color="#be123c",
            corner_radius=10, state="disabled",
            command=self._stop,
        )
        self.stop_btn.grid(row=0, column=1, padx=4, sticky="ew")

        self.pause_btn = ctk.CTkButton(
            btn_row, text="⏸  Pause", height=44,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#78350f", hover_color="#92400e",
            corner_radius=10, state="disabled",
            command=self._toggle_pause,
        )
        self.pause_btn.grid(row=0, column=2, padx=4, sticky="ew")

        self.save_btn = ctk.CTkButton(
            btn_row, text="💾  Save MP3", height=44,
            font=ctk.CTkFont(size=13),
            fg_color="#065f46", hover_color="#047857",
            corner_radius=10,
            command=self._save_audio,
        )
        self.save_btn.grid(row=0, column=3, padx=4, sticky="ew")

        ctk.CTkButton(
            btn_row, text="🗑  Clear", height=44,
            font=ctk.CTkFont(size=13),
            fg_color="#1e293b", hover_color="#334155",
            border_width=1, border_color="#475569",
            corner_radius=10,
            command=self._clear_text,
        ).grid(row=0, column=4, padx=(4, 0), sticky="ew")

        # Keyboard shortcut hint
        ctk.CTkLabel(
            card,
            text="Ctrl+Enter = Speak   ·   Space = Pause/Resume   ·   Esc = Stop   ·   Ctrl+S = Save",
            font=ctk.CTkFont(size=10),
            text_color=("#94a3b8", "#334155"),
        ).grid(row=4, column=0, pady=(0, 8))

    # Settings (right) ────────────────────────────────────────────────────────
    def _build_settings(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14,
                            fg_color=("#f8fafc", "#1e293b"),
                            border_width=1,
                            border_color=("#e2e8f0", "#334155"))
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="⚙️  Voice Settings",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=("#1e293b", "#e2e8f0"),
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))

        row = 1

        # Gender
        row = self._section(card, "Gender", row)
        gf = ctk.CTkFrame(card, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        gf.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 14))
        gf.grid_columnconfigure((0, 1), weight=1)
        for i, g in enumerate(["Female", "Male"]):
            ctk.CTkRadioButton(
                gf,
                text="♀  Female" if g == "Female" else "♂  Male",
                variable=self.gender_var, value=g,
                command=self._refresh_voice_list,
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=i, padx=14, pady=10, sticky="w")
        row += 1

        # Voice selector
        row = self._section(card, "Voice", row)
        self.voice_menu = ctk.CTkOptionMenu(
            card, variable=self.voice_var,
            font=ctk.CTkFont(size=12), height=36,
            corner_radius=8, dynamic_resizing=False, anchor="w",
        )
        self.voice_menu.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 14))
        row += 1

        # Sliders
        row = self._build_slider(card, "🚀  Speed",  self.rate_var,   -50, 100, row,
                                 self.rate_disp,   "%")
        row = self._build_slider(card, "🎵  Pitch",  self.pitch_var,  -20,  20, row,
                                 self.pitch_disp,  " Hz")
        row = self._build_slider(card, "🔊  Volume", self.volume_var, -50,  50, row,
                                 self.volume_disp, "%",
                                 live_fn=self._sync_pygame_volume)

        card.grid_rowconfigure(row, weight=1)
        row += 1

        # Presets
        row = self._section(card, "Presets", row)
        pf = ctk.CTkFrame(card, fg_color="transparent")
        pf.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 10))
        pf.grid_columnconfigure((0, 1, 2), weight=1)
        for i, (name, rate, pitch, vol) in enumerate([
            ("📖 Narration",  0, 0, 0),
            ("🎙 Podcast",   10, 2, 5),
            ("⚡ Fast",      40, 0, 0),
        ]):
            r, p, v = rate, pitch, vol
            ctk.CTkButton(
                pf, text=name, height=32,
                font=ctk.CTkFont(size=12),
                fg_color=("#e2e8f0", "#1e3a5f"),
                text_color=("#1e293b", "#93c5fd"),
                hover_color=("#cbd5e1", "#1e4a7f"),
                corner_radius=8,
                command=lambda _r=r, _p=p, _v=v: self._apply_preset(_r, _p, _v),
            ).grid(row=0, column=i, padx=3, sticky="ew")
        row += 1

        # Reset
        ctk.CTkButton(
            card, text="↺  Reset to Defaults", height=34,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            border_color=("#94a3b8", "#475569"),
            text_color=("#64748b", "#94a3b8"),
            hover_color=("#f1f5f9", "#0f172a"),
            corner_radius=8,
            command=self._reset_defaults,
        ).grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 14))

    def _section(self, parent, text: str, row: int) -> int:
        ctk.CTkLabel(parent, text=text,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=("#64748b", "#64748b"),
                     ).grid(row=row, column=0, sticky="w", padx=16, pady=(8, 2))
        return row + 1

    def _build_slider(self, parent, label, var, from_, to, row,
                      disp_var, suffix, live_fn=None):
        sf = ctk.CTkFrame(parent, fg_color=("#f1f5f9", "#0f172a"), corner_radius=10)
        sf.grid(row=row, column=0, sticky="ew", padx=14, pady=(0, 10))
        sf.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(sf, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(top, text=label,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=("#334155", "#94a3b8")).pack(side="left")
        ctk.CTkLabel(top, textvariable=disp_var,
                     font=ctk.CTkFont(family="Courier New", size=13),
                     text_color="#38bdf8", width=68).pack(side="right")

        def on_slide(v, _var=var, _d=disp_var, _sfx=suffix, _fn=live_fn):
            val  = int(float(v))
            _var.set(val)
            sign = "+" if val > 0 else ""
            _d.set(f"{sign}{val:>3}{_sfx}")
            if _fn:
                _fn(val)

        ctk.CTkSlider(sf, from_=from_, to=to, variable=var,
                      command=on_slide, height=14, corner_radius=4,
                      ).pack(fill="x", padx=10, pady=(4, 10))
        on_slide(var.get())
        return row + 1

    # Status bar ──────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        sb = ctk.CTkFrame(self, height=28, corner_radius=0,
                          fg_color=("#e2e8f0", "#0f172a"))
        sb.grid(row=2, column=0, sticky="ew")
        sb.grid_propagate(False)
        sb.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            sb, textvariable=self.status_var,
            font=ctk.CTkFont(size=11),
            text_color=("#64748b", "#475569"),
            anchor="w",
        )
        self.status_lbl.grid(row=0, column=0, sticky="ew", padx=14)

        ctk.CTkLabel(sb, text="VoiceForge 1.1  ·  🌐 Requires internet",
                     font=ctk.CTkFont(size=11),
                     text_color=("#94a3b8", "#334155"),
                     ).grid(row=0, column=1, padx=14)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _refresh_voice_list(self):
        gender = self.gender_var.get()
        labels = [lbl for lbl, _ in VOICES[gender]]
        self.voice_menu.configure(values=labels)
        self.voice_var.set(labels[0])

    def _get_tts_params(self):
        vid   = VOICE_LOOKUP.get(self.voice_var.get(), "en-US-JennyNeural")
        rate  = self.rate_var.get()
        pitch = self.pitch_var.get()
        vol   = self.volume_var.get()
        return (
            vid,
            f"{'+' if rate  >= 0 else ''}{rate}%",
            f"{'+' if pitch >= 0 else ''}{pitch}Hz",
            f"{'+' if vol   >= 0 else ''}{vol}%",
        )

    async def _synthesize(self, text: str, out_path: str):
        vid, rate_s, pitch_s, vol_s = self._get_tts_params()
        comm = edge_tts.Communicate(text, vid,
                                    rate=rate_s, pitch=pitch_s, volume=vol_s)
        await comm.save(out_path)

    def _speak(self):
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            self._set_status("⚠  Please enter some text first.", "#f87171")
            return
        if len(text) > MAX_CHARS:
            self._set_status(
                f"⚠  Text too long ({len(text):,} chars). "
                f"Please keep it under {MAX_CHARS:,}.", "#f87171")
            return

        self._stop()
        self.waveform.clear()
        self.speak_btn.configure(state="disabled", text="⏳  Synthesising…")
        self.stop_btn.configure(state="normal")
        self.save_btn.configure(state="disabled")
        self._set_status("🔄  Generating speech via Edge TTS…", "#38bdf8")

        def worker():
            try:
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.close()
                self.temp_file = tmp.name

                asyncio.run(self._synthesize(text, self.temp_file))

                # Extract real waveform (runs on main thread via after())
                self.after(0, lambda: self.waveform.load(self.temp_file))

                pygame.mixer.music.load(self.temp_file)
                self._sync_pygame_volume(self.volume_var.get())
                pygame.mixer.music.play()
                self.is_playing = True
                self.is_paused  = False

                self.after(0, self.waveform.start)
                self.after(0, lambda: self.speak_btn.configure(
                    state="normal", text="▶  Speak"))
                self.after(0, lambda: self.pause_btn.configure(state="normal"))
                self.after(0, lambda: self._set_status("🔊  Playing…", "#4ade80"))

                # Block until playback finishes or is stopped
                while pygame.mixer.music.get_busy() or self.is_paused:
                    if not self.is_playing:
                        break
                    time.sleep(0.1)

                self.is_playing = False
                self.is_paused  = False
                self.after(0, self._on_done)

            except OSError:
                self.after(0, lambda: self._on_error(
                    "No internet connection — Edge TTS requires internet access."))
            except Exception as exc:
                msg = str(exc)
                if any(k in msg.lower() for k in ("connect", "network", "ssl", "timeout")):
                    msg = "No internet connection — Edge TTS requires internet access."
                self.after(0, lambda: self._on_error(msg))

        threading.Thread(target=worker, daemon=True).start()

    def _stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused  = False
        self.waveform.stop()
        self.stop_btn.configure(state="disabled")
        self.pause_btn.configure(state="disabled", text="⏸  Pause",
                                 fg_color="#78350f", hover_color="#92400e")
        self.speak_btn.configure(state="normal", text="▶  Speak")
        self.save_btn.configure(state="normal")

    def _toggle_pause(self):
        if not self.is_playing and not self.is_paused:
            return
        if not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.waveform.pause()
            self.pause_btn.configure(text="▶  Resume",
                                     fg_color="#065f46", hover_color="#047857")
            self._set_status("⏸  Paused", "#f59e0b")
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.waveform.resume()
            self.pause_btn.configure(text="⏸  Pause",
                                     fg_color="#78350f", hover_color="#92400e")
            self._set_status("🔊  Playing…", "#4ade80")

    def _sync_pygame_volume(self, val: int):
        # Maps [-50, 0, +50] → [0.0, 1.0, 1.0]
        # 0 = full volume; negative = quieter; positive = still full (hardware limit)
        pygame_vol = max(0.0, min(1.0, (val + 50) / 50.0))
        pygame.mixer.music.set_volume(pygame_vol)

    def _on_done(self):
        self._set_status("✅  Done  ·  Ready for next speech", "#94a3b8")
        self.stop_btn.configure(state="disabled")
        self.pause_btn.configure(state="disabled", text="⏸  Pause",
                                 fg_color="#78350f", hover_color="#92400e")
        self.save_btn.configure(state="normal")
        self.waveform.stop()

    def _on_error(self, msg: str):
        self.speak_btn.configure(state="normal", text="▶  Speak")
        self.stop_btn.configure(state="disabled")
        self.pause_btn.configure(state="disabled", text="⏸  Pause",
                                 fg_color="#78350f", hover_color="#92400e")
        self.save_btn.configure(state="normal")
        self.waveform.clear()
        self._set_status(f"❌  {msg}", "#f87171")

    def _save_audio(self):
        text = self.text_box.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("No Text", "Please enter text to convert first.")
            return
        if len(text) > MAX_CHARS:
            messagebox.showwarning("Too Long",
                f"Text exceeds {MAX_CHARS:,} characters. Please shorten it.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3"), ("All files", "*.*")],
            title="Save Audio File",
        )
        if not path:
            return
        self._set_status("💾  Saving audio…", "#38bdf8")
        self.save_btn.configure(state="disabled")

        def worker():
            try:
                asyncio.run(self._synthesize(text, path))
                name = Path(path).name
                self.after(0, lambda: self._set_status(f"✅  Saved: {name}", "#4ade80"))
            except OSError:
                self.after(0, lambda: self._on_error(
                    "No internet connection — cannot save audio."))
            except Exception as exc:
                self.after(0, lambda: self._on_error(str(exc)))
            finally:
                self.after(0, lambda: self.save_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _clear_text(self):
        self.text_box.delete("1.0", "end")
        self.waveform.clear()
        self._update_char_count()

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        ctk.set_appearance_mode("dark" if self._is_dark else "light")
        self.theme_btn.configure(
            text="☀  Light mode" if self._is_dark else "🌙  Dark mode")

    def _reset_defaults(self):
        self.rate_var.set(0);   self.rate_disp.set("  0%")
        self.pitch_var.set(0);  self.pitch_disp.set("  0 Hz")
        self.volume_var.set(0); self.volume_disp.set("  0%")
        self._sync_pygame_volume(0)
        self._set_status("↺  Settings reset to defaults.", "#94a3b8")

    def _apply_preset(self, rate: int, pitch: int, vol: int):
        self.rate_var.set(rate)
        self.pitch_var.set(pitch)
        self.volume_var.set(vol)
        sign = lambda v: "+" if v > 0 else ""
        self.rate_disp.set(f"{sign(rate)}{rate:>3}%")
        self.pitch_disp.set(f"{sign(pitch)}{pitch:>3} Hz")
        self.volume_disp.set(f"{sign(vol)}{vol:>3}%")
        self._sync_pygame_volume(vol)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _attach_context_menu(self, ctk_textbox):
        """Right-click menu for the text editor."""
        inner = ctk_textbox._textbox
        menu  = tk.Menu(self, tearoff=0,
                        bg="#1e293b", fg="#e2e8f0",
                        activebackground="#0369a1", activeforeground="#ffffff",
                        borderwidth=0, relief="flat",
                        font=("Segoe UI", 11))
        menu.add_command(label="  Cut",        command=lambda: inner.event_generate("<<Cut>>"))
        menu.add_command(label="  Copy",       command=lambda: inner.event_generate("<<Copy>>"))
        menu.add_command(label="  Paste",      command=lambda: inner.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="  Select All", command=lambda: inner.tag_add("sel", "1.0", "end"))

        def show(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        ctk_textbox.bind("<Button-3>", show)
        inner.bind("<Button-3>", show)

    def _set_status(self, text: str, color: str = "#94a3b8"):
        self.status_var.set(text)
        self.status_lbl.configure(text_color=color)

    def _update_char_count(self, _=None):
        n = len(self.text_box.get("1.0", "end").strip())
        if n > MAX_CHARS:
            color = "#f87171"   # red – over limit
        elif n > MAX_CHARS * 0.85:
            color = "#f59e0b"   # amber – approaching limit
        else:
            color = "#64748b"   # normal
        self.char_count.configure(
            text=f"{n:,} / {MAX_CHARS:,} chars",
            text_color=color,
        )

    def _on_close(self):
        """Clean shutdown: stop audio, remove temp file, quit pygame."""
        self._stop()
        pygame.mixer.quit()
        pygame.quit()
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except Exception:
                pass
        self.destroy()


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = VoiceForgeApp()
    app.mainloop()

import threading
import re
from gi.repository import Gtk, Adw, GLib, Gio

from ..controller import ZeroneController
from . import apply_css_to_widget
from .settings import _load_accent_color_file

def _(s):
    import builtins
    t = getattr(builtins, '_', None)
    if callable(t):
        return t(s)
    return s


class TTSPage(Gtk.Box):
    """Full-page Text-to-Speech converter."""

    def __init__(self, controller: ZeroneController, on_close=None, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.controller = controller
        self.on_close = on_close
        self._playing = False
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self):
        # ── Header row: breadcrumb + title ────────────────────────────────
        header_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
            margin_start=16, margin_end=16,
            margin_top=10, margin_bottom=6,
        )
        self.append(header_row)

        crumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        home_btn = Gtk.Button(label=_("Home"), css_classes=["flat", "breadcrumb-home"])
        home_btn.connect("clicked", lambda *_: self.on_close() if self.on_close else None)
        crumb_box.append(home_btn)
        crumb_box.append(Gtk.Label(label="›", css_classes=["breadcrumb-sep"]))
        crumb_box.append(Gtk.Label(label=_("Text to Speech"), css_classes=["breadcrumb-current"]))
        header_row.append(crumb_box)

        header_row.append(Gtk.Label(
            label=_("Text to Speech"),
            css_classes=["title"],
            halign=Gtk.Align.CENTER,
            hexpand=True,
        ))
        # Balance spacer same width as crumb_box
        header_row.append(Gtk.Box(hexpand=False))

        self.append(Gtk.Separator())

        # ── Scrollable content ────────────────────────────────────────────
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(scroll)

        content = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=20,
            margin_start=24, margin_end=24,
            margin_top=20, margin_bottom=24,
        )
        scroll.set_child(content)

        # ── Text input card ───────────────────────────────────────────────
        input_group = Adw.PreferencesGroup(title=_("Text"))
        content.append(input_group)

        text_row = Adw.ActionRow()
        input_group.add(text_row)

        text_scroll = Gtk.ScrolledWindow(
            vexpand=False, hexpand=True,
            min_content_height=160, max_content_height=320,
        )
        text_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        text_scroll.set_margin_top(10)
        text_scroll.set_margin_bottom(10)
        text_scroll.set_margin_start(6)
        text_scroll.set_margin_end(6)

        self.text_view = Gtk.TextView(
            wrap_mode=Gtk.WrapMode.WORD_CHAR,
            accepts_tab=False,
            hexpand=True,
        )
        buf = self.text_view.get_buffer()
        buf.create_tag("placeholder", foreground_rgba=self._dim_color())
        self._placeholder_active = False
        self._set_placeholder()
        # Remove placeholder on focus-in
        focus_ctrl = Gtk.EventControllerFocus.new()
        focus_ctrl.connect("enter", self._on_focus_in)
        focus_ctrl.connect("leave", self._on_focus_out)
        self.text_view.add_controller(focus_ctrl)
        buf.connect("changed", self._on_text_changed)
        text_scroll.set_child(self.text_view)
        text_row.set_child(text_scroll)

        # Character counter
        self._char_label = Gtk.Label(
            label="0 " + _("characters"),
            css_classes=["caption", "dim-label"],
            halign=Gtk.Align.END,
            margin_end=8, margin_bottom=6,
        )
        content.append(self._char_label)

        # ── Voice settings card ───────────────────────────────────────────
        voice_group = Adw.PreferencesGroup(title=_("Voice Settings"))
        content.append(voice_group)

        # Speed / Rate row
        speed_row = Adw.ActionRow(
            title=_("Speed"),
            subtitle=_("Playback speed (0.5 = slow, 1.0 = normal, 2.0 = fast)"),
        )
        voice_group.add(speed_row)

        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                            valign=Gtk.Align.CENTER)
        self._speed_label = Gtk.Label(label="1.0", width_chars=3)
        self._speed_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.5, 2.0, 0.1)
        self._speed_scale.set_value(1.0)
        self._speed_scale.set_size_request(160, -1)
        self._speed_scale.set_draw_value(False)
        self._speed_scale.connect("value-changed", self._on_speed_changed)
        speed_box.append(self._speed_scale)
        speed_box.append(self._speed_label)
        speed_row.add_suffix(speed_box)

        # Current TTS engine info row
        engine_row = Adw.ActionRow(
            title=_("Engine"),
            subtitle=_("Change TTS engine in Settings → General → Voice"),
        )
        voice_group.add(engine_row)
        try:
            tts = self.controller.handlers.tts
            engine_name = type(tts).__name__.replace("Handler", "").replace("TTS", " TTS")
        except Exception:
            engine_name = _("Not configured")
        engine_row.add_suffix(Gtk.Label(
            label=engine_name,
            css_classes=["dim-label", "caption"],
            valign=Gtk.Align.CENTER,
        ))

        # Voice selector row
        voice_row = Adw.ActionRow(
            title=_("Voice / Language"),
            subtitle=_("Select the voice or language for speech output"),
        )
        voice_group.add(voice_row)

        self._voice_combo = Gtk.ComboBoxText(valign=Gtk.Align.CENTER)
        self._voice_combo.set_size_request(200, -1)
        voice_row.add_suffix(self._voice_combo)

        # Refresh button to reload voices list
        refresh_btn = Gtk.Button(
            icon_name="view-refresh-symbolic",
            css_classes=["flat", "circular"],
            valign=Gtk.Align.CENTER,
            tooltip_text=_("Refresh voices list"),
        )
        refresh_btn.connect("clicked", self._load_voices)
        voice_row.add_suffix(refresh_btn)

        # Load voices async so UI doesn't freeze
        self._load_voices()

        # ── Action buttons ────────────────────────────────────────────────
        btn_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
            halign=Gtk.Align.CENTER,
            margin_top=8,
        )
        content.append(btn_box)

        # Clear button
        clear_btn = Gtk.Button(
            label=_("Clear"),
            css_classes=["flat"],
        )
        clear_btn.connect("clicked", self._on_clear)
        btn_box.append(clear_btn)

        # Play/Stop button
        self._play_btn = Gtk.Button(
            label="  " + _("Read Aloud"),
            css_classes=["suggested-action", "pill"],
        )
        play_icon = Gtk.Image(icon_name="media-playback-start-symbolic")
        self._play_btn.set_child(
            self._make_btn_content("media-playback-start-symbolic", _("Read Aloud"))
        )
        self._play_btn.connect("clicked", self._on_play_stop)
        btn_box.append(self._play_btn)

        # Download button
        self._dl_btn = Gtk.Button(css_classes=["pill"])
        self._dl_btn.set_child(
            self._make_btn_content("document-save-symbolic", _("Download"))
        )
        self._dl_btn.connect("clicked", self._on_download)
        btn_box.append(self._dl_btn)

        # ── Progress indicator ────────────────────────────────────────────
        self._progress_bar = Gtk.ProgressBar(
            pulse_step=0.08,
            visible=False,
            margin_top=8,
        )
        content.append(self._progress_bar)
        self._pulse_id = None

    # ── Helpers ────────────────────────────────────────────────────────────

    def _make_btn_content(self, icon_name, label_text):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.append(Gtk.Image(icon_name=icon_name))
        box.append(Gtk.Label(label=label_text))
        return box

    def _dim_color(self):
        from gi.repository import Gdk
        c = Gdk.RGBA()
        c.parse("rgba(128,128,128,0.5)")
        return c

    def _set_placeholder(self):
        buf = self.text_view.get_buffer()
        buf.set_text("Enter text to convert to speech...")
        buf.apply_tag_by_name("placeholder", buf.get_start_iter(), buf.get_end_iter())
        self._placeholder_active = True

    def _clear_placeholder(self):
        if self._placeholder_active:
            self.text_view.get_buffer().set_text("")
            self._placeholder_active = False

    def _on_focus_in(self, ctrl):
        self._clear_placeholder()

    def _on_focus_out(self, ctrl):
        buf = self.text_view.get_buffer()
        if buf.get_char_count() == 0:
            self._set_placeholder()

    def _get_text(self):
        if self._placeholder_active:
            return ""
        buf = self.text_view.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)

    def _on_text_changed(self, buf):
        if self._placeholder_active:
            return
        count = buf.get_char_count()
        self._char_label.set_label(f"{count} characters")

    def _on_speed_changed(self, scale):
        val = round(scale.get_value(), 1)
        self._speed_label.set_label(str(val))

    def _on_clear(self, btn):
        self.text_view.get_buffer().set_text("")
        self._set_placeholder()

    # ── Play / Stop ────────────────────────────────────────────────────────

    def _on_play_stop(self, btn):
        if self._playing:
            self._stop()
        else:
            self._play()

    def _play(self):
        text = self._get_text().strip()
        if not text:
            return

        # Clean markdown
        clean = re.sub(r'[#*`_~]', '', text)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean).strip()
        if not clean:
            return

        self._playing = True
        self._play_btn.set_child(
            self._make_btn_content("media-playback-stop-symbolic", _("Stop"))
        )
        self._play_btn.remove_css_class("suggested-action")
        self._play_btn.add_css_class("destructive-action")

        # Start progress pulse
        self._progress_bar.set_visible(True)
        self._pulse_id = GLib.timeout_add(80, self._pulse)

        def speak():
            try:
                tts = self.controller.handlers.tts
                tts.play_audio(clean)
            except Exception as e:
                print(f"TTS page error: {e}")
            GLib.idle_add(self._on_finished)

        threading.Thread(target=speak, daemon=True).start()

    def _stop(self):
        try:
            self.controller.handlers.tts.stop()
        except Exception:
            pass
        self._on_finished()

    def _on_finished(self):
        self._playing = False
        self._play_btn.set_child(
            self._make_btn_content("media-playback-start-symbolic", _("Read Aloud"))
        )
        self._play_btn.remove_css_class("destructive-action")
        self._play_btn.add_css_class("suggested-action")
        self._progress_bar.set_visible(False)
        if self._pulse_id:
            GLib.source_remove(self._pulse_id)
            self._pulse_id = None

    def _load_voices(self, *args):
        """Load voices from TTS handler into the combo box."""
        self._voice_combo.remove_all()
        self._voice_combo.append_text("Loading...")
        self._voice_combo.set_active(0)
        self._voice_combo.set_sensitive(False)

        def fetch():
            try:
                tts = self.controller.handlers.tts
                voices = tts.get_voices()
                current = tts.get_current_voice()
            except Exception as e:
                print(f"Voice load error: {e}")
                voices = ()
                current = None

            def populate():
                self._voice_combo.remove_all()
                if not voices:
                    self._voice_combo.append_text("No voices available")
                    self._voice_combo.set_active(0)
                    self._voice_combo.set_sensitive(False)
                    return
                active_idx = 0
                for i, (label, value) in enumerate(voices):
                    self._voice_combo.append(value, label)
                    if value == current:
                        active_idx = i
                self._voice_combo.set_active(active_idx)
                self._voice_combo.set_sensitive(True)
                self._voice_combo.connect("changed", self._on_voice_changed)
            GLib.idle_add(populate)

        threading.Thread(target=fetch, daemon=True).start()

    def _on_voice_changed(self, combo):
        """Apply selected voice to TTS handler."""
        voice_id = combo.get_active_id()
        if not voice_id:
            return
        try:
            self.controller.handlers.tts.set_voice(voice_id)
        except Exception as e:
            print(f"Voice set error: {e}")

    def _on_download(self, btn):
        """Save TTS audio to a file chosen by the user."""
        text = self._get_text().strip()
        if not text:
            return
        clean = re.sub(r'[#*`_~]', '', text)
        clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean).strip()
        if not clean:
            return

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Save Audio File"))
        dialog.set_initial_name("speech.wav")

        f = Gio.File.new_for_path(GLib.get_home_dir())
        dialog.set_initial_folder(f)

        def on_save(d, result):
            try:
                file = d.save_finish(result)
                if not file:
                    return
                path = file.get_path()
                btn.set_sensitive(False)
                btn.set_child(self._make_btn_content("content-loading-symbolic", _("Saving…")))
                def do_save():
                    try:
                        self.controller.handlers.tts.save_audio(clean, path)
                    except Exception as e:
                        print(f"Download error: {e}")
                    GLib.idle_add(lambda: (
                        btn.set_sensitive(True),
                        btn.set_child(self._make_btn_content("document-save-symbolic", _("Download")))
                    ))
                threading.Thread(target=do_save, daemon=True).start()
            except Exception:
                pass

        win = self.get_root()
        dialog.save(win, None, on_save)

    def _pulse(self):
        if self._playing:
            self._progress_bar.pulse()
            return True
        return False

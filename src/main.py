import sys
import os
import gettext
import gi 
gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '5')
gi.require_version('Adw', '1')
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, Adw, Gio, Gdk, GLib

from .ui.settings import Settings
from .window import MainWindow
from .ui.shortcuts import Shortcuts
from .ui.thread_editing import ThreadEditing
from .ui.extension import Extension
from .ui.mini_window import MiniWindow


class MyApp(Adw.Application):
    def __init__(self, version, **kwargs):
        self.version = version
        super().__init__(flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.settings = Gio.Settings.new("com.zeroneai.app")
        self.add_main_option("run-action", 0, GLib.OptionFlags.NONE, GLib.OptionArg.STRING, "Run an action", "ACTION")
        css = '''
        .code{
        background-color: rgb(38,38,38);
        }

        .code .sourceview text{
            background-color: rgb(38,38,38);
        }
        .code .sourceview border gutter{
            background-color: rgb(38,38,38);
        }
        .sourceview{
            color: rgb(192,191,188);
        }
        .copy-action{
            color:rgb(255,255,255);
            background-color: rgb(38,162,105);
        }
        .large{
            -gtk-icon-size:100px;
        }
        .empty-folder{
            font-size:25px;
            font-weight:800;
            -gtk-icon-size:120px;
        }
        .user{
            background-color: rgba(61, 152, 255,0.03);
        }
        .assistant{
            background-color: rgba(184, 134, 17,0.02);
        }
        .done{
            background-color: rgba(33, 155, 98,0.02);
        }
        .failed{
            background-color: rgba(254, 31, 41,0.02);
        }
        .file{
            background-color: rgba(222, 221, 218,0.03);
        }
        .folder{
            background-color: rgba(189, 233, 255,0.03);
        }
        .message-warning{
            background-color: rgba(184, 134, 17,0.02);
        }
        .transparent{
            background-color: rgba(0,0,0,0);
        }
        .chart{
            background-color: rgba(61, 152, 255,0.25);
        }
        .right-angles{
            border-radius: 0;
        }
        .image{
            -gtk-icon-size:400px;
        }
        .video {
            min-height: 400px;
        }
        .mini-window {
            border-radius: 12px;
            border: 1px solid alpha(@card_fg_color, 0.15);
            box-shadow: 0 2px 4px alpha(black, 0.1);
            margin: 4px;
        }
        @keyframes pulse_opacity {
          0% { opacity: 1.0; }
          50% { opacity: 0.5; }
          100% { opacity: 1.0; }
        }

        .pulsing-label {
          animation-name: pulse_opacity;
          animation-duration: 1.8s;
          animation-timing-function: ease-in-out;
          animation-iteration-count: infinite;
        }

        /* Chat history row styling */
        .navigation-sidebar row.chat-row-selected {
          background-color: alpha(@accent_bg_color, 0.15);
          border-radius: 6px;
        }
        
        .navigation-sidebar row.chat-row-selected:hover {
          background-color: alpha(@accent_bg_color, 0.25);
        }

        .window-bar-label {
                color: @view_fg_color;
                font-weight: 600;
        }
        @keyframes chat_locked_pulse {
            0% { background-color: alpha(@view_fg_color, 0.06); }
            50% { background-color: alpha(@view_fg_color, 0.12); }
            100% { background-color: alpha(@view_fg_color, 0.06); }
        }
        .chat-locked {
                background-color: alpha(@view_fg_color, 0.06);
                animation: chat_locked_pulse 1.6s ease-in-out infinite;
        }
        '''
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css, -1)
        display = Gdk.Display.get_default() 
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        # Add custom icons directory to icon theme search path
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        if icon_theme is not None:
            import os
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            icons_dir = os.path.join(base, "data", "icons")
            if os.path.exists(icons_dir):
                icon_theme.add_search_path(icons_dir)

        # ── Accent color CSS provider (stored in JSON, no schema needed) ──
        self._accent_css_provider = Gtk.CssProvider()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._accent_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
            )
        self._apply_accent_color(self._load_accent_color())

        self.connect('activate', self.on_activate)
        action = Gio.SimpleAction.new("about", None)
        action.connect('activate', self.on_about_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("shortcuts", None)
        action.connect('activate', self.on_shortcuts_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("settings", None)
        action.connect('activate', self.settings_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("thread_editing", None)
        action.connect('activate', self.thread_editing_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("extension", None)
        action.connect('activate', self.extension_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("export_current_chat", None)
        action.connect('activate', self.export_current_chat_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("export_all_chats", None)
        action.connect('activate', self.export_all_chats_action)
        self.add_action(action)
        action = Gio.SimpleAction.new("import_chats", None)
        action.connect('activate', self.import_chats_action)
        self.add_action(action)
    
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def on_shortcuts_action(self, *a):
        shortcuts = Shortcuts(self)
        shortcuts.present()

    # ── Accent color helpers (JSON storage, no GSchema key needed) ────
    def _accent_config_path(self):
        import os
        return os.path.join(GLib.get_user_config_dir(), "zeroneai_accent.json")

    def _load_accent_color(self):
        import json, os
        try:
            with open(self._accent_config_path()) as f:
                return json.load(f).get("color", "#5D5CDE")
        except Exception:
            return "#5D5CDE"

    def save_accent_color(self, color: str):
        import json
        try:
            with open(self._accent_config_path(), "w") as f:
                json.dump({"color": color}, f)
        except Exception:
            pass
        self._apply_accent_color(color)

    def _apply_accent_color(self, color: str):
        """Apply a hex color as the app accent color via CSS override."""
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        except Exception:
            r, g, b = 93, 92, 222  # default #5D5CDE

        css = f"""
@define-color accent_color rgb({r},{g},{b});
@define-color accent_bg_color rgb({r},{g},{b});
@define-color accent_fg_color white;
.breadcrumb-home {{ color: rgb({r},{g},{b}); }}
.settings-tab-btn:checked {{ border-bottom-color: rgb({r},{g},{b}); color: rgb({r},{g},{b}); }}
.lib-tab-btn:checked {{ border-bottom-color: rgb({r},{g},{b}); color: rgb({r},{g},{b}); }}
.msg-action-btn {{ color: rgb({r},{g},{b}); }}
.msg-action-btn:hover {{ background-color: alpha(rgb({r},{g},{b}), 0.15); border-radius: 6px; }}
.user-bubble {{ background-color: rgb({r},{g},{b}); border-radius: 18px; padding: 10px 14px; color: white; }}
"""
        self._accent_css_provider.load_from_string(css)

    def on_about_action(self, *a):
        Adw.AboutWindow(transient_for=self.props.active_window,
                        application_name='ZERONE AI',
                        application_icon='com.zeroneai.app',
                        developer_name='AHMED',
                        version=self.version,
                        website='https://github.com/b2-3c',
                        developers=['AHMED https://github.com/b2-3c'],
                        copyright='© 2025 AHMED').present()

    def thread_editing_action(self, *a):
        threadediting = ThreadEditing(self)
        threadediting.present()

    def settings_action(self, *a):
        # Open settings as inline page
        if hasattr(self, "win"):
            self.win.open_settings_page()

    def settings_action_paged(self, page=None, *a):
        # Open settings as inline page (page selection not yet supported inline)
        if hasattr(self, "win"):
            self.win.open_settings_page()
    
    def close_settings(self, *a):
        settings = Gio.Settings.new('com.zeroneai.app')
        settings.set_int("chat", self.win.chat_id)
        settings.set_string("path", os.path.normpath(self.win.main_path))
        self.win.update_settings()
        self.settingswindow.destroy()
        return True

    def extension_action(self, *a):
        extension = Extension(self)
        def close(win):
            settings = Gio.Settings.new('com.zeroneai.app')
            settings.set_int("chat", self.win.chat_id)
            settings.set_string("path", os.path.normpath(self.win.main_path))
            self.win.update_settings()
            win.destroy()
            return True
        extension.connect("close-request", close) 
        extension.present()
    
    def export_current_chat_action(self, *a):
        """Export the current chat"""
        if hasattr(self, "win"):
            self.win.export_chat(export_all=False)
    
    def export_all_chats_action(self, *a):
        """Export all chats"""
        if hasattr(self, "win"):
            self.win.export_chat(export_all=True)
    
    def import_chats_action(self, *a):
        """Import chats from a file"""
        if hasattr(self, "win"):
            self.win.import_chat(None)
    
    def stdout_monitor_action(self, *a):
        """Show the stdout monitor dialog"""
        self.win.show_stdout_monitor_dialog()
    
    def close_window(self, *a):
        if hasattr(self,"mini_win"):
            self.mini_win.close()
        if all(element.poll() is not None for element in self.win.streams):
            settings = Gio.Settings.new('com.zeroneai.app')
            settings.set_int("window-width", self.win.get_width())
            settings.set_int("window-height", self.win.get_height())
            self.win.controller.close_application()
            return False
        else:
            dialog = Adw.MessageDialog(
                transient_for=self.win,
                heading=_("Terminal threads are still running in the background"),
                body=_("When you close the window, they will be automatically terminated"),
                body_use_markup=True
            )
            dialog.add_response("cancel", _("Cancel"))
            dialog.add_response("close", _("Close"))
            dialog.set_response_appearance("close", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.set_default_response("cancel")
            dialog.set_close_response("cancel")
            dialog.connect("response", self.close_message)
            dialog.present()
            return True
    
    def close_message(self,a,status):
        if status=="close":
            for i in self.win.streams:
                i.terminate()
            self.win.controller.close_application()
            self.win.destroy()
    
    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        if options.contains("run-action"):
            action_name = options.lookup_value("run-action").get_string()
            if self.lookup_action(action_name):
                self.activate_action(action_name, None)
            else:
                command_line.printerr(f"Action '{action_name}' not found.\n")
                return 1
        
        self.activate()
        return 0

    def apply_language(self):
        """Apply the selected language from settings"""
        import locale
        import gettext
        import os
        lang = self.settings.get_string("app-language")
        if lang == "system" or not lang:
            return
        # Find locale directory
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        locale_dir = os.path.join(base, "po", "locale")
        # Also try system locale dirs
        locale_dirs = [locale_dir, "/usr/share/locale", "/usr/local/share/locale"]
        for ldir in locale_dirs:
            if os.path.exists(os.path.join(ldir, lang, "LC_MESSAGES", "zeroneai.mo")):
                locale_dir = ldir
                break
        try:
            lang_obj = gettext.translation("zeroneai", localedir=locale_dir, languages=[lang])
            lang_obj.install()
            import builtins
            builtins._ = lang_obj.gettext
        except Exception as e:
            print(f"Language {lang} not available: {e}")

    def on_activate(self, app):
        self.apply_language()
        if not hasattr(self,"win"):
            self.win = MainWindow(application=app)
            self.win.connect("close-request", self.close_window)

        if self.settings.get_string("startup-mode") == "mini":
            if hasattr(self,"mini_win"):
                self.mini_win.close()
            self.mini_win = MiniWindow(application=self, main_window=self.win)
            self.mini_win.present()
            self.settings.set_string("startup-mode", "normal")
        else:
            self.win.present()

    def focus_message(self, *a):
        self.win.focus_input()

    def reload_chat(self,*a):
        self.win.show_chat()
        self.win.notification_block.add_toast(
                Adw.Toast(title=_('Chat is rebooted')))

    def reload_folder(self,*a):
        self.win.update_folder()
        self.win.notification_block.add_toast(
                Adw.Toast(title=_('Folder is rebooted')))

    def new_chat(self,*a):
        self.win.new_chat(None)
        self.win.notification_block.add_toast(
                Adw.Toast(title=_('Chat is created')))

    def start_recording(self,*a):
        if not self.win.recording:
            self.win.start_recording(self.win.recording_button)
        else:
            self.win.stop_recording(self.win.recording_button)

    def stop_tts(self,*a):
        self.win.mute_tts(self.win.mute_tts_button)

    def stop_chat(self, *a):
        if hasattr(self, "win") and not self.win.status:
            self.win.stop_chat()
    
    def do_shutdown(self):
        self.win.save_chat()
        settings = Gio.Settings.new('com.zeroneai.app')
        settings.set_int("chat", self.win.chat_id)
        settings.set_string("path", os.path.normpath(self.win.main_path))
        self.win.stream_number_variable += 1
        Gtk.Application.do_shutdown(self)
        os._exit(1)

    def zoom(self, *a):
        zoom = min(250, self.settings.get_int("zoom") + 10)
        self.win.set_zoom(zoom)
        self.settings.set_int("zoom", zoom)

    def zoom_out(self, *a):
        zoom = max(100, self.settings.get_int("zoom") - 10)
        self.win.set_zoom(zoom)
        self.settings.set_int("zoom", zoom)
    
    def save(self, *a):
        self.win.save()
    def pretty_print_chat(self, *a):
        for msg in self.win.chat:
            print(msg["User"], msg["Message"])
    def debug(self, *a):
        self.pretty_print_chat()

def main(version):
    app = MyApp(application_id="com.zeroneai.app", version = version)
    app.create_action('reload_chat', app.reload_chat, ['<primary>r'])
    app.create_action('reload_folder', app.reload_folder, ['<primary>e'])
    app.create_action('new_chat', app.new_chat, ['<primary>t'])
    app.create_action('focus_message', app.focus_message, ['<primary>l'])
    app.create_action('start_recording', app.start_recording, ['<primary>g'])
    app.create_action('stop_chat', app.stop_chat, ['<primary>q'])
    app.create_action('stop_tts', app.stop_tts, ['<primary>k'])
    app.create_action('save', app.save, ['<primary>s'])
    app.create_action('zoom', app.zoom, ['<primary>plus'])
    app.create_action('zoom', app.zoom, ['<primary>equal'])
    app.create_action('zoom_out', app.zoom_out, ['<primary>minus'])
    app.create_action('debug', app.debug, ['<primary>b'])
    app.run(sys.argv)

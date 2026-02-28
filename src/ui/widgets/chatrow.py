"""Chat row widget for Adwaita-styled chat history"""
import gettext
import unicodedata
from gi.repository import Adw, Gtk, Gio, Pango


class ChatRow(Gtk.ListBoxRow):
    """A chat row widget styled according to Adwaita HIG"""
    
    def __init__(self, chat_name: str, chat_index: int, is_selected: bool = False, level: int = 0, is_open: bool = False):
        super().__init__()
        self.chat_index = chat_index
        self.is_selected = is_selected
        self.level = level
        self.is_open = is_open

        # Process chat name
        processed_name = chat_name.replace("\n", " ").strip()
        words = processed_name.split()
        if len(words) > 8:
            processed_name = " ".join(words[:8]) + "..."
        else:
            processed_name = " ".join(words)
        self.chat_name = processed_name

        # Check for emoji/symbol at the beginning
        first_emoji = None
        if processed_name:
            first_char = processed_name[0]
            if unicodedata.category(first_char) in ["So", "Sk"]:
                first_emoji = first_char
                display_name = processed_name[1:].strip()
                if not display_name and len(words) > 1:
                    display_name = processed_name
            else:
                display_name = processed_name
        else:
            display_name = processed_name

        # Main container
        margin_start = 12 + (level * 20)
        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            margin_top=6,
            margin_bottom=6,
            margin_start=margin_start,
            margin_end=6,
        )
        self.set_child(self.main_box)

        # Chat icon
        if first_emoji:
            self.chat_icon = Gtk.Label(label=first_emoji)
            self.chat_icon.set_size_request(16, 16)
        else:
            self.chat_icon = Gtk.Image.new_from_icon_name("chat-bubbles-text-symbolic")
        self.chat_icon.add_css_class("dim-label")
        self.main_box.append(self.chat_icon)

        # Chat name label
        self.name_label = Gtk.Label(
            label=display_name,
            xalign=0,
            hexpand=True,
            ellipsize=Pango.EllipsizeMode.END,
            max_width_chars=30,
        )
        if chat_name != display_name:
            self.set_tooltip_text(chat_name)
        self.main_box.append(self.name_label)

        # Three-dot menu button (shown on hover)
        self.menu_revealer = Gtk.Revealer(
            transition_type=Gtk.RevealerTransitionType.SLIDE_LEFT,
            transition_duration=150,
            reveal_child=False,
        )
        self.main_box.append(self.menu_revealer)

        self.menu_button = Gtk.MenuButton(
            icon_name="view-more-symbolic",
            css_classes=["flat", "circular"],
            valign=Gtk.Align.CENTER,
        )
        self.menu_button.set_name(str(chat_index))
        self.menu_revealer.set_child(self.menu_button)

        # Stack for edit/generate (kept for API compatibility, not shown)
        self.edit_stack = Gtk.Stack()
        self.generate_button = Gtk.Button(name=str(chat_index))
        self.edit_button = Gtk.Button(name=str(chat_index))
        self.edit_stack.add_named(self.generate_button, "generate")
        self.edit_stack.add_named(self.edit_button, "edit")
        self.edit_stack.set_visible_child_name("edit")

        # Stub buttons for legacy signal connection
        self.clone_button  = Gtk.Button(name=str(chat_index))
        self.clear_button  = Gtk.Button(name=str(chat_index))
        self.delete_button = Gtk.Button(name=str(chat_index))

        # Apply selected styling
        if is_selected:
            self.add_css_class("chat-row-selected")
            if isinstance(self.chat_icon, Gtk.Image):
                self.chat_icon.set_from_icon_name("chat-bubbles-text-symbolic")
            self.chat_icon.remove_css_class("dim-label")
            self.chat_icon.add_css_class("accent")
            self.name_label.add_css_class("heading")
        else:
            self.add_css_class("chat-row")
            if is_open:
                self.add_css_class("chat-locked")
                self.name_label.add_css_class("window-bar-label")

        # Hover controllers
        hover_controller = Gtk.EventControllerMotion()
        hover_controller.connect("enter", self._on_hover_enter)
        hover_controller.connect("leave", self._on_hover_leave)
        self.add_controller(hover_controller)

    def _on_hover_enter(self, controller, x, y):
        self.menu_revealer.set_reveal_child(True)

    def _on_hover_leave(self, controller):
        if not self.menu_button.get_active():
            self.menu_revealer.set_reveal_child(False)

    def show_generate_button(self):
        self.edit_stack.set_visible_child_name("generate")

    def show_edit_button(self):
        self.edit_stack.set_visible_child_name("edit")

    def get_edit_stack(self) -> Gtk.Stack:
        return self.edit_stack

    def connect_signals(self, on_generate, on_edit, on_clone, on_clear, on_delete):
        """Connect all signal handlers via GAction and build popover menu."""
        # Store callbacks
        self._cb_generate = on_generate
        self._cb_edit     = on_edit
        self._cb_clone    = on_clone
        self._cb_clear    = on_clear
        self._cb_delete   = on_delete

        # Build GAction group
        action_group = Gio.SimpleActionGroup()

        def _add(name, cb):
            a = Gio.SimpleAction.new(name, None)
            a.connect("activate", lambda action, param, btn=self.menu_button: cb(btn))
            action_group.add_action(a)

        _add("edit-name",     on_edit)
        _add("generate-name", on_generate)
        _add("clone",         on_clone)
        _add("clear",         on_clear)
        _add("delete",        on_delete)

        self.insert_action_group("row", action_group)
        self._action_group = action_group

        # Build menu model
        menu = Gio.Menu()

        sec1 = Gio.Menu()
        sec1.append(_("Edit name"),      "row.edit-name")
        sec1.append(_("Generate name"),  "row.generate-name")
        menu.append_section(None, sec1)

        sec2 = Gio.Menu()
        sec2.append(_("Duplicate chat"), "row.clone")
        sec2.append(_("Clear chat"),     "row.clear")
        menu.append_section(None, sec2)

        sec3 = Gio.Menu()
        sec3.append(_("Delete chat"),    "row.delete")
        menu.append_section(None, sec3)

        self.menu_button.set_menu_model(menu)

        # Also wire stub buttons for any legacy callers
        self.generate_button.connect("clicked", on_generate)
        self.edit_button.connect("clicked", on_edit)
        self.clone_button.connect("clicked", on_clone)
        self.clear_button.connect("clicked", on_clear)
        self.delete_button.connect("clicked", on_delete)

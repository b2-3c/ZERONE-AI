"""
Library page for Zerone AI — card grid design matching the HTML reference.
"""
import json
import os
import datetime
import uuid

from gi.repository import Gtk, Adw, Gio, Pango, Gdk


class LibraryItem:
    def __init__(self, id=None, name="", item_type="template", content="",
                 timestamp=None, is_favorite=False, is_active=False):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.item_type = item_type
        self.content = content
        self.timestamp = timestamp or datetime.datetime.now().isoformat()
        self.is_favorite = is_favorite
        self.is_active = is_active

    def to_dict(self):
        return {"id": self.id, "name": self.name, "type": self.item_type,
                "content": self.content, "timestamp": self.timestamp,
                "isFavorite": self.is_favorite, "isActive": self.is_active}

    @classmethod
    def from_dict(cls, d):
        return cls(id=d.get("id"), name=d.get("name", ""),
                   item_type=d.get("type", "template"),
                   content=d.get("content", ""),
                   timestamp=d.get("timestamp"),
                   is_favorite=d.get("isFavorite", False),
                   is_active=d.get("isActive", False))


class LibraryManager:
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.library_path = os.path.join(config_dir, "library.json")
        self.items: list[LibraryItem] = []
        self.load()
        self._ensure_defaults()

    def load(self):
        try:
            if os.path.exists(self.library_path):
                with open(self.library_path, "r", encoding="utf-8") as f:
                    self.items = [LibraryItem.from_dict(d) for d in json.load(f)]
        except Exception as e:
            print(f"[Library] Error loading: {e}")
            self.items = []

    def save(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.library_path, "w", encoding="utf-8") as f:
                json.dump([i.to_dict() for i in self.items], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Library] Error saving: {e}")

    def _ensure_defaults(self):
        if not any(i.item_type == "template" for i in self.items):
            self.add_item(LibraryItem(name=_("Technical Article Writing"), item_type="template",
                content=_("Write a detailed technical article about [Topic] that includes:\n- Introduction\n- Core concepts\n- Practical examples\n- Conclusion")))
            self.add_item(LibraryItem(name=_("Data Analysis"), item_type="template",
                content=_("Analyze the following data:\n- Data summary\n- Key trends\n- Insights\n- Recommendations\n\nData: [Insert data here]")))
        if not any(i.item_type == "character" for i in self.items):
            self.add_item(LibraryItem(name=_("Patient Teacher"), item_type="character",
                content=_("You are a patient and understanding teacher. You explain concepts clearly using everyday examples.")))
            self.add_item(LibraryItem(name=_("Financial Analyst"), item_type="character",
                content=_("You are an expert financial analyst. You provide data-driven financial advice and explain complex concepts clearly.")))
        self.save()

    def add_item(self, item):
        self.items.insert(0, item)
        self.save()
        return item

    def update_item(self, item_id, **kwargs):
        for item in self.items:
            if item.id == item_id:
                for k, v in kwargs.items():
                    setattr(item, k, v)
                self.save()
                return True
        return False

    def delete_item(self, item_id):
        self.items = [i for i in self.items if i.id != item_id]
        self.save()

    def toggle_favorite(self, item_id):
        for item in self.items:
            if item.id == item_id:
                item.is_favorite = not item.is_favorite
                self.save()
                return item.is_favorite
        return False

    def activate_character(self, item_id):
        for item in self.items:
            if item.item_type == "character":
                item.is_active = (item.id == item_id)
        self.save()

    def deactivate_character(self, item_id):
        for item in self.items:
            if item.id == item_id:
                item.is_active = False
        self.save()

    def get_active_character(self):
        for item in self.items:
            if item.item_type == "character" and item.is_active:
                return item
        return None

    def get_by_type(self, tab):
        if tab == "all":        return list(self.items)
        if tab == "favorites":  return [i for i in self.items if i.is_favorite]
        if tab == "templates":  return [i for i in self.items if i.item_type == "template"]
        if tab == "characters": return [i for i in self.items if i.item_type == "character"]
        if tab == "bag":        return [i for i in self.items if i.item_type == "bag"]
        if tab == "files":      return [i for i in self.items if i.item_type == "file"]
        return []

    def search(self, query, tab):
        items = self.get_by_type(tab)
        if not query:
            return items
        q = query.lower()
        return [i for i in items if q in i.name.lower() or q in i.content.lower()]

    def get_templates(self):
        return [i for i in self.items if i.item_type == "template"]


# ── Badge CSS (matching HTML .badge-template etc.) ──────────────────────────

_BADGE_CSS = """
/* ── Compact badge pills ── */
.badge-template  { background: #dbeafe; color: #1e40af; border-radius:999px;
                   padding:1px 8px; font-size:11px; font-weight:600; }
.badge-character { background: #dcfce7; color: #166534; border-radius:999px;
                   padding:1px 8px; font-size:11px; font-weight:600; }
.badge-bag       { background: #fef3c7; color: #92400e; border-radius:999px;
                   padding:1px 8px; font-size:11px; font-weight:600; }
.badge-file      { background: #fce7f3; color: #be185d; border-radius:999px;
                   padding:1px 8px; font-size:11px; font-weight:600; }
.badge-active    { background: #d1fae5; color: #065f46; border-radius:999px;
                   padding:1px 8px; font-size:11px; font-weight:600; }

/* ── Library card ── */
.lib-card {
    border-radius: 12px;
    border: 1px solid alpha(@borders, 0.6);
}
.lib-card:hover {
    border-color: @accent_color;
}

/* ── Compact library action buttons ── */
.lib-action-btn {
    min-height: 26px;
    padding: 2px 12px;
    font-size: 12px;
    border-radius: 999px;
}

/* ── Library tab buttons — same underline style as settings ── */
.lib-tab-btn {
    border-radius: 0px;
    border-bottom: 2px solid transparent;
    min-height: 38px;
    padding: 4px 16px;
    font-size: 13px;
    font-weight: 500;
}
.lib-tab-btn:checked {
    border-bottom-color: @accent_color;
    color: @accent_color;
}
.lib-tab-btn:not(:checked) { opacity: 0.65; }

/* ── Compact flat circular icon buttons ── */
.lib-icon-btn {
    min-width: 28px;
    min-height: 28px;
    padding: 2px;
}

/* ── Breadcrumb ── */
.breadcrumb-home {
    font-size: 13px;
    padding: 0px 4px;
    min-height: 0px;
    color: @accent_color;
}
.breadcrumb-current {
    font-size: 13px;
    opacity: 0.65;
}
.breadcrumb-sep {
    font-size: 13px;
    opacity: 0.4;
}
"""
_css_installed = False
def _ensure_css():
    global _css_installed
    if not _css_installed:
        provider = Gtk.CssProvider()
        provider.load_from_string(_BADGE_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        _css_installed = True

TYPE_BADGE = {
    "template":  (_("Template"),  "template"),
    "character": (_("Character"), "character"),
    "bag":       (_("Bag"),       "bag"),
    "file":      (_("File"),      "file"),
}


# ── Card widget ──────────────────────────────────────────────────────────────

class LibraryCard(Gtk.Frame):
    def __init__(self, item: LibraryItem, manager: LibraryManager,
                 on_refresh, on_use_template, on_use_character):
        super().__init__(css_classes=["card", "lib-card"])
        self.item = item
        self.manager = manager
        self.on_refresh = on_refresh
        self.on_use_template = on_use_template
        self.on_use_character = on_use_character

        # Compact outer box
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                        margin_start=12, margin_end=12,
                        margin_top=10, margin_bottom=10)
        self.set_child(outer)

        # Row 1: badge + active badge + spacer + compact fav + compact options
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        outer.append(top_row)

        badge_label, badge_css = TYPE_BADGE.get(item.item_type, (_("Unknown"), "file"))
        badge = Gtk.Label(label=badge_label, css_classes=["badge-" + badge_css], xalign=0)
        top_row.append(badge)

        if item.is_active and item.item_type == "character":
            top_row.append(Gtk.Label(label=_("Active"), css_classes=["badge-active"]))

        top_row.append(Gtk.Box(hexpand=True))  # spacer

        fav_btn = Gtk.Button(css_classes=["flat", "circular", "lib-icon-btn"],
                             valign=Gtk.Align.CENTER)
        fav_icon = Gtk.Image(icon_name="starred-symbolic" if item.is_favorite else "non-starred-symbolic",
                             pixel_size=14)
        fav_btn.set_child(fav_icon)
        if item.is_favorite:
            fav_btn.add_css_class("accent")
        fav_btn.connect("clicked", lambda *a: (self.manager.toggle_favorite(item.id), on_refresh()))
        top_row.append(fav_btn)

        opts_btn = Gtk.MenuButton(css_classes=["flat", "circular", "lib-icon-btn"],
                                  valign=Gtk.Align.CENTER)
        opts_icon = Gtk.Image(icon_name="view-more-symbolic", pixel_size=14)
        opts_btn.set_child(opts_icon)
        popover = Gtk.PopoverMenu()
        menu = Gio.Menu()
        menu.append(_("Edit"),   "card.edit")
        menu.append(_("Delete"), "card.delete")
        popover.set_menu_model(menu)
        opts_btn.set_popover(popover)
        top_row.append(opts_btn)

        ag = Gio.SimpleActionGroup()
        edit_a = Gio.SimpleAction.new("edit", None)
        edit_a.connect("activate", lambda *a: self._on_edit())
        ag.add_action(edit_a)
        del_a = Gio.SimpleAction.new("delete", None)
        del_a.connect("activate", lambda *a: self._on_delete())
        ag.add_action(del_a)
        self.insert_action_group("card", ag)

        # Row 2: name — compact
        outer.append(Gtk.Label(label=item.name, xalign=0,
                               css_classes=["body"],
                               wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR,
                               max_width_chars=40))

        # Row 3: content preview — small text, 2 lines max
        preview = item.content[:100] + ("…" if len(item.content) > 100 else "")
        outer.append(Gtk.Label(label=preview, xalign=0,
                               css_classes=["caption", "dim-label"],
                               wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR,
                               lines=2, ellipsize=Pango.EllipsizeMode.END,
                               max_width_chars=50))

        # Row 4: date + compact action button
        bot_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        outer.append(bot_row)

        try:
            date_str = datetime.datetime.fromisoformat(item.timestamp).strftime("%Y-%m-%d")
        except Exception:
            date_str = ""
        bot_row.append(Gtk.Label(label=date_str, css_classes=["caption", "dim-label"],
                                 hexpand=True, xalign=0))

        action = self._make_action_btn()
        if action:
            bot_row.append(action)

    def _make_action_btn(self):
        t = self.item.item_type
        if t == "template":
            btn = Gtk.Button(label=_("Use"),
                             css_classes=["suggested-action", "lib-action-btn"])
            btn.connect("clicked", lambda *a: self.on_use_template(self.item))
        elif t == "character":
            if self.item.is_active:
                btn = Gtk.Button(label=_("Deactivate"),
                                 css_classes=["lib-action-btn"])
            else:
                btn = Gtk.Button(label=_("Activate"),
                                 css_classes=["suggested-action", "lib-action-btn"])
            btn.connect("clicked", self._on_toggle_char)
        elif t == "bag":
            btn = Gtk.Button(label=_("Copy"), css_classes=["lib-action-btn"])
            btn.connect("clicked", self._on_copy)
        else:
            return None
        return btn

    def _on_toggle_char(self, btn):
        if self.item.is_active:
            self.manager.deactivate_character(self.item.id)
        else:
            self.manager.activate_character(self.item.id)
        self.on_refresh()
        if self.on_use_character:
            self.on_use_character(self.manager.get_active_character())

    def _on_copy(self, btn):
        display = Gdk.Display.get_default()
        if display:
            display.get_clipboard().set_content(
                Gdk.ContentProvider.new_for_value(self.item.content))

    def _on_edit(self):
        def on_save(d):
            self.manager.update_item(self.item.id,
                                     name=d.get_name(), content=d.get_content())
            self.on_refresh()
        ItemEditDialog(parent=self.get_root(), item=self.item, on_save=on_save).present()

    def _on_delete(self):
        dlg = Adw.MessageDialog(transient_for=self.get_root(), modal=True,
                                heading=_("Delete Item"),
                                body=_("Are you sure?"))
        dlg.add_response("cancel", _("Cancel"))
        dlg.add_response("delete", _("Delete"))
        dlg.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.connect("response", lambda d, r:
                    (self.manager.delete_item(self.item.id), self.on_refresh())
                    if r == "delete" else None)
        dlg.present()


# ── Edit / Add dialog ────────────────────────────────────────────────────────

class ItemEditDialog(Adw.Dialog):
    def __init__(self, parent, item: LibraryItem = None, on_save=None):
        super().__init__()
        self.item = item
        self.is_edit = item is not None
        self.on_save = on_save
        self.set_title(_("Edit Item") if self.is_edit else _("Add Item"))
        self.set_content_width(460)
        self.set_content_height(420)

        tv = Adw.ToolbarView()
        self.set_child(tv)
        header = Adw.HeaderBar()
        tv.add_top_bar(header)

        cancel = Gtk.Button(label=_("Cancel"), css_classes=["flat"])
        cancel.connect("clicked", lambda *_: self.close())
        header.pack_start(cancel)

        save = Gtk.Button(label=_("Save"), css_classes=["suggested-action"])
        save.connect("clicked", self._do_save)
        header.pack_end(save)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        tv.set_content(scroll)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_start=16, margin_end=16,
                      margin_top=16, margin_bottom=16)
        scroll.set_child(box)

        if not self.is_edit:
            type_grp = Adw.PreferencesGroup(title=_("Type"))
            self.type_combo = Adw.ComboRow(title=_("Category"))
            self.type_combo.set_model(
                Gtk.StringList.new([_("Template"), _("Character"), _("Bag"), _("File")]))
            type_grp.add(self.type_combo)
            box.append(type_grp)

        name_grp = Adw.PreferencesGroup(title=_("Name"))
        self.name_entry = Adw.EntryRow(title=_("Item name"))
        if self.is_edit:
            self.name_entry.set_text(item.name)
        name_grp.add(self.name_entry)
        box.append(name_grp)

        content_grp = Adw.PreferencesGroup(title=_("Content"))
        frame = Gtk.Frame(css_classes=["card"])
        sw = Gtk.ScrolledWindow(min_content_height=120)
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content_text = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                         margin_start=8, margin_end=8,
                                         margin_top=8, margin_bottom=8)
        if self.is_edit:
            self.content_text.get_buffer().set_text(item.content)
        sw.set_child(self.content_text)
        frame.set_child(sw)
        content_grp.add(frame)
        box.append(content_grp)

    def _do_save(self, btn):
        if self.on_save:
            self.on_save(self)
        self.close()

    def get_name(self):
        return self.name_entry.get_text().strip()

    def get_type(self):
        if self.is_edit:
            return self.item.item_type
        return ["template", "character", "bag", "file"][self.type_combo.get_selected()]

    def get_content(self):
        buf = self.content_text.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True).strip()


# ── Main Library Page ────────────────────────────────────────────────────────

class LibraryWindow(Gtk.Box):
    TABS = [
        ("all",        _("All")),
        ("favorites",  _("Favorites")),
        ("templates",  _("Templates")),
        ("characters", _("Characters")),
        ("bag",        _("Bag")),
        ("files",      _("Files")),
    ]

    def __init__(self, manager: LibraryManager,
                 on_use_template=None, on_use_character=None,
                 on_close=None, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        _ensure_css()
        self.manager = manager
        self.on_use_template = on_use_template
        self.on_use_character = on_use_character
        self.on_close = on_close
        self.current_tab = "all"
        self.search_query = ""
        self._build()
        self._load_items()

    def _build(self):
        # ── Header: breadcrumb (start) + title (center) + actions (end) ──
        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8,
                             margin_start=16, margin_end=16,
                             margin_top=10, margin_bottom=6)
        self.append(header_row)

        # Breadcrumb on the LEFT
        crumb_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        home_btn = Gtk.Button(label=_("Home"), css_classes=["flat", "breadcrumb-home"])
        home_btn.connect("clicked", lambda *_: self.on_close() if self.on_close else None)
        crumb_box.append(home_btn)
        crumb_box.append(Gtk.Label(label="›", css_classes=["breadcrumb-sep"]))
        crumb_box.append(Gtk.Label(label=_("Library"), css_classes=["breadcrumb-current"]))
        header_row.append(crumb_box)

        # Title in CENTER
        header_row.append(Gtk.Label(label=_("My Library"),
                                    css_classes=["title"],
                                    halign=Gtk.Align.CENTER,
                                    hexpand=True))

        # Actions on the RIGHT
        self.search_btn = Gtk.ToggleButton(icon_name="system-search-symbolic",
                                           css_classes=["flat", "circular"])
        self.search_btn.connect("toggled", self._on_search_toggled)
        header_row.append(self.search_btn)

        add_btn = Gtk.Button(label=_("Add Item"), css_classes=["suggested-action", "pill"])
        add_btn.connect("clicked", self._on_add_item)
        header_row.append(add_btn)

        # Search bar
        self.search_bar = Gtk.SearchBar(show_close_button=False)
        self.search_entry = Gtk.SearchEntry(placeholder_text=_("Search library…"), hexpand=True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_bar.set_child(self.search_entry)
        self.search_bar.connect_entry(self.search_entry)
        self.search_btn.connect("toggled",
            lambda btn: (
                self.search_bar.set_search_mode(btn.get_active()),
                self.search_entry.grab_focus() if btn.get_active() else None
            ))
        self.append(self.search_bar)

        # Tab bar
        tab_scroll = Gtk.ScrolledWindow()
        tab_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0,
                          margin_start=16, margin_end=16)
        tab_scroll.set_child(tab_box)
        self.append(tab_scroll)
        self.append(Gtk.Separator())

        self.tab_buttons = {}
        group_btn = None
        for tab_id, tab_label in self.TABS:
            btn = Gtk.ToggleButton(label=tab_label, active=(tab_id == "all"),
                                   css_classes=["flat", "lib-tab-btn"],
                                   margin_top=2, margin_bottom=2)
            if group_btn is None:
                group_btn = btn
            else:
                btn.set_group(group_btn)
            btn.connect("toggled", self._on_tab_toggled, tab_id)
            tab_box.append(btn)
            self.tab_buttons[tab_id] = btn

        # Scrollable card grid
        outer_scroll = Gtk.ScrolledWindow(vexpand=True)
        outer_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.append(outer_scroll)

        self.grid = Gtk.FlowBox(
            valign=Gtk.Align.START,
            max_children_per_line=4,
            min_children_per_line=1,
            selection_mode=Gtk.SelectionMode.NONE,
            row_spacing=10, column_spacing=10,
            margin_start=12, margin_end=12,
            margin_top=12, margin_bottom=12,
            homogeneous=True,
        )
        outer_scroll.set_child(self.grid)

        # Empty state
        self.empty_state = Adw.StatusPage(
            title=_("No Items"),
            description=_("Add items to your library to get started"),
            icon_name="user-bookmarks-symbolic",
            vexpand=True)
        self.empty_state.set_visible(False)
        self.append(self.empty_state)

    def _on_tab_toggled(self, btn, tab_id):
        if btn.get_active():
            self.current_tab = tab_id
            self._load_items()

    def _on_search_toggled(self, btn):
        if not btn.get_active():
            self.search_entry.set_text("")
            self.search_query = ""
            self._load_items()

    def _on_search_changed(self, entry):
        self.search_query = entry.get_text()
        self._load_items()

    def _load_items(self):
        while self.grid.get_first_child():
            self.grid.remove(self.grid.get_first_child())

        items = self.manager.search(self.search_query, self.current_tab)

        if not items:
            self.grid.set_visible(False)
            self.empty_state.set_visible(True)
            self.empty_state.set_description(
                _("No items match your search") if self.search_query
                else _("Add items to your library to get started"))
            return

        self.grid.set_visible(True)
        self.empty_state.set_visible(False)

        for item in items:
            card = LibraryCard(
                item=item, manager=self.manager,
                on_refresh=self._load_items,
                on_use_template=self._handle_use_template,
                on_use_character=self._handle_use_character)
            self.grid.append(card)

    def _handle_use_template(self, item: LibraryItem):
        if self.on_use_template:
            self.on_use_template(item.content)
        if self.on_close:
            self.on_close()

    def _handle_use_character(self, character):
        if self.on_use_character:
            self.on_use_character(character)

    def _on_add_item(self, btn):
        def on_save(dialog):
            name = dialog.get_name()
            content = dialog.get_content()
            item_type = dialog.get_type()
            if name and content:
                self.manager.add_item(LibraryItem(name=name, item_type=item_type, content=content))
                self._load_items()
        ItemEditDialog(parent=self.get_root(), on_save=on_save).present()


# ── Template picker ──────────────────────────────────────────────────────────

class TemplatePickerDialog(Adw.Dialog):
    def __init__(self, manager: LibraryManager, on_select, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.on_select = on_select
        self.set_title(_("Choose Template"))
        self.set_content_width(420)
        self.set_content_height(380)
        self._build()
        self._load()

    def _build(self):
        tv = Adw.ToolbarView()
        self.set_child(tv)
        header = Adw.HeaderBar(css_classes=["flat"])
        tv.add_top_bar(header)
        close_btn = Gtk.Button(label=_("Close"), css_classes=["flat"])
        close_btn.connect("clicked", lambda *_: self.close())
        header.pack_start(close_btn)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                      margin_start=12, margin_end=12,
                      margin_top=12, margin_bottom=12)
        tv.set_content(box)

        self.search = Gtk.SearchEntry(placeholder_text=_("Search templates…"))
        self.search.connect("search-changed", self._on_search)
        box.append(self.search)

        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.listbox = Gtk.ListBox(css_classes=["boxed-list"],
                                   selection_mode=Gtk.SelectionMode.NONE)
        scroll.set_child(self.listbox)
        box.append(scroll)

    def _load(self, query=""):
        while self.listbox.get_first_child():
            self.listbox.remove(self.listbox.get_first_child())
        templates = self.manager.get_templates()
        if query:
            templates = [t for t in templates
                         if query.lower() in t.name.lower()
                         or query.lower() in t.content.lower()]
        for t in templates:
            row = Adw.ActionRow(
                title=t.name,
                subtitle=(t.content[:60] + "…") if len(t.content) > 60 else t.content,
                activatable=True)
            row.set_name(t.id)
            row.connect("activated", self._on_activated, t)
            self.listbox.append(row)

    def _on_search(self, entry):
        self._load(entry.get_text())

    def _on_activated(self, row, item):
        if self.on_select:
            self.on_select(item.content)
        self.close()

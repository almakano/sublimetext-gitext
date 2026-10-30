import html
import json
import os
import re

import sublime
import sublime_plugin

from .lib.git import find_folder, get_git_status, run_git_command
from .lib.ui import show_popup

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
ADDED_SCOPE = "gitext.diff.added"
SCHEME_NAME = "gitext_diff.sublime-color-scheme"
SCHEME_PATH = "Packages/User/" + SCHEME_NAME
SCHEME_CACHE = {"content": None}
PHANTOM_SETS = {}


def global_color_scheme():
    return sublime.load_settings("Preferences.sublime-settings").get("color_scheme")


def parse_scheme(raw):
    try:
        return json.loads(raw.lstrip("\ufeff"))
    except Exception:
        pass
    cleaned = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
    cleaned = re.sub(r",\s*}", "}", cleaned)
    cleaned = re.sub(r",\s*\]", "]", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        return None


def build_scheme(base):
    """Схема на основе base с правилом для добавленных строк."""
    name = os.path.basename(base or "")
    if not name or name == SCHEME_NAME:
        return None
    merged = {"name": "GitExt Diff", "variables": {}, "globals": {}, "rules": []}
    loaded = 0
    paths = sorted(sublime.find_resources(name), key=lambda p: p.startswith("Packages/User/"))
    for path in paths:
        try:
            data = parse_scheme(sublime.load_resource(path))
        except Exception:
            continue
        if not data:
            continue
        loaded += 1
        merged["variables"].update(data.get("variables") or {})
        merged["globals"].update(data.get("globals") or {})
        merged["rules"].extend(data.get("rules") or [])
    if not loaded:
        return None
    merged["rules"].append({"scope": ADDED_SCOPE, "background": "#123a1c"})
    return json.dumps(merged, indent=2)


def write_scheme(content):
    path = os.path.join(sublime.packages_path(), "User", SCHEME_NAME)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        return False
    SCHEME_CACHE["content"] = content
    return True


def ensure_scheme():
    """Создаёт схему при старте, чтобы путь из сохранённой сессии находился."""
    content = build_scheme(global_color_scheme())
    path = os.path.join(sublime.packages_path(), "User", SCHEME_NAME)
    if content and (content != SCHEME_CACHE["content"] or not os.path.exists(path)):
        write_scheme(content)


def fix_view_scheme(view):
    """Убирает из сессии устаревшее имя схемы пакета."""
    scheme = view.settings().get("color_scheme") or ""
    if os.path.basename(scheme) != SCHEME_NAME or scheme == SCHEME_PATH:
        return
    view.settings().erase("color_scheme")


class GitextDiffTabCommand(sublime_plugin.TextCommand):
    def run(self, edit, silent=False):
        self.silent = silent
        file_path = self.view.file_name()
        window = self.view.window()
        if not file_path:
            if not silent:
                show_popup(window, "File must be saved")
            return

        folder = find_folder(window, file_path)
        if not folder:
            if not silent:
                show_popup(window, "File not in project folder")
            return

        rel_path = os.path.relpath(file_path, folder).replace("\\", "/")
        run_git_command(["diff", "--no-color", "-U0", "--", rel_path], folder, self.show_diff)

    def show_diff(self, output, error):
        window = self.view.window()
        if not window:
            return
        self.clear_marks()
        if error:
            if not self.silent:
                show_popup(window, error, "Error")
            return

        hunks = self.parse_hunks(output or "")
        if not hunks:
            if not self.silent:
                show_popup(window, "No changes", "Git Diff")
            return

        lines = self.view.lines(sublime.Region(0, self.view.size()))
        added = []
        phantoms = []
        for hunk in hunks:
            start = hunk["start"] - 1
            for region in lines[start:start + hunk["count"]]:
                end = region.end() + 1 if region.end() < self.view.size() else region.end()
                added.append(sublime.Region(region.begin(), end))
            if hunk["deleted"] and hasattr(sublime, "PhantomSet"):
                insert_at = start if hunk["count"] else start + 1
                anchor = lines[max(0, min(insert_at - 1, len(lines) - 1))] if lines else sublime.Region(0, 0)
                phantoms.append(sublime.Phantom(anchor, self.deleted_html(hunk["deleted"]), sublime.LAYOUT_BLOCK))

        scheme = self.prepare_scheme() if added else None
        if scheme:
            self.view.settings().set("color_scheme", scheme)
        self.view.add_regions("gitext_added", added, ADDED_SCOPE if scheme else "region.greenish", flags=sublime.DRAW_NO_OUTLINE)
        if phantoms:
            phantom_set = PHANTOM_SETS.get(self.view.id())
            if phantom_set is None:
                phantom_set = sublime.PhantomSet(self.view, "gitext_diff")
                PHANTOM_SETS[self.view.id()] = phantom_set
            phantom_set.update(phantoms)

    def clear_marks(self):
        self.view.erase_regions("gitext_added")
        phantom_set = PHANTOM_SETS.get(self.view.id())
        if phantom_set is not None:
            phantom_set.update([])
        if os.path.basename(self.view.settings().get("color_scheme") or "") == SCHEME_NAME:
            self.view.settings().erase("color_scheme")

    def deleted_html(self, deleted):
        rows = "".join(
            '<div class="del">{}</div>'.format(html.escape(line.replace("\t", "    ")) or "&nbsp;")
            for line in deleted
        )
        return (
            '<body id="gitext-diff">'
            '<style>div.del { background-color: #451317; color: #f8f8f2; margin: 0; '
            'font-family: monospace; white-space: pre; }</style>'
            + rows
            + '</body>'
        )

    def parse_hunks(self, output):
        hunks = []
        current = None
        for line in output.splitlines():
            match = HUNK_RE.match(line)
            if match:
                count = match.group(2)
                current = {
                    "start": int(match.group(1)),
                    "count": int(count) if count is not None else 1,
                    "deleted": [],
                }
                hunks.append(current)
            elif current is not None and line.startswith("-"):
                current["deleted"].append(line[1:])
        return hunks

    def prepare_scheme(self):
        base = self.view.settings().get("color_scheme")
        if not base or os.path.basename(base) == SCHEME_NAME:
            base = global_color_scheme()
        content = build_scheme(base)
        if content is None:
            return None
        path = os.path.join(sublime.packages_path(), "User", SCHEME_NAME)
        if content != SCHEME_CACHE["content"] or not os.path.exists(path):
            if not write_scheme(content):
                return None
        return SCHEME_PATH

    def is_enabled(self):
        window = self.view.window()
        if not window or not self.view.file_name():
            return False
        folder = find_folder(window, self.view.file_name())
        return bool(folder) and 'not a git repository' not in get_git_status(folder)


class GitextDiffTabListener(sublime_plugin.EventListener):
    def on_load_async(self, view):
        fix_view_scheme(view)
        if not sublime.load_settings("GitExt.sublime-settings").get("show_gitdiff_on_open", True):
            return
        window = view.window()
        if not window or not view.file_name():
            return
        folder = find_folder(window, view.file_name())
        if not folder or 'not a git repository' in get_git_status(folder):
            return
        view.run_command("gitext_diff_tab", {"silent": True})

    def on_activated_async(self, view):
        fix_view_scheme(view)


def plugin_loaded():
    ensure_scheme()
    for window in sublime.windows():
        for view in window.views():
            fix_view_scheme(view)

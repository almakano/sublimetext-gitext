import os

import sublime_plugin

from .lib.ui import show_popup


class GitextConfigCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0] if self.window.folders() else None
        if not folder:
            return
        config_path = os.path.join(folder, ".git", "config")
        if os.path.exists(config_path):
            self.window.open_file(config_path)
        else:
            show_popup(self.window, "No .git/config file found")

    def is_enabled(self):
        return bool(self.window.folders())

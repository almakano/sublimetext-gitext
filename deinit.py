import os
import shutil

import sublime_plugin

from .lib.git import get_git_status
from .lib.ui import show_popup


class GitextDeinitCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0] if self.window.folders() else None
        if not folder:
            show_popup(self.window, "No folder open", "Error")
            return

        git_dir = os.path.join(folder, ".git")
        if not os.path.exists(git_dir):
            show_popup(self.window, "No .git directory found", "Error")
            return

        self.folder = folder
        self.window.show_quick_panel(["Yes, remove .git", "No, cancel"], self.on_confirm)

    def on_confirm(self, index):
        if index != 0:
            show_popup(self.window, "Git deinit canceled", "Canceled")
            return

        git_dir = os.path.join(self.folder, ".git")
        try:
            shutil.rmtree(git_dir)
            show_popup(self.window, ".git directory removed", "Git Deinit")
        except Exception as e:
            show_popup(self.window, str(e), "Error")

    def is_enabled(self):
        if not self.window.folders():
            return False
        return 'not a git repository' not in get_git_status(self.window.folders()[0])

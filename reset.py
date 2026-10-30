import sublime_plugin

from .lib.git import run_git_command
from .lib.ui import show_popup


class GitextResetCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0] if self.window.folders() else None
        if not folder:
            show_popup(self.window, "No folder open", "Error")
            return
        run_git_command(["reset"], folder, lambda o, e: show_popup(self.window, o if o else e, "Git Reset"))

    def is_enabled(self):
        return bool(self.window.folders())

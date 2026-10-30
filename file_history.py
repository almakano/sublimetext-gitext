import os

import sublime_plugin

from .lib.git import run_git_command
from .lib.ui import show_popup


class GitextFileHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = self.view.file_name()
        if not file_path:
            show_popup(self.view.window(), "File must be saved")
            return

        folder = self.view.window().folders()[0] if self.view.window().folders() else None
        if not folder or not file_path.startswith(folder):
            show_popup(self.view.window(), "File not in project folder")
            return

        rel_path = os.path.relpath(file_path, folder)

        def callback(output, error):
            if error:
                show_popup(self.view.window(), error, "Error")
                return

            new_view = self.view.window().new_file()
            new_view.set_name("History — " + os.path.basename(rel_path))
            new_view.set_syntax_file("Packages/Git Formats/Git Log.sublime-syntax")
            new_view.set_scratch(True)
            new_view.run_command("append", {"characters": output})

        run_git_command(["log", "-p", "--", rel_path], folder, callback)

    def is_enabled(self):
        return bool(self.view.file_name())

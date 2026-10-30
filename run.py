import os
import subprocess

import sublime
import sublime_plugin

from .lib.git import windows_startupinfo


class GitextRunCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = self.view.file_name()
        if not file_path or not os.path.exists(file_path):
            return

        if sublime.platform() == "windows":
            os.startfile(file_path)
        elif sublime.platform() == "osx":
            subprocess.Popen(["open", file_path], startupinfo=windows_startupinfo())
        else:
            subprocess.Popen(["xdg-open", file_path], startupinfo=windows_startupinfo())

    def is_enabled(self):
        return bool(self.view.file_name())

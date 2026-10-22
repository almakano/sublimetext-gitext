import sublime_plugin

from .GitExt import run_git_command, show_popup


class GitextPullCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0]
        run_git_command(["pull"], folder, lambda output, error: show_popup(self.window, output if output else error, "Git Pull" if output else "Error"))

    def is_enabled(self):
        return bool(self.window.folders())

import sublime_plugin

from .GitExt import get_git_status_lines, resolve_folder, run_git_command, show_popup


def has_staged_changes(folder):
    """Есть ли изменения в индексе: git commit -m."""
    return any(line[0] not in " ?" for line in get_git_status_lines(folder))


def has_tracked_changes(folder):
    """Есть ли изменения отслеживаемых файлов: git commit -am."""
    return any(not line.startswith("??") for line in get_git_status_lines(folder))


class GitextCommitCommand(sublime_plugin.WindowCommand):
    """Коммит файлов из индекса: git commit -m."""

    def run(self, paths=None):
        folder = resolve_folder(self.window, paths)
        if not folder:
            show_popup(self.window, "No folder open", "Error")
            return

        self.folder = folder
        self.window.show_input_panel("Commit message (-m):", "", self.do_commit, None, None)

    def do_commit(self, message):
        if not message.strip():
            show_popup(self.window, "Empty commit message", "Git Commit")
            return
        run_git_command(["commit", "-m", message], self.folder, self.done)

    def done(self, output, error):
        show_popup(self.window, output if output else error, "Git Commit")

    def is_enabled(self, paths=None):
        folder = resolve_folder(self.window, paths)
        return bool(folder and has_staged_changes(folder))


class GitextCommitAllCommand(sublime_plugin.WindowCommand):
    """Коммит всех изменений отслеживаемых файлов: git commit -am."""

    def run(self, paths=None):
        folder = resolve_folder(self.window, paths)
        if not folder:
            show_popup(self.window, "No folder open", "Error")
            return

        self.folder = folder
        self.window.show_input_panel("Commit message (-am):", "", self.do_commit, None, None)

    def do_commit(self, message):
        if not message.strip():
            show_popup(self.window, "Empty commit message", "Git Commit")
            return
        run_git_command(["commit", "-am", message], self.folder, self.done)

    def done(self, output, error):
        show_popup(self.window, output if output else error, "Git Commit")

    def is_enabled(self, paths=None):
        folder = resolve_folder(self.window, paths)
        return bool(folder and has_tracked_changes(folder))

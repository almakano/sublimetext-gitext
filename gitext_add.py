import os

import sublime_plugin

from .GitExt import find_folder, get_git_status, get_git_status_lines, resolve_folder, run_git_command, show_popup


def git_rel_paths(window, paths):
    """Папка репозитория и пути файлов относительно неё."""
    folder = find_folder(window, paths[0]) if paths else None
    if not folder:
        return None, []

    rel_paths = [
        os.path.relpath(path, folder).replace("\\", "/")
        for path in paths
        if find_folder(window, path) == folder
    ]
    return folder, rel_paths


def has_changes_to_add(folder, rel_paths):
    """Есть ли у путей неиндексированные изменения или они новые."""
    for line in get_git_status_lines(folder):
        is_untracked = line.startswith("??")
        if not is_untracked and line[1] in " ?":
            continue
        path = line[3:].rsplit(" -> ", 1)[-1].strip('"')
        for rel_path in rel_paths:
            if rel_path == "." or path == rel_path or path.startswith(rel_path.rstrip("/") + "/"):
                return True
    return False


class GitextAddFileCommand(sublime_plugin.WindowCommand):
    """Добавляет в индекс текущий файл или выбранные в сайдбаре пути."""

    def run(self, paths=None):
        paths = paths or self.current_paths()
        if not paths:
            show_popup(self.window, "File must be saved", "GitExt")
            return

        folder, rel_paths = git_rel_paths(self.window, paths)
        if not folder:
            show_popup(self.window, "File not in project folder", "Error")
            return
        if not rel_paths:
            show_popup(self.window, "Selection is not in the project folder", "Error")
            return

        self.rel_paths = rel_paths
        run_git_command(["add", "--"] + rel_paths, folder, self.done)

    def current_paths(self):
        view = self.window.active_view()
        if view and view.file_name():
            return [view.file_name()]
        return []

    def done(self, output, error):
        if error:
            show_popup(self.window, error, "Error")
        else:
            self.window.status_message("GitExt: added " + ", ".join(self.rel_paths))

    def is_enabled(self, paths=None):
        if not (self.window and self.window.folders()):
            return False
        paths = paths or self.current_paths()
        if not paths:
            return False
        folder, rel_paths = git_rel_paths(self.window, paths)
        return bool(folder and rel_paths and has_changes_to_add(folder, rel_paths))


class GitextAddCommand(sublime_plugin.WindowCommand):
    def run(self, paths=None):
        folder = resolve_folder(self.window, paths)
        if not folder:
            show_popup(self.window, "No folder open", "Error")
            return

        def add_callback(output, error):
            if output:
                show_popup(self.window, output, "Git Add")
            elif error:
                show_popup(self.window, error, "Error")

        run_git_command(["add", "."], folder, add_callback)

    def is_enabled(self, paths=None):
        # Проверяем, есть ли изменения для добавления
        folder = resolve_folder(self.window, paths)
        if not folder:
            return False

        # Команда активна, если есть неотслеживаемые или измененные файлы
        output = get_git_status(folder)
        return any(line.startswith(('??', ' M', ' D', ' A')) for line in output.splitlines())

import os

import sublime_plugin

from .GitExt import get_git_status, run_git_command, show_popup


class GitextInitCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0]
        run_git_command(["init"], folder, lambda output, error: self.after_init(folder, output, error))

    def after_init(self, folder, output, error):
        if error:
            show_popup(self.window, error, "Error")
            return

        # Создаём .gitignore, если его нет
        gitignore_path = os.path.join(folder, ".gitignore")
        if not os.path.exists(gitignore_path):
            rules = [
                "# OS files",
                ".DS_Store",
                "Thumbs.db",
                "",
                "# Python",
                "__pycache__/",
                "*.py[cod]",
                "*.pyo",
                "*.pyd",
                "*.env",
                ".env",
                "env/",
                "venv/",
                "",
                "# Node",
                "node_modules/",
                "npm-debug.log",
                "yarn-error.log",
                "",
                "# IDE",
                ".idea/",
                ".vscode/",
                "*.sublime-project",
                "*.sublime-workspace",
                "",
                "# Logs",
                "*.log",
                "",
                "# Compiled",
                "dist/",
                "build/",
                "*.egg-info/",
                "",
                "# Archives",
                "*.zip",
                "*.rar",
                "*.7z",
                "*.gz",
            ]
            try:
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(rules) + "\n")
            except Exception as e:
                show_popup(self.window, str(e), "Error")
                return

        show_popup(self.window, output, "Git Init")

    def is_enabled(self):
        if not self.window.folders():
            return False
        res = get_git_status(self.window.folders()[0])
        print('GitExt Init is_enabled', res)
        return 'not a git repository' in res

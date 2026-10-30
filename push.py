import sublime_plugin

from .lib.git import run_git_command
from .lib.ui import show_popup


class GitextPushCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0]

        def get_remotes_callback(output, error):
            if error:
                show_popup(self.window, error, "Error")
                return

            remotes = [line.split('\t')[0] for line in output.splitlines() if line]

            if not remotes:
                show_popup(self.window, "No remote repositories found", "Error")
                return

            def on_remote_select(index):
                if index == -1:
                    return

                remote = remotes[index]

                # Получаем текущую ветку
                def get_current_branch_callback(output, error):
                    if error:
                        show_popup(self.window, error, "Error")
                        return

                    current_branch = output.strip()
                    if not current_branch:
                        show_popup(self.window, "Could not determine current branch", "Error")
                        return

                    # Выполняем push
                    run_git_command(
                        ["push", remote, current_branch], 
                        folder, 
                        lambda output, error: show_popup(
                            self.window, 
                            f"Pushed to {remote}/{current_branch}" if output else error,
                            "Success" if output else "Error"
                        )
                    )

                run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], folder, get_current_branch_callback)

            self.window.show_quick_panel(remotes, on_remote_select)

        run_git_command(["remote"], folder, get_remotes_callback)

    def is_enabled(self):
        return bool(self.window.folders())

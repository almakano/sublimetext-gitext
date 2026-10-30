import sublime
import sublime_plugin

from .lib.git import run_git_command, run_git_sync
from .lib.ui import show_popup


class GitextBranchCommand(sublime_plugin.WindowCommand):
    def run(self):
        folder = self.window.folders()[0]

        def callback(output, error):
            if error:
                show_popup(self.window, error, "Error")
                return

            branches = [line.strip().replace("* ", "") for line in output.splitlines() if line.strip()]
            items = []

            for b in branches:
                is_remote = b.startswith("remotes/")
                local_name = b.split("/")[-1] if is_remote else b
                items.append([local_name, "Remote" if is_remote else "Local"])

            def on_select(index):
                if index == -1:
                    return
                branch = branches[index]
                local_branch = branch.split("/")[-1]
                is_remote = branch.startswith("remotes/")

                actions = []

                if is_remote:
                    if not self.branch_exists_local(folder, local_branch):
                        actions.append("Checkout")
                    actions.append("Delete remote")
                else:
                    actions.append("Checkout")
                    actions.append("Delete local")

                def on_action(i):
                    if i == -1:
                        return
                    action = actions[i]

                    def action_callback(output, error):
                        if error:
                            show_popup(self.window, error, "Error")
                        else:
                            sublime.status_message(action + " " + local_branch)

                    if action == "Checkout":
                        run_git_command(["checkout", local_branch], folder, action_callback)
                    elif action == "Delete local":
                        run_git_command(["branch", "-d", local_branch], folder, action_callback)
                    elif action == "Delete remote":
                        remote, name = branch.split("/")[1], branch.split("/")[-1]
                        run_git_command(["push", remote, "--delete", name], folder, action_callback)

                self.window.show_quick_panel(actions, on_action)

            self.window.show_quick_panel(items, on_select)

        run_git_command(["branch", "--all"], folder, callback)

    def branch_exists_local(self, folder, name):
        try:
            output = run_git_sync(["branch"], folder)
            return name in output
        except Exception:
            return False

    def is_enabled(self):
        return bool(self.window.folders())

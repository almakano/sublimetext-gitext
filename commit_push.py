import sublime_plugin

from .lib.git import get_git_status_lines, resolve_folder, run_git_command
from .lib.ui import show_popup


class GitextCommitPushCommand(sublime_plugin.WindowCommand):
    def run(self, paths=None):
        folder = resolve_folder(self.window, paths)
        if not folder:
            show_popup(self.window, "No folder open", "Error")
            return
        self.folder = folder
        self.window.show_input_panel("Commit message:", "", self.do_add, None, None)

    def do_add(self, message):
        if not message.strip():
            show_popup(self.window, "Empty commit message", "Git Commit")
            return
        self.commit_message = message
        run_git_command(["add", "."], self.folder, self.do_commit)

    def do_commit(self, output, error):
        run_git_command(["commit", "-m", self.commit_message], self.folder, self.after_commit)

    def after_commit(self, output, error):
        if error and "nothing to commit" in error.lower():
            show_popup(self.window, error, "Git Commit")
            return
        run_git_command(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], self.folder, self.check_upstream)

    def check_upstream(self, output, error):
        if error and "no upstream" in error.lower():
            run_git_command(["branch", "-r"], self.folder, self.show_remote_branches)
        else:
            run_git_command(["push"], self.folder, lambda o, e: show_popup(self.window, o if o else e, "Git Push"))

    def show_remote_branches(self, output, error):
        if error:
            show_popup(self.window, error, "Error")
            return
        branches = [b.strip() for b in output.splitlines() if b.strip()]
        self.branches = branches
        self.window.show_quick_panel(branches, self.on_branch_selected)

    def on_branch_selected(self, index):
        if index == -1:
            return
        branch_full = self.branches[index]  # например: upstream/feature-x
        parts = branch_full.split("/", 1)
        if len(parts) == 2:
            remote, branch = parts
        else:
            remote, branch = "origin", branch_full
        run_git_command(["push", "-u", remote, branch], self.folder,
                        lambda o, e: show_popup(self.window, o if o else e, "Git Push with upstream"))

    def is_enabled(self, paths=None):
        folder = resolve_folder(self.window, paths)
        return bool(folder and get_git_status_lines(folder))
